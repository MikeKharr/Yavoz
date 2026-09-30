import json
import tempfile
import unittest
from pathlib import Path

from yavoz.catalog import КЛАССЫ, Каталог
from yavoz.process import Кандидат, ключ_порядка
from yavoz.secrets import МАСКА, замаскировать


class КлассификацияСайтов(unittest.TestCase):
    def setUp(self) -> None:
        self.к = Каталог.умолчания()

    def test_каждый_домен_получает_ожидаемый_класс(self):
        случаи = {
            "https://shkola.gosweb.gosuslugi.ru/sveden": "государственный",
            "https://vk.ru/wall-1_2": "соцсеть",
            "https://www.rusprofile.ru/person/x": "реестр",
            "https://dmitrovsk1943.mybb.ru/viewtopic.php": "форум",
            "https://ria.ru/2026/x.html": "новости",
            "https://kursksu.ru/people/view/316": "обычный",
        }
        for url, ожидаем in случаи.items():
            self.assertEqual(self.к.класс(url).имя, ожидаем, url)

    def test_предпочитаемый_перебивает_прочие_классы(self):
        к = Каталог.умолчания()
        к.правила["предпочитаемый"] = ["kursksu.ru"]
        self.assertEqual(к.класс("https://kursksu.ru/x").имя, "предпочитаемый")
        # даже если домен попал и в дискриминируемые — предпочитаемый идёт первым
        к.правила["реестр"] = ["kursksu.ru"]
        self.assertEqual(к.класс("https://kursksu.ru/x").имя, "предпочитаемый")

    def test_порядок_строк_в_файле_на_класс_не_влияет(self):
        прямой = Каталог.умолчания()
        обратный = Каталог(правила={к: list(reversed(в))
                                    for к, в in прямой.правила.items()})
        for url in ("https://vk.ru/x", "https://rusprofile.ru/x", "https://ria.ru/x"):
            self.assertEqual(прямой.класс(url).имя, обратный.класс(url).имя, url)

    def test_реестр_соцсеть_и_форум_не_свой_сайт(self):
        for url in ("https://vk.ru/x", "https://rusprofile.ru/person/x",
                    "https://x.mybb.ru/y"):
            self.assertFalse(self.к.свой_сайт(url), url)

    def test_у_каждого_класса_потолок_из_набора(self):
        for кл in КЛАССЫ.values():
            self.assertIn(кл.потолок, ("высокая", "средняя", "низкая"), кл.имя)


class ЧтениеИЗапись(unittest.TestCase):
    def setUp(self) -> None:
        self.путь = Path(tempfile.mkdtemp()) / "catalog.json"

    def test_нет_файла_значит_умолчания(self):
        self.assertEqual(Каталог.прочитать(self.путь).правила,
                         Каталог.умолчания().правила)

    def test_битый_файл_не_роняет_а_даёт_умолчания(self):
        self.путь.write_text("{не json", encoding="utf-8")
        self.assertEqual(Каталог.прочитать(self.путь).правила,
                         Каталог.умолчания().правила)

    def test_записанное_читается_обратно(self):
        к = Каталог.умолчания()
        к.правила["предпочитаемый"] = ["kursksu.ru", "khsu.ru"]
        к.записать(self.путь)
        self.assertEqual(Каталог.прочитать(self.путь).правила["предпочитаемый"],
                         ["kursksu.ru", "khsu.ru"])

    def test_класс_без_списка_в_файле_берёт_умолчание(self):
        self.путь.write_text(json.dumps({"предпочитаемый": ["a.ru"]}), encoding="utf-8")
        к = Каталог.прочитать(self.путь)
        self.assertEqual(к.правила["предпочитаемый"], ["a.ru"])
        self.assertIn("vk.ru", к.правила["соцсеть"])


class Детерминированность(unittest.TestCase):
    """Порядок кандидатов не должен зависеть от очереди выдачи."""

    def кандидат(self, url, балл, порядок=2):
        return Кандидат(url=url, балл=балл, доводы=[], уверенность="низкая",
                        класс="обычный", порядок_класса=порядок)

    def test_при_равных_баллах_решает_класс(self):
        свой = self.кандидат("https://b.ru/x", 50, порядок=2)
        реестр = self.кандидат("https://a.ru/x", 50, порядок=5)
        self.assertLess(ключ_порядка(свой), ключ_порядка(реестр))

    def test_при_равных_баллах_и_классе_решает_глубина_пути(self):
        глубокий = self.кандидат("https://a.ru/staff/ivanov", 50)
        мелкий = self.кандидат("https://a.ru/x", 50)
        self.assertLess(ключ_порядка(глубокий), ключ_порядка(мелкий))

    def test_полное_совпадение_решает_алфавит_а_не_порядок_прихода(self):
        первый = self.кандидат("https://b.ru/x", 50)
        второй = self.кандидат("https://a.ru/x", 50)
        прямо = sorted([первый, второй], key=ключ_порядка)
        наоборот = sorted([второй, первый], key=ключ_порядка)
        self.assertEqual([к.url for к in прямо], [к.url for к in наоборот])
        self.assertEqual(прямо[0].url, "https://a.ru/x")

    def test_балл_важнее_класса(self):
        слабый_свой = self.кандидат("https://a.ru/x", 10, порядок=2)
        сильный_реестр = self.кандидат("https://b.ru/x", 90, порядок=5)
        self.assertLess(ключ_порядка(сильный_реестр), ключ_порядка(слабый_свой))


class Маска(unittest.TestCase):
    def test_видны_первые_два_и_последние_четыре(self):
        м = замаскировать("y0_AgAAAABxYzKeyEndHere")
        self.assertTrue(м.startswith("y0"))
        self.assertTrue(м.endswith("Here"))
        self.assertEqual(len(м), len("y0_AgAAAABxYzKeyEndHere"))

    def test_середина_скрыта_целиком(self):
        м = замаскировать("y0_AgAAAABxYzKeyEndHere")
        self.assertNotIn("AgAAAABxYzKey", м)
        self.assertEqual(м.count(МАСКА), len("y0_AgAAAABxYzKeyEndHere") - 6)

    def test_короткое_значение_не_раскрывается(self):
        self.assertEqual(замаскировать("abcdefgh"), МАСКА * 8)

    def test_пустое_остаётся_пустым(self):
        self.assertEqual(замаскировать(""), "")
        self.assertEqual(замаскировать("   "), "")

    def test_маску_нельзя_сохранить_как_токен(self):
        import os
        from yavoz.secrets import ПЕРЕМЕННАЯ, Хранилище
        os.environ.pop(ПЕРЕМЕННАЯ, None)
        х = Хранилище(Path(tempfile.mkdtemp()) / ".env")
        х.запомнить("y0_AgAAAABxYzKeyEndHere", сохранить=False)
        with self.assertRaises(ValueError):
            х.запомнить(х.маска, сохранить=True)
        self.assertEqual(х.значение, "y0_AgAAAABxYzKeyEndHere")
        os.environ.pop(ПЕРЕМЕННАЯ, None)


if __name__ == "__main__":
    unittest.main()
