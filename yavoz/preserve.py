"""Возврат в книгу того, что теряет openpyxl при сохранении.

openpyxl не умеет расширенные проверки данных (выпадающие списки) и молча
выбрасывает их. В рабочем файле это не мелочь: лист живёт этими списками.
Поэтому после сохранения переносим блок проверок из исходной книги в новую,
не трогая ничего другого.
"""
from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path

WORKBOOK = "xl/workbook.xml"
RELS = "xl/_rels/workbook.xml.rels"

# Блок проверок из расширения x14 стоит последним элементом листа.
EXTLST = re.compile(r"<extLst>.*?</extLst>", re.S)
# Обычные проверки (без расширения) идут перед hyperlinks/pageMargins.
DATAVAL = re.compile(r"<dataValidations\b.*?</dataValidations>", re.S)
# Идентификаторы ревизий тянут за собой объявление пространства имён xr.
XR_UID = re.compile(r'\s+xr:uid="[^"]*"')


def _листы(zf: zipfile.ZipFile) -> dict[str, str]:
    """Имя листа -> путь его XML внутри архива."""
    wb = zf.read(WORKBOOK).decode("utf-8")
    rels = zf.read(RELS).decode("utf-8")
    цели: dict[str, str] = {}
    for m in re.finditer(r"<Relationship\b([^>]*?)/>", rels):
        атр = m.group(1)
        rid = re.search(r'Id="([^"]+)"', атр)
        tgt = re.search(r'Target="([^"]+)"', атр)
        if rid and tgt:
            цели[rid.group(1)] = tgt.group(1)
    итог: dict[str, str] = {}
    for m in re.finditer(r"<sheet\b([^>]*?)/>", wb):
        атр = m.group(1)
        имя = re.search(r'name="([^"]+)"', атр)
        rid = re.search(r'r:id="([^"]+)"', атр)
        if not (имя and rid):
            continue
        путь = _путь_части(цели.get(rid.group(1), ""))
        if путь:
            итог[_разэкранировать(имя.group(1))] = путь
    return итог


def _путь_части(цель: str) -> str:
    """Target бывает «worksheets/s.xml», «/xl/worksheets/s.xml» и «xl/worksheets/s.xml»."""
    if not цель:
        return ""
    цель = цель.lstrip("/")
    return цель if цель.startswith("xl/") else f"xl/{цель}"


def _разэкранировать(s: str) -> str:
    return (s.replace("&amp;", "&").replace("&lt;", "<")
             .replace("&gt;", ">").replace("&quot;", '"').replace("&apos;", "'"))


def _вырезать(xml: str) -> tuple[str, str]:
    """Возвращает (блок extLst с проверками, обычный блок dataValidations)."""
    ext = ""
    for m in EXTLST.finditer(xml):
        if "dataValidation" in m.group(0):
            ext = m.group(0)
            break
    обычный = ""
    m = DATAVAL.search(xml)
    if m:
        обычный = m.group(0)
    return ext, обычный


def _вставить(xml: str, ext: str, обычный: str) -> str:
    if обычный and "<dataValidations" not in xml:
        # По схеме обычные проверки стоят перед hyperlinks, иначе перед pageMargins.
        for якорь in ("<hyperlinks>", "<pageMargins", "<legacyDrawing", "</worksheet>"):
            поз = xml.find(якорь)
            if поз != -1:
                xml = xml[:поз] + обычный + xml[поз:]
                break
    if ext:
        существующий = ""
        for m in EXTLST.finditer(xml):
            if "dataValidation" in m.group(0):
                существующий = m.group(0)
                break
        if существующий:
            xml = xml.replace(существующий, ext)
        else:
            поз = xml.rfind("</worksheet>")
            xml = xml[:поз] + ext + xml[поз:]
    return xml


def перенести_проверки(исходник: Path, цель: Path) -> dict[str, int]:
    """Копирует проверки данных из исходной книги в сохранённую. Меняет цель на месте."""
    отчёт: dict[str, int] = {}
    with zipfile.ZipFile(исходник) as zi:
        листы_и = _листы(zi)
        блоки: dict[str, tuple[str, str]] = {}
        for имя, путь in листы_и.items():
            try:
                xml = zi.read(путь).decode("utf-8")
            except KeyError:
                continue
            ext, обычный = _вырезать(xml)
            if ext or обычный:
                # xr:uid требует объявления пространства имён, которого может не быть
                блоки[имя] = (XR_UID.sub("", ext), XR_UID.sub("", обычный))
    if not блоки:
        return отчёт

    with zipfile.ZipFile(цель) as zt:
        листы_ц = _листы(zt)
        части = {n: zt.read(n) for n in zt.namelist()}
        инфо = {i.filename: i for i in zt.infolist()}

    for имя, (ext, обычный) in блоки.items():
        путь = листы_ц.get(имя)
        if not путь or путь not in части:
            continue
        xml = части[путь].decode("utf-8")
        новый = _вставить(xml, ext, обычный)
        if новый != xml:
            части[путь] = новый.encode("utf-8")
            отчёт[имя] = len(re.findall(r"<(?:x14:)?dataValidation\b", ext + обычный))

    времянка = цель.with_suffix(".tmp.xlsx")
    with zipfile.ZipFile(времянка, "w", zipfile.ZIP_DEFLATED) as zo:
        for имя_части, данные in части.items():
            zi_info = инфо.get(имя_части)
            zo.writestr(zi_info or имя_части, данные)
    shutil.move(времянка, цель)
    return отчёт
