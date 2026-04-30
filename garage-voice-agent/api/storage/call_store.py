from __future__ import annotations

import json
from abc import ABC, abstractmethod
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Any

def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class CallStore(ABC):
    @abstractmethod
    def list_calls(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_call(self, call_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def upsert_call(self, call: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class JsonCallStore(CallStore):
    def __init__(self, calls_path: Path) -> None:
        self.calls_path = calls_path
        self._lock = Lock()
        self.calls_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.calls_path.exists():
            self._write_calls([])

    def list_calls(self) -> list[dict[str, Any]]:
        calls = self._read_calls()
        return sorted(calls, key=lambda call: call["timestamps"]["created_at"], reverse=True)

    def get_call(self, call_id: str) -> dict[str, Any] | None:
        for call in self._read_calls():
            if call["id"] == call_id:
                return call
        return None

    def upsert_call(self, call: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            calls = self._read_calls_unlocked()
            call = deepcopy(call)
            call.setdefault("timestamps", {})
            call["timestamps"].setdefault("created_at", _now_iso())
            call["timestamps"]["updated_at"] = _now_iso()
            for index, existing in enumerate(calls):
                if existing["id"] == call["id"]:
                    calls[index] = call
                    self._write_calls_unlocked(calls)
                    return call
            calls.append(call)
            self._write_calls_unlocked(calls)
            return call

    def _read_calls(self) -> list[dict[str, Any]]:
        with self._lock:
            return self._read_calls_unlocked()

    def _read_calls_unlocked(self) -> list[dict[str, Any]]:
        return self._read_json(self.calls_path, [])

    def _write_calls(self, calls: list[dict[str, Any]]) -> None:
        with self._lock:
            self._write_calls_unlocked(calls)

    def _write_calls_unlocked(self, calls: list[dict[str, Any]]) -> None:
        self._write_json(self.calls_path, calls)

    @staticmethod
    def _read_json(path: Path, default: Any) -> Any:
        if not path.exists():
            return deepcopy(default)
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    @staticmethod
    def _write_json(path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
