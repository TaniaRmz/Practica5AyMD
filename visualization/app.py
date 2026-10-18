"""Para abrirlo: streamlit run visualization/app.py"""

from pathlib import Path
import sys

# Esto permite abrir la aplicación desde la carpeta del proyecto.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st

from src.config import LABELS, PROCESSED, SOURCE
from src.visualization.charts import distribution, heatmap, profile_chart, projection_chart, scree, time_chart
from src.visualization.data import read_results
from src.visualization.metrics import aggregate, hourly_profile, observed_power, period_notes, summarize

st.set_page_config(page_title="Consumo eléctrico | Práctica 5", page_icon="⚡", layout="wide")
st.title("Consumo eléctrico en casa")
st.caption("Práctica 5 · Almacenes y Minería de Datos · Un hogar, mediciones por minuto")


@st.cache_data(show_spinner="Cargando los datos preparados…", max_entries=1)
def load_data(version):
    return read_results(PROCESSED)


if not (PROCESSED / "results.json").exists() or not (PROCESSED / "prepared.parquet").exists():
    st.info("Primero coloca el dataset completo en data/data-raw/ y ejecuta el procesamiento.")
    st.code("python -m src.pipeline")
    st.markdown(f"[Descargar el dataset en UCI]({SOURCE})")
    st.stop()

version = (PROCESSED / "results.json").stat().st_mtime_ns
prepared, physical, report = load_data(version)
quality, model = report["quality"], report["model"]
first = pd.Timestamp(quality["start"]).date()
last = pd.Timestamp(quality["end"]).date()
with st.sidebar:
    st.header("Explorar los datos")
    dates = st.date_input("Rango de fechas", value=(first, last), min_value=first, max_value=last)
    level = st.selectbox("Agrupar por", ["Día", "Semana", "Mes"])
    st.caption("Los filtros se aplican a las pestañas Consumo y Datos.")
    st.divider()
    st.caption("Las pestañas Calidad, Pearson y PCA describen el procesamiento completo. Los ajustes usan solo entrenamiento.")
    st.markdown(f"[Fuente: UCI]({SOURCE})")

if len(dates) != 2:
    st.info("Selecciona una fecha inicial y una final.")
    st.stop()
start, end = pd.Timestamp(dates[0]), pd.Timestamp(dates[1]) + pd.Timedelta(days=1)
mask = physical["timestamp"].ge(start) & physical["timestamp"].lt(end)
view = physical.loc[mask]
consumption, quality_tab, pearson_tab, pca_tab, details = st.tabs(
    ["Consumo", "Calidad de datos", "Pearson", "PCA", "Datos"]
)

with consumption:
    if view.empty or not view["power_observed"].any():
        st.warning("No hay mediciones observadas en este periodo. Prueba otro rango.")
    else:
        # El primer y último día del archivo pueden estar incompletos.
        coverage_start = max(start, pd.Timestamp(quality["start"]))
        coverage_end = min(end, pd.Timestamp(quality["end"]) + pd.Timedelta(minutes=1))
        metrics = summarize(view, coverage_start, coverage_end)
        a, b, c, d = st.columns(4)
        a.metric("Energía observada", f"{metrics['energy_kwh']:,.1f} kWh")
        b.metric("Potencia media", f"{metrics['mean_kw']:.2f} kW")
        c.metric("Potencia máxima", f"{metrics['peak_kw']:.2f} kW")
        d.metric("Cobertura de potencia", f"{metrics['coverage']:.2%}")
        st.caption("La energía suma las mediciones observadas de potencia × 1/60 h. Excluye potencia imputada y minutos descartados. No estima el consumo de los huecos.")
        freq = {"Día": "D", "Semana": "W-MON", "Mes": "MS"}[level]
        summary = aggregate(view, freq)
        st.subheader("Cambios en el tiempo")
        st.plotly_chart(time_chart(summary), use_container_width=True)
        left, right = st.columns(2)
        with left:
            st.subheader("Perfil por hora")
            st.plotly_chart(profile_chart(hourly_profile(view)), use_container_width=True)
            st.caption("Compara la potencia media de cada hora. La cobertura desigual puede influir en el perfil.")
        with right:
            st.subheader("Distribución de potencia")
            values = observed_power(view)["Global_active_power"]
            st.plotly_chart(distribution(values), use_container_width=True)
        st.subheader("Lectura del periodo")
        for note in period_notes(view):
            st.write(note)
        st.caption("Son comparaciones descriptivas. La cobertura y la selección de fechas pueden cambiar los resultados.")
        st.subheader("Detalle del periodo")
        st.dataframe(summary, use_container_width=True)
        st.download_button("Descargar tabla del periodo", summary.to_csv().encode("utf-8-sig"),
                           "consumo_periodo.csv", "text/csv")

