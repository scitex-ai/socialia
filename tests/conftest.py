"""Pytest fixtures for socialia tests.

Subprocess coverage is configured in pyproject.toml via coverage.py's subprocess patch; test collection must not install .pth files or overwrite caller-owned coverage environment variables.

All fixtures here are real hand-rolled fakes — no ``unittest.mock``,
``pytest-mock``, or ``monkeypatch`` is used anywhere in the socialia test
tree (rule PA-306 / STX-NM00*). See
``_skills/general/02_package_12_no-mocks.md`` for the rationale.
"""

from __future__ import annotations

import os
from typing import Any, Callable, Optional

import pytest


# --- env_save_restore -------------------------------------------------------
#
# Replaces ``monkeypatch.setenv`` / ``monkeypatch.delenv`` patterns.  Yields
# a controller whose ``set`` / ``delete`` methods mutate the process
# environment for the duration of the test and restores the snapshot on
# teardown.  Used for any test that needs to manipulate SOCIALIA_*, SCITEX_*,
# or other env vars without using ``monkeypatch`` (forbidden by PA-306).


class _EnvController:
    def __init__(self, snapshot: dict[str, Optional[str]]) -> None:
        self._snapshot = snapshot

    def set(self, key: str, value: str) -> None:
        if key not in self._snapshot:
            self._snapshot[key] = os.environ.get(key)
        os.environ[key] = value

    def delete(self, key: str) -> None:
        if key not in self._snapshot:
            self._snapshot[key] = os.environ.get(key)
        os.environ.pop(key, None)

    def clear(self) -> None:
        """Snapshot every current env var and pop it; restore on teardown."""
        for key in list(os.environ.keys()):
            if key not in self._snapshot:
                self._snapshot[key] = os.environ[key]
            del os.environ[key]


@pytest.fixture
def env_save_restore():
    """Yield an _EnvController; restore os.environ deltas on teardown."""
    snapshot: dict[str, Optional[str]] = {}
    controller = _EnvController(snapshot)
    try:
        yield controller
    finally:
        for key, original in snapshot.items():
            if original is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original


# --- Fake HTTP collaborators ------------------------------------------------
#
# These replace ``MagicMock``/``patch("...requests")`` patterns.  Each fake
# exposes only the surface the SUT actually touches; tests stamp a
# ``FakeResponse`` per call into the fake's queue / return slot and then
# inspect the recorded call afterwards.


class FakeResponse:
    """A real, honest stand-in for ``requests.Response`` covering the
    attributes the socialia clients read: ``status_code``, ``text``,
    ``headers``, and a ``.json()`` callable.
    """

    def __init__(
        self,
        status_code: int,
        json_data: Optional[Any] = None,
        text: str = "",
        headers: Optional[dict] = None,
    ) -> None:
        self.status_code = status_code
        self._json = json_data if json_data is not None else {}
        self.text = text
        self.headers = headers or {}

    def json(self) -> Any:
        return self._json


class _RecordingCall:
    __slots__ = ("method", "args", "kwargs")

    def __init__(self, method: str, args: tuple, kwargs: dict) -> None:
        self.method = method
        self.args = args
        self.kwargs = kwargs


