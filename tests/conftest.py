"""Shared pytest fixtures for music-parser tests."""
import sys
import os
import tempfile
from pathlib import Path

import pytest

# Make the app directory importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))


@pytest.fixture
def temp_music_dir():
    """Create a temporary directory for music output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def real_youtube_video():
    """Return a real YouTube video URL for integration tests."""
    return "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


@pytest.fixture
def real_soundcloud_track():
    """Return a real SoundCloud track URL for integration tests."""
    return "https://soundcloud.com/monstercat/alan-walker-spectre"
