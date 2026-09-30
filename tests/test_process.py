import tempfile
import unittest
from pathlib import Path

from tests.fixtures import книга, сколько_проверок
from yavoz import xlsx
from yavoz.process import Обработчик, выбрать, журнал
from yavoz.rank import ВЫСОКАЯ, НИЗКАЯ, Персона
from yavoz.search import Hit

СТРОКИ = [
    {"B": "Беспалов", "C": "Дмитрий", "D": "Викторович",
     "S": "Курский государственный университет",
     "T": "Декан факультета физической культуры и спорта"},
    {"B": "Осташенков", "C": "Александр", "D": "Павлович",
     "S": "Военный комиссариат города Чебоксары", "T": "Старший специалист-эксперт"},
    {"B": "Занятая", "C": "Строка", "D": "Проверенная", "S": "Школа", "T": "Учитель",
     "V": "https://уже.заполнено/ранее"},
]


class ПоискЗаглушка:
    """Отдаёт заранее заданную выдачу и считает вызовы."""

    def __init__(self, выдача: dict[str, list[Hit]]) -> None:
        self.выдача = выдача
        self.запросы: list[str] = []

    def find(self, query: str, limit: int = 10) -> list[Hit]:
        self.запросы.append(query)
        for ключ, hits in self.выдача.items():
            if ключ in query:
                return hits
        return []


def читатель(страницы: dict[str, str]):
    def читать(url: str) -> tuple[str, str]:
        return страницы.get(url, ""), ""
    return читать


class ВыборИсточника(unittest.TestCase):
    def test_официальная_страница_с_должностью_обходит_соцсеть(self):
        персона = Персона("Беспалов", "Дмитрий", "Викторович",
                          "Курский государственный университет",
                          "Декан факультета физической культуры и спорта")
        находки = [
            Hit("https://vk.ru/wall-1_2", "Беспалов Дмитрий", "поздравляем декана"),
            Hit("https://kursksu.ru/people/view/316", "Беспалов Дмитрий Викторович", ""),
        ]
        страницы = {
            "https://vk.ru/wall-1_2": "Беспалов Дмитрий Викторович поздравляем",
            "https://kursksu.ru/people/view/316":
                "Беспалов Дмитрий Викторович — декан факультета физической культуры и спорта "
                "Курского государственного университета",
        }
        кандидаты = выбрать(персона, находки, читатель(страницы))
        self.assertEqual(кандидаты[0].url, "https://kursksu.ru/people/view/316")
        self.assertEqual(кандидаты[0].уверенность, ВЫСОКАЯ)

    def test_когда_официального_нет_берём_лучшее_и_метим_низкой(self):
        персона = Персона("Осташенков", "Александр", "Павлович",
                          "Военный комиссариат города Чебоксары", "Старший специалист-эксперт")
        находки = [Hit("https://vk.ru/wall-2_3", "Осташенков Александр", "военкомат")]
        кандидаты = выбрать(персона, находки,
                            читатель({"https://vk.ru/wall-2_3": "Осташенков Александр Павлович"}))
        self.assertEqual(кандидаты[0].url, "https://vk.ru/wall-2_3")
        self.assertEqual(кандидаты[0].уверенность, НИЗКАЯ)


class ОбработкаФайла(unittest.TestCase):
    def setUp(self) -> None:
        self.каталог = Path(tempfile.mkdtemp())
        self.источник = книга(self.каталог / "исходный.xlsx", СТРОКИ)
        self.цель = self.каталог / "обработано исходный.xlsx"
        self.поиск = ПоискЗаглушка({
            "Беспалов": [Hit("https://kursksu.ru/people/view/316", "Беспалов", "")],
            "Осташенков": [Hit("https://vk.ru/wall-2_3", "Осташенков", "")],
        })
        self.страницы = {
            "https://kursksu.ru/people/view/316":
                "Беспалов Дмитрий Викторович декан факультета физической культуры и спорта",
            "https://vk.ru/wall-2_3": "Осташенков Александр Павлович",
        }

    def обработать(self):
        о = Обработчик(self.поиск, читатель=читатель(self.страницы))
        return о.файл(self.источник, self.цель)

    def test_u_заполняется_формулой_с_номером_строки(self):
        self.обработать()
        ws = xlsx.найти_лист(xlsx.открыть(self.цель))
        self.assertEqual(ws["U2"].value, xlsx.формула_запроса(2))
        self.assertIn("B3 & \" \" & C3", ws["U3"].value)

    def test_v_получает_ссылку_и_примечание_с_уверенностью(self):
        self.обработать()
        ws = xlsx.найти_лист(xlsx.открыть(self.цель))
        self.assertEqual(ws["V2"].value, "https://kursksu.ru/people/view/316")
        self.assertIsNotNone(ws["V2"].comment)
        self.assertIn("уверенность", ws["V2"].comment.text)

    def test_заполненный_v_не_трогаем_и_поиск_по_нему_не_зовём(self):
        итоги = self.обработать()
        занятая = [и for и in итоги if и.фио.startswith("Занятая")][0]
        self.assertEqual(занятая.действие, "пропущено")
        self.assertFalse(any("Занятая" in з for з in self.поиск.запросы))
        ws = xlsx.найти_лист(xlsx.открыть(self.цель))
        self.assertEqual(ws["V4"].value, "https://уже.заполнено/ранее")

    def test_выпадающие_списки_переживают_обработку(self):
        было = сколько_проверок(self.источник)
        self.assertGreater(было, 0, "стенд обязан дать книгу с проверками")
        self.обработать()
        self.assertEqual(сколько_проверок(self.цель), было)

    def test_остальные_листы_и_их_формулы_на_месте(self):
        self.обработать()
        кн = xlsx.открыть(self.цель)
        self.assertEqual(кн.sheetnames, ["БД в работе", "списки", "Аналитика"])
        self.assertEqual(кн["Аналитика"]["B1"].value, "=COUNTA('БД в работе'!B:B)")

    def test_отказ_поиска_не_роняет_файл_а_метит_строку(self):
        class Падающий:
            def find(self, query, limit=10):
                raise RuntimeError("сеть недоступна")
        о = Обработчик(Падающий(), читатель=читатель({}))
        итоги = о.файл(self.источник, self.цель)
        ошибки = [и for и in итоги if и.действие == "ошибка"]
        self.assertEqual(len(ошибки), 2)
        self.assertTrue(self.цель.exists(), "файл обязан сохраниться даже при отказах")

    def test_журнал_считает_действия_и_уверенность(self):
        данные = журнал(self.обработать(), "исходный.xlsx")
        self.assertEqual(данные["итого"]["заполнено"], 2)
        self.assertEqual(данные["итого"]["пропущено"], 1)
        self.assertIn(ВЫСОКАЯ, данные["уверенность"])


