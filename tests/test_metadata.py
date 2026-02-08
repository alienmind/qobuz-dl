from unittest.mock import patch

from qobuz_dl.metadata import _format_copyright, _format_genres, get_safe


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
    assert get_safe(data, ["a", "b"], "default") == "default"


@patch("qobuz_dl.metadata.log_missing_field")
def test_get_safe_logging(mock_log):
    data = {}
    get_safe(data, ["missing"], "default", context_id="ctx")
    mock_log.assert_called_once_with("ctx", "missing", "default")


# --- Format tests ---

# --- Format tests ---


def test_format_genres_list():
    genres = ["Rock/Pop", "Rock"]
    assert _format_genres(genres) == "Rock, Pop"


def test_format_genres_empty():
    assert _format_genres([]) == ""


def test_format_copyright():
    assert _format_copyright("(P) 2023 Label") == "\u2117 2023 Label"
    assert _format_copyright("(C) 2023 Label") == "\u00a9 2023 Label"
    assert _format_copyright(None) is None
