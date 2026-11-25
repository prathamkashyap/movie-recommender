import csv
import io
import os
from collections import Counter
from html import escape
from pathlib import Path
from textwrap import shorten

import streamlit as st

from recommender.catalog import Movie, load_movies
from recommender.engine import Filters, Match, Recommender
from recommender.posters import poster_urls

ROOT = Path(__file__).resolve().parent
DATASET_URL = "https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata"
MAX_SEEDS = 3
DISCOVER_WIDGETS = ("seeds", "genre", "min_votes", "count", "years", "diversify")


@st.cache_resource(show_spinner="Loading movie catalog…")
def get_recommender() -> Recommender:
    return Recommender(load_movies(ROOT))


@st.cache_data(ttl=1800, max_entries=256, show_spinner=False)
def get_posters(ids: tuple[int, ...], token: str) -> dict[int, str]:
    return poster_urls(ids, token)


def get_poster_token() -> str:
    token = os.getenv("TMDB_READ_ACCESS_TOKEN")
    if token is None:
        try:
            token = st.secrets.get("TMDB_READ_ACCESS_TOKEN", "")
        except FileNotFoundError:
            token = ""
    return token.strip()


def title_label(movie: Movie, disambiguate: bool = False) -> str:
    year = movie.year if movie.year is not None else "year unknown"
    label = f"{movie.title} · {year}"
    return f"{label} · TMDB {movie.id}" if disambiguate else label


def _seed_ids_from_url(engine: Recommender) -> list[int]:
    seeds = []
    for value in st.query_params.get_all("movie"):
        if not value.isascii() or not value.isdecimal() or len(value) > 10:
            continue
        movie_id = int(value)
        if movie_id in engine.by_id and movie_id not in seeds:
            seeds.append(movie_id)
        if len(seeds) == MAX_SEEDS:
            break
    return seeds


def update_seed_url() -> None:
    ids = st.session_state.seeds
    if ids:
        st.query_params["movie"] = [str(movie_id) for movie_id in ids]
    elif "movie" in st.query_params:
        del st.query_params["movie"]


def use_example() -> None:
    st.session_state.seeds = [27205, 157336]
    update_seed_url()


def toggle_watchlist(movie_id: int) -> None:
    watchlist = st.session_state.watchlist
    if movie_id in watchlist:
        watchlist.remove(movie_id)
    else:
        watchlist.append(movie_id)


def filter_options(engine: Recommender) -> tuple[Filters, int]:
    with st.expander("Filters & result count"):
        genre_col, votes_col, count_col = st.columns(3)
        genre = genre_col.selectbox(
            "Genre", (None, *engine.genres), format_func=lambda v: v or "All genres", key="genre"
        )
        votes = votes_col.selectbox("Minimum TMDB votes", (0, 100, 500, 1000), key="min_votes")
        count = count_col.selectbox("Films to show", (6, 12, 18), key="count")
        start, end = None, None
        if engine.year_range and engine.year_range[0] < engine.year_range[1]:
            earliest, latest = engine.year_range
            chosen = st.slider("Release years", earliest, latest, (earliest, latest), key="years")
            if chosen != engine.year_range:
                start, end = chosen
    return Filters(genre, start, end, votes), count


def _why(match: Match) -> str:
    closest = escape(title_label(match.closest_seed))
    reasons = " · ".join(escape(reason) for reason in match.reasons)
    return f'<p class="movie-why"><strong>Closest to {closest}</strong><br>{reasons}</p>'


def display_movie(movie: Movie, poster_url: str | None, match: Match | None = None) -> None:
    meta = []
    if movie.year:
        meta.append(f"<span>{movie.year}</span>")
    if movie.runtime:
        meta.append(f"<span>{movie.runtime} min</span>")
    if movie.votes:
        meta.append(
            f'<span class="movie-rating" title="TMDB rating from {movie.votes:,} votes">'
            f"★ {movie.rating:g}/10</span>"
        )
    title = escape(movie.title)
    genres = escape(" · ".join(movie.genres[:3]))
    synopsis = escape(shorten(movie.overview, width=220, placeholder="…"))
    poster = (
        f'<img src="{escape(poster_url, quote=True)}" alt="" loading="lazy">' if poster_url else ""
    )
    reason = _why(match) if match else ""
    layout = "movie-card with-poster" if poster else "movie-card"
    st.html(f"""
        <article class="{layout}">
          {poster}<div>
            <h3><a href="{movie.url}" target="_blank" rel="noopener noreferrer">{title}</a></h3>
            <p class="movie-meta">{"".join(meta)}</p>
            <p class="movie-genres">{genres}</p>
            <p class="movie-overview">{synopsis or "Synopsis unavailable."}</p>
            {reason}
          </div>
        </article>
    """)
    with st.expander(f"More about {movie.title}"):
        st.html(f"<p>{escape(movie.overview or 'Synopsis unavailable.')}</p>")
        if movie.directors:
            st.text("Directed by " + ", ".join(movie.directors))
        if movie.cast:
            st.text("Cast: " + ", ".join(movie.cast))
        if movie.votes:
            st.caption(f"{movie.votes:,} TMDB votes in the dataset")
    saved = movie.id in st.session_state.watchlist
    st.button(
        "Remove from watchlist" if saved else "Save to watchlist",
        key=f"watch_{movie.id}",
        on_click=toggle_watchlist,
        args=(movie.id,),
        help=f"{'Remove' if saved else 'Save'} {title_label(movie)}",
    )


