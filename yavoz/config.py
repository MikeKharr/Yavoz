"""Настройки берутся из окружения и из файла .env рядом с проектом."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_env(path: Path | None = None) -> None:
    """Читает .env, не перекрывая уже заданные переменные окружения."""
    env = path or (ROOT / ".env")
    if not env.is_file():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


@dataclass(frozen=True)
class Config:
    yadisk_token: str
    search_api_key: str
    folder_id: str
    port: int
    max_rows: int

    @property
    def missing(self) -> list[str]:
        нет = []
        if not self.yadisk_token:
            нет.append("YADISK_TOKEN")
        if not self.search_api_key:
            нет.append("YANDEX_SEARCH_API_KEY")
        if not self.folder_id:
            нет.append("YANDEX_FOLDER_ID")
        return нет


def read_config() -> Config:
    load_env()
    return Config(
        yadisk_token=os.environ.get("YADISK_TOKEN", "").strip(),
        search_api_key=os.environ.get("YANDEX_SEARCH_API_KEY", "").strip(),
        folder_id=os.environ.get("YANDEX_FOLDER_ID", "").strip(),
        port=int(os.environ.get("YAVOZ_PORT", "8765")),
        max_rows=int(os.environ.get("YAVOZ_MAX_ROWS", "0")),
    )
