from unittest.mock import Mock

import requests

from recommender.posters import poster_urls


def test_no_token_means_no_network(monkeypatch):
    lookup = Mock(side_effect=AssertionError("Network request without a token"))
    monkeypatch.setattr(requests, "get", lookup)
    assert poster_urls([27205], "") == {}
    lookup.assert_not_called()


def test_failed_and_malformed_posters_do_not_block_valid_results(monkeypatch):
    responses = {
        1: Mock(status_code=200, **{"json.return_value": {"poster_path": "/inception.jpg"}}),
        2: Mock(status_code=429),
        3: Mock(status_code=200, **{"json.return_value": {"poster_path": None}}),
        4: Mock(status_code=200, **{"json.return_value": {"poster_path": "//other.host/a.jpg"}}),
        5: Mock(status_code=200, **{"json.return_value": ["invalid response"]}),
        6: Mock(status_code=200, **{"json.side_effect": ValueError("Invalid JSON")}),
    }

    def lookup(url, **options):
        assert url.startswith("https://api.themoviedb.org/3/movie/")
        assert options["headers"]["Authorization"] == "Bearer test-token"
        assert options["allow_redirects"] is False
        assert options["timeout"] == (2, 2)
        movie_id = int(url.rsplit("/", 1)[-1])
        if movie_id == 7:
            raise requests.Timeout
        return responses[movie_id]

    monkeypatch.setattr(requests, "get", lookup)
    assert poster_urls(range(1, 8), "test-token") == {
        1: "https://image.tmdb.org/t/p/w342/inception.jpg"
    }
