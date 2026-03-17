from abc import ABC, abstractmethod

class ProviderAdapter(ABC):
    provider: str

    @abstractmethod
    def supports_url(self, url: str) -> bool: ...

    @abstractmethod
    def fetch_metadata(self, url: str) -> dict: ...

    @abstractmethod
    def download_audio(self, url: str, target_dir: str) -> tuple[str, dict]: ...
