"""Сборка архива для передачи пользователю Windows.

Архив собирается через zipfile, а не zip(1): тот не помечает имена как UTF-8,
и кириллические названия в проводнике Windows превращаются в мусор.

Секреты и рабочие файлы в архив не попадают — это проверяется, а не обещается.
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

КОРЕНЬ = Path(__file__).resolve().parent.parent
ИМЯ = "Yavoz"
ЗАПРЕЩЕНО = (".env", ".venv", "work", ".git", "__pycache__")
ПРИЗНАК_ТОКЕНА = "y0_"


def собрать() -> list[tuple[Path, str]]:
    """Пары «файл на диске → путь внутри архива»."""
    состав: list[tuple[Path, str]] = []
    for файл in sorted((КОРЕНЬ / "yavoz").glob("*.py")):
        состав.append((файл, f"{ИМЯ}/yavoz/{файл.name}"))
    for имя in ("requirements.txt", "catalog.json"):
        состав.append((КОРЕНЬ / имя, f"{ИМЯ}/{имя}"))
    for имя in ("ЗАПУСК.bat", "ЧИТАТЬ ПЕРВЫМ.txt"):
        состав.append((КОРЕНЬ / "поставка" / имя, f"{ИМЯ}/{имя}"))
    return состав


def проверить(состав: list[tuple[Path, str]]) -> list[str]:
    отказы = []
    for файл, внутри in состав:
        if not файл.is_file():
            отказы.append(f"нет файла: {файл}")
            continue
        if any(з in внутри for з in ЗАПРЕЩЕНО):
            отказы.append(f"запрещённый путь: {внутри}")
        try:
            текст = файл.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if ПРИЗНАК_ТОКЕНА in текст:
            отказы.append(f"похоже на токен внутри: {внутри}")
    return отказы


def main() -> int:
    состав = собрать()
    отказы = проверить(состав)
    if отказы:
        for о in отказы:
            print(f"ОТКАЗ: {о}", file=sys.stderr)
        return 1

    архив = КОРЕНЬ / "поставка" / f"{ИМЯ}.zip"
    архив.parent.mkdir(exist_ok=True)
    архив.unlink(missing_ok=True)
    with zipfile.ZipFile(архив, "w", zipfile.ZIP_DEFLATED) as z:
        for файл, внутри in состав:
            z.write(файл, внутри)

    с_utf8 = sum(1 for i in zipfile.ZipFile(архив).infolist() if i.flag_bits & 0x800)
    кириллических = sum(1 for _, в in состав if any(ord(c) > 127 for c in в))
    print(f"готово: {архив}")
    print(f"файлов: {len(состав)}, размер: {архив.stat().st_size // 1024} КБ")
    print(f"имён с пометкой UTF-8: {с_utf8} (кириллических имён: {кириллических})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
