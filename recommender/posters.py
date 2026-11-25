"""Optional poster lookups. Failures leave the movie cards usable."""

import re
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor

import requests

POSTER_FILENAME = re.compile(r"/[a-zA-Z0-9_-]+\.(?:jpg|jpeg|png)")


def _poster_url(movie_id: int, token: str) -> str | None:
    try:
        response = requests.get(
            f"https://api.themoviedb.org/3/movie/{movie_id}",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            timeout=(2, 2),
            allow_redirects=False,
        )
        if response.status_code != 200:
            return None
        data = response.json()
    except (requests.RequestException, ValueError):
        return None
    path = data.get("poster_path") if isinstance(data, dict) else None
    if isinstance(path, str) and POSTER_FILENAME.fullmatch(path):
        return f"https://image.tmdb.org/t/p/w342{path}"
    return None


def poster_urls(movie_ids: Iterable[int], token: str) -> dict[int, str]:
    ids = tuple(dict.fromkeys(movie_ids))
    if not ids or not token:
        return {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        urls = executor.map(_poster_url, ids, (token for _ in ids))
        return {movie_id: url for movie_id, url in zip(ids, urls, strict=True) if url}
