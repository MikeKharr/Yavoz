"""Сборка временной книги, похожей на рабочую: четыре листа и выпадающие списки."""
from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path

from openpyxl import Workbook

ШАПКА = {"A": " ID Лектора", "B": "Фамилия", "C": "Имя", "D": "Отчество",
         "S": "Место работы", "T": "Должность",
         "U": "Ссылка на подтверждение по запросу",
         "V": "Ссылка на подтверждение в интеренете"}

# Блок из настоящего файла: проверки данных живут в расширении x14.
EXTLST = (
    '<extLst><ext uri="{CCE6A557-97BC-4b89-ADB6-D9C93CAAB3DF}"'
    ' xmlns:x14="http://schemas.microsoft.com/office/spreadsheetml/2009/9/main">'
    '<x14:dataValidations count="1"'
    ' xmlns:xm="http://schemas.microsoft.com/office/excel/2006/main">'
    '<x14:dataValidation type="list" allowBlank="1">'
    "<x14:formula1><xm:f>списки!$E$2:$E$9</xm:f></x14:formula1>"
    "<xm:sqref>P2:P50</xm:sqref>"
    "</x14:dataValidation></x14:dataValidations></ext></extLst>"
)


def книга(путь: Path, строки: list[dict], с_проверками: bool = True) -> Path:
    wb = Workbook()
    лист = wb.active
    лист.title = "БД в работе"
    for столбец, текст in ШАПКА.items():
        лист[f"{столбец}1"] = текст
    for i, данные in enumerate(строки, start=2):
        for столбец, значение in данные.items():
            лист[f"{столбец}{i}"] = значение
    справочник = wb.create_sheet("списки")
    справочник["E1"] = "Итоговый статус по СН"
    справочник["E2"] = "Подтверждено"
    аналитика = wb.create_sheet("Аналитика")
    аналитика["A1"] = "Итог"
    аналитика["B1"] = "=COUNTA('БД в работе'!B:B)"
    wb.save(путь)
    if с_проверками:
        _вживить(путь)
    return путь


def _вживить(путь: Path) -> None:
    """Добавляет блок проверок в XML первого листа — openpyxl так не умеет."""
    времянка = путь.with_suffix(".src.xlsx")
    with zipfile.ZipFile(путь) as zin:
        части = {n: zin.read(n) for n in zin.namelist()}
    цель = next(n for n in части if re.fullmatch(r"xl/worksheets/sheet1\.xml", n))
    xml = части[цель].decode("utf-8")
    части[цель] = xml.replace("</worksheet>", EXTLST + "</worksheet>").encode("utf-8")
    with zipfile.ZipFile(времянка, "w", zipfile.ZIP_DEFLATED) as zout:
        for имя, данные in части.items():
            zout.writestr(имя, данные)
    shutil.move(времянка, путь)


def сколько_проверок(путь: Path) -> int:
    with zipfile.ZipFile(путь) as z:
        всего = 0
        for имя in z.namelist():
            if имя.startswith("xl/worksheets/"):
                всего += len(re.findall(r"<(?:x14:)?dataValidation\b",
                                        z.read(имя).decode("utf-8")))
    return всего
