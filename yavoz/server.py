"""Приложение на localhost: каталог на Диске -> обработанные копии рядом."""
from __future__ import annotations

import json
import queue
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .config import Config, read_config
from .process import Обработчик, журнал, сохранить_журнал
from .search import Search
from .yadisk import PREFIX, Disk, processed_path

РАБОЧИЙ = Path(__file__).resolve().parent.parent / "work"

СТРАНИЦА = """<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Yavoz</title>
<style>
:root{--фон:#faf9f7;--текст:#1c1b19;--серый:#6b6862;--рамка:#e2ded7;--акцент:#7a5c2e;--ошибка:#8c2f2f}
@media (prefers-color-scheme:dark){:root{--фон:#171614;--текст:#ece9e3;--серый:#9c978e;--рамка:#332f2a;--акцент:#c9a464;--ошибка:#d98a8a}}
*{box-sizing:border-box}
body{margin:0;background:var(--фон);color:var(--текст);font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;padding:32px 16px}
main{max-width:860px;margin:0 auto}
h1{font-size:24px;margin:0 0 4px} p.под{color:var(--серый);margin:0 0 28px}
label{display:block;font-size:13px;color:var(--серый);margin-bottom:6px}
input{width:100%;padding:10px 12px;border:1px solid var(--рамка);border-radius:8px;background:transparent;color:inherit;font:inherit}
button{margin-top:14px;padding:10px 18px;border:0;border-radius:8px;background:var(--акцент);color:#fff;font:inherit;cursor:pointer}
button[disabled]{opacity:.5;cursor:default}
#итоги{margin-top:28px;border:1px solid var(--рамка);border-radius:10px;overflow:hidden;display:none}
#итоги.видно{display:block}
.шапка{padding:10px 14px;border-bottom:1px solid var(--рамка);font-size:14px;color:var(--серый)}
#строки{max-height:52vh;overflow:auto;font-size:14px}
.стр{display:grid;grid-template-columns:52px 1fr auto;gap:10px;padding:7px 14px;border-bottom:1px solid var(--рамка)}
.стр:last-child{border-bottom:0}
.н{color:var(--серый);font-variant-numeric:tabular-nums}
.знак{font-size:12px;padding:1px 8px;border-radius:99px;border:1px solid var(--рамка);white-space:nowrap}
.высокая{color:#2e6b3f;border-color:#2e6b3f55}.средняя{color:var(--акцент);border-color:#7a5c2e55}
.низкая{color:var(--серый)}.ошибка{color:var(--ошибка);border-color:#8c2f2f55}
a{color:var(--акцент);word-break:break-all}
</style></head><body><main>
<h1>Yavoz</h1>
<p class="под">Каталог на Яндекс.Диске → рядом появятся копии с приставкой «обработано».</p>
<label for="каталог">Путь к каталогу на Диске</label>
<input id="каталог" value="disk:/" placeholder="disk:/Верификация">
<button id="пуск">Обработать</button>
<div id="итоги"><div class="шапка" id="шапка">—</div><div id="строки"></div></div>
</main><script>
const $=s=>document.querySelector(s);
$('#пуск').onclick=()=>{
  const каталог=$('#каталог').value.trim(); if(!каталог) return;
  $('#пуск').disabled=true; $('#строки').innerHTML=''; $('#итоги').classList.add('видно');
  $('#шапка').textContent='Читаю каталог…';
  const s=new EventSource('/run?folder='+encodeURIComponent(каталог));
  s.onmessage=e=>{
    const д=JSON.parse(e.data);
    if(д.вид==='файл'){доб('','Файл: '+(д.файл||'')+' — лист «'+д.лист+'», строк '+д.строк,'');}
    else if(д.вид==='строка'){
      const знак=д.действие==='заполнено'?д.уверенность:д.действие;
      доб(д.номер+'/'+д.всего, д.фио+(д.url?' — <a href="'+д.url+'" target="_blank" rel="noopener">'+д.url+'</a>':' — '+(д.примечание||'')), знак);
      $('#шапка').textContent='Обработано '+д.номер+' из '+д.всего;
    }
    else if(д.вид==='сохранено'){доб('','Сохранено: '+д.файл,'');}
    else if(д.вид==='готово'){$('#шапка').textContent=д.текст; $('#пуск').disabled=false; s.close();}
    else if(д.вид==='ошибка'){доб('', 'Ошибка: '+д.текст,'ошибка'); $('#пуск').disabled=false; s.close();}
  };
  s.onerror=()=>{$('#пуск').disabled=false; s.close();};
};
function доб(н,текст,знак){
  const d=document.createElement('div'); d.className='стр';
  d.innerHTML='<span class="н">'+н+'</span><span>'+текст+'</span>'+(знак?'<span class="знак '+знак+'">'+знак+'</span>':'<span></span>');
  $('#строки').appendChild(d); d.scrollIntoView({block:'nearest'});
}
</script></body></html>"""


def обработать_каталог(cfg: Config, folder: str, событие) -> None:
    диск = Disk(cfg.yadisk_token)
    поиск = Search(cfg.search_api_key, cfg.folder_id)
    обработчик = Обработчик(поиск)
    файлы = диск.list_xlsx(folder)
    событие({"вид": "файл", "лист": "—", "строк": 0, "файл": f"найдено файлов: {len(файлы)}"})
    if not файлы:
        событие({"вид": "готово", "текст": "В каталоге нет необработанных .xlsx"})
        return
    for ф in файлы:
        местный = РАБОЧИЙ / ф.name
        диск.download(ф.path, местный)
        цель = РАБОЧИЙ / f"{PREFIX}{ф.name}"
        событие({"вид": "файл", "лист": "—", "строк": 0, "файл": ф.name})
        итоги = обработчик.файл(местный, цель, предел=cfg.max_rows, событие=событие)
        диск.upload(цель, processed_path(folder, ф.name))
        сохранить_журнал(журнал(итоги, ф.name), РАБОЧИЙ / f"журнал {ф.name}.json")
    событие({"вид": "готово", "текст": f"Готово: файлов {len(файлы)}"})


class Ручка(BaseHTTPRequestHandler):
    cfg: Config

    def log_message(self, *_args) -> None:  # тише в консоли
        pass

    def do_GET(self) -> None:
        путь = urlparse(self.path)
        if путь.path == "/":
            тело = СТРАНИЦА.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(тело)))
            self.end_headers()
            self.wfile.write(тело)
            return
        if путь.path == "/run":
            self._поток(parse_qs(путь.query).get("folder", ["disk:/"])[0])
            return
        self.send_response(404)
        self.end_headers()

    def _поток(self, folder: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        очередь: queue.Queue = queue.Queue()

        def работа() -> None:
            try:
                обработать_каталог(self.cfg, folder, очередь.put)
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
            данные = json.dumps(событие, ensure_ascii=False)
            try:
                self.wfile.write(f"data: {данные}\n\n".encode("utf-8"))
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                break


def main() -> None:
    cfg = read_config()
    if cfg.missing:
        print("Не заданы переменные: " + ", ".join(cfg.missing))
        print("Скопируйте .env.example в .env и заполните — см. README.md")
        raise SystemExit(1)
    Ручка.cfg = cfg
    РАБОЧИЙ.mkdir(exist_ok=True)
    сервер = ThreadingHTTPServer(("127.0.0.1", cfg.port), Ручка)
    print(f"Yavoz: http://127.0.0.1:{cfg.port}")
    сервер.serve_forever()


if __name__ == "__main__":
    main()
