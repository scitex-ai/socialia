"""Tests for Twitter client.

All collaborators are injected via ``Twitter(session_factory=...)``; tests
construct a hand-rolled ``FakeOAuthSession`` (see ``conftest.py``) and
configure ``FakeResponse`` objects ahead of the call.  No mocks.
"""

import importlib

from socialia.twitter import Twitter

from tests.conftest import FakeResponse


# --- Helpers ----------------------------------------------------------------


def _clear_twitter_env(env, *, set_socialia_prefix: bool = True):
    """Clear every Twitter credential env var across known prefixes.

    Tests that exercise the credential-fallback paths need a clean slate;
    this helper centralises the brand-prefix bookkeeping so the per-test
    bodies stay focused on a single Act + Assert.
    """
    env.delete("SOCIALIA_ENV_PREFIX")
    for prefix in ("SOCIALIA", "SCITEX", "SCITEX_SOCIAL"):
        for suffix in (
            "X_CONSUMER_KEY",
            "X_CONSUMER_KEY_SECRET",
            "X_ACCESSTOKEN",
            "X_ACCESSTOKEN_SECRET",
        ):
            env.delete(f"{prefix}_{suffix}")
    # Reload branding so prefix changes take effect.
    from socialia import _branding

    importlib.reload(_branding)


class FakeReadBackend:
    def __init__(self) -> None:
        self.calls = []

    def available(self) -> bool:
        return True

    def search_tweets(
        self, query: str, limit: int = 10, include_users: bool = True
    ) -> dict:
        self.calls.append(("search_tweets", query, limit, include_users))
        return {"success": True, "tweets": [{"id": "1", "text": query}], "count": 1}

    def user_tweets(self, username: str, limit: int = 10) -> dict:
        self.calls.append(("user_tweets", username, limit))
        return {"success": True, "tweets": [{"id": "2", "text": username}], "count": 1}

    def mentions(self, username: str, limit: int = 10) -> dict:
        self.calls.append(("mentions", username, limit))
        return {"success": True, "mentions": [{"id": "3"}], "count": 1}

    def replies(self, username: str, limit: int = 10) -> dict:
        self.calls.append(("replies", username, limit))
        return {"success": True, "replies": [{"id": "4"}], "count": 1}


# --- Initialisation ---------------------------------------------------------


class TestTwitterInit:
    def test_init_with_credentials_records_consumer_key(self, twitter_credentials):
        # Arrange
        creds = twitter_credentials
        # Act
        client = Twitter(**creds)
        # Assert
        assert client.consumer_key == "test_consumer_key"

    def test_init_with_credentials_records_consumer_secret(self, twitter_credentials):
        # Arrange
        creds = twitter_credentials
        # Act
        client = Twitter(**creds)
        # Assert
        assert client.consumer_secret == "test_consumer_secret"

    def test_init_with_credentials_records_access_token(self, twitter_credentials):
        # Arrange
        creds = twitter_credentials
        # Act
        client = Twitter(**creds)
        # Assert
        assert client.access_token == "test_access_token"

    def test_init_with_credentials_records_access_token_secret(
        self, twitter_credentials
    ):
        # Arrange
        creds = twitter_credentials
        # Act
        client = Twitter(**creds)
        # Assert
        assert client.access_token_secret == "test_access_token_secret"

    def test_init_from_environment_reads_consumer_key(self, env_save_restore):
        # Arrange
        _clear_twitter_env(env_save_restore)
        env_save_restore.set("SOCIALIA_X_CONSUMER_KEY", "env_consumer_key")
        env_save_restore.set("SOCIALIA_X_CONSUMER_KEY_SECRET", "env_consumer_secret")
        env_save_restore.set("SOCIALIA_X_ACCESSTOKEN", "env_access_token")
        env_save_restore.set("SOCIALIA_X_ACCESSTOKEN_SECRET", "env_access_secret")
        # Act
        client = Twitter()
        # Assert
        assert client.consumer_key == "env_consumer_key"

    def test_init_from_environment_reads_consumer_secret(self, env_save_restore):
        # Arrange
        _clear_twitter_env(env_save_restore)
        env_save_restore.set("SOCIALIA_X_CONSUMER_KEY", "env_consumer_key")
        env_save_restore.set("SOCIALIA_X_CONSUMER_KEY_SECRET", "env_consumer_secret")
        env_save_restore.set("SOCIALIA_X_ACCESSTOKEN", "env_access_token")
        env_save_restore.set("SOCIALIA_X_ACCESSTOKEN_SECRET", "env_access_secret")
        # Act
        client = Twitter()
        # Assert
        assert client.consumer_secret == "env_consumer_secret"


