from app.adapters.base import ProviderAdapter

class AdapterRegistry:
    def __init__(self):
        self._adapters: list[ProviderAdapter] = []

    def register(self, adapter: ProviderAdapter) -> None:
        self._adapters.append(adapter)

    def resolve(self, url: str) -> ProviderAdapter:
        for adapter in self._adapters:
            if adapter.supports_url(url):
                return adapter
        raise ValueError('No adapter for URL')
