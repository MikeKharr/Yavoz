"""Яндекс.Диск: перечисление каталога, скачивание и загрузка файлов."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import requests

API = "https://cloud-api.yandex.net/v1/disk/resources"
TIMEOUT = 60


class DiskError(RuntimeError):
    pass


@dataclass(frozen=True)
class DiskFile:
    name: str
    path: str
    size: int


class Disk:
    def __init__(self, token: str, session: requests.Session | None = None) -> None:
        if not token:
            raise DiskError("нет токена Яндекс.Диска")
        self._session = session or requests.Session()
        self._headers = {"Authorization": f"OAuth {token}"}

    def _get(self, url: str, **params: object) -> dict:
        r = self._session.get(url, headers=self._headers, params=params, timeout=TIMEOUT)
        if r.status_code == 401:
            raise DiskError("Яндекс.Диск не принял токен (401)")
        if r.status_code == 404:
            raise DiskError(f"на Диске нет пути: {params.get('path')}")
        if not r.ok:
            raise DiskError(f"Диск ответил {r.status_code}: {r.text[:200]}")
        return r.json()

    def list_xlsx(self, folder: str) -> list[DiskFile]:
        """Все .xlsx каталога, кроме уже обработанных и временных файлов Excel."""
        найдено: list[DiskFile] = []
        offset = 0
        while True:
            data = self._get(API, path=folder, limit=200, offset=offset,
                             fields="_embedded.items.name,_embedded.items.path,"
                                    "_embedded.items.type,_embedded.items.size,_embedded.total")
            items = data.get("_embedded", {}).get("items", [])
            for it in items:
                if it.get("type") != "file":
                    continue
                name = it["name"]
                if not name.lower().endswith(".xlsx"):
                    continue
                if name.startswith("~$") or name.lower().startswith(PREFIX.lower()):
                    continue
                найдено.append(DiskFile(name=name, path=it["path"], size=int(it.get("size", 0))))
            offset += len(items)
            if not items or offset >= int(data.get("_embedded", {}).get("total", 0)):
                break
        return sorted(найдено, key=lambda f: f.name)

    def download(self, path: str, target: Path) -> Path:
        href = self._get(f"{API}/download", path=path)["href"]
        r = self._session.get(href, timeout=TIMEOUT, stream=True)
        if not r.ok:
            raise DiskError(f"скачивание не удалось: {r.status_code}")
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("wb") as fh:
            for chunk in r.iter_content(65536):
                fh.write(chunk)
        return target

    def upload(self, source: Path, path: str, overwrite: bool = True) -> None:
        href = self._get(f"{API}/upload", path=path, overwrite=str(overwrite).lower())["href"]
        with source.open("rb") as fh:
            r = self._session.put(href, data=fh, timeout=TIMEOUT * 5)
        if r.status_code not in (201, 202):
            raise DiskError(f"загрузка не удалась: {r.status_code} {r.text[:200]}")


PREFIX = "обработано "


def processed_path(folder: str, name: str) -> str:
    return f"{folder.rstrip('/')}/{PREFIX}{name}"
