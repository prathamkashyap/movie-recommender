"""Weighted content similarity and ranking with a sparse catalog index."""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from math import sqrt
from types import MappingProxyType

import numpy as np
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer

from recommender.catalog import Movie

METADATA_WEIGHTS = {"genres": 0.18, "keywords": 0.30, "cast": 0.08, "directors": 0.12}
OVERVIEW_WEIGHT = 0.32
RATING_PRIOR_VOTES = 100
DIVERSITY_PENALTY = 0.30


@dataclass(frozen=True, slots=True)
class Filters:
    genre: str | None = None
    start_year: int | None = None
    end_year: int | None = None
    min_votes: int = 0

    def matches(self, movie: Movie) -> bool:
        if movie.year is None and (self.start_year is not None or self.end_year is not None):
            return False
        return (
            (self.genre is None or self.genre in movie.genres)
            and (self.start_year is None or movie.year >= self.start_year)
            and (self.end_year is None or movie.year <= self.end_year)
            and movie.votes >= self.min_votes
        )


@dataclass(frozen=True, slots=True)
class Match:
    movie: Movie
    similarity: float
    closest_seed: Movie
    reasons: tuple[str, ...]


def _metadata_tokens(values: Sequence[str]) -> list[str]:
    return [value.casefold() for value in values]


def _overview_matrix(movies: Sequence[Movie]) -> csr_matrix:
    vectorizer = TfidfVectorizer(
        dtype=np.float32, strip_accents="unicode", stop_words="english", ngram_range=(1, 2)
    )
    # A catalog can contain empty overviews or overviews with only stop words.
    analyzer = vectorizer.build_analyzer()
    overviews = [movie.overview for movie in movies]
    if not any(analyzer(overview) for overview in overviews):
        return csr_matrix((len(movies), 0), dtype=np.float32)
    return vectorizer.fit_transform(overviews)


def _shared(candidate: Sequence[str], seed: Sequence[str]) -> list[str]:
    seed_tokens = set(_metadata_tokens(seed))
    return [value for value in candidate if value.casefold() in seed_tokens]


def _explain(movie: Movie, seed: Movie) -> tuple[str, ...]:
    reasons = []
    for field, label, limit in (
        ("directors", "Director", 2),
        ("keywords", "Themes", 3),
        ("genres", "Genres", 2),
        ("cast", "Cast", 2),
    ):
        values = _shared(getattr(movie, field), getattr(seed, field))[:limit]
        if values:
            reasons.append(f"{label}: {', '.join(values)}")
    return tuple(reasons) or ("Similar plot language",)


class Recommender:
    """Build once and serve read-only queries using numeric TMDB IDs."""

    def __init__(self, movies: Iterable[Movie]):
        self.movies = tuple(movies)
        self._positions = {movie.id: index for index, movie in enumerate(self.movies)}
        if not self.movies or len(self._positions) != len(self.movies):
            raise ValueError("The catalog must contain movies with unique TMDB IDs.")
        self.by_id = MappingProxyType({movie.id: movie for movie in self.movies})
        self.genres = tuple(sorted({genre for movie in self.movies for genre in movie.genres}))
        years = [movie.year for movie in self.movies if movie.year is not None]
        self.year_range = (min(years), max(years)) if years else None

        blocks = [_overview_matrix(self.movies) * sqrt(OVERVIEW_WEIGHT)]
        for field, weight in METADATA_WEIGHTS.items():
            values = [getattr(movie, field) for movie in self.movies]
            if any(values):
                vectorizer = TfidfVectorizer(analyzer=_metadata_tokens, dtype=np.float32)
                blocks.append(vectorizer.fit_transform(values) * sqrt(weight))
        self._features = hstack(blocks, format="csr", dtype=np.float32)
        total_votes = sum(movie.votes for movie in self.movies)
        self._average_rating = (
            sum(movie.rating * movie.votes for movie in self.movies) / total_votes
            if total_votes
            else 0.0
        )

    def _adjusted_rating(self, movie: Movie) -> float:
        return (movie.votes * movie.rating + RATING_PRIOR_VOTES * self._average_rating) / (
            movie.votes + RATING_PRIOR_VOTES
        )

    def top_rated(self, filters: Filters = Filters(), limit: int = 6) -> list[Movie]:
        candidates = [movie for movie in self.movies if movie.votes and filters.matches(movie)]
        return sorted(
            candidates, key=lambda movie: (-self._adjusted_rating(movie), -movie.votes, movie.id)
        )[: max(0, limit)]

    def recommend(
        self,
        seed_ids: Sequence[int],
        filters: Filters = Filters(),
        limit: int = 6,
        diversify: bool = False,
    ) -> list[Match]:
        seed_ids = tuple(dict.fromkeys(seed_ids))
        if any(movie_id not in self.by_id for movie_id in seed_ids):
            raise ValueError("Every seed must be a movie in the catalog.")
        if not seed_ids or limit <= 0:
            return []

        seed_positions = [self._positions[movie_id] for movie_id in seed_ids]
        similarities = (self._features @ self._features[seed_positions].T).toarray()
        relevance = similarities.mean(axis=1)
        selected = set(seed_positions)
        candidates = [
            i
            for i, movie in enumerate(self.movies)
            if i not in selected and relevance[i] > 0 and filters.matches(movie)
        ]
        candidates.sort(key=lambda i: (-relevance[i], -self.movies[i].votes, self.movies[i].id))
        ranked = self._diversify(candidates, relevance, limit) if diversify else candidates[:limit]
        matches = []
        for i in ranked:
            movie = self.movies[i]
            seed = self.movies[seed_positions[int(similarities[i].argmax())]]
            matches.append(Match(movie, min(1.0, float(relevance[i])), seed, _explain(movie, seed)))
        return matches

    def _diversify(self, candidates: list[int], relevance: np.ndarray, limit: int) -> list[int]:
        ranked = []
        redundancy = np.zeros(len(self.movies), dtype=np.float32)
        # Stable candidate order breaks ties by unadjusted relevance, votes and ID.
        while candidates and len(ranked) < limit:
            best = max(candidates, key=lambda i: relevance[i] - DIVERSITY_PENALTY * redundancy[i])
            ranked.append(best)
            candidates.remove(best)
            if candidates and len(ranked) < limit:
                similarity = (self._features @ self._features[best].T).toarray().ravel()
                np.maximum(redundancy, similarity, out=redundancy)
        return ranked
