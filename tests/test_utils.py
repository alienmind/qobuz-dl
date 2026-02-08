import os
import pytest
from qobuz_dl.utils import make_m3u


def test_make_m3u_utf8_encoding(tmp_path):
    """Test that make_m3u writes with utf-8 encoding."""
    # Setup
    pl_dir = tmp_path
    # Create dummy tracks
    (pl_dir / "Song \u2665.mp3").touch()  # Heart symbol
    (pl_dir / "cover.jpg").touch()

    # We need to mock mutagen or create valid audio files if make_m3u reads metadata.
    # make_m3u iterates os.listdir and reads metadata using mutagen.File.
    # This is hard to test without real files or mocking mutagen.File.

    from unittest.mock import patch, MagicMock

    # We need to patch EasyMP3 since make_m3u uses it
    with patch("qobuz_dl.utils.EasyMP3") as mock_mp3:
        # Setup mock behavior
        instance = mock_mp3.return_value
        # Mock dictionary access for tags
        tags = {"TITLE": ["Song \u2665"], "ARTIST": ["Artist"]}
        instance.__getitem__.side_effect = tags.__getitem__
        # Mock info.length
        instance.info.length = 100

        # Run make_m3u directly (it uses os.walk which finds the real files we created)
        make_m3u(str(pl_dir))

    # Verify file exists and content
    m3u_file = pl_dir / f"{pl_dir.name}.m3u"
    assert m3u_file.exists()

    # Read to verify encoding
    content = m3u_file.read_text(encoding="utf-8")
    assert "Song \u2665" in content
