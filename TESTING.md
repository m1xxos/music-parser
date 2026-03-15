# Testing Guide

## Running Tests

### Unit Tests (default)
Unit tests run by default and don't require network access:

```bash
pytest -v
```

Or explicitly:
```bash
pytest -v -m "not integration"
```

### Integration Tests
Integration tests make real network requests and download actual audio files:

```bash
pytest -v -m "integration"
```

**Requirements for integration tests:**
- Network access
- `ffmpeg` installed (`brew install ffmpeg` on macOS, `apt-get install ffmpeg` on Linux)

## Test Structure

### Unit Tests (`tests/test_downloader.py`, `tests/test_api.py`)
- Mocked external dependencies
- Fast execution
- Run on every commit/PR

### Integration Tests (`tests/test_integration.py`)
- Real YouTube/SoundCloud downloads
- Test actual audio processing
- Run in CI on main branch pushes

## CI/CD Pipeline

The GitHub Actions workflow runs:
1. **Unit Tests** - Fast tests without network access
2. **Integration Tests** - Full download tests with real URLs
3. **Security Scanning** - Dependency vulnerability checks
4. **Docker Build & Scan** - Container image security analysis

## Test Markers

- `@pytest.mark.unit` - Unit tests (no network)
- `@pytest.mark.integration` - Integration tests (requires network)
