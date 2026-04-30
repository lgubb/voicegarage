from functools import lru_cache

from api.config import get_api_settings
from api.storage.call_store import CallStore, JsonCallStore


@lru_cache
def get_call_store() -> CallStore:
    settings = get_api_settings()
    return JsonCallStore(settings.local_call_store_path)
