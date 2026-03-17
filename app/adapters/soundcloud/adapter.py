from app.adapters.youtube.adapter import YouTubeAdapter

class SoundCloudAdapter(YouTubeAdapter):
    provider = 'soundcloud'

    def supports_url(self, url: str) -> bool:
        return 'soundcloud.com' in url
