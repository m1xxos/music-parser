from app.adapters.youtube.adapter import YouTubeAdapter

class RuTubeAdapter(YouTubeAdapter):
    provider = 'rutube'

    def supports_url(self, url: str) -> bool:
        return 'rutube.ru' in url
