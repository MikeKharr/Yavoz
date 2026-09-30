"""Приложение на localhost: каталог на Диске -> обработанные копии рядом."""
from __future__ import annotations

import json
import queue
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import stats
from .catalog import КЛАССЫ, ФАЙЛ, Каталог
from .config import ROOT, Config, read_config
from .page import СТРАНИЦА
from .process import Обработчик, журнал, сохранить_журнал
from .search import создать
from .secrets import Хранилище
from .yadisk import PREFIX, Disk, processed_path

РАБОЧИЙ = ROOT / "work"
КАТАЛОГ = ROOT / ФАЙЛ
ПРЕДЕЛ_ТЕЛА = 64 * 1024


def обработать_каталог(cfg: Config, токен: str, folder: str, событие,
                       предел: int | None = None) -> None:
    диск = Disk(токен)
    поиск = создать(cfg.источник, cfg.search_api_key, cfg.folder_id)
    обработчик = Обработчик(поиск, каталог=Каталог.прочитать(КАТАЛОГ))
    файлы = диск.list_xlsx(folder)
    событие({"вид": "файл", "лист": "—", "строк": 0,
             "файл": f"найдено файлов: {len(файлы)}"})
    if not файлы:
        событие({"вид": "готово", "текст": "В каталоге нет необработанных .xlsx"})
        return
    for ф in файлы:
        местный = РАБОЧИЙ / ф.name
        диск.download(ф.path, местный)
        цель = РАБОЧИЙ / f"{PREFIX}{ф.name}"
        событие({"вид": "файл", "лист": "—", "строк": 0, "файл": ф.name})
        итоги = обработчик.файл(местный, цель, событие=событие,
                                предел=cfg.max_rows if предел is None else предел)
        диск.upload(цель, processed_path(folder, ф.name))
        сохранить_журнал(журнал(итоги, ф.name), stats.путь_журнала(РАБОЧИЙ, ф.name))
    событие({"вид": "готово", "текст": f"Готово: файлов {len(файлы)}"})