# --- Validation -------------------------------------------------------------


class TestTwitterValidateCredentials:
    def test_validate_credentials_returns_true_when_all_set(self, twitter_credentials):
        # Arrange
        client = Twitter(**twitter_credentials)
        # Act
        ok = client.validate_credentials()
        # Assert
        assert ok is True

    def test_validate_credentials_returns_false_when_only_one_set(
        self, env_save_restore
    ):
        # Arrange
        _clear_twitter_env(env_save_restore)
        client = Twitter(consumer_key="only_one")
        # Act
        ok = client.validate_credentials()
        # Assert
        assert ok is False


class TestTwitterReadBackend:
    def test_search_tweets_uses_read_backend_without_oauth(self, env_save_restore):
        # Arrange
        _clear_twitter_env(env_save_restore)
        backend = FakeReadBackend()
        client = Twitter(read_backend=backend)
        # Act
        result = client.search_tweets("ai agents", limit=3)
        # Assert
        assert (result["success"], backend.calls[0]) == (
            True,
            ("search_tweets", "ai agents", 3, True),
        )

    def test_feed_uses_read_backend_when_username_is_set(self, env_save_restore):
        # Arrange
        _clear_twitter_env(env_save_restore)
        backend = FakeReadBackend()
        client = Twitter(read_backend=backend, read_username="@alice")
        # Act
        result = client.feed(limit=5)
        # Assert
        assert (result["success"], backend.calls[0]) == (
            True,
            ("user_tweets", "alice", 5),
        )

    def test_mentions_uses_read_backend_when_username_is_set(self, env_save_restore):
        # Arrange
        _clear_twitter_env(env_save_restore)
        backend = FakeReadBackend()
        client = Twitter(read_backend=backend, read_username="alice")
        # Act
        result = client.mentions(limit=5)
        # Assert
        assert (result["success"], backend.calls[0]) == (
            True,
            ("mentions", "alice", 5),
        )

    def test_replies_uses_read_backend_when_username_is_set(self, env_save_restore):
        # Arrange
        _clear_twitter_env(env_save_restore)
        backend = FakeReadBackend()
        client = Twitter(read_backend=backend, read_username="alice")
        # Act
        result = client.replies(limit=5)
        # Assert
        assert (result["success"], backend.calls[0]) == (
            True,
            ("replies", "alice", 5),
        )

    def test_validate_read_credentials_needs_username_for_backend(
        self, env_save_restore
    ):
        # Arrange
        _clear_twitter_env(env_save_restore)
        client = Twitter(read_backend=FakeReadBackend())
        # Act
        ok = client.validate_read_credentials()
        # Assert
        assert ok is False


# --- Posting ---------------------------------------------------------------


