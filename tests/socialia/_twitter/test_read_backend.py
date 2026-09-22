"""Tests for the optional Xquik Twitter read backend."""

from socialia._twitter.read_backend import XquikReadBackend

from tests.conftest import FakeResponse


class FakeHTTP:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.response


class TestXquikReadBackend:
    def test_available_returns_false_without_api_key(self):
        # Arrange
        backend = XquikReadBackend(api_key="", http=FakeHTTP(FakeResponse(200)))
        # Act
        available = backend.available()
        # Assert
        assert available is False

    def test_search_uses_x_api_key_header_for_xquik_keys(self):
        # Arrange
        http = FakeHTTP(
            FakeResponse(
                200,
                json_data={
                    "tweets": [
                        {
                            "id": "1",
                            "text": "hello",
                            "author": {"username": "alice"},
                        }
                    ]
                },
            )
        )
        backend = XquikReadBackend(
            api_key="xq_test", base_url="https://x", http=http
        )
        # Act
        backend.search_tweets("agents", limit=3)
        # Assert
        assert http.calls[0][1]["headers"]["X-API-Key"] == "xq_test"

    def test_search_uses_x_api_key_header_for_other_keys(self):
        # Arrange
        http = FakeHTTP(FakeResponse(200, json_data={"tweets": []}))
        backend = XquikReadBackend(
            api_key="token", base_url="https://x", http=http
        )
        # Act
        backend.search_tweets("agents")
        # Assert
        assert http.calls[0][1]["headers"]["X-API-Key"] == "token"

    def test_search_normalizes_tweets(self):
        # Arrange
        http = FakeHTTP(
            FakeResponse(
                200,
                json_data={
                    "data": [
                        {
                            "tweetId": "42",
                            "fullText": "Research thread",
                            "createdAt": "2026-01-01T00:00:00Z",
                            "user": {"username": "alice", "name": "Alice"},
                            "metrics": {"like_count": 7, "retweet_count": 2},
                        }
                    ]
                },
            )
        )
        backend = XquikReadBackend(
            api_key="xq_test", base_url="https://x", http=http
        )
        # Act
        result = backend.search_tweets("research")
        tweet = result["tweets"][0]
        # Assert
        assert (tweet["id"], tweet["author_username"], tweet["likes"]) == (
            "42",
            "alice",
            7,
        )

    def test_user_tweets_builds_user_tweets_path(self):
        # Arrange
        http = FakeHTTP(FakeResponse(200, json_data={"tweets": []}))
        backend = XquikReadBackend(
            api_key="xq_test", base_url="https://x", http=http
        )
        # Act
        backend.user_tweets("@alice", limit=5)
        # Assert
        assert (http.calls[0][0][0], http.calls[0][1]["params"]) == (
            "https://x/api/v1/x/users/alice/tweets",
            {"includeReplies": "false"},
        )

    def test_error_status_returns_failure(self):
        # Arrange
        http = FakeHTTP(
            FakeResponse(402, json_data={"error": "credits"}, text="Payment")
        )
        backend = XquikReadBackend(
            api_key="xq_test", base_url="https://x", http=http
        )
        # Act
        result = backend.search_tweets("research")
        # Assert
        assert result["success"] is False
