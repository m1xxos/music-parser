from pathlib import Path
import yt_dlp
from app.adapters.base import ProviderAdapter

class YouTubeAdapter(ProviderAdapter):
    provider = 'youtube'

    def supports_url(self, url: str) -> bool:
        return 'youtube.com' in url or 'youtu.be' in url

    def fetch_metadata(self, url: str) -> dict:
        with yt_dlp.YoutubeDL({'quiet': True, 'skip_download': True, 'no_warnings': True}) as ydl:
            return ydl.extract_info(url, download=False)

    def download_audio(self, url: str, target_dir: str) -> tuple[str, dict]:
        outtmpl = str(Path(target_dir) / '%(id)s.%(ext)s')
        opts = {'format':'bestaudio/best','outtmpl':outtmpl,'postprocessors':[{'key':'FFmpegExtractAudio','preferredcodec':'mp3','preferredquality':'320'}],'noplaylist':True,'quiet':True,'no_warnings':True}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
        mp3 = next(Path(target_dir).glob('*.mp3'))
        return str(mp3), info
