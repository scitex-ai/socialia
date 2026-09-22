"""Tests for socialia analytics module.

The ``requests`` collaborator is injected via ``GoogleAnalytics(http=...)``;
tests use the hand-rolled ``FakeRequestsModule`` and an env-controller
fixture instead of unittest.mock + monkeypatch.
"""

import importlib

from socialia.analytics import GoogleAnalytics

from tests.conftest import FakeResponse


# --- Helpers ----------------------------------------------------------------


def _clear_ga_env(env, *, prefix: str = "SOCIALIA"):
    """Wipe Google Analytics env vars across known brand prefixes.

    We must clear the whole environment (not just GA vars) because the
    branding-aware ``get_env`` falls back through several prefixes and any
    stray var set by the host shell drifts the test.
    """
    env.clear()
    if prefix != "SOCIALIA":
        env.set("SOCIALIA_ENV_PREFIX", prefix)
    from socialia import _branding

    importlib.reload(_branding)


# --- Initialisation ---------------------------------------------------------


class TestGoogleAnalyticsInit:
    def test_init_without_env_leaves_measurement_id_none(self, env_save_restore):
        # Arrange
        _clear_ga_env(env_save_restore)
        # Act
        ga = GoogleAnalytics()
        # Assert
        assert ga.measurement_id is None

    def test_init_without_env_leaves_api_secret_none(self, env_save_restore):
        # Arrange
        _clear_ga_env(env_save_restore)
        # Act
        ga = GoogleAnalytics()
        # Assert
        assert ga.api_secret is None

    def test_init_reads_socialia_measurement_id_from_environment(
        self, env_save_restore
    ):
        # Arrange
        _clear_ga_env(env_save_restore)
        env_save_restore.set(
            "SOCIALIA_GOOGLE_ANALYTICS_MEASUREMENT_ID", "G-TEST123"
        )
        env_save_restore.set(
            "SOCIALIA_GOOGLE_ANALYTICS_API_SECRET", "secret123"
        )
        # Act
        ga = GoogleAnalytics()
        # Assert
        assert ga.measurement_id == "G-TEST123"

    def test_init_reads_socialia_api_secret_from_environment(
        self, env_save_restore
    ):
        # Arrange
        _clear_ga_env(env_save_restore)
        env_save_restore.set(
            "SOCIALIA_GOOGLE_ANALYTICS_MEASUREMENT_ID", "G-TEST123"
        )
        env_save_restore.set(
            "SOCIALIA_GOOGLE_ANALYTICS_API_SECRET", "secret123"
        )
        # Act
        ga = GoogleAnalytics()
        # Assert
        assert ga.api_secret == "secret123"

    def test_init_reads_scitex_prefixed_measurement_id(self, env_save_restore):
        # Arrange
        _clear_ga_env(env_save_restore, prefix="SCITEX")
        env_save_restore.set(
            "SCITEX_GOOGLE_ANALYTICS_MEASUREMENT_ID", "G-SCITEX"
        )
        env_save_restore.set(
            "SCITEX_GOOGLE_ANALYTICS_API_SECRET", "scitex_secret"
        )
        # Act
        ga = GoogleAnalytics()
        # Assert
        assert ga.measurement_id == "G-SCITEX"

    def test_init_reads_scitex_prefixed_api_secret(self, env_save_restore):
        # Arrange
        _clear_ga_env(env_save_restore, prefix="SCITEX")
        env_save_restore.set(
            "SCITEX_GOOGLE_ANALYTICS_MEASUREMENT_ID", "G-SCITEX"
        )
        env_save_restore.set(
            "SCITEX_GOOGLE_ANALYTICS_API_SECRET", "scitex_secret"
        )
        # Act
        ga = GoogleAnalytics()
        # Assert
        assert ga.api_secret == "scitex_secret"


# --- Credential validation --------------------------------------------------


class TestGoogleAnalyticsValidation:
    def test_validate_credentials_without_env_reports_measurement_protocol_false(
        self, env_save_restore
    ):
        # Arrange
        _clear_ga_env(env_save_restore)
        ga = GoogleAnalytics()
        # Act
        result = ga.validate_credentials()
        # Assert
        assert result["measurement_protocol"] is False

    def test_validate_credentials_with_env_reports_measurement_protocol_true(
        self, env_save_restore
    ):
        # Arrange
        _clear_ga_env(env_save_restore)
        env_save_restore.set(
            "SOCIALIA_GOOGLE_ANALYTICS_MEASUREMENT_ID", "G-TEST123"
        )
        env_save_restore.set(
            "SOCIALIA_GOOGLE_ANALYTICS_API_SECRET", "secret123"
        )
        ga = GoogleAnalytics()
        # Act
        result = ga.validate_credentials()
        # Assert
        assert result["measurement_protocol"] is True


