"""Хранение токена Диска: в памяти на время работы и, по желанию, в .env.

Значение не печатается нигде — ни в журнал, ни в ответ, ни в сообщение об
ошибке. Наружу отдаётся только признак «задан или нет».
"""
from __future__ import annotations

import os
from pathlib import Path

ПЕРЕМЕННАЯ = "YADISK_TOKEN"


class Хранилище:
    def __init__(self, env: Path) -> None:
        self._env = env
        self._значение = ""

    @property
    def задан(self) -> bool:
        return bool(self.значение)

    @property
    def значение(self) -> str:
        """Из памяти, иначе из окружения (которое наполняет .env при старте)."""
        return self._значение or os.environ.get(ПЕРЕМЕННАЯ, "").strip()

    def запомнить(self, токен: str, сохранить: bool = False) -> None:
        токен = (токен or "").strip()
        if not токен:
            raise ValueError("пустой токен")
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
