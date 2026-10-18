import plotly.express as px
import plotly.graph_objects as go
import numpy as np

TEAL = "#087F8C"


def style(fig):
    fig.update_layout(template="plotly_white", font=dict(family="Arial", color="#17324D"),
                      paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=15, r=15, t=40, b=25))
    return fig


def time_chart(table):
    fig = px.line(table, x=table.index, y="Potencia media (kW)",
                  labels={"timestamp": "Fecha"}, color_discrete_sequence=[TEAL])
    fig.update_traces(connectgaps=False)
    return style(fig)


def profile_chart(profile):
    fig = px.bar(x=profile.index, y=profile.values,
                 labels={"x": "Hora del día", "y": "Potencia media observada (kW)"},
                 color_discrete_sequence=[TEAL])
    fig.update_xaxes(dtick=2)
    return style(fig)


def heatmap(corr):
    fig = px.imshow(corr, zmin=-1, zmax=1, color_continuous_scale="RdBu_r",
                    text_auto=".2f", aspect="auto")
    fig.update_layout(height=550)
    return style(fig)


def scree(variance):
    fig = go.Figure()
    fig.add_bar(x=variance["component"], y=variance["explained"] * 100,
                name="Por componente", marker_color=TEAL)
    fig.add_scatter(x=variance["component"], y=variance["cumulative"] * 100,
                    name="Acumulada", mode="lines+markers", line_color="#D07824")
    fig.add_hline(y=95, line_dash="dash", annotation_text="95 %")
    fig.update_yaxes(title="Varianza explicada (%)", range=[0, 105])
    return style(fig)


def distribution(values):
    # Así enviamos 45 barras al navegador en lugar de millones de puntos.
    counts, edges = np.histogram(values, bins=45)
    return style(px.bar(x=(edges[:-1] + edges[1:]) / 2, y=counts,
                        labels={"x": "Potencia activa (kW)", "y": "Minutos"},
                        color_discrete_sequence=[TEAL]))


def projection_chart(projection):
    return style(px.scatter(projection, x="PC1", y="PC2", color="power_kw",
                            color_continuous_scale="Viridis", opacity=0.45,
                            labels={"power_kw": "Potencia (kW)"},
                            hover_data=["timestamp", "partition"]))
