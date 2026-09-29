"""Выбор наиболее официального источника среди найденных страниц.

Оценка складывается из трёх независимых частей: класс домена, подсказки в пути
и то, что реально написано на странице. Ни одна часть сама по себе решения не
принимает — страница с правильным доменом, но без фамилии, проигрывает.
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from urllib.parse import urlsplit

import requests

TIMEOUT = 20
MAX_BYTES = 800_000

# Домены, где публикация означает официальное подтверждение.
ОФИЦИАЛЬНЫЕ = (".gov.ru", ".gosuslugi.ru", ".mil.ru", ".edu.ru", ".ac.ru", ".mos.ru")
# Обязательный раздел «Сведения об образовательной организации» и его соседи.
ПУТИ = ("/sveden", "pedagogicheskiy-sostav", "pedagogical", "/struktura", "/structure",
        "/staff", "/people", "/person", "/sotrudniki", "/kafedr", "/prepodavateli",
        "/rukovodstvo", "/personal", "/employee", "/teachers")
СОЦСЕТИ = ("vk.com", "vk.ru", "ok.ru", "t.me", "telegram", "dzen.ru", "livejournal",
           "facebook.", "instagram.", "twitter.", "x.com")
АГРЕГАТОРЫ = ("hh.ru", "zoon.ru", "prodoctorov", "spravka", "rusprofile", "list-org",
              "zachestnyibiznes", "sbis.ru", "orgpage", "yell.ru", "2gis", "profi.ru",
              "avito.ru", "linkedin.")
НОВОСТИ = ("ria.ru", "tass.ru", "rbc.ru", "kommersant", "iz.ru", "lenta.ru", "gazeta.ru",
           "interfax", "regnum", "news", "vesti")

СТОПСЛОВА = {"кафедры", "кафедра", "имени", "отдела", "отдел", "центра", "центр",
             "института", "институт", "факультета", "факультет", "школы", "школа",
             "университета", "университет", "филиала", "филиал", "управления",
             "города", "область", "области", "района", "район", "гбоу", "мбоу", "моу",
             "фгбоу", "маоу", "гапоу", "гбпоу", "мбудо", "гбуз", "фгаоу", "ноу", "ано"}


def нормализовать(текст: str) -> str:
    текст = (текст or "").lower().replace("ё", "е")
    return re.sub(r"[^0-9a-zа-я]+", " ", текст).strip()


def значимые(текст: str, минимум: int = 4) -> list[str]:
    слова = [с for с in нормализовать(текст).split() if len(с) >= минимум and с not in СТОПСЛОВА]
    # порядок сохраняем, повторы убираем
    видели, итог = set(), []
    for с in слова:
        if с not in видели:
            видели.add(с)
            итог.append(с)
    return итог


@dataclass
class Персона:
    фамилия: str
    имя: str
    отчество: str
    организация: str
    должность: str

    def запрос(self) -> str:
        части = [self.фамилия, self.имя, self.отчество, self.организация, self.должность]
        return " ".join(ч.strip() for ч in части if ч and ч.strip())


@dataclass
class Оценка:
    балл: int = 0
    доводы: list[str] = field(default_factory=list)

    def плюс(self, балл: int, довод: str) -> None:
        self.балл += балл
        self.доводы.append(f"{'+' if балл >= 0 else ''}{балл} {довод}")


def оценить_адрес(url: str) -> Оценка:
    """Часть оценки, которую видно по одному адресу, без загрузки страницы."""
    о = Оценка()
    host = (urlsplit(url).hostname or "").lower()
    path = urlsplit(url).path.lower()
    if any(host.endswith(d) or d.strip(".") + "." in host for d in ОФИЦИАЛЬНЫЕ):
        о.плюс(40, "государственный домен")
    if any(п in path for п in ПУТИ):
        о.плюс(25, "раздел о сотрудниках или структуре")
    if any(с in host for с in СОЦСЕТИ):
        о.плюс(-30, "соцсеть")
    if any(а in host for а in АГРЕГАТОРЫ):
        о.плюс(-25, "агрегатор или справочник")
    if any(н in host for н in НОВОСТИ):
        о.плюс(-12, "новостной сайт")
    if host.endswith(".ru") or host.endswith(".рф"):
        о.плюс(3, "российский домен")
    return о


def оценить_текст(текст: str, персона: Персона, заголовок: str = "") -> Оценка:
    """Часть оценки, которая опирается на то, что действительно есть на странице."""
    о = Оценка()
    т = нормализовать(текст)
    з = нормализовать(заголовок)
    фам = нормализовать(персона.фамилия)
    if фам and фам in т:
        о.плюс(20, "фамилия на странице")
        имя = нормализовать(персона.имя)
        отч = нормализовать(персона.отчество)
        if имя and имя in т:
            о.плюс(8, "имя на странице")
        if отч and отч in т:
            о.плюс(5, "отчество на странице")
        if фам in з:
            о.плюс(10, "фамилия в заголовке")
    слова_долж = значимые(персона.должность)
    if слова_долж:
        попало = sum(1 for с in слова_долж if с in т)
        if попало and попало >= max(1, len(слова_долж) // 2):
            о.плюс(25, f"должность на странице ({попало} из {len(слова_долж)})")
        elif попало:
            о.плюс(8, "должность упомянута частично")
    слова_орг = значимые(персона.организация, минимум=5)
    if слова_орг:
        попало = sum(1 for с in слова_орг if с in т)
        if попало >= max(1, len(слова_орг) // 2):
            о.плюс(12, "организация на странице")
    return о


def достал_текст(html_текст: str) -> str:
    """Грубое извлечение видимого текста: скрипты и стили выкидываем, теги снимаем."""
    без = re.sub(r"(?is)<(script|style|noscript).*?</\1>", " ", html_текст)
    без = re.sub(r"(?s)<[^>]+>", " ", без)
    return re.sub(r"\s+", " ", html.unescape(без)).strip()


def заголовок_страницы(html_текст: str) -> str:
    m = re.search(r"(?is)<title[^>]*>(.*?)</title>", html_текст)
    return html.unescape(re.sub(r"\s+", " ", m.group(1))).strip() if m else ""


def загрузить(url: str, session: requests.Session | None = None) -> tuple[str, str]:
    """Возвращает (видимый текст, заголовок). Пустые строки, если страница не далась."""
    s = session or requests.Session()
    try:
        r = s.get(url, timeout=TIMEOUT, stream=True,
                  headers={"User-Agent": "Mozilla/5.0 (compatible; Yavoz/1.0)"})
        if not r.ok:
            return "", ""
        куски, всего = [], 0
        for кусок in r.iter_content(65536):
            куски.append(кусок)
            всего += len(кусок)
            if всего >= MAX_BYTES:
                break
        сырой = b"".join(куски).decode(r.encoding or "utf-8", errors="replace")
    except requests.RequestException:
        return "", ""
    return достал_текст(сырой), заголовок_страницы(сырой)


ВЫСОКАЯ, СРЕДНЯЯ, НИЗКАЯ = "высокая", "средняя", "низкая"


def уверенность(балл: int, доводы: list[str]) -> str:
    есть = lambda ч: any(ч in д for д in доводы)  # noqa: E731
    официальный = есть("государственный домен") or есть("раздел о сотрудниках")
    if балл >= 70 and есть("фамилия на странице") and есть("должность на странице"):
        return ВЫСОКАЯ
    if балл >= 40 and есть("фамилия на странице") and (официальный or есть("должность")):
        return СРЕДНЯЯ
    return НИЗКАЯ
