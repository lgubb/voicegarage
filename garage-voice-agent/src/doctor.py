from __future__ import annotations

import asyncio
import ssl
from urllib.parse import urlparse

import aiohttp
import certifi
from livekit import api as livekit_api

from api.config import get_api_settings
from config import get_settings


def _mask(value: str | None) -> str:
    if not value:
        return "missing"
    if len(value) <= 8:
        return f"set:{len(value)} chars"
    return f"{value[:4]}...{value[-4:]} ({len(value)} chars)"


def _print_env() -> bool:
    agent_settings = get_settings()
    api_settings = get_api_settings()
    checks = {
        "LIVEKIT_URL": agent_settings.livekit_url,
        "LIVEKIT_API_KEY": agent_settings.livekit_api_key,
        "LIVEKIT_API_SECRET": agent_settings.livekit_api_secret,
        "DEEPGRAM_API_KEY": agent_settings.deepgram_api_key,
        "LLM_MODEL": agent_settings.resolved_llm_model,
        "OPENAI_API_KEY": agent_settings.openai_api_key,
        "ELEVENLABS_API_KEY": agent_settings.elevenlabs_api_key,
        "API_LOCAL_STORE": str(api_settings.local_call_store_path),
    }
    for name, value in checks.items():
        if name in {"LLM_MODEL", "API_LOCAL_STORE"}:
            print(f"{name}: {value or 'missing'}")
        else:
            print(f"{name}: {_mask(value)}")

    missing = [
        name
        for name in [
            "LIVEKIT_URL",
            "LIVEKIT_API_KEY",
            "LIVEKIT_API_SECRET",
            "DEEPGRAM_API_KEY",
            "ELEVENLABS_API_KEY",
        ]
        if not checks[name]
    ]
    if not checks["OPENAI_API_KEY"]:
        missing.append("OPENAI_API_KEY")
    if missing:
        print(f"\nMissing required variables: {', '.join(missing)}")
        return False

    parsed = urlparse(agent_settings.livekit_url or "")
    if parsed.scheme not in {"wss", "ws", "https", "http"} or not parsed.netloc:
        print("\nLIVEKIT_URL does not look valid. Expected something like wss://xxx.livekit.cloud")
        return False

    return True


async def _check_livekit_auth() -> bool:
    settings = get_settings()
    timeout = aiohttp.ClientTimeout(total=10)
    ssl_context = None
    if settings.livekit_url and settings.livekit_url.startswith("wss://"):
        ssl_context = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(
        ssl=False if settings.livekit_url and settings.livekit_url.startswith("ws://") else ssl_context
    )

    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        client = livekit_api.LiveKitAPI(
            settings.livekit_url,
            settings.livekit_api_key,
            settings.livekit_api_secret,
            timeout=timeout,
            session=session,
        )
        try:
            await client.room.list_rooms(livekit_api.ListRoomsRequest())
        except aiohttp.ClientConnectorCertificateError as exc:
            print("\nLiveKit auth check: FAILED")
            print(f"Error: {type(exc).__name__}: {exc}")
            print("\nThis is a local TLS certificate issue, not a LiveKit credential issue.")
            print(f"The doctor tried to use certifi: {certifi.where()}")
            return False
        except Exception as exc:
            print("\nLiveKit auth check: FAILED")
            print(f"Error: {type(exc).__name__}: {exc}")
            print("\nMost likely causes:")
            print("- LIVEKIT_API_KEY and LIVEKIT_API_SECRET are not from the same LiveKit project as LIVEKIT_URL.")
            print("- You copied a participant token or cloud auth token instead of the project API secret.")
            print("- The key was rotated or deleted in LiveKit Cloud.")
            return False
        finally:
            await client.aclose()

    print("\nLiveKit auth check: OK")
    return True


def main() -> int:
    print("Auto Voice Agent doctor\n")
    print(f"CA bundle: {certifi.where()}\n")
    if not _print_env():
        return 1
    return 0 if asyncio.run(_check_livekit_auth()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