class FakeRequestsModule:
    """Hand-rolled stand-in for the ``requests`` module surface that
    socialia uses (``get`` / ``post`` / ``delete``).

    Configure responses per-method via ``self.get_response``,
    ``self.post_response``, ``self.delete_response`` (a single
    ``FakeResponse`` returned for every call) or via ``self.responses``
    (a per-(method,url) lookup).  All calls are recorded onto
    ``self.calls`` for assertion.
    """

    def __init__(self) -> None:
        self.calls: list[_RecordingCall] = []
        self.get_response: Optional[FakeResponse] = None
        self.post_response: Optional[FakeResponse] = None
        self.delete_response: Optional[FakeResponse] = None
        # Optional iterable / list to return responses in sequence.
        self.get_sequence: list[FakeResponse] = []
        self.post_sequence: list[FakeResponse] = []
        self.delete_sequence: list[FakeResponse] = []

    def _pop_or_single(
        self,
        sequence: list[FakeResponse],
        single: Optional[FakeResponse],
        method: str,
    ) -> FakeResponse:
        if sequence:
            return sequence.pop(0)
        if single is not None:
            return single
        raise AssertionError(
            f"FakeRequestsModule.{method}() called with no response configured"
        )

    def get(self, *args, **kwargs) -> FakeResponse:
        self.calls.append(_RecordingCall("get", args, kwargs))
        return self._pop_or_single(self.get_sequence, self.get_response, "get")

    def post(self, *args, **kwargs) -> FakeResponse:
        self.calls.append(_RecordingCall("post", args, kwargs))
        return self._pop_or_single(self.post_sequence, self.post_response, "post")

    def delete(self, *args, **kwargs) -> FakeResponse:
        self.calls.append(_RecordingCall("delete", args, kwargs))
        return self._pop_or_single(
            self.delete_sequence, self.delete_response, "delete"
        )


class FakeOAuthSession:
    """Hand-rolled stand-in for ``requests_oauthlib.OAuth1Session`` that
    Twitter clients consume.  Surface: ``get`` / ``post`` / ``delete``
    returning ``FakeResponse``.
    """

    def __init__(self) -> None:
        self.calls: list[_RecordingCall] = []
        self.get_response: Optional[FakeResponse] = None
        self.post_response: Optional[FakeResponse] = None
        self.delete_response: Optional[FakeResponse] = None
        self.get_sequence: list[FakeResponse] = []
        self.post_sequence: list[FakeResponse] = []
        self.delete_sequence: list[FakeResponse] = []

    def _resolve(
        self,
        sequence: list[FakeResponse],
        single: Optional[FakeResponse],
        method: str,
    ) -> FakeResponse:
        if sequence:
            return sequence.pop(0)
        if single is not None:
            return single
        raise AssertionError(
            f"FakeOAuthSession.{method}() called with no response configured"
        )

    def get(self, *args, **kwargs) -> FakeResponse:
        self.calls.append(_RecordingCall("get", args, kwargs))
        return self._resolve(self.get_sequence, self.get_response, "get")

    def post(self, *args, **kwargs) -> FakeResponse:
        self.calls.append(_RecordingCall("post", args, kwargs))
        return self._resolve(self.post_sequence, self.post_response, "post")

    def delete(self, *args, **kwargs) -> FakeResponse:
        self.calls.append(_RecordingCall("delete", args, kwargs))
        return self._resolve(self.delete_sequence, self.delete_response, "delete")


@pytest.fixture
def fake_oauth_session() -> FakeOAuthSession:
    """Hand-rolled stand-in for the Twitter OAuth1 session collaborator."""
    return FakeOAuthSession()


@pytest.fixture
def twitter_session_factory(
    fake_oauth_session: FakeOAuthSession,
) -> Callable[[], FakeOAuthSession]:
    """Zero-arg callable returning the shared FakeOAuthSession instance.

    Wire it via ``Twitter(..., session_factory=twitter_session_factory)``;
    every ``_get_session()`` call returns the same fake instance so the test
    can configure responses and inspect calls.
    """
    return lambda: fake_oauth_session


@pytest.fixture
def fake_http() -> FakeRequestsModule:
    """Hand-rolled stand-in for the ``requests`` module surface."""
    return FakeRequestsModule()


@pytest.fixture
def twitter_credentials() -> dict:
    """Provide test Twitter credentials."""
    return {
        "consumer_key": "test_consumer_key",
        "consumer_secret": "test_consumer_secret",
        "access_token": "test_access_token",
        "access_token_secret": "test_access_token_secret",
    }


@pytest.fixture
def linkedin_credentials() -> dict:
    """Provide test LinkedIn credentials."""
    return {
        "access_token": "test_linkedin_token",
    }
