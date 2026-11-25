from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from app import watchlist_csv
from recommender.catalog import Movie

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("TMDB_READ_ACCESS_TOKEN", "")
    return AppTest.from_file(str(APP_PATH), default_timeout=25)


def test_discovery_watchlist_and_filters(app):
    app.run()
    assert not app.exception
    assert app.header[0].value == "Top rated"

    example = next(
        button for button in app.button if button.label == "Try Inception + Interstellar"
    )
    example.click().run()
    assert not app.exception
    assert app.query_params["movie"] == ["27205", "157336"]
    assert app.header[0].value == "Recommended for you"
    assert len([button for button in app.button if button.label == "Save to watchlist"]) == 6

    app.selectbox(key="genre").select("Science Fiction").run()
    saved_film = next(button for button in app.button if button.label == "Save to watchlist")
    key = saved_film.key
    saved_film.click().run()
    assert app.button(key=key).label == "Remove from watchlist"

    app.get("button_group")[0].set_value("Watchlist").run()
    assert not app.exception
    assert app.header[0].value == "Your watchlist"
    assert app.get("download_button")[0].proto.label == "Download CSV"
    app.button(key=key).click().run()
    assert app.info[0].value.startswith("Save films")

    app.get("button_group")[0].set_value("Discover").run()
    assert not app.exception
    assert app.multiselect(key="seeds").value == [27205, 157336]
    assert app.selectbox(key="genre").value == "Science Fiction"
    app.selectbox(key="genre").select(None).run()
    app.multiselect(key="seeds").unselect(27205).unselect(157336).run()
    assert "movie" not in app.query_params
    assert app.header[0].value == "Top rated"


def test_shareable_links_ignore_bad_and_repeated_ids(app):
    app.query_params["movie"] = ["nothing", "27205", "27205", "1231231234", "157336", "155", "77"]
    app.run()
    assert not app.exception
    assert app.multiselect(key="seeds").value == [27205, 157336, 155]
    assert app.header[0].value == "Recommended for you"


def test_csv_keeps_non_english_titles_and_escapes_formulas():
    csv_data = watchlist_csv([Movie(1, "=Film", 2009), Movie(2, "Amélie")])
    assert csv_data.startswith(b"\xef\xbb\xbf")
    lines = csv_data.decode("utf-8-sig").splitlines()
    assert lines == [
        "tmdb_id,title,year,tmdb_url",
        "1,'=Film,2009,https://www.themoviedb.org/movie/1",
        "2,Amélie,,https://www.themoviedb.org/movie/2",
    ]
