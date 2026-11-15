"""Owning decoder controls; public mutation/file-preservation cases are separate."""

from pathlib import Path

import pytest

from socialia._schedule_store import _decode_schedule


@pytest.mark.parametrize("text,key", [
    ('[{"id":"first","id":"last"}]', "id"),
    ('[{"id":"first","i\\u0064":"last"}]', "id"),
    ('[{"status":"cancelled","status":"cancelled"}]', "status"),
    ('[{"extension":{"key":1,"key":2}}]', "key"),
])
def test_duplicate_field_error_identifies_source_and_decoded_key(text, key):
    # Arrange
    source = Path("owned.json")
    error = None
    # Act
    try:
        _decode_schedule(text, source=source)
    except ValueError as caught:
        error = str(caught)
    # Assert
    assert error == f"Schedule file {source} contains duplicate object key {key!r}"


@pytest.mark.parametrize("text,expected", [
    ("[]", []),
    ('[{"key":1},{"key":2}]', [{"key": 1}, {"key": 2}]),
    ('[{"extension":{"key":1}},{"extension":{"key":2}}]',
     [{"extension": {"key": 1}}, {"extension": {"key": 2}}]),
])
def test_distinct_objects_keep_their_independent_key_spaces(text, expected):
    # Arrange
    source = Path("owned.json")
    # Act
    result = _decode_schedule(text, source=source)
    # Assert
    assert result == expected
