from pathlib import Path

import pytest

from recommender.catalog import Movie, load_movies
from recommender.engine import Filters, Recommender


@pytest.fixture
def engine():
    return Recommender(
        [
            Movie(
                1,
                "The Signal",
                2014,
                "Astronauts land on an icy moon.",
                ("Science Fiction",),
                ("space",),
                directors=("Alex Lane",),
            ),
            Movie(
                2,
                "The Signal",
                1990,
                "A detective searches a city.",
                ("Crime",),
                rating=9.8,
                votes=1,
            ),
            Movie(
                3,
                "Ice Moon",
                2015,
                "Astronauts find ice on a moon.",
                ("Science Fiction",),
                ("space",),
                directors=("Alex Lane",),
                rating=8.3,
                votes=500,
            ),
            Movie(
                4,
                "Ice Moon II",
                2016,
                "Astronauts find ice on a moon.",
                ("Science Fiction",),
                ("space",),
                directors=("Alex Lane",),
                rating=7.9,
                votes=800,
            ),
            Movie(
                5,
                "The Long Orbit",
                2018,
                "A mission beyond the stars.",
                ("Science Fiction",),
                ("space", "exploration"),
                rating=7.8,
                votes=400,
            ),
            Movie(
                6,
                "City Nights",
                None,
                "A detective searches a city.",
                ("Crime",),
                rating=8.0,
                votes=250,
            ),
        ]
    )


def test_duplicate_titles_resolve_by_id_and_exclude_all_seeds(engine):
    assert engine.recommend([2])[0].movie.id == 6
    match = engine.recommend([1, 2])[0]
    assert match.movie.id == 4
    assert match.closest_seed.id == 1
    assert "Director: Alex Lane" in match.reasons
    assert "Themes: space" in match.reasons
    assert 0 < match.similarity < 1
    assert engine.recommend([1, 1]) == engine.recommend([1])


def test_filters_apply_before_ranking_and_missing_dates_are_handled(engine):
    filters = Filters(genre="Science Fiction", start_year=2016, end_year=2018, min_votes=500)
    assert [match.movie.id for match in engine.recommend([1], filters)] == [4]
    assert [movie.id for movie in engine.top_rated(filters)] == [4]
    assert engine.recommend([2], Filters(start_year=1980)) == []
    assert engine.recommend([2], Filters(genre="Horror")) == []


def test_diversified_ranking_penalizes_near_duplicates():
    space, adventure = ("Science Fiction",), ("Adventure",)
    engine = Recommender(
        [
            Movie(1, "Flight", genres=space),
            Movie(2, "Flight II", genres=space),
            Movie(3, "Flight III", genres=space),
            Movie(4, "Lost Treasure", genres=adventure),
            Movie(5, "Abandoned Temple", genres=adventure),
        ]
    )
    assert [match.movie.id for match in engine.recommend([1, 5], limit=2)] == [2, 3]
    diverse = engine.recommend([1, 5], limit=2, diversify=True)
    assert [match.movie.id for match in diverse] == [2, 4]


def test_top_rated_uses_vote_counts(engine):
    ranked = engine.top_rated()
    assert ranked[0].id == 3
    assert ranked[0].rating < engine.by_id[2].rating


def test_empty_features_and_invalid_seeds():
    engine = Recommender([Movie(1, "Empty"), Movie(2, "Stop words", overview="the a")])
    assert engine.recommend([1]) == []
    assert engine.recommend([]) == []
    assert engine.top_rated() == []
    with pytest.raises(ValueError, match="Every seed"):
        engine.recommend([99])
    with pytest.raises(ValueError, match="unique"):
        Recommender([Movie(1, "First"), Movie(1, "Repeat")])


def test_bundled_catalog_joins_by_tmdb_id():
    movies = load_movies(Path(__file__).resolve().parents[1])
    index = Recommender(movies)
    assert len(index.movies) == 4803
    assert index.year_range == (1916, 2017)
    assert index.by_id[27205].title == "Inception"
    assert index.by_id[27205].directors == ("Christopher Nolan",)
    assert {movie.year for movie in movies if movie.title == "Batman"} == {1966, 1989}
    assert index.recommend([27205], limit=6)[0].similarity > 0
