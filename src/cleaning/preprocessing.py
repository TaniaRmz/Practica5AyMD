"""Limpieza del archivo, antes de escalar las columnas."""

import numpy as np
import pandas as pd

from src.config import NUMERIC


def clean_data(path, max_fill=5):
    if not path.exists() or path.stat().st_size == 0:
        raise ValueError(f"El archivo está vacío o no existe: {path}")
    raw = pd.read_csv(path, sep=";", na_values=["?", "", "nan"], low_memory=False)
    required = ["Date", "Time"] + NUMERIC
    missing = set(required) - set(raw.columns)
    if missing:
        raise ValueError(f"Faltan estas columnas: {sorted(missing)}")

    report = {
        "initial_rows": len(raw), "initial_columns": len(raw.columns),
        "initial_types": raw.dtypes.astype(str).to_dict(),
        "initial_missing": raw[required].isna().sum().astype(int).to_dict(),
    }
    # La fecha usa día/mes/año. Quitamos los espacios antes de convertirla.
    timestamp = pd.to_datetime(
        raw["Date"].astype("string").str.strip() + " "
        + raw["Time"].astype("string").str.strip(),
        format="%d/%m/%Y %H:%M:%S", errors="coerce",
    )
    data = raw[NUMERIC].apply(pd.to_numeric, errors="coerce")
    report["numeric_conversion_failures"] = (
        data.isna() & raw[NUMERIC].notna()
    ).sum().astype(int).to_dict()
    data = data.replace([np.inf, -np.inf], np.nan)
    # Una medición negativa de estas variables no tiene sentido físico.
    report["negative_values"] = (data < 0).sum().astype(int).to_dict()
    data = data.mask(data < 0)
    data.insert(0, "timestamp", timestamp)
    report["invalid_dates"] = int(timestamp.isna().sum())
    data = data.dropna(subset=["timestamp"])
    report["exact_duplicates"] = int(data.duplicated().sum())
    data = data.drop_duplicates().sort_values("timestamp")
    if data["timestamp"].duplicated().any():
        raise ValueError("Hay mediciones distintas para el mismo minuto. Revisa los duplicados.")
    if len(data) < 20:
        raise ValueError("Hay muy pocas filas para separar entrenamiento y evaluación.")
    if (data["timestamp"].dt.second != 0).any():
        raise ValueError("Se esperaban mediciones por minuto, sin segundos distintos de cero.")

    report["start"] = data["timestamp"].min().isoformat()
    report["end"] = data["timestamp"].max().isoformat()
    # Separamos antes de ajustar cualquier transformación.
    cutoff = data["timestamp"].iloc[int(len(data) * 0.8)]
    report["cutoff"] = cutoff.isoformat()
    expected = int((data["timestamp"].max() - data["timestamp"].min()).total_seconds() / 60) + 1
    report["missing_timestamps"] = expected - len(data)

    # Agregar los minutos ausentes evita llenar huecos de muchas horas como si fueran cortos.
    data = data.set_index("timestamp").asfreq("min")
    missing_before = data[NUMERIC].isna()
    power_observed = data["Global_active_power"].notna()
    report["missing_before_fill"] = missing_before.sum().astype(int).to_dict()
    report["descriptive_before_fill"] = data[NUMERIC].describe().to_dict()
    filled = data[NUMERIC].ffill(limit=max_fill)
    report["filled_cells"] = int((missing_before & filled.notna()).sum().sum())
    complete = filled.notna().all(axis=1)
    report["dropped_incomplete_rows"] = int((~complete).sum())
    clean = filled.loc[complete].copy()
    clean["was_imputed"] = missing_before.loc[complete].any(axis=1)
    clean["power_observed"] = power_observed.loc[complete]
    clean["partition"] = np.where(clean.index < cutoff, "entrenamiento", "evaluacion")
    clean = clean.reset_index()
    report["clean_rows"] = len(clean)
    report["imputed_rows"] = int(clean["was_imputed"].sum())
    report["partition_rows"] = clean["partition"].value_counts().astype(int).to_dict()
    report["max_fill_minutes"] = max_fill
    report["text_normalization"] = (
        "Se quitaron espacios de fecha y hora. No hay categorías de texto libres "
        "que necesiten cambios de mayúsculas o acentos."
    )
    return clean, report
