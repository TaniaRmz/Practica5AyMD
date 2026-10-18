import pandas as pd


def observed_power(data):
    return data.loc[data["power_observed"], ["timestamp", "Global_active_power"]].copy()


def summarize(data, start, end):
    observed = observed_power(data)
    expected = int((pd.Timestamp(end) - pd.Timestamp(start)).total_seconds() / 60)
    return {
        "rows": len(data), "observed": len(observed),
        "coverage": len(observed) / expected if expected else 0,
        # La potencia está en kW y cada lectura representa un minuto.
        "energy_kwh": float(observed["Global_active_power"].sum() / 60),
        "mean_kw": float(observed["Global_active_power"].mean()),
        "peak_kw": float(observed["Global_active_power"].max()),
    }


def aggregate(data, frequency):
    observed = observed_power(data).set_index("timestamp")
    table = observed["Global_active_power"].resample(frequency).agg(["mean", "max", "count", "sum"])
    table["sum"] = table["sum"] / 60
    table.loc[table["count"] == 0, ["mean", "max", "sum"]] = float("nan")
    return table.rename(columns={"mean": "Potencia media (kW)", "max": "Pico (kW)",
                                 "count": "Minutos observados", "sum": "Energía observada (kWh)"})


def hourly_profile(data):
    observed = observed_power(data)
    return observed.groupby(observed["timestamp"].dt.hour)["Global_active_power"].mean()


def period_notes(data):
    profile = hourly_profile(data)
    values = observed_power(data)["Global_active_power"]
    threshold = values.quantile(0.9)
    high = values.ge(threshold)
    daily = aggregate(data, "D")
    covered = daily.loc[daily["Minutos observados"] >= 1440 * 0.95]
    notes = [
        f"La hora de mayor potencia media en este rango es {profile.idxmax():02d}:00 "
        f"({profile.max():.2f} kW).",
        f"Los minutos con al menos {threshold:.3f} kW representan {high.mean():.1%} "
        f"de las lecturas observadas y {values[high].sum() / values.sum():.1%} de su energía.",
    ]
    if not covered.empty:
        highest = covered["Potencia media (kW)"].idxmax()
        notes.append(f"Entre los días con al menos 95 % de cobertura, {highest.date()} "
                     f"tiene la mayor potencia media ({covered.loc[highest, 'Potencia media (kW)']:.2f} kW).")
    else:
        notes.append("No hay días con al menos 95 % de cobertura para comparar sus extremos.")
    return notes