def show_movies(movies: list[Movie], token: str, matches: dict[int, Match] | None = None) -> None:
    ids = tuple(sorted(movie.id for movie in movies))
    posters = get_posters(ids, token) if token else {}
    for offset in range(0, len(movies), 2):
        for column, movie in zip(st.columns(2), movies[offset : offset + 2], strict=False):
            with column, st.container(border=True):
                match = matches.get(movie.id) if matches else None
                display_movie(movie, posters.get(movie.id), match)


def show_discover(engine: Recommender, token: str) -> None:
    labels = {movie.id: title_label(movie) for movie in engine.movies}
    label_counts = Counter(labels.values())
    for movie_id, label in labels.items():
        if label_counts[label] > 1:
            labels[movie_id] = title_label(engine.by_id[movie_id], disambiguate=True)

    with st.container(border=True):
        seeds = st.multiselect(
            "Start with movies you like",
            options=labels,
            format_func=labels.__getitem__,
            max_selections=MAX_SEEDS,
            placeholder="Search by title…",
            key="seeds",
            on_change=update_seed_url,
        )
        if not seeds and {27205, 157336} <= engine.by_id.keys():
            st.button("Try Inception + Interstellar", on_click=use_example)
        filters, count = filter_options(engine)
        diversify = False
        if seeds:
            diversify = st.toggle(
                "Mix up the results",
                key="diversify",
                help="Reduce similarity between the films in this list.",
            )

    if seeds:
        matches = engine.recommend(seeds, filters, count, diversify=diversify)
        st.header("Recommended for you")
        if matches:
            show_movies([match.movie for match in matches], token, {m.movie.id: m for m in matches})
        else:
            st.info(
                "No similar films fit these filters. Try a broader year range or another genre."
            )
    else:
        st.header("Top rated")
        st.caption(
            "Ranked using TMDB ratings and vote counts. Add a title above to find similar films."
        )
        movies = engine.top_rated(filters, count)
        if movies:
            show_movies(movies, token)
        else:
            st.info("No rated films fit these filters. Try lowering the minimum vote count.")


def _csv_cell(title: str) -> str:
    """Keep titles that begin with a spreadsheet formula marker literal."""
    return f"'{title}" if title.lstrip().startswith(("=", "+", "-", "@")) else title


def watchlist_csv(movies: list[Movie]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(("tmdb_id", "title", "year", "tmdb_url"))
    writer.writerows((movie.id, _csv_cell(movie.title), movie.year, movie.url) for movie in movies)
    return buffer.getvalue().encode("utf-8-sig")


def show_watchlist(engine: Recommender, token: str) -> None:
    st.header("Your watchlist")
    if not st.session_state.watchlist:
        st.info("Save films from Discover to build your watchlist.")
        return
    movies = [engine.by_id[movie_id] for movie_id in st.session_state.watchlist]
    st.caption("Saved for this session. Download a copy to keep it.")
    st.download_button(
        "Download CSV",
        watchlist_csv(movies),
        "movie-watchlist.csv",
        "text/csv",
        on_click="ignore",
    )
    show_movies(movies, token)


def show_about(token: str) -> None:
    with st.expander("About this catalog"):
        st.markdown(
            f"Film metadata and ratings come from the [TMDB 5000 dataset]({DATASET_URL}). "
            "Ratings reflect the snapshot. Recommendations use plot text, genres, keywords, "
            "cast and directors."
        )
        if token:
            st.image(str(ROOT / "static" / "tmdb-logo.svg"), width=100)
            st.caption("This product uses the TMDB API but is not endorsed or certified by TMDB.")


def main() -> None:
    st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="wide")
    st.html(ROOT / "static" / "app.css")
    st.html("""
        <section class="cinema-hero" aria-labelledby="page-title">
          <h1 id="page-title">Movie Recommender</h1>
          <p>Find your next film from the ones you already love.</p>
        </section>
    """)
    try:
        engine = get_recommender()
    except (OSError, ValueError, KeyError, csv.Error):
        st.error("The movie catalog could not load. Check that both TMDB CSVs are beside app.py.")
        st.stop()

    if "watchlist" not in st.session_state:
        st.session_state.watchlist = []
    if "seeds" not in st.session_state:
        st.session_state.seeds = _seed_ids_from_url(engine)
    token = get_poster_token()
    page = st.segmented_control(
        "View",
        ("Discover", "Watchlist"),
        default="Discover",
        required=True,
        label_visibility="collapsed",
    )
    if page == "Watchlist":
        # Streamlit discards state for unmounted widgets unless it is saved explicitly.
        for key in DISCOVER_WIDGETS:
            if key in st.session_state:
                st.session_state[key] = st.session_state[key]
        show_watchlist(engine, token)
    else:
        show_discover(engine, token)
    show_about(token)


if __name__ == "__main__":
    main()
