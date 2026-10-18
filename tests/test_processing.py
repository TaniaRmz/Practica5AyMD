"""Revisamos que no se use el futuro y que la energía tenga las unidades correctas."""

from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from src.cleaning.preprocessing import clean_data
from src.cleaning.reduction import prepare_features
from src.config import NUMERIC
from src.visualization.metrics import summarize


def measurements(size=200):
    rng = np.random.default_rng(15)
    data = pd.DataFrame(rng.uniform(1, 10, (size, 7)), columns=NUMERIC)
    data.insert(0, "timestamp", pd.date_range("2007-01-01", periods=size, freq="min"))
    data["partition"] = np.where(np.arange(size) < size * 0.8, "entrenamiento", "evaluacion")
    data["was_imputed"] = False
    data["power_observed"] = True
    return data


class ProcessingTests(unittest.TestCase):
    def test_future_does_not_change_training(self):
        original = measurements()
        modified = original.copy()
        modified.loc[modified["partition"].eq("evaluacion"), NUMERIC] *= 1000
        first = prepare_features(original)
        second = prepare_features(modified)
        # Las operaciones numéricas pueden cambiar en el último decimal.
        self.assertEqual(first[-1]["kept"], second[-1]["kept"])
        self.assertEqual(first[-1]["removed"], second[-1]["removed"])
        for key in ["scaler_mean", "scaler_scale"]:
            np.testing.assert_allclose(list(first[-1][key].values()), list(second[-1][key].values()))
        np.testing.assert_allclose(first[-1]["pca_coefficients"], second[-1]["pca_coefficients"], atol=1e-12)
        self.assertAlmostEqual(first[-1]["retained_variance"], second[-1]["retained_variance"])
        pd.testing.assert_frame_equal(first[1], second[1])
        np.testing.assert_allclose(first[0].iloc[:160][NUMERIC], second[0].iloc[:160][NUMERIC])

    def test_short_fill_uses_past_and_long_gap_stays_missing(self):
        data = measurements(100)
        times = data.pop("timestamp")
        data["Date"] = times.dt.strftime("%d/%m/%Y")
        data["Time"] = times.dt.strftime("%H:%M:%S")
        data.loc[10:17, NUMERIC] = np.nan
        previous = data.loc[9, "Global_active_power"]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "raw.txt"
            data[["Date", "Time"] + NUMERIC].to_csv(path, sep=";", index=False)
            cleaned, report = clean_data(path)
        indexed = cleaned.set_index("timestamp")
        self.assertAlmostEqual(indexed.loc[times.iloc[10], "Global_active_power"], previous)
        self.assertFalse(indexed.loc[times.iloc[10], "power_observed"])
        self.assertNotIn(times.iloc[15], indexed.index)
        self.assertEqual(report["dropped_incomplete_rows"], 3)

    def test_energy_uses_minutes_and_excludes_imputation(self):
        data = measurements(60)
        data["Global_active_power"] = 6.0
        data.loc[0:9, "power_observed"] = False
        result = summarize(data, "2007-01-01", "2007-01-01 01:00:00")
        self.assertAlmostEqual(result["energy_kwh"], 5.0)
        self.assertAlmostEqual(result["coverage"], 50 / 60)


if __name__ == "__main__":
    unittest.main()
