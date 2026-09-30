"""Каталог сайтов: чего предпочитаем, что дискриминируем, и с каким весом.

Правила лежат данными, а не в коде, поэтому их можно менять из приложения и
видеть целиком. Порядок разбора задан явно: первое совпавшее правило решает,
поэтому оценка одного и того же адреса не зависит ни от чего, кроме каталога.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

ФАЙЛ = "catalog.json"

# Класс задаёт и вес, и приоритет при равных баллах, и предельную уверенность.
# Чем меньше «порядок», тем выше кандидат встаёт при равенстве очков.
@dataclass(frozen=True)
class Класс:
    имя: str
    вес: int
    порядок: int
    потолок: str      # предельная уверенность: высокая | средняя | низкая
    описание: str


КЛАССЫ: dict[str, Класс] = {
    "предпочитаемый": Класс("предпочитаемый", 45, 0, "высокая",
                            "сайт, которому доверяем как публикации работодателя"),
    "государственный": Класс("государственный", 40, 1, "высокая",
                             "домен государственной организации"),
    "обычный": Класс("обычный", 0, 2, "высокая", "прочие сайты"),
    "новости": Класс("новости", -12, 3, "средняя",
                     "новостной сайт: сообщает о человеке, но не подтверждает должность"),
    "форум": Класс("форум", -25, 4, "средняя", "форум или блог: пишет кто угодно"),
    "реестр": Класс("реестр", -25, 5, "средняя",
                    "реестр или справочник: пересказывает чужие данные"),
    "соцсеть": Класс("соцсеть", -30, 6, "средняя", "соцсеть"),
}

ПОТОЛКИ = ("высокая", "средняя", "низкая")

# Умолчания собраны из разбора настоящих прогонов, а не придуманы.
УМОЛЧАНИЯ: dict[str, list[str]] = {
    "предпочитаемый": [],
    "государственный": [".gov.ru", ".gosuslugi.ru", ".mil.ru", ".edu.ru", ".ac.ru",
                        ".mos.ru", "gosweb.gosuslugi.ru"],
    "новости": ["ria.ru", "tass.ru", "rbc.ru", "kommersant", "iz.ru", "lenta.ru",
                "gazeta.ru", "interfax", "regnum", "vesti"],
    "форум": ["mybb.", "forum", "pikabu", "otzovik", "irecommend", "livejournal",
              "blogspot", "ucoz", "narod.ru"],
    "реестр": ["hh.ru", "zoon.ru", "prodoctorov", "spravka", "rusprofile", "list-org",
               "zachestnyibiznes", "sbis.", "orgpage", "yell.ru", "2gis", "profi.ru",
               "avito.ru", "linkedin.", "wikipedia.org", "wikiwand", "ru.ruwiki",
               "vuzopedia", "checko.ru", "audit-it", "seldon", "kartoteka"],
    "соцсеть": ["vk.com", "vk.ru", "ok.ru", "t.me", "telegram", "dzen.ru",
                "facebook.", "instagram.", "twitter.", "x.com"],
}

# Путь, по которому узнаётся раздел о сотрудниках. Значит это только на сайте,
# который сам не реестр, не соцсеть и не форум.
ПУТИ_СОТРУДНИКОВ = ("/sveden", "pedagogicheskiy-sostav", "pedagogical", "/struktura",
                    "/structure", "/staff", "/people", "/person", "/sotrudniki",
                    "/kafedr", "/prepodavateli", "/rukovodstvo", "/personal",
                    "/employee", "/teachers")


@dataclass
class Каталог:
    правила: dict[str, list[str]] = field(default_factory=dict)

    @classmethod
    def умолчания(cls) -> "Каталог":
        return cls(правила={к: list(в) for к, в in УМОЛЧАНИЯ.items()})

    @classmethod
    def прочитать(cls, путь: Path) -> "Каталог":
        """Битый или отсутствующий файл даёт умолчания, а не отказ."""
        if not путь.is_file():
            return cls.умолчания()
        try:
            данные = json.loads(путь.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return cls.умолчания()
        правила = {}
        for класс in КЛАССЫ:
            значения = данные.get(класс)
            правила[класс] = [str(з).strip().lower() for з in значения
                              if str(з).strip()] if isinstance(значения, list) else \
                list(УМОЛЧАНИЯ.get(класс, []))
        return cls(правила=правила)

    def записать(self, путь: Path) -> None:
        путь.write_text(json.dumps(self.правила, ensure_ascii=False, indent=2),
                        encoding="utf-8")

    def класс(self, url: str) -> Класс:
        """Первое совпавшее правило в заданном порядке классов.

        Порядок фиксирован списком ниже, поэтому один и тот же адрес получает
        один и тот же класс независимо от порядка строк в файле.
        """
        host = (urlsplit(url).hostname or "").lower()
        for имя in ("предпочитаемый", "соцсеть", "реестр", "форум", "государственный",
                    "новости"):
            for образец in self.правила.get(имя, ()):
                if образец and образец in host:
                    return КЛАССЫ[имя]
        return КЛАССЫ["обычный"]

    def свой_сайт(self, url: str) -> bool:
        """Сайт, на котором раздел о сотрудниках означает публикацию работодателя."""
        return self.класс(url).имя in ("предпочитаемый", "государственный",
                                       "обычный", "новости")
