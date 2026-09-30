import json
import tempfile
import unittest
from pathlib import Path

from yavoz import stats


def журнал(каталог: Path, файл: str, время: str, строки: list[dict],
           итого: dict, уверенность: dict) -> Path:
    путь = stats.путь_журнала(каталог, файл)
    путь.write_text(json.dumps({"файл": файл, "время": время, "строки": строки,
                                "итого": итого, "уверенность": уверенность},
                               ensure_ascii=False), encoding="utf-8")
    return путь


class Сводка(unittest.TestCase):
    def setUp(self) -> None:
        self.каталог = Path(tempfile.mkdtemp())
        # Имена подобраны так, чтобы алфавитный порядок противоречил порядку по
        # времени: по алфавиту «новый» раньше «старого», а свежий — «старый».
        журнал(self.каталог, "новый.xlsx", "2026-09-30 01:00:00",
               [{}] * 5, {"заполнено": 3, "пропущено": 1, "ошибка": 1},
               {"высокая": 2, "низкая": 1})
        журнал(self.каталог, "старый.xlsx", "2026-09-30 02:00:00",
               [{}] * 2, {"заполнено": 2}, {"средняя": 2})

    def test_пустой_каталог_даёт_пустую_сводку_а_не_отказ(self):
        self.assertEqual(stats.прочитать(Path(tempfile.mkdtemp())), [])

    def test_строки_считаются_по_журналу(self):
        по_файлам = {с.файл: с for с in stats.прочитать(self.каталог)}
        self.assertEqual(по_файлам["новый.xlsx"].строк, 5)
        self.assertEqual(по_файлам["старый.xlsx"].строк, 2)

    def test_свежие_сверху_а_не_по_алфавиту(self):
        имена = [с.файл for с in stats.прочитать(self.каталог)]
        # Алфавит дал бы обратное — значит проверка различает сортировку по времени
        # и её отсутствие, а не совпадает с ней случайно.
        self.assertEqual(имена, ["старый.xlsx", "новый.xlsx"])
        self.assertNotEqual(имена, sorted(имена))

    def test_все_действия_есть_даже_нулевые(self):
        второй = [с for с in stats.прочитать(self.каталог) if с.файл == "старый.xlsx"][0]
        self.assertEqual(set(второй.действия), set(stats.ДЕЙСТВИЯ))
        self.assertEqual(второй.действия["ошибка"], 0)

    def test_итого_складывает_по_всем_файлам(self):
        и = stats.итого(stats.прочитать(self.каталог))
        self.assertEqual(и["файлов"], 2)
        self.assertEqual(и["строк"], 7)
        self.assertEqual(и["заполнено"], 5)
        self.assertEqual(и["ошибка"], 1)
        self.assertEqual(и["высокая"], 2)
        self.assertEqual(и["средняя"], 2)

    def test_битый_журнал_пропускается_а_остальные_читаются(self):
        (self.каталог / f"{stats.ПРЕФИКС}битый.xlsx.json").write_text("{не json",
                                                                     encoding="utf-8")
        сводки = stats.прочитать(self.каталог)
        self.assertEqual(len(сводки), 2)

    def test_как_json_несёт_и_файлы_и_итого(self):
        д = stats.как_json(self.каталог)
        self.assertEqual(len(д["файлы"]), 2)
        self.assertEqual(д["итого"]["строк"], 7)


class Токен(unittest.TestCase):
    def setUp(self) -> None:
        import os
        from yavoz.secrets import ПЕРЕМЕННАЯ, Хранилище
        self.каталог = Path(tempfile.mkdtemp())
        self.env = self.каталог / ".env"
        self.env.write_text("YAVOZ_SEARCH=ddg\nYAVOZ_MAX_ROWS=5\n", encoding="utf-8")
        os.environ.pop(ПЕРЕМЕННАЯ, None)
        self.хранилище = Хранилище(self.env)

    def tearDown(self) -> None:
        import os
        from yavoz.secrets import ПЕРЕМЕННАЯ
        os.environ.pop(ПЕРЕМЕННАЯ, None)

    def test_пустой_токен_отвергается(self):
        with self.assertRaises(ValueError):
            self.хранилище.запомнить("   ")

    def test_в_памяти_без_записи_в_файл(self):
        self.хранилище.запомнить("значение", сохранить=False)
        self.assertTrue(self.хранилище.задан)
        self.assertNotIn("YADISK_TOKEN", self.env.read_text(encoding="utf-8"))

    def test_запись_сохраняет_соседние_строки(self):
        self.хранилище.запомнить("значение", сохранить=True)
        строки = self.env.read_text(encoding="utf-8").splitlines()
        self.assertIn("YAVOZ_SEARCH=ddg", строки)
        self.assertIn("YAVOZ_MAX_ROWS=5", строки)

    def test_повторная_запись_не_плодит_строки(self):
        self.хранилище.запомнить("раз", сохранить=True)
        self.хранилище.запомнить("два", сохранить=True)
        строки = self.env.read_text(encoding="utf-8").splitlines()
        self.assertEqual(sum(1 for с in строки if с.startswith("YADISK_TOKEN=")), 1)

    def test_файл_доступен_только_владельцу(self):
        self.хранилище.запомнить("значение", сохранить=True)
        self.assertEqual(self.env.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
