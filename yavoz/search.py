"""Поисковый API Яндекс Облака: запрос и разбор выдачи."""
from __future__ import annotations

import base64
import xml.etree.ElementTree as ET
from dataclasses import dataclass

import requests

ENDPOINT = "https://searchapi.api.cloud.yandex.net/v2/web/search"
TIMEOUT = 40


class SearchError(RuntimeError):
    pass


@dataclass(frozen=True)
class Hit:
    url: str
    title: str
    snippet: str


class Search:
    def __init__(self, api_key: str, folder_id: str, session: requests.Session | None = None) -> None:
        if not api_key or not folder_id:
            raise SearchError("нет ключа или каталога Поискового API")
        self._session = session or requests.Session()
        self._headers = {"Authorization": f"Api-Key {api_key}", "Content-Type": "application/json"}
        self._folder = folder_id

    def find(self, query: str, limit: int = 10) -> list[Hit]:
        body = {
            "query": {
                "searchType": "SEARCH_TYPE_RU",
                "queryText": query,
                "familyMode": "FAMILY_MODE_NONE",
                "page": "0",
            },
            "groupSpec": {"groupMode": "GROUP_MODE_FLAT", "groupsOnPage": str(limit), "docsInGroup": "1"},
            "folderId": self._folder,
            "responseFormat": "FORMAT_XML",
            "l10N": "LOCALIZATION_RU",
        }
        r = self._session.post(ENDPOINT, json=body, headers=self._headers, timeout=TIMEOUT)
        if r.status_code in (401, 403):
            raise SearchError(f"Поисковый API не принял ключ ({r.status_code})")
        if not r.ok:
            raise SearchError(f"Поисковый API ответил {r.status_code}: {r.text[:200]}")
        raw = r.json().get("rawData")
        if not raw:
            raise SearchError("в ответе Поискового API нет rawData")
        return parse_xml(base64.b64decode(raw).decode("utf-8", errors="replace"))


def _text(node: ET.Element | None) -> str:
    if node is None:
        return ""
    return "".join(node.itertext()).strip()


def parse_xml(xml: str) -> list[Hit]:
    """Разбирает XML выдачи. Вынесено отдельно, чтобы проверять без сети."""
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as err:
        raise SearchError(f"выдача не разобралась: {err}") from err
    ошибка = root.find(".//response/error")
    if ошибка is not None and _text(ошибка):
        raise SearchError(f"Поисковый API вернул ошибку: {_text(ошибка)[:200]}")
    hits: list[Hit] = []
    for doc in root.iter("doc"):
        url = _text(doc.find("url"))
        if not url:
            continue
        passages = " ".join(_text(p) for p in doc.iter("passage"))
        hits.append(Hit(url=url, title=_text(doc.find("title")),
                        snippet=(passages or _text(doc.find("headline")))[:600]))
    return hits
