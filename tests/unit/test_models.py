from app.domain.models.edit_profile import EditProfile
from app.domain.models.export_artifact import sanitize_filename


def test_edit_profile_defaults():
    p = EditProfile(job_id='j1')
    assert p.trim_start_seconds == 0


def test_edit_profile_none_trim_start_defaults_to_zero():
    p = EditProfile(job_id='j1', trim_start_seconds=None)
    assert p.trim_start_seconds == 0


def test_filename_sanitization():
    assert sanitize_filename('A/B:C?') == 'ABC'
