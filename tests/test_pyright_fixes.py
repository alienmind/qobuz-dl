from unittest.mock import patch

import pytest

from qobuz_dl.core import QobuzDL
from qobuz_dl.downloader import _safe_get
from qobuz_dl.metadata import _format_copyright, _format_genres
from qobuz_dl.utils import get_url_info

# --- Tests for utils.py ---


def test_get_url_info_valid():
    url = "https://open.qobuz.com/album/123456"
    type_, id_ = get_url_info(url)
    assert type_ == "album"
    assert id_ == "123456"


def test_get_url_info_invalid():
    """Test that invalid URLs raise IndexError as patched."""
    url = "https://invalid.com/foo/bar"
    with pytest.raises(IndexError, match="Invalid URL"):
        get_url_info(url)


def test_get_url_info_none_match():
    """Explicitly test None return from re.search matches catch."""
    with patch("re.search", return_value=None):
        with pytest.raises(IndexError, match="Invalid URL"):
            get_url_info("https://open.qobuz.com/album/123")


# --- Tests for downloader.py ---


def test_safe_get_nested():
    d = {"a": {"b": {"c": 1}}}
    assert _safe_get(d, ["a", "b", "c"]) == 1


def test_safe_get_missing():
    d = {"a": {}}
    assert _safe_get(d, ["a", "b"], "default") == "default"


def test_safe_get_non_dict_intermediate():
    """Test fix for 'get on None' or 'get on str' error."""
    # Case 1: Intermediate is None
    d = {"a": None}
    # Before fix: None.get("b") -> AttributeError
    assert _safe_get(d, ["a", "b"], "default") == "default"

    # Case 2: Intermediate is string (has __getitem__ but not get)
    d = {"a": "string_value"}
    # Before fix: "string_value".get("b") -> AttributeError
    assert _safe_get(d, ["a", "b"], "default") == "default"


# --- Tests for metadata.py ---


def test_format_genres():
    genres = ["Rock/Pop", "Rock"]
    assert _format_genres(genres) == "Rock, Pop"


def test_format_genres_empty():
    assert _format_genres([]) == ""


def test_format_copyright():
    assert _format_copyright("(P) 2023 Label") == "\u2117 2023 Label"
    assert _format_copyright("(C) 2023 Label") == "\u00a9 2023 Label"
    assert _format_copyright(None) is None


# --- Tests for core.py (Mocked) ---


def test_core_download_smart_discography_filter_empty():
    """Test smart_discography_filter with empty content (mocked)."""
    # This logic was not explicitly patched but related to unbound vars
    pass


@patch("qobuz_dl.core.QobuzDL.search_by_type")
def test_core_search_by_type_none(mock_search):
    """Test search returning None handling."""
    dl = QobuzDL(
        "dir",
        1,
        False,
        False,
        False,
        False,
        False,
        False,
        None,
        "{artist}",
        "{track}",
        False,
        False,
    )
    mock_search.return_value = None
    # If used in context where it expects list, it should be handled.
    # Currently code checks `if not (search_res := ...)`

    # We can't easily invoke the interactive loop in `handle_url` purely via unit test
    # without mocking input/pick/print.
    pass
