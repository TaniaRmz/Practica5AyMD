"""Ejecutar desde la raíz: python -m src.pipeline"""

import argparse
import json
from pathlib import Path
import shutil

import numpy as np
import pandas as pd

from src.cleaning.preprocessing import clean_data
from src.cleaning.reduction import prepare_features
from src.config import LABELS, PROCESSED, RAW, ROOT, SOURCE
from src.presentation import create_presentation
from src.visualization.metrics import hourly_profile, observed_power


def describe_components(weights, count):
    notes = []
    for component in weights.columns[:count]:
        strongest = weights[component].abs().nlargest(3).index
        terms = ", ".join(f"{name} ({weights.loc[name, component]:+.2f})" for name in strongest)
        positive = [LABELS[name] for name in weights.index if weights.loc[name, component] >= 0.30]
        negative = [LABELS[name] for name in weights.index if weights.loc[name, component] <= -0.30]
        if positive and negative:
            meaning = f"Contrapone las variaciones de {', '.join(positive)} frente a {', '.join(negative)}."
        else:
            relevant = positive or negative or [LABELS[strongest[0]]]
            meaning = f"Resume principalmente variaciones conjuntas de {', '.join(relevant)}."
        notes.append(f"{component}: los mayores pesos corresponden a {terms}. {meaning} "
                     "Esta lectura describe el eje, sin establecer causas.")
    return notes


def make_findings(clean):
    observed = observed_power(clean)
    profile = hourly_profile(clean)
    peak_hour, low_hour = int(profile.idxmax()), int(profile.idxmin())
    values = observed["Global_active_power"]
    p90 = float(values.quantile(0.9))
    high = values.ge(p90)
    energy_share = float(values[high].sum() / values.sum())
    daily = observed.set_index("timestamp")["Global_active_power"].resample("D").agg(["mean", "count"])
    complete = daily.loc[daily["count"] >= 1440 * 0.95]
    if complete.empty:
        daily_note = "No hay días con al menos 95 % de cobertura. No se comparan extremos diarios."
    else:
        top = complete["mean"].idxmax()
        daily_note = (f"Entre los días con al menos 95 % de cobertura, {top.date()} "
                      f"tiene la mayor potencia media: {complete.loc[top, 'mean']:.2f} kW. "
                      "Esto describe un día de este hogar, sin explicar la causa.")
    return {
        "hour": f"La hora con mayor potencia media es {peak_hour:02d}:00 ({profile.loc[peak_hour]:.2f} kW). "
                f"La menor corresponde a {low_hour:02d}:00 ({profile.loc[low_hour]:.2f} kW). "
                "La comparación usa solo lecturas observadas y puede cambiar por diferencias de cobertura.",
        "concentration": f"Los minutos con potencia de al menos {p90:.3f} kW (percentil 90) "
                         f"representan {high.mean():.1%} de las lecturas observadas y "
                         f"{energy_share:.1%} de su energía. Los empates pueden superar el 10 % de los minutos.",
        "day": daily_note,
        "profile": {str(int(k)): float(v) for k, v in profile.items()},
        "p90": p90, "high_minutes_fraction": float(high.mean()), "high_energy_fraction": energy_share,
        "daily": [{"date": str(index.date()), "mean": float(row["mean"]), "count": int(row["count"])}
                  for index, row in complete.iterrows()],
    }


def run_pipeline(input_path, output=PROCESSED, presentation_dir=None):
    input_path, output = Path(input_path), Path(output)
    print("1/4 Cargando y limpiando el archivo…", flush=True)
    clean, quality = clean_data(input_path)
    print(f"    {quality['initial_rows']:,} filas originales; {len(clean):,} filas limpias.", flush=True)
    print("2/4 Calculando z-score, Pearson y PCA…", flush=True)
    prepared, corr, variance, weights, projection, model = prepare_features(clean)
    findings = make_findings(clean)
    projection_r = float(projection["PC1"].corr(projection["power_kw"]))
    projection_note = (f"En las filas dibujadas, PC1 y la potencia activa tienen r = {projection_r:.2f}. "
                       "El color ayuda a seguir ese gradiente de demanda en la proyección. "
                       "La vista no basta para afirmar que existan grupos separados.")
    report = {"source": SOURCE, "quality": quality, "model": model, "findings": findings,
              "projection_note": projection_note,
              "component_notes": describe_components(weights, model["components_retained"])}
    output.mkdir(parents=True, exist_ok=True)
    print("3/4 Guardando los datos preparados…", flush=True)
    prepared.to_parquet(output / "prepared.parquet", index=False)
    corr.to_csv(output / "correlation.csv")
    variance.to_csv(output / "variance.csv", index=False)
    weights.to_csv(output / "weights.csv")
    projection.to_parquet(output / "projection.parquet", index=False)
    # Guardamos el resumen al final para que la app encuentre todos los archivos.
    (output / "results.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    notes = "# Resultados del procesamiento\n\n"
    notes += f"Archivo original: {quality['initial_rows']:,} filas. Dataset preparado: {quality['clean_rows']:,} filas.\n\n"
    notes += f"Periodo: {quality['start']} a {quality['end']}. Corte temporal: {quality['cutoff']}.\n\n"
    notes += "## Hallazgos para revisar en equipo\n\n" + "\n\n".join(findings[k] for k in ["hour", "concentration", "day"])
    notes += "\n\n## Pearson\n\n" + json.dumps(model["removed"], ensure_ascii=False, indent=2)
    notes += f"\n\n## PCA\n\n{model['components_retained']} componentes, {model['retained_variance']:.2%} de varianza del entrenamiento.\n\n"
    notes += "\n\n".join(report["component_notes"])
    notes += "\n\n" + projection_note
    (output / "hallazgos.md").write_text(notes + "\n", encoding="utf-8")
    print("4/4 Preparando las 10 diapositivas…", flush=True)
    deck = Path(presentation_dir) if presentation_dir else output / "presentacion"
    create_presentation(report, variance, weights, deck)
    print(f"Listo. Resultados: {output.resolve()}", flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description="Preparación del consumo eléctrico doméstico.")
    parser.add_argument("--input", type=Path, help="Ruta del TXT original, separado por punto y coma.")
    args = parser.parse_args()
    target = RAW / "household_power_consumption.txt"
    source = args.input or target
    if args.input is None and (not target.exists() or target.stat().st_size == 0):
        source = ROOT / "household_power_consumption.txt"
    if not source.exists() or source.stat().st_size == 0:
        parser.exit(1, "Falta el dataset completo. Coloca household_power_consumption.txt en data/data-raw/.\n")
    # Copiamos el original a su carpeta sin cambiar su contenido.
    RAW.mkdir(parents=True, exist_ok=True)
    if source.resolve() != target.resolve():
        if target.exists() and target.stat().st_size:
            parser.exit(1, "Ya hay un original en data/data-raw/. Usa ese archivo o revisa las dos versiones.\n")
        shutil.copy2(source, target)
    try:
        run_pipeline(target, PROCESSED, ROOT / "presentacion")
    except (ValueError, KeyError) as error:
        parser.exit(1, f"No se pudo procesar el archivo: {error}\n")


if __name__ == "__main__":
    main()
