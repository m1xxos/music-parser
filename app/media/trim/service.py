import subprocess
from pathlib import Path

def trim_audio(source_path: str, start_seconds: float | None, end_seconds: float | None, work_dir: str) -> str:
    if start_seconds is None and end_seconds is None:
        return source_path
    out_path = str(Path(work_dir) / 'trimmed.mp3')
    cmd = ['ffmpeg', '-y', '-i', source_path]
    if start_seconds is not None:
        cmd += ['-ss', str(start_seconds)]
    if end_seconds is not None:
        cmd += ['-to', str(end_seconds)]
    cmd += ['-acodec', 'libmp3lame', '-q:a', '2', out_path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f'ffmpeg trim failed: {res.stderr}')
    return out_path
