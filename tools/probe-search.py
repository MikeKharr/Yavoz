"""Один живой запрос к Поисковому API — проверить форму запроса и разбор ответа.

Диск не нужен: хватает YANDEX_SEARCH_API_KEY и YANDEX_FOLDER_ID.
Стоит один запрос (0,488 руб. днём).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from yavoz.config import read_config          # noqa: E402
from yavoz.rank import Персона, оценить_адрес  # noqa: E402
from yavoz.search import Search, SearchError   # noqa: E402

# Строка из настоящего файла владельца: у этого человека в образце
# столбец V заполнен страницей вуза, так что ответ есть с чем сверить.
ПРОБА = Персона(
    фамилия="Беспалов", имя="Дмитрий", отчество="Викторович",
    организация="Курский государственный университет",
    должность="Декан факультета физической культуры и спорта",
)


def main() -> int:
    cfg = read_config()
    нет = [п for п in ("YANDEX_SEARCH_API_KEY", "YANDEX_FOLDER_ID") if п in cfg.missing]
    if нет:
        print("Не заданы: " + ", ".join(нет))
        return 1

    запрос = ПРОБА.запрос()
    print(f"запрос: {запрос}\n")
    try:
        находки = Search(cfg.search_api_key, cfg.folder_id).find(запрос, limit=10)
    except SearchError as err:
        print(f"ОТКАЗ: {err}")
        print("\nЭто и есть то, что проверялось: форма запроса написана по документации,")
        print("на живом сервисе не гонялась. Пришлите текст отказа — поправлю.")
        return 2

    if not находки:
        print("Ответ разобран, но находок ноль — стоит проверить каталог и квоту.")
        return 3

    print(f"находок: {len(находки)}\n")
    for i, h in enumerate(находки, 1):
        о = оценить_адрес(h.url)
        print(f"{i:>2}. [{о.балл:>4}] {h.url}")
        print(f"      {h.title[:90]}")
    print("\nФорма запроса и разбор ответа работают.")
    print("В образце владельца для этой строки стоит https://kursksu.ru/people/view/316 —")
    print("сверьте, попал ли он в список и на каком месте.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