# --- Track-event ------------------------------------------------------------


class TestGoogleAnalyticsTrackEvent:
    def test_track_event_without_credentials_returns_success_false(
        self, env_save_restore
    ):
        # Arrange
        _clear_ga_env(env_save_restore)
        ga = GoogleAnalytics()
        # Act
        result = ga.track_event("test_event")
        # Assert
        assert result["success"] is False

    def test_track_event_without_credentials_includes_error_key(
        self, env_save_restore
    ):
        # Arrange
        _clear_ga_env(env_save_restore)
        ga = GoogleAnalytics()
        # Act
        result = ga.track_event("test_event")
        # Assert
        assert "error" in result

    def test_track_event_success_returns_success_true(
        self, env_save_restore, fake_http
    ):
        # Arrange
        _clear_ga_env(env_save_restore)
        env_save_restore.set(
            "SOCIALIA_GOOGLE_ANALYTICS_MEASUREMENT_ID", "G-TEST123"
        )
        env_save_restore.set(
            "SOCIALIA_GOOGLE_ANALYTICS_API_SECRET", "secret123"
        )
        fake_http.post_response = FakeResponse(status_code=204)
        ga = GoogleAnalytics(http=fake_http)
        # Act
        result = ga.track_event("test_event", {"key": "value"})
        # Assert
        assert result["success"] is True

    def test_track_event_success_invokes_http_post_exactly_once(
        self, env_save_restore, fake_http
    ):
        # Arrange
        _clear_ga_env(env_save_restore)
        env_save_restore.set(
            "SOCIALIA_GOOGLE_ANALYTICS_MEASUREMENT_ID", "G-TEST123"
        )
        env_save_restore.set(
            "SOCIALIA_GOOGLE_ANALYTICS_API_SECRET", "secret123"
        )
        fake_http.post_response = FakeResponse(status_code=204)
        ga = GoogleAnalytics(http=fake_http)
        ga.track_event("test_event", {"key": "value"})
        # Act
        post_count = sum(1 for c in fake_http.calls if c.method == "post")
        # Assert
        assert post_count == 1

    def test_track_event_failure_returns_success_false(
        self, env_save_restore, fake_http
    ):
        # Arrange
        _clear_ga_env(env_save_restore)
        env_save_restore.set(
            "SOCIALIA_GOOGLE_ANALYTICS_MEASUREMENT_ID", "G-TEST123"
        )
        env_save_restore.set(
            "SOCIALIA_GOOGLE_ANALYTICS_API_SECRET", "secret123"
        )
        fake_http.post_response = FakeResponse(
            status_code=400, text="Bad Request"
        )
        ga = GoogleAnalytics(http=fake_http)
        # Act
        result = ga.track_event("test_event")
        # Assert
        assert result["success"] is False


# --- CLI surface (Click-based) ---------------------------------------------


class TestAnalyticsCLI:
    """Exercise the public ``main(argv)`` Click entry point — no mocks
    needed because we go via ``--help``.
    """

    def test_analytics_track_help_returns_exit_zero(self, capsys):
        # Arrange
        from socialia.cli import main
        # Act
        rc = main(["analytics", "track", "--help"])
        # Assert
        assert rc == 0

    def test_analytics_track_help_mentions_event_name_argument(self, capsys):
        # Arrange
        from socialia.cli import main
        main(["analytics", "track", "--help"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "EVENT_NAME" in out or "event_name" in out.lower()

    def test_analytics_track_help_documents_param_flag(self, capsys):
        # Arrange
        from socialia.cli import main
        main(["analytics", "track", "--help"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "--param" in out

    def test_analytics_realtime_alias_renders_show_realtime_help(self, capsys):
        # Arrange
        from socialia.cli import main
        main(["analytics", "realtime", "--help"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "show-realtime" in out

    def test_analytics_pageviews_alias_renders_show_pageviews_help(self, capsys):
        # Arrange
        from socialia.cli import main
        main(["analytics", "pageviews", "--help"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "show-pageviews" in out

    def test_analytics_pageviews_alias_documents_start_flag(self, capsys):
        # Arrange
        from socialia.cli import main
        main(["analytics", "pageviews", "--help"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "--start" in out

    def test_analytics_pageviews_alias_documents_end_flag(self, capsys):
        # Arrange
        from socialia.cli import main
        main(["analytics", "pageviews", "--help"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "--end" in out

    def test_analytics_sources_alias_renders_show_sources_help(self, capsys):
        # Arrange
        from socialia.cli import main
        main(["analytics", "sources", "--help"])
        # Act
        out = capsys.readouterr().out
        # Assert
        assert "show-sources" in out
