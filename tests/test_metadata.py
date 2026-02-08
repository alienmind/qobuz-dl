from unittest.mock import patch
from qobuz_dl.metadata import _format_genres, get_safe


def test_format_genres_deduplication():
    """Test that duplicate genres are removed while preserving order."""
    genres = ["Pop/Rock", "Pop/Rock→Rock", "Pop/Rock→Rock→Alternatif et Indé"]
    expected = "Pop, Rock, Alternatif et Indé"
    assert _format_genres(genres) == expected


def test_format_genres_simple():
    genres = ["Pop", "Rock", "Pop"]
    assert _format_genres(genres) == "Pop, Rock"


def test_get_safe_returns_value():
    data = {"a": {"b": "value"}}
    assert get_safe(data, ["a", "b"], "default") == "value"


def test_get_safe_returns_default_missing_key():
    data = {"a": {}}
    assert get_safe(data, ["a", "b"], "default") == "default"


def test_get_safe_returns_default_none_value():
    data = {"a": {"b": None}}
    # Assuming get_safe treats None as missing and returns default?
    # Let's check implementation behavior:
    # "if val is None: return default"
    assert get_safe(data, ["a", "b"], "default") == "default"


@patch("qobuz_dl.metadata.log_missing_field")
def test_get_safe_logging(mock_log):
    data = {}
    get_safe(data, ["missing"], "default", context_id="ctx")
    mock_log.assert_called_once_with("ctx", "missing", "default")