class Ручка(BaseHTTPRequestHandler):
    cfg: Config
    токены: Хранилище
    последний_каталог: str = ""

    def log_message(self, *_args) -> None:
        pass

    # --- отправка ---

    def _отдать(self, код: int, тело: bytes, тип: str) -> None:
        self.send_response(код)
        self.send_header("Content-Type", тип)
        self.send_header("Content-Length", str(len(тело)))
        self.end_headers()
        self.wfile.write(тело)

    def _json(self, код: int, данные: dict) -> None:
        self._отдать(код, json.dumps(данные, ensure_ascii=False).encode("utf-8"),
                     "application/json; charset=utf-8")

    # --- маршруты ---

    def do_GET(self) -> None:
        путь = urlparse(self.path).path.rstrip("/") or "/"
        if путь == "/":
            self._отдать(200, СТРАНИЦА.encode("utf-8"), "text/html; charset=utf-8")
        elif путь == "/api/state":
            self._json(200, {"токен_задан": self.токены.задан,
                             "токен_маска": self.токены.маска,
                             "каталог": type(self).последний_каталог,
                             "источник": self.cfg.источник,
                             "предел_строк": self.cfg.max_rows})
        elif путь == "/api/stats":
            self._json(200, stats.как_json(РАБОЧИЙ))
        elif путь == "/api/catalog":
            к = Каталог.прочитать(КАТАЛОГ)
            self._json(200, {
                "правила": к.правила,
                "классы": [{"имя": кл.имя, "вес": кл.вес, "потолок": кл.потолок,
                            "описание": кл.описание}
                           for кл in sorted(КЛАССЫ.values(), key=lambda к: к.порядок)],
            })
        elif путь == "/run":
            запрос = parse_qs(urlparse(self.path).query)
            try:
                предел = max(0, int(запрос.get("limit", ["0"])[0]))
            except ValueError:
                предел = 0
            self._поток(запрос.get("folder", ["disk:/"])[0], предел)
        else:
            self._json(404, {"ошибка": "нет такого пути"})

    def do_POST(self) -> None:
        путь = urlparse(self.path).path.rstrip("/") or "/"
        if путь not in ("/api/token", "/api/catalog"):
            self._json(404, {"ошибка": "нет такого пути"})
            return
        длина = int(self.headers.get("content-length") or 0)
        if длина > ПРЕДЕЛ_ТЕЛА:
            self._json(400, {"ошибка": "слишком большое тело запроса"})
            return
        try:
            данные = json.loads(self.rfile.read(длина) or b"{}")
        except json.JSONDecodeError:
            self._json(400, {"ошибка": "тело не разобралось как JSON"})
            return
        if путь == "/api/catalog":
            self._сохранить_каталог(данные)
            return
        try:
            # Значение токена не попадает ни в журнал, ни в ответ.
            self.токены.запомнить(str(данные.get("токен") or ""),
                                  bool(данные.get("сохранить")))
        except ValueError:
            self._json(400, {"ошибка": "пустой токен"})
            return
        except OSError:
            self._json(500, {"ошибка": "не удалось записать .env"})
            return
        self._json(200, {"задан": True, "сохранён": bool(данные.get("сохранить"))})

    def _сохранить_каталог(self, данные: dict) -> None:
        правила = данные.get("правила")
        if not isinstance(правила, dict):
            self._json(400, {"ошибка": "нет поля «правила»"})
            return
        чистые = {}
        for класс in КЛАССЫ:
            значения = правила.get(класс, [])
            if not isinstance(значения, list):
                self._json(400, {"ошибка": f"«{класс}» должен быть списком"})
                return
            # Порядок сохраняем, повторы и пустые строки убираем.
            видели, список = set(), []
            for з in значения:
                з = str(з).strip().lower()
                if з and з not in видели:
                    видели.add(з)
                    список.append(з)
            чистые[класс] = список
        try:
            Каталог(правила=чистые).записать(КАТАЛОГ)
        except OSError:
            self._json(500, {"ошибка": "не удалось записать каталог"})
            return
        self._json(200, {"сохранён": True, "правила": чистые})

    # --- поток событий ---

    def _поток(self, folder: str, предел: int = 0) -> None:
        if not self.токены.задан:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.end_headers()
            self._событие({"вид": "ошибка",
                           "текст": "токен Яндекс.Диска не задан — введите его выше"})
            return
        type(self).последний_каталог = folder
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        очередь: queue.Queue = queue.Queue()
        токен = self.токены.значение

        def работа() -> None:
            try:
                обработать_каталог(self.cfg, токен, folder, очередь.put, предел)
            except Exception as err:
                traceback.print_exc()
                очередь.put({"вид": "ошибка", "текст": f"{type(err).__name__}: {err}"})
            finally:
                очередь.put(None)

        threading.Thread(target=работа, daemon=True).start()
        while True:
            событие = очередь.get()
            if событие is None:
                break
            if not self._событие(событие):
                break

    def _событие(self, данные: dict) -> bool:
        строка = f"data: {json.dumps(данные, ensure_ascii=False)}\n\n"
        try:
            self.wfile.write(строка.encode("utf-8"))
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            return False
        return True


def main() -> None:
    cfg = read_config()
    Ручка.cfg = cfg
    Ручка.токены = Хранилище(ROOT / ".env")
    РАБОЧИЙ.mkdir(exist_ok=True)
    if cfg.источник == "yandex" and cfg.missing:
        # Источник выдачи ключа со страницы не получает — это остаётся в .env.
        print("Не заданы: " + ", ".join(п for п in cfg.missing if п != "YADISK_TOKEN"))
        print("См. README.md, раздел «Откуда берётся выдача»")
    print(f"Yavoz: http://127.0.0.1:{cfg.port}")
    if not Ручка.токены.задан:
        print("Токен Яндекс.Диска не задан — введите его на странице")
    ThreadingHTTPServer(("127.0.0.1", cfg.port), Ручка).serve_forever()


if __name__ == "__main__":
    main()
