"""Хранение токена Диска: в памяти на время работы и, по желанию, в .env.

Значение не печатается нигде — ни в журнал, ни в ответ, ни в сообщение об
ошибке. Наружу отдаётся только признак «задан или нет».
"""
from __future__ import annotations

import os
from pathlib import Path

ПЕРЕМЕННАЯ = "YADISK_TOKEN"


МАСКА = "•"


def замаскировать(значение: str) -> str:
    """Первые два и последние четыре знака видимы, остальное — точки.

    Короткое значение не раскрывается вовсе: у восьми знаков «видимые» шесть
    означали бы, что маска почти ничего не прячет.
    """
    значение = (значение or "").strip()
    if not значение:
        return ""
    if len(значение) < 12:
        return МАСКА * len(значение)
    return f"{значение[:2]}{МАСКА * (len(значение) - 6)}{значение[-4:]}"


class Хранилище:
    def __init__(self, env: Path) -> None:
        self._env = env
        self._значение = ""

    @property
    def задан(self) -> bool:
        return bool(self.значение)

    @property
    def маска(self) -> str:
        return замаскировать(self.значение)

    @property
    def значение(self) -> str:
        """Из памяти, иначе из окружения (которое наполняет .env при старте)."""
        return self._значение or os.environ.get(ПЕРЕМЕННАЯ, "").strip()

    def запомнить(self, токен: str, сохранить: bool = False) -> None:
        токен = (токен or "").strip()
        if not токен:
            raise ValueError("пустой токен")
        if МАСКА in токен:
            # Страница показывает значение маской; если её прислали назад без
            # правки, это не новый токен, а тот же самый — записывать нельзя.
            raise ValueError("получена маска, а не токен")
        self._значение = токен
        os.environ[ПЕРЕМЕННАЯ] = токен
        if сохранить:
            self._в_файл(токен)

    def _в_файл(self, токен: str) -> None:
        """Заменяет строку переменной, остальные строки .env сохраняет как есть."""
        новая = f"{ПЕРЕМЕННАЯ}={токен}"
        строки: list[str] = []
        заменили = False
        if self._env.is_file():
            for строка in self._env.read_text(encoding="utf-8").splitlines():
                if строка.startswith(f"{ПЕРЕМЕННАЯ}="):
                    строки.append(новая)
                    заменили = True
                else:
                    строки.append(строка)
        if not заменили:
            строки.append(новая)
        прежняя = os.umask(0o077)
        try:
            self._env.write_text("\n".join(строки) + "\n", encoding="utf-8")
            self._env.chmod(0o600)
        finally:
            os.umask(прежняя)
