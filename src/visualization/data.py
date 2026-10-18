"""Lectura de los archivos que ya procesamos."""

import json

import pandas as pd

from src.config import PROCESSED


def read_results(folder=PROCESSED):
    report = json.loads((folder / "results.json").read_text(encoding="utf-8"))
    data = pd.read_parquet(folder / "prepared.parquet")
    # Deshacemos el z-score solo para mostrar las unidades que conocemos.
    # El archivo preparado se conserva tal como salió del procesamiento.
    model = report["model"]
    physical = data.copy()
    for column in model["kept"]:
        physical[column] = data[column] * model["scaler_scale"][column] + model["scaler_mean"][column]
    return data, physical, report