class TestTwitterPost:
    def test_post_without_credentials_reports_success_false(self, env_save_restore):
        # Arrange
        _clear_twitter_env(env_save_restore)
        client = Twitter()
        # Act
        result = client.post("Test")
        # Assert
        assert result["success"] is False

    def test_post_without_credentials_error_mentions_credentials(
        self, env_save_restore
    ):
        # Arrange
        _clear_twitter_env(env_save_restore)
        client = Twitter()
        # Act
        result = client.post("Test")
        # Assert
        assert "credentials" in result["error"].lower()

    def test_post_success_returns_success_true(
        self, twitter_credentials, fake_oauth_session, twitter_session_factory
    ):
        # Arrange
        fake_oauth_session.post_response = FakeResponse(
            status_code=201, json_data={"data": {"id": "12345"}}
        )
        client = Twitter(**twitter_credentials, session_factory=twitter_session_factory)
        # Act
        result = client.post("Hello World!")
        # Assert
        assert result["success"] is True

    def test_post_success_returns_id_from_api_response(
        self, twitter_credentials, fake_oauth_session, twitter_session_factory
    ):
        # Arrange
        fake_oauth_session.post_response = FakeResponse(
            status_code=201, json_data={"data": {"id": "12345"}}
        )
        client = Twitter(**twitter_credentials, session_factory=twitter_session_factory)
        # Act
        result = client.post("Hello World!")
        # Assert
        assert result["id"] == "12345"

    def test_post_success_returns_x_com_url(
        self, twitter_credentials, fake_oauth_session, twitter_session_factory
    ):
        # Arrange
        fake_oauth_session.post_response = FakeResponse(
            status_code=201, json_data={"data": {"id": "12345"}}
        )
        client = Twitter(**twitter_credentials, session_factory=twitter_session_factory)
        # Act
        result = client.post("Hello World!")
        # Assert
        assert "x.com" in result["url"]

    def test_post_failure_returns_success_false(
        self, twitter_credentials, fake_oauth_session, twitter_session_factory
    ):
        # Arrange
        fake_oauth_session.post_response = FakeResponse(
            status_code=403, text="Forbidden"
        )
        client = Twitter(**twitter_credentials, session_factory=twitter_session_factory)
        # Act
        result = client.post("Hello World!")
        # Assert
        assert result["success"] is False

    def test_post_failure_includes_status_code_in_error(
        self, twitter_credentials, fake_oauth_session, twitter_session_factory
    ):
        # Arrange
        fake_oauth_session.post_response = FakeResponse(
            status_code=403, text="Forbidden"
        )
        client = Twitter(**twitter_credentials, session_factory=twitter_session_factory)
        # Act
        result = client.post("Hello World!")
        # Assert
        assert "403" in result["error"]

    def test_post_with_reply_to_sends_reply_payload_field(
        self, twitter_credentials, fake_oauth_session, twitter_session_factory
    ):
        # Arrange
        fake_oauth_session.post_response = FakeResponse(
            status_code=201, json_data={"data": {"id": "67890"}}
        )
        client = Twitter(**twitter_credentials, session_factory=twitter_session_factory)
        # Act
        client.post("Reply text", reply_to="12345")
        # Assert
        assert "reply" in fake_oauth_session.calls[0].kwargs["json"]


# --- Deleting --------------------------------------------------------------


class TestTwitterDelete:
    def test_delete_success_returns_success_true(
        self, twitter_credentials, fake_oauth_session, twitter_session_factory
    ):
        # Arrange
        fake_oauth_session.delete_response = FakeResponse(status_code=200)
        client = Twitter(**twitter_credentials, session_factory=twitter_session_factory)
        # Act
        result = client.delete("12345")
        # Assert
        assert result["success"] is True

    def test_delete_success_marks_deleted_true(
        self, twitter_credentials, fake_oauth_session, twitter_session_factory
    ):
        # Arrange
        fake_oauth_session.delete_response = FakeResponse(status_code=200)
        client = Twitter(**twitter_credentials, session_factory=twitter_session_factory)
        # Act
        result = client.delete("12345")
        # Assert
        assert result["deleted"] is True

    def test_delete_failure_returns_success_false(
        self, twitter_credentials, fake_oauth_session, twitter_session_factory
    ):
        # Arrange
        fake_oauth_session.delete_response = FakeResponse(
            status_code=404, text="Not Found"
        )
        client = Twitter(**twitter_credentials, session_factory=twitter_session_factory)
        # Act
        result = client.delete("invalid_id")
        # Assert
        assert result["success"] is False

    def test_delete_failure_includes_status_code_in_error(
        self, twitter_credentials, fake_oauth_session, twitter_session_factory
    ):
        # Arrange
        fake_oauth_session.delete_response = FakeResponse(
            status_code=404, text="Not Found"
        )
        client = Twitter(**twitter_credentials, session_factory=twitter_session_factory)
        # Act
        result = client.delete("invalid_id")
        # Assert
        assert "404" in result["error"]