if __name__ == "__main__":
    unittest.main()


class ВыборИсточника2(unittest.TestCase):
    """Источник выбирается настройкой, и обязательность доступов от него зависит."""

    def test_по_умолчанию_бесплатный_и_ключи_яндекса_не_нужны(self):
        from yavoz.config import Config
        cfg = Config(yadisk_token="t", search_api_key="", folder_id="",
                     port=1, max_rows=0, источник="ddg")
        self.assertEqual(cfg.missing, [])

    def test_для_яндекса_ключ_и_каталог_обязательны(self):
        from yavoz.config import Config
        cfg = Config(yadisk_token="t", search_api_key="", folder_id="",
                     port=1, max_rows=0, источник="yandex")
        self.assertEqual(cfg.missing, ["YANDEX_SEARCH_API_KEY", "YANDEX_FOLDER_ID"])

    def test_токен_диска_обязателен_при_любом_источнике(self):
        from yavoz.config import Config
        for источник in ("ddg", "yandex"):
            cfg = Config(yadisk_token="", search_api_key="k", folder_id="f",
                         port=1, max_rows=0, источник=источник)
            self.assertIn("YADISK_TOKEN", cfg.missing)

    def test_неизвестный_источник_отказывает_а_не_молчит(self):
        from yavoz.search import SearchError, создать
        with self.assertRaises(SearchError):
            создать("выдуманный")

    def test_бесплатный_источник_выдерживает_паузу_между_запросами(self):
        import time as _time
        from yavoz.search import DuckSearch
        поиск = DuckSearch(пауза=0.05)
        поиск._DDGS = lambda: type("X", (), {"text": lambda *a, **k: []})()
        начало = _time.monotonic()
        поиск.find("раз")
        поиск.find("два")
        self.assertGreaterEqual(_time.monotonic() - начало, 0.05)


class ПараллельноеЧтение(unittest.TestCase):
    """Страницы читаются разом, но результат не зависит от порядка их прихода."""

    def персона(self):
        return Персона("Иванов", "Иван", "Иванович", "Школа 1", "Учитель истории")

    def находки(self, сколько=4):
        return [Hit(f"https://s{i}.ru/staff/ivanov", f"Иванов {i}", "")
                for i in range(сколько)]

    def test_читатель_зовётся_по_разу_на_каждый_верхний_адрес(self):
        звонки = []
        def читать(url):
            звонки.append(url)
            return "Иванов Иван Иванович учитель истории", ""
        выбрать(self.персона(), self.находки(6), читать)
        self.assertEqual(len(звонки), 4, "читаем ровно верхние четыре")
        self.assertEqual(len(set(звонки)), 4, "каждый адрес по одному разу")

    def test_разный_порядок_ответов_даёт_один_и_тот_же_итог(self):
        import time as _time
        медленный = "https://s0.ru/staff/ivanov"
        def читать(url):
            # Первый адрес отвечает последним — если бы порядок зависел от
            # времени ответа, итог бы поехал.
            if url == медленный:
                _time.sleep(0.05)
            return "Иванов Иван Иванович учитель истории", ""
        первый = выбрать(self.персона(), self.находки(), читать)
        второй = выбрать(self.персона(), list(reversed(self.находки())), читать)
        self.assertEqual([к.url for к in первый], [к.url for к in второй])

    def test_отказ_одной_страницы_не_роняет_остальные(self):
        def читать(url):
            if url.endswith("s1.ru/staff/ivanov"):
                return "", ""
            return "Иванов Иван Иванович учитель истории", ""
        к = выбрать(self.персона(), self.находки(), читать)
        self.assertEqual(len(к), 4)

    def test_страницы_читаются_разом_а_не_по_очереди(self):
        """Единственная проверка, различающая параллельное чтение и последовательное.

        Четыре страницы по 0,1 с: по очереди это 0,4 с, разом — около 0,1 с.
        Порог 0,25 с лежит между ними с запасом в обе стороны.
        """
        import time as _time
        def читать(url):
            _time.sleep(0.1)
            return "Иванов Иван Иванович учитель истории", ""
        начало = _time.monotonic()
        выбрать(self.персона(), self.находки(4), читать)
        прошло = _time.monotonic() - начало
        self.assertLess(прошло, 0.25, f"похоже на последовательное чтение: {прошло:.2f} с")
