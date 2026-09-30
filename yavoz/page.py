"""Разметка страницы. Вынесена из server.py, чтобы логика не тонула в вёрстке."""

СТРАНИЦА = r"""<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Yavoz</title>
<style>
:root{
  --фон:#faf9f7; --плита:#fffefc; --текст:#1c1b19; --серый:#6b6862; --рамка:#e2ded7;
  --акцент:#7a5c2e; --ошибка:#8c2f2f; --успех:#2e6b3f;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --фон:#171614; --плита:#1e1d1a; --текст:#ece9e3; --серый:#9c978e; --рамка:#332f2a;
  --акцент:#c9a464; --ошибка:#d98a8a; --успех:#7fb08f;
}}
:root[data-theme="dark"]{
  --фон:#171614; --плита:#1e1d1a; --текст:#ece9e3; --серый:#9c978e; --рамка:#332f2a;
  --акцент:#c9a464; --ошибка:#d98a8a; --успех:#7fb08f;
}
*{box-sizing:border-box}
body{margin:0;background:var(--фон);color:var(--текст);
  font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;padding:32px 16px}
main{max-width:920px;margin:0 auto;display:flex;flex-direction:column;gap:24px}
h1{font-size:25px;margin:0 0 2px;letter-spacing:-.01em}
p.под{color:var(--серый);margin:0}
section{background:var(--плита);border:1px solid var(--рамка);border-radius:12px;padding:18px 20px}
h2{font-size:15px;margin:0 0 12px;letter-spacing:.02em;text-transform:uppercase;color:var(--серый)}
label{display:block;font-size:13px;color:var(--серый);margin:0 0 6px}
input{width:100%;padding:10px 12px;border:1px solid var(--рамка);border-radius:8px;
  background:var(--фон);color:inherit;font:inherit}
input:focus-visible{outline:2px solid var(--акцент);outline-offset:1px}
.строка{display:flex;gap:12px;align-items:flex-end;flex-wrap:wrap}
.строка>div{flex:1 1 260px}
button{padding:10px 18px;border:0;border-radius:8px;background:var(--акцент);color:#fff;
  font:inherit;cursor:pointer;white-space:nowrap}
button.тихая{background:transparent;color:var(--акцент);border:1px solid var(--рамка)}
button[disabled]{opacity:.5;cursor:default}
.помощь{font-size:13.5px;color:var(--серый);margin:10px 0 0}
.помощь a{color:var(--акцент)}
.галка{display:flex;gap:8px;align-items:center;font-size:13.5px;color:var(--серый);margin:10px 0 0}
.галка input{width:auto}
.знак{font-size:12px;padding:1px 8px;border-radius:99px;border:1px solid var(--рамка);white-space:nowrap}
.высокая{color:var(--успех);border-color:color-mix(in srgb,var(--успех) 40%,transparent)}
.средняя{color:var(--акцент);border-color:color-mix(in srgb,var(--акцент) 40%,transparent)}
.низкая{color:var(--серый)}
.ошибка,.отказ{color:var(--ошибка);border-color:color-mix(in srgb,var(--ошибка) 40%,transparent)}
#строки{max-height:46vh;overflow:auto;font-size:14px;margin:0 -20px -18px;border-top:1px solid var(--рамка)}
.стр{display:grid;grid-template-columns:58px 1fr auto;gap:10px;padding:7px 20px;
  border-bottom:1px solid var(--рамка);align-items:baseline}
.стр:last-child{border-bottom:0}
.н{color:var(--серый);font-variant-numeric:tabular-nums;font-size:13px}
a{color:var(--акцент);word-break:break-all}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{text-align:right;padding:7px 8px;border-bottom:1px solid var(--рамка)}
th:first-child,td:first-child{text-align:left}
th{font-size:12px;text-transform:uppercase;letter-spacing:.03em;color:var(--серый);font-weight:500}
tbody tr:last-child td{border-bottom:0}
tfoot td{font-weight:600;border-top:1px solid var(--рамка);border-bottom:0}
td{font-variant-numeric:tabular-nums}
.ноль{color:var(--серый);opacity:.45}
details{border-top:1px solid var(--рамка);margin:0 -20px -18px;padding:0}
summary{padding:14px 20px;cursor:pointer;font-size:14px;color:var(--акцент)}
.руководство{padding:0 20px 18px;font-size:14.5px}
.руководство h3{font-size:14px;margin:18px 0 6px;text-transform:uppercase;
  letter-spacing:.03em;color:var(--серый)}
.руководство ol,.руководство ul{margin:6px 0;padding-left:22px}
.руководство li{margin:4px 0}
.руководство code{background:var(--фон);border:1px solid var(--рамка);border-radius:4px;
  padding:1px 5px;font-size:13px}
.руководство table{margin:8px 0}
#шапка{font-size:13.5px;color:var(--серый);margin:0 0 12px}
.пусто{color:var(--серый);font-size:14px;margin:0}
@media (max-width:520px){
  body{padding:20px 16px}
  .стр{grid-template-columns:44px 1fr;row-gap:2px}
  .стр .знак{grid-column:2}
}
</style></head><body><main>

<header>
  <h1>Yavoz</h1>
  <p class="под">Каталог на Яндекс.Диске → рядом появятся копии с приставкой «обработано»,
  со заполненными столбцами U и V.</p>
</header>

<section>
  <h2>Доступ к Яндекс.Диску</h2>
  <div class="строка">
    <div>
      <label for="токен">OAuth-токен Яндекс.Диска</label>
      <input id="токен" type="password" autocomplete="off" spellcheck="false"
             placeholder="вставьте токен">
    </div>
    <button id="сохранить" class="тихая">Сохранить</button>
  </div>
  <label class="галка"><input id="в-файл" type="checkbox" checked>
    запомнить в <code>.env</code>, чтобы не вводить каждый раз</label>
  <p class="помощь" id="помощь-токен">
    Токен даёт приложению право читать и записывать файлы на вашем Диске. Получить:
    <a href="https://yandex.ru/dev/disk/poligon/" target="_blank" rel="noopener">яндекс.ру/dev/disk/poligon</a>
    — на этой странице войдите под своей учётной записью и нажмите
    «Получить OAuth-токен», затем скопируйте выданную строку сюда.
    Токен уходит только на этот локальный сервер, передаётся методом POST (не в адресе)
    и никуда больше не отправляется.
  </p>
</section>

<section>
  <h2>Обработка</h2>
  <div class="строка">
    <div>
      <label for="каталог">Путь к каталогу на Диске</label>
      <input id="каталог" value="disk:/yavoz" placeholder="disk:/Верификация">
    </div>
    <button id="пуск">Обработать</button>
  </div>
  <p class="помощь" id="ссылка-каталога"></p>
  <p class="помощь">Берутся все <code>.xlsx</code> каталога, кроме уже обработанных.
  Строки, где столбец V заполнен, пропускаются.</p>
  <div id="ход" hidden>
    <p id="шапка">—</p>
    <div id="строки"></div>
  </div>
</section>

<section>
  <h2>Обработанные файлы</h2>
  <div id="сводка"><p class="пусто">Пока ничего не обработано.</p></div>
</section>

<section>
  <h2>Руководство</h2>
  <details>
    <summary>Как этим пользоваться</summary>
    <div class="руководство">

      <h3>Что делает приложение</h3>
      <p>Берёт файлы <code>.xlsx</code> из указанного каталога на Яндекс.Диске и для каждого
      кладёт рядом копию с приставкой «обработано». Исходный файл не изменяется никогда.</p>
      <p>В копии заполняются два столбца:</p>
      <ul>
        <li><b>U</b> «Ссылка на подтверждение по запросу» — формула поиска по ФИО,
        месту работы и должности. Та же, что в вашем образце.</li>
        <li><b>V</b> «Ссылка на подтверждение в интернете» — наиболее официальный
        найденный источник.</li>
      </ul>

      <h3>Порядок работы</h3>
      <ol>
        <li>Вставьте токен Диска в поле выше и нажмите «Сохранить».</li>
        <li>Положите файлы в каталог на Диске.</li>
        <li>Впишите путь к каталогу и нажмите «Обработать».</li>
        <li>Дождитесь конца: ход работы идёт построчно, каждая строка с пометкой.</li>
        <li>Проверьте таблицу «Обработанные файлы» и скачайте результат с Диска.</li>
      </ol>

      <h3>Какие столбцы нужны в файле</h3>
      <p>Лист данных определяется по шапке: тот, где в <code>B1</code> стоит «Фамилия».
      Если таких листов несколько, берётся самый длинный. Читаются только:</p>
      <table>
        <tr><th>Столбец</th><th>Что в нём</th></tr>
        <tr><td><code>B</code>, <code>C</code>, <code>D</code></td><td>фамилия, имя, отчество</td></tr>
        <tr><td><code>S</code></td><td>место работы</td></tr>
        <tr><td><code>T</code></td><td>должность</td></tr>
      </table>
      <p>Остальные столбцы могут быть пустыми — на них ничего не завязано.</p>

      <h3>Пометки в строках и в таблице</h3>
      <table>
        <tr><th>Пометка</th><th>Что значит</th></tr>
        <tr><td><span class="знак высокая">высокая</span></td>
            <td>официальный домен или раздел о сотрудниках, и фамилия с должностью
            есть на самой странице</td></tr>
        <tr><td><span class="знак средняя">средняя</span></td>
            <td>фамилия на странице есть, и одно из двух — либо официальный домен,
            либо должность</td></tr>
        <tr><td><span class="знак низкая">низкая</span></td>
            <td>ничего официального не нашлось. Ссылка всё равно записана: лучше
            с пометкой, чем ничего. Такие строки стоит просмотреть руками</td></tr>
        <tr><td><span class="знак">пропущено</span></td>
            <td>в столбце V уже было значение — оно не затирается</td></tr>
        <tr><td><span class="знак отказ">не найдено</span></td>
            <td>поиск не дал ни одного результата</td></tr>
        <tr><td><span class="знак ошибка">ошибка</span></td>
            <td>сеть или поиск отказали на этой строке. Остальные строки
            обрабатываются дальше, файл всё равно сохраняется</td></tr>
      </table>
      <p>Уровень уверенности пишется ещё и <b>примечанием к ячейке V</b> — в самой
      ячейке он сломал бы ссылку. Наведите в Excel на уголок ячейки.</p>

      <h3>Сколько ждать и сколько стоит</h3>
      <p>На строку приходится один поисковый запрос, пауза в две секунды и до четырёх
      загрузок страниц. Файл в сто строк идёт порядка получаса. Поиск по умолчанию
      бесплатный.</p>

      <h3>Если что-то не так</h3>
      <ul>
        <li><b>«Яндекс.Диск не принял токен»</b> — токен истёк или скопирован не
        полностью. Получите новый по ссылке выше.</li>
        <li><b>«на Диске нет пути»</b> — проверьте путь; он начинается с
        <code>disk:/</code> и учитывает регистр.</li>
        <li><b>«не нашёл лист, где в B1 стоит „Фамилия“»</b> — файл другой формы,
        чем ожидается.</li>
        <li><b>Много строк с пометкой «низкая»</b> — покажите файл, правила отбора
        настраиваются.</li>
      </ul>

      <h3>Ограничение первого запуска</h3>
      <p>Если в <code>.env</code> задано <code>YAVOZ_MAX_ROWS</code>, из каждого файла
      берётся только столько строк — это для пробы. Уберите строку, чтобы обрабатывать
      файл целиком.</p>

    </div>
  </details>
</section>

</main><script>
const $ = s => document.querySelector(s);
const УВЕРЕННОСТЬ = ['высокая','средняя','низкая'];
const ДЕЙСТВИЯ = ['заполнено','пропущено','не найдено','ошибка'];

async function сохранитьТокен(){
  const токен = $('#токен').value.trim();
  if(!токен){ помощь('Вставьте токен.', true); return false; }
  $('#сохранить').disabled = true;
  try{
    const о = await fetch('/api/token', {method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({токен, сохранить: $('#в-файл').checked})});
    const д = await о.json();
    if(!о.ok){ помощь(д.ошибка || 'Не удалось сохранить.', true); return false; }
    $('#токен').value = '';
    $('#токен').placeholder = 'токен задан';
    помощь(д.сохранён ? 'Токен задан и записан в .env.' : 'Токен задан на время работы.', false);
    return true;
  } finally { $('#сохранить').disabled = false; }
}
function помощь(текст, плохо){
  const p = document.createElement('p');
  p.className = 'помощь';
  p.style.color = плохо ? 'var(--ошибка)' : 'var(--успех)';
  p.textContent = текст;
  const прежний = document.getElementById('итог-токена');
  if(прежний) прежний.remove();
  p.id = 'итог-токена';
  $('#помощь-токен').after(p);
}
$('#сохранить').onclick = сохранитьТокен;
$('#токен').addEventListener('keydown', e => { if(e.key === 'Enter') сохранитьТокен(); });

$('#пуск').onclick = async () => {
  if($('#токен').value.trim()){ if(!await сохранитьТокен()) return; }
  const каталог = $('#каталог').value.trim();
  if(!каталог) return;
  $('#пуск').disabled = true;
  $('#строки').innerHTML = '';
  $('#ход').hidden = false;
  $('#шапка').textContent = 'Читаю каталог…';
  const s = new EventSource('/run?folder=' + encodeURIComponent(каталог));
  s.onmessage = e => {
    const д = JSON.parse(e.data);
    if(д.вид === 'файл'){
      доб('', 'Файл: ' + (д.файл || '') + (д.лист && д.лист !== '—' ? ' — лист «' + д.лист + '», строк ' + д.строк : ''), '');
    } else if(д.вид === 'строка'){
      const знак = д.действие === 'заполнено' ? д.уверенность : д.действие;
      const тело = д.url
        ? экран(д.фио) + ' — <a href="' + экран(д.url) + '" target="_blank" rel="noopener">' + экран(д.url) + '</a>'
        : экран(д.фио) + (д.примечание ? ' — ' + экран(д.примечание) : '');
      доб(д.номер + '/' + д.всего, тело, знак);
      $('#шапка').textContent = 'Обработано ' + д.номер + ' из ' + д.всего;
    } else if(д.вид === 'сохранено'){
      доб('', 'Сохранено: ' + экран(д.файл), '');
    } else if(д.вид === 'готово'){
      $('#шапка').textContent = д.текст;
      $('#пуск').disabled = false; s.close(); сводка();
    } else if(д.вид === 'ошибка'){
      доб('', 'Ошибка: ' + экран(д.текст), 'ошибка');
      $('#пуск').disabled = false; s.close(); сводка();
    }
  };
  s.onerror = () => { $('#пуск').disabled = false; s.close(); сводка(); };
};
function экран(т){ const d = document.createElement('div'); d.textContent = т ?? ''; return d.innerHTML; }
function доб(н, разметка, знак){
  const d = document.createElement('div');
  d.className = 'стр';
  d.innerHTML = '<span class="н">' + экран(н) + '</span><span>' + разметка + '</span>'
    + (знак ? '<span class="знак ' + экран(знак).replace(' ','-') + '">' + экран(знак) + '</span>' : '<span></span>');
  $('#строки').appendChild(d);
  d.scrollIntoView({block:'nearest'});
}

function адресДиска(путь){
  // disk:/Папка/Вложенная -> https://disk.yandex.ru/client/disk/Папка/Вложенная
  const хвост = (путь || '').trim().replace(/^disk:\/+/, '').replace(/^\/+/, '').replace(/\/+$/, '');
  const части = хвост ? хвост.split('/').map(encodeURIComponent).join('/') : '';
  return 'https://disk.yandex.ru/client/disk' + (части ? '/' + части : '');
}
function обновитьСсылку(){
  const путь = $('#каталог').value.trim();
  const цель = $('#ссылка-каталога');
  if(!путь){ цель.textContent = ''; return; }
  const адрес = адресДиска(путь);
  цель.innerHTML = 'Каталог на Диске: <a href="' + экран(адрес)
    + '" target="_blank" rel="noopener">' + экран(адрес) + '</a>';
}
$('#каталог').addEventListener('input', обновитьСсылку);

async function сводка(){
  let д;
  try { д = await (await fetch('/api/stats')).json(); } catch { return; }
  const цель = $('#сводка');
  if(!д.файлы || !д.файлы.length){
    цель.innerHTML = '<p class="пусто">Пока ничего не обработано.</p>'; return;
  }
  const шапка = ['Файл','Строк', ...ДЕЙСТВИЯ, ...УВЕРЕННОСТЬ];
  let html = '<table><thead><tr>' + шапка.map(с => '<th>' + с + '</th>').join('') + '</tr></thead><tbody>';
  for(const ф of д.файлы){
    html += '<tr><td>' + экран(ф.файл) + '</td><td>' + ф.строк + '</td>'
      + ДЕЙСТВИЯ.map(к => клетка(ф.действия[к])).join('')
      + УВЕРЕННОСТЬ.map(к => клетка(ф.уверенность[к])).join('') + '</tr>';
  }
  html += '</tbody><tfoot><tr><td>Всего: ' + д.итого.файлов + '</td><td>' + д.итого.строк + '</td>'
    + ДЕЙСТВИЯ.map(к => клетка(д.итого[к])).join('')
    + УВЕРЕННОСТЬ.map(к => клетка(д.итого[к])).join('') + '</tr></tfoot></table>';
  цель.innerHTML = html;
}
function клетка(н){ н = н || 0; return '<td' + (н ? '' : ' class="ноль"') + '>' + н + '</td>'; }

fetch('/api/state').then(r => r.json()).then(с => {
  if(с.токен_задан) $('#токен').placeholder = 'токен задан';
  if(с.каталог) $('#каталог').value = с.каталог;
}).catch(() => {}).finally(обновитьСсылку);
обновитьСсылку();
сводка();
</script></body></html>"""
