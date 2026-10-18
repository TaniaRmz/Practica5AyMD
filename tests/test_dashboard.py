from datetime import date
import unittest

from streamlit.testing.v1 import AppTest

from src.config import PROCESSED, ROOT


@unittest.skipUnless((PROCESSED / "prepared.parquet").exists(), "Primero ejecuta el pipeline")
class DashboardTests(unittest.TestCase):
    def test_filters_and_day_without_measurements(self):
        app = AppTest.from_file(str(ROOT / "visualization" / "app.py"), default_timeout=60).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.tabs), 5)
        app.sidebar.selectbox[0].set_value("Mes").run()
        self.assertEqual(len(app.exception), 0)
        app.radio[0].set_value("Z-score y componentes").run()
        self.assertEqual(len(app.exception), 0)
        # En el archivo de UCI este día no tiene mediciones de potencia.
        app.sidebar.date_input[0].set_value((date(2007, 4, 29), date(2007, 4, 29))).run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("No hay mediciones" in warning.value for warning in app.warning))


if __name__ == "__main__":
    unittest.main()
