"""Сводка по обработанным файлам: читается из журналов прогонов."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

ПРЕФИКС = "журнал "
ДЕЙСТВИЯ = ("заполнено", "пропущено", "не найдено", "ошибка")
УВЕРЕННОСТЬ = ("высокая", "средняя", "низкая")


@dataclass
class СводкаФайла:
    файл: str
    время: str
    строк: int
    действия: dict[str, int] = field(default_factory=dict)
    уверенность: dict[str, int] = field(default_factory=dict)


def путь_журнала(рабочий: Path, файл: str) -> Path:
    return рабочий / f"{ПРЕФИКС}{файл}.json"


def прочитать(рабочий: Path) -> list[СводкаФайла]:
    """Все журналы каталога, свежие сверху. Битый журнал пропускается, не роняет."""
    сводки: list[СводкаФайла] = []
    if not рабочий.is_dir():
        return сводки
    for путь in sorted(рабочий.glob(f"{ПРЕФИКС}*.json")):
        try:
            данные = json.loads(путь.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        строки = данные.get("строки") or []
        сводки.append(СводкаФайла(
            файл=данные.get("файл") or путь.stem[len(ПРЕФИКС):],
            время=данные.get("время", ""),
            строк=len(строки),
            # Порядок ключей задан, а не взят из данных: столбцы таблицы
            # не должны переставляться от прогона к прогону.
            действия={д: (данные.get("итого") or {}).get(д, 0) for д in ДЕЙСТВИЯ},
            уверенность={у: (данные.get("уверенность") or {}).get(у, 0)
                         for у in УВЕРЕННОСТЬ},
        ))
    сводки.sort(key=lambda с: с.время, reverse=True)
    return сводки


def итого(сводки: list[СводкаФайла]) -> dict:
    всего = {"файлов": len(сводки), "строк": sum(с.строк for с in сводки)}
    for д in ДЕЙСТВИЯ:
        всего[д] = sum(с.действия.get(д, 0) for с in сводки)
    for у in УВЕРЕННОСТЬ:
        всего[у] = sum(с.уверенность.get(у, 0) for с in сводки)
    return всего


def как_json(рабочий: Path) -> dict:
    сводки = прочитать(рабочий)
    return {"файлы": [asdict(с) for с in сводки], "итого": итого(сводки)}
