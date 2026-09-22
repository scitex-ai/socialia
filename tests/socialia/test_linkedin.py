"""Tests for LinkedIn client.

The ``requests`` collaborator is injected via ``LinkedIn(http=...)``; tests
construct a hand-rolled ``FakeRequestsModule`` (see ``conftest.py``) and
configure ``FakeResponse`` objects ahead of each call.  No mocks.
"""

import importlib

from socialia.linkedin import LinkedIn

from tests.conftest import FakeResponse


# --- Helpers ----------------------------------------------------------------


def _clear_linkedin_env(env):
    """Clear LinkedIn token env vars across known brand prefixes."""
    env.delete("SOCIALIA_ENV_PREFIX")
    for prefix in ("SOCIALIA", "SCITEX", "SCITEX_SOCIAL"):
        env.delete(f"{prefix}_LINKEDIN_ACCESS_TOKEN")
    from socialia import _branding

    importlib.reload(_branding)


# --- Initialisation ---------------------------------------------------------


class TestLinkedInInit:
    def test_init_with_explicit_token_stores_access_token(
        self, linkedin_credentials
    ):
        # Arrange
        creds = linkedin_credentials
        # Act
        client = LinkedIn(**creds)
        # Assert
        assert client.access_token == "test_linkedin_token"

    def test_init_from_environment_reads_access_token(self, env_save_restore):
        # Arrange
        _clear_linkedin_env(env_save_restore)
        env_save_restore.set("SOCIALIA_LINKEDIN_ACCESS_TOKEN", "env_token")
        # Act
        client = LinkedIn()
        # Assert
        assert client.access_token == "env_token"


# --- Validation -------------------------------------------------------------


class TestLinkedInValidateCredentials:
    def test_validate_credentials_returns_true_when_token_present(
        self, linkedin_credentials
    ):
        # Arrange
        client = LinkedIn(**linkedin_credentials)
        # Act
        ok = client.validate_credentials()
        # Assert
        assert ok is True

    def test_validate_credentials_returns_false_when_token_absent(
        self, env_save_restore
    ):
        # Arrange
        _clear_linkedin_env(env_save_restore)
        client = LinkedIn()
        # Act
        ok = client.validate_credentials()
        # Assert
        assert ok is False


# --- Posting ---------------------------------------------------------------


class TestLinkedInPost:
    def test_post_without_credentials_reports_success_false(
        self, env_save_restore
    ):
        # Arrange
        _clear_linkedin_env(env_save_restore)
        client = LinkedIn()
        # Act
        result = client.post("Test")
        # Assert
        assert result["success"] is False

    def test_post_without_credentials_error_mentions_token(self, env_save_restore):
        # Arrange
        _clear_linkedin_env(env_save_restore)
        client = LinkedIn()
        # Act
        result = client.post("Test")
        # Assert
        assert "token" in result["error"].lower()

    def test_get_user_urn_builds_person_urn_from_userinfo_sub(
        self, linkedin_credentials, fake_http
    ):
        # Arrange
        fake_http.get_response = FakeResponse(
            status_code=200, json_data={"sub": "user123"}
        )
        client = LinkedIn(**linkedin_credentials, http=fake_http)
        # Act
        urn = client._get_user_urn()
        # Assert
        assert urn == "urn:li:person:user123"

    def test_post_success_marks_success_true(
        self, linkedin_credentials, fake_http
    ):
        # Arrange
        fake_http.get_response = FakeResponse(
            status_code=200, json_data={"sub": "user123"}
        )
        fake_http.post_response = FakeResponse(
            status_code=201,
            json_data={},
            headers={"X-RestLi-Id": "share123"},
        )
        client = LinkedIn(**linkedin_credentials, http=fake_http)
        # Act
        result = client.post("Hello LinkedIn!")
        # Assert
        assert result["success"] is True

    def test_post_success_returns_post_id_from_response_header(
        self, linkedin_credentials, fake_http
    ):
        # Arrange
        fake_http.get_response = FakeResponse(
            status_code=200, json_data={"sub": "user123"}
        )
        fake_http.post_response = FakeResponse(
            status_code=201,
            json_data={},
            headers={"X-RestLi-Id": "share123"},
        )
        client = LinkedIn(**linkedin_credentials, http=fake_http)
        # Act
        result = client.post("Hello LinkedIn!")
        # Assert
        assert result["id"] == "share123"

    def test_post_failure_marks_success_false(
        self, linkedin_credentials, fake_http
    ):
        # Arrange
        fake_http.get_response = FakeResponse(
            status_code=200, json_data={"sub": "user123"}
        )
        fake_http.post_response = FakeResponse(
            status_code=401, text="Unauthorized"
        )
        client = LinkedIn(**linkedin_credentials, http=fake_http)
        # Act
        result = client.post("Test post")
        # Assert
        assert result["success"] is False

    def test_post_failure_includes_status_code_in_error(
        self, linkedin_credentials, fake_http
    ):
        # Arrange
        fake_http.get_response = FakeResponse(
            status_code=200, json_data={"sub": "user123"}
        )
        fake_http.post_response = FakeResponse(
            status_code=401, text="Unauthorized"
        )
        client = LinkedIn(**linkedin_credentials, http=fake_http)
        # Act
        result = client.post("Test post")
        # Assert
        assert "401" in result["error"]


# --- Deleting --------------------------------------------------------------


class TestLinkedInDelete:
    def test_delete_success_marks_success_true(
        self, linkedin_credentials, fake_http
    ):
        # Arrange
        fake_http.delete_response = FakeResponse(status_code=204)
        client = LinkedIn(**linkedin_credentials, http=fake_http)
        # Act
        result = client.delete("share123")
        # Assert
        assert result["success"] is True

    def test_delete_success_marks_deleted_true(
        self, linkedin_credentials, fake_http
    ):
        # Arrange
        fake_http.delete_response = FakeResponse(status_code=204)
        client = LinkedIn(**linkedin_credentials, http=fake_http)
        # Act
        result = client.delete("share123")
        # Assert
        assert result["deleted"] is True

    def test_delete_failure_marks_success_false(
        self, linkedin_credentials, fake_http
    ):
        # Arrange
        fake_http.delete_response = FakeResponse(
            status_code=404, text="Not Found"
        )
        client = LinkedIn(**linkedin_credentials, http=fake_http)
        # Act
        result = client.delete("invalid_id")
        # Assert
        assert result["success"] is False

    def test_delete_failure_includes_status_code_in_error(
        self, linkedin_credentials, fake_http
    ):
        # Arrange
        fake_http.delete_response = FakeResponse(
            status_code=404, text="Not Found"
        )
        client = LinkedIn(**linkedin_credentials, http=fake_http)
        # Act
        result = client.delete("invalid_id")
        # Assert
        assert "404" in result["error"]