# --- Threads ---------------------------------------------------------------


class TestTwitterThread:
    def test_post_thread_success_marks_success_true(
        self, twitter_credentials, fake_oauth_session, twitter_session_factory
    ):
        # Arrange
        fake_oauth_session.post_sequence = [
            FakeResponse(status_code=201, json_data={"data": {"id": "1"}}),
            FakeResponse(status_code=201, json_data={"data": {"id": "2"}}),
            FakeResponse(status_code=201, json_data={"data": {"id": "3"}}),
        ]
        client = Twitter(**twitter_credentials, session_factory=twitter_session_factory)
        # Act
        result = client.post_thread(["First", "Second", "Third"])
        # Assert
        assert result["success"] is True

    def test_post_thread_success_returns_one_id_per_tweet(
        self, twitter_credentials, fake_oauth_session, twitter_session_factory
    ):
        # Arrange
        fake_oauth_session.post_sequence = [
            FakeResponse(status_code=201, json_data={"data": {"id": "1"}}),
            FakeResponse(status_code=201, json_data={"data": {"id": "2"}}),
            FakeResponse(status_code=201, json_data={"data": {"id": "3"}}),
        ]
        client = Twitter(**twitter_credentials, session_factory=twitter_session_factory)
        # Act
        result = client.post_thread(["First", "Second", "Third"])
        # Assert
        assert len(result["ids"]) == 3

    def test_post_thread_success_returns_one_url_per_tweet(
        self, twitter_credentials, fake_oauth_session, twitter_session_factory
    ):
        # Arrange
        fake_oauth_session.post_sequence = [
            FakeResponse(status_code=201, json_data={"data": {"id": "1"}}),
            FakeResponse(status_code=201, json_data={"data": {"id": "2"}}),
            FakeResponse(status_code=201, json_data={"data": {"id": "3"}}),
        ]
        client = Twitter(**twitter_credentials, session_factory=twitter_session_factory)
        # Act
        result = client.post_thread(["First", "Second", "Third"])
        # Assert
        assert len(result["urls"]) == 3

    def test_post_thread_partial_failure_reports_success_false(
        self, twitter_credentials, fake_oauth_session, twitter_session_factory
    ):
        # Arrange
        fake_oauth_session.post_sequence = [
            FakeResponse(status_code=201, json_data={"data": {"id": "1"}}),
            FakeResponse(status_code=403, text="Rate limited"),
        ]
        client = Twitter(**twitter_credentials, session_factory=twitter_session_factory)
        # Act
        result = client.post_thread(["First", "Second", "Third"])
        # Assert
        assert result["success"] is False

    def test_post_thread_partial_failure_returns_partial_ids_list(
        self, twitter_credentials, fake_oauth_session, twitter_session_factory
    ):
        # Arrange
        fake_oauth_session.post_sequence = [
            FakeResponse(status_code=201, json_data={"data": {"id": "1"}}),
            FakeResponse(status_code=403, text="Rate limited"),
        ]
        client = Twitter(**twitter_credentials, session_factory=twitter_session_factory)
        # Act
        result = client.post_thread(["First", "Second", "Third"])
        # Assert
        assert len(result["partial_ids"]) == 1