with quality_tab:
    st.subheader("Qué cambió durante la limpieza")
    a, b, c, d = st.columns(4)
    a.metric("Filas originales", f"{quality['initial_rows']:,}")
    b.metric("Filas preparadas", f"{quality['clean_rows']:,}")
    c.metric("Duplicados exactos", f"{quality['exact_duplicates']:,}")
    d.metric("Filas con imputación", f"{quality['imputed_rows']:,}")
    st.write("Se unen fecha y hora, se convierten las mediciones a números y se ordenan por minuto. Se rellena hacia adelante un máximo de cinco minutos. Las filas que aún tienen faltantes se descartan.")
    st.write(quality["text_normalization"])
    st.caption(f"Minutos ausentes en el archivo: {quality['missing_timestamps']:,}. Fechas inválidas: {quality['invalid_dates']:,}. Filas incompletas descartadas: {quality['dropped_incomplete_rows']:,}.")
    table = pd.DataFrame({"Tipo detectado": quality["initial_types"],
                          "Faltantes al cargar": quality["initial_missing"]})
    st.dataframe(table, use_container_width=True)
    st.subheader("Separación temporal")
    st.write(f"El entrenamiento termina antes de {quality['cutoff']}. Pearson, z-score y PCA se ajustan únicamente en ese bloque. El resto se transforma con los mismos parámetros.")
    st.dataframe(pd.Series(quality["partition_rows"], name="Filas"))

with pearson_tab:
    st.subheader("Relaciones entre las variables")
    st.caption("Correlaciones del bloque de entrenamiento, después de la limpieza.")
    corr = pd.read_csv(PROCESSED / "correlation.csv", index_col=0)
    st.plotly_chart(heatmap(corr), use_container_width=True)
    st.write("Usamos |r| ≥ 0.95 como umbral de redundancia. Se conserva la potencia activa primero por su utilidad para explicar el consumo. Después se revisan las otras variables en el orden del archivo.")
    if model["removed"]:
        st.dataframe(pd.DataFrame(model["removed"]), use_container_width=True)
    else:
        st.info("Ninguna variable supera el umbral ni es constante.")
    st.write("Variables conservadas: " + ", ".join(model["kept"]))
    st.caption("La correlación lineal no prueba causalidad. El orden de selección también influye en qué variable se conserva.")

with pca_tab:
    st.subheader("Una representación con menos dimensiones")
    st.write(f"PCA usa las variables conservadas, estandarizadas con z-score. Retenemos {model['components_retained']} componentes y {model['retained_variance']:.2%} de la varianza del entrenamiento, con una meta de al menos 95 %.")
    variance = pd.read_csv(PROCESSED / "variance.csv")
    st.plotly_chart(scree(variance), use_container_width=True)
    st.subheader("Pesos de las variables")
    st.caption("Coeficientes de las variables estandarizadas en cada componente. Un peso grande en valor absoluto indica mayor participación. El signo global del componente puede invertirse sin cambiar su significado.")
    weights = pd.read_csv(PROCESSED / "weights.csv", index_col=0)
    st.dataframe(weights.iloc[:, :model["components_retained"]].round(3), use_container_width=True)
    for line in report["component_notes"]:
        st.write(line)
    projection = pd.read_parquet(PROCESSED / "projection.parquet")
    st.plotly_chart(projection_chart(projection), use_container_width=True)
    st.write(report["projection_note"])
    st.caption(f"Vista de {len(projection):,} filas distribuidas uniformemente en el orden temporal, solo para dibujar. El procesamiento usa todas las filas limpias. Esta vista ayuda a explorar patrones, pero no demuestra grupos por sí sola.")

with details:
    st.subheader("Consultar las mediciones")
    units = st.radio("Mostrar valores", ["Unidades originales", "Z-score y componentes"], horizontal=True)
    selected = view if units == "Unidades originales" else prepared.loc[mask]
    st.caption("Se muestran hasta 1,000 filas. La descarga incluye hasta 50,000 filas del rango para mantenerla ligera.")
    st.dataframe(selected.head(1000).rename(columns=LABELS), use_container_width=True, hide_index=True)
    st.download_button("Descargar primeras 50,000 filas", selected.head(50000).to_csv(index=False).encode("utf-8-sig"),
                       "mediciones_periodo.csv", "text/csv")
