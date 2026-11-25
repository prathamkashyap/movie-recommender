"""Read the original TMDB export and join movie metadata to credits by ID."""

import csv
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import TypedDict


class Credit(TypedDict, total=False):
    name: str
    job: str


@dataclass(frozen=True, slots=True)
class Movie:
    id: int
    title: str
    year: int | None = None
    overview: str = ""
    genres: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    cast: tuple[str, ...] = ()
    directors: tuple[str, ...] = ()
    runtime: int | None = None
    rating: float = 0
    votes: int = 0

    @property
    def url(self) -> str:
        return f"https://www.themoviedb.org/movie/{self.id}"


def _names(entries: list[Credit]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(entry["name"] for entry in entries if entry.get("name")))


def _credits(row: dict[str, str]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    cast = json.loads(row["cast"] or "[]")
    crew = json.loads(row["crew"] or "[]")
    return _names(cast[:5]), _names([person for person in crew if person.get("job") == "Director"])


def load_movies(data_dir: Path) -> tuple[Movie, ...]:
    with (data_dir / "tmdb_5000_credits.csv").open(encoding="utf-8-sig", newline="") as file:
        credits = {int(row["movie_id"]): _credits(row) for row in csv.DictReader(file)}

    movies = []
    with (data_dir / "tmdb_5000_movies.csv").open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            movie_id = int(row["id"])
            cast, directors = credits.get(movie_id, ((), ()))
            runtime = int(float(row["runtime"] or 0))
            release = row["release_date"]
            movies.append(
                Movie(
                    id=movie_id,
                    title=row["title"],
                    year=date.fromisoformat(release).year if release else None,
                    overview=row["overview"],
                    genres=_names(json.loads(row["genres"] or "[]")),
                    keywords=_names(json.loads(row["keywords"] or "[]")),
                    cast=cast,
                    directors=directors,
                    runtime=runtime or None,
                    rating=float(row["vote_average"] or 0),
                    votes=int(row["vote_count"] or 0),
                )
            )
    movies.sort(key=lambda movie: (movie.title.casefold(), movie.year or 0, movie.id))
    return tuple(movies)
