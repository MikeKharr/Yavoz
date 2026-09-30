"""Проверка живого доступа: какой из двух эндпоинтов пускает ваш ключ.

Диск не нужен. Тратит до двух запросов: обычный поиск (0,488 руб.)
и генеративный (5,08 руб.). Печатает, что ответил каждый.
"""
from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from yavoz.config import read_config          # noqa: E402
from yavoz.rank import Персона, оценить_адрес  # noqa: E402
from yavoz.search import parse_xml             # noqa: E402

ОБЫЧНЫЙ = "https://searchapi.api.cloud.yandex.net/v2/web/search"
ГЕНЕРАТИВНЫЙ = "https://searchapi.api.cloud.yandex.net/v2/gen/search"
ОЖИДАЕМ = "https://kursksu.ru/people/view/316"

ПРОБА = Персона(
    фамилия="Беспалов", имя="Дмитрий", отчество="Викторович",
    организация="Курский государственный университет",
    должность="Декан факультета физической культуры и спорта",
)


def обычный(ключ: str, каталог: str, запрос: str) -> None:
    тело = {
        "query": {"searchType": "SEARCH_TYPE_RU", "queryText": запрос,
                  "familyMode": "FAMILY_MODE_NONE", "page": "0"},
        "groupSpec": {"groupMode": "GROUP_MODE_FLAT", "groupsOnPage": "10",
                      "docsInGroup": "1"},
        "folderId": каталог, "responseFormat": "FORMAT_XML", "l10N": "LOCALIZATION_RU",
    }
    r = requests.post(ОБЫЧНЫЙ, json=тело, timeout=40,
                      headers={"Authorization": f"Api-Key {ключ}",
                               "Content-Type": "application/json"})
    print(f"   код {r.status_code}")
    if not r.ok:
        print(f"   ответ: {r.text[:400]}")
        return
    сырой = r.json().get("rawData")
    if not сырой:
        print(f"   в ответе нет rawData, ключи: {list(r.json())[:8]}")
        return
    находки = parse_xml(base64.b64decode(сырой).decode("utf-8", errors="replace"))
    print(f"   находок: {len(находки)}")
    for i, h in enumerate(находки[:10], 1):
        метка = "  <== ожидаемый" if ОЖИДАЕМ in h.url else ""
        print(f"   {i:>2}. [{оценить_адрес(h.url).балл:>4}] {h.url}{метка}")


def генеративный(ключ: str, каталог: str, запрос: str) -> None:
    тело = {
        "messages": [{"content": запрос, "role": "ROLE_USER"}],
        "folderId": каталог, "fixMisspell": True, "searchType": "SEARCH_TYPE_RU",
    }
    r = requests.post(ГЕНЕРАТИВНЫЙ, json=тело, timeout=90,
                      headers={"Authorization": f"Api-Key {ключ}",
                               "Content-Type": "application/json"})
    print(f"   код {r.status_code}")
    if not r.ok:
        print(f"   ответ: {r.text[:400]}")
        return
    # Ответ может прийти потоком JSON Lines — берём последний непустой объект.
    куски = [json.loads(с) for с in r.text.splitlines() if с.strip()]
    if not куски:
        print("   пустой ответ")
        return
    последний = куски[-1]
    данные = последний.get("result", последний)
    текст = (данные.get("message") or {}).get("content", "")
    источники = данные.get("sources") or []
    print(f"   кусков в ответе: {len(куски)}, источников: {len(источники)}")
    if текст:
        print(f"   ответ модели: {текст[:300]}")
    for i, s in enumerate(источники[:10], 1):
        url = s.get("url", "")
        метка = "  <== ожидаемый" if ОЖИДАЕМ in url else ""
        использован = "использован" if s.get("used") else "не использован"
        print(f"   {i:>2}. [{оценить_адрес(url).балл:>4}] {url} ({использован}){метка}")


def main() -> int:
    cfg = read_config()
    нет = [п for п in ("YANDEX_SEARCH_API_KEY", "YANDEX_FOLDER_ID") if п in cfg.missing]
    if нет:
        print("Не заданы: " + ", ".join(нет))
        return 1

    запрос = ПРОБА.запрос()
    print(f"запрос: {запрос}")
    print(f"в образце владельца для этой строки стоит: {ОЖИДАЕМ}\n")

    for имя, ф in (("обычный поиск  /v2/web/search  (0,488 руб.)", обычный),
                   ("генеративный   /v2/gen/search  (5,08 руб.)", генеративный)):
        print(f"== {имя}")
        try:
            ф(cfg.search_api_key, cfg.folder_id, запрос)
        except Exception as err:
            print(f"   отказ: {type(err).__name__}: {err}")
        print()

    print("Что смотреть: какой эндпоинт дал код 200 и попал ли ожидаемый источник")
    print("в список. Если оба дали 403 — сервисному аккаунту не хватает роли.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
