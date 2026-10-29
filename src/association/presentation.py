"""Gráficas y siete diapositivas con los resultados calculados."""
from html import escape
import json
import math
import plotly.graph_objects as go
from plotly.offline import get_plotlyjs
from src.config import PROCESSED, ROOT


def create_outputs(report, comparison, positive, relevant, sensitivity):
    folder = ROOT / 'presentacion'
    graphs = ROOT / 'graficas' / 'practica6'
    graphs.mkdir(parents=True, exist_ok=True)
    charts = {}
    for key, column, label in [('itemsets', 'itemsets', 'Conjuntos frecuentes'), ('tiempos', 'segundos_mediana', 'Tiempo (segundos)')]:
        fig = go.Figure()
        for name, rows in comparison.groupby('algoritmo', sort=False):
            fig.add_scatter(x=rows.min_support, y=rows[column], name=name, mode='lines+markers',
                            line=dict(dash='solid' if name == 'Apriori' else 'dash'))
        fig.update_layout(xaxis_title='Soporte mínimo', yaxis_title=label)
        fig.update_xaxes(type='log')
        charts[key] = fig
    fig = go.Figure()
    for room, rows in sensitivity.groupby('habitacion', sort=False):
        fig.add_scatter(x=rows.umbral_Wh, y=rows.soporte * 100, name=room, mode='lines+markers')
    fig.update_layout(xaxis_title='Umbral (Wh por hora)', yaxis_title='Horas activas (%)')
    charts['umbrales'] = fig
    fig = go.Figure(go.Scatter(x=positive.soporte * 100, y=positive.confianza * 100, mode='markers',
        text=positive.antecedente + ' ⇒ ' + positive.consecuente,
        marker=dict(color=positive.lift, colorscale='Viridis', showscale=True, colorbar=dict(title='Lift'))))
    fig.update_layout(xaxis_title='Soporte (%)', yaxis_title='Confianza (%)')
    charts['metricas'] = fig
    top = relevant.head(12).iloc[::-1]
    fig = go.Figure(go.Bar(x=top.lift, y=top.antecedente + ' ⇒ ' + top.consecuente, orientation='h'))
    fig.update_layout(xaxis_title='Lift', margin=dict(l=300), height=650)
    charts['reglas'] = fig
    for key, fig in charts.items():
        fig.update_layout(template='plotly_white', font=dict(family='Arial', size=17),
                          paper_bgcolor='#f6f4ef', plot_bgcolor='#f6f4ef',
                          legend=dict(orientation='h', y=1.18))
        fig.write_html(graphs / f'{key}.html', include_plotlyjs=True)
    chosen = relevant.head(3)
    descriptions = [f'{r.antecedente} ⇒ {r.consecuente}. Soporte {r.soporte:.2%}, confianza {r.confianza:.2%}, lift {r.lift:.2f}. Coinciden en {r.horas_conjuntas:,} horas. El resultado aparece en {r.soporte_consecuente:.2%} de todas las horas.' for r in chosen.itertuples()]
    counts = comparison.loc[comparison.algoritmo == 'Apriori'].set_index('min_support').itemsets
    slides = [
      ('Reglas de asociación del consumo eléctrico', [
        'Práctica 6 · Almacenes y Minería de Datos',
        'Buscamos actividades que coinciden durante una hora en un hogar.',
        f"Dataset de UCI: {report['quality']['initial_rows']:,} mediciones por minuto. Periodo {report['inicio'][:10]} a {report['fin'][:10]}.",
        'Continuamos el proyecto de la práctica 5 y reutilizamos su limpieza.'], None),
      ('Una hora como transacción', [
        f"Analizamos {report['horas_completas']:,} horas con 60 minutos válidos. {report['horas_con_imputacion']} horas incluyen algún minuto rellenado.",
        'Sumamos los Wh de cada submedidor. Una habitación está activa cuando supera 100 Wh en la hora.',
        'Comparamos 0, 50, 100 y 200 Wh. Elegimos 100 Wh para reducir actividad pequeña o de fondo. Puede omitir usos breves.',
        'Madrugada 00–05, mañana 06–10, mediodía 11–13, tarde 14–18, noche 19–23. Añadimos el día de la semana.'], 'umbrales'),
      ('Apriori y FP-Growth', [
        'Ejemplo didáctico: CMH, CMH, CH, MH, CM. C = Cocina; M = Mañana; H = Climatización. Soporte mínimo: 3 de 5 horas.',
        'Apriori: cada ítem aparece 4 veces; cada par, 3. Probamos CMH: aparece 2 veces y se descarta. Si un subconjunto es infrecuente, podamos sus extensiones.',
        'FP-Growth: ordenamos C → M → H y compartimos prefijos en un árbol. En los prefijos de H, C y M aparecen 3 veces cada uno; juntos, 2. Recuperamos CH y MH.',
        f'Coinciden los conjuntos y sus soportes en los ocho umbrales. Con soporte 0.5 % hay {counts.loc[.005]} conjuntos. Con 80 % hay {counts.loc[.8]}.',
        'Un soporte bajo conserva patrones menos frecuentes y aumenta la búsqueda. Uno alto pierde actividades poco comunes.'], 'itemsets'),
      ('Comparación de tiempos', [
        'Medimos solo la búsqueda de conjuntos frecuentes sobre la misma tabla.',
        'Alternamos el orden de los algoritmos y usamos la mediana de tres repeticiones por soporte.',
        f"Apriori fue más rápido en los ocho soportes. Con 1 %, tardó {comparison.loc[(comparison.algoritmo == 'Apriori') & (comparison.min_support == .01), 'segundos_mediana'].iloc[0]:.4f} s frente a {comparison.loc[(comparison.algoritmo == 'FP-Growth') & (comparison.min_support == .01), 'segundos_mediana'].iloc[0]:.4f} s de FP-Growth. Hay solo {report['items']} ítems."], 'tiempos'),
      ('Soporte, confianza y lift', [
        'Soporte: proporción de horas con ambas partes de la regla. Confianza: proporción con el resultado entre las horas con el antecedente.',
        'Lift: confianza dividida entre la frecuencia habitual del resultado. Un valor mayor que 1 indica asociación positiva.',
        f"Usamos soporte mínimo 1 % (al menos {math.ceil(report['horas_completas'] * .01)} horas) y confianza 60 % (seis de cada diez casos).",
        f"Conservamos {report['reglas_lift_positivo']} reglas con lift > 1. Son umbrales exploratorios, no valores universales."], 'metricas'),
      ('Reglas con habitaciones como resultado', descriptions + [
        'Estas reglas señalan coincidencias de climatización con otras actividades. No significan que la cocina encienda el calentador.'], None),
      ('Utilidad y límites', [
        'Las coincidencias ayudan a ubicar horarios para revisar hábitos y uso simultáneo de aparatos.',
        'Podrían orientar cambios de horario. Para afirmar ahorro hay que medir energía y considerar la tarifa.',
        'Describimos un hogar durante el periodo analizado. Las reglas no demuestran causalidad ni orden temporal. Tampoco validan un pronóstico.',
        'Climatización reúne calentador y aire acondicionado. Lavandería incluye refrigerador. No podemos distinguir cada aparato.',
        'Fuente: Hebrail y Berard, UCI. DOI 10.24432/C58K54. Métodos: Apriori, FP-Growth y mlxtend.'], None)
    ]
    sections = []
    for i, (title, lines, chart) in enumerate(slides):
        paragraphs = ''.join('<p>' + escape(line) + '</p>' for line in lines)
        box = f'<div class="chart" id="{chart}"></div>' if chart else ''
        sections.append(f'<section class="slide {"active" if i == 0 else ""}"><h1>{escape(title)}</h1><div class="content {"split" if chart else ""}"><div>{paragraphs}</div>{box}</div></section>')
    html = '''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Práctica 6</title><style>
*{box-sizing:border-box}body{margin:0;background:#f6f4ef;color:#17324d;font-family:Arial,sans-serif}.slide{display:none;padding:4vh 5vw 9vh;min-height:100vh}.slide.active{display:block}h1{font-size:clamp(30px,3.2vw,50px);margin:0 0 3vh}p{font-size:clamp(18px,1.65vw,26px);line-height:1.38;margin:0 0 2.5vh}.slide:nth-child(3) p{font-size:clamp(16px,1.35vw,21px);margin-bottom:2vh}.split{display:grid;grid-template-columns:44% 56%;gap:20px}.chart{height:64vh;min-width:0}nav{position:fixed;bottom:12px;right:4vw;display:flex;align-items:center;gap:14px}button{font:inherit;padding:7px 16px;background:#17324d;color:white;border:0;cursor:pointer}@media(max-width:800px){.split{display:block}.chart{height:45vh}.slide{padding-bottom:75px}}@media print{nav{display:none}.slide{display:block!important;page-break-after:always;height:100vh}}
</style><script>''' + get_plotlyjs() + '</script><main>' + ''.join(sections) + '</main>' + '''<nav><button id="prev">Anterior</button><span id="count"></span><button id="next">Siguiente</button><button id="full">Pantalla completa</button></nav><script>
const figures=PAYLOAD;const slides=[...document.querySelectorAll('.slide')];let current=0;const drawn=new Set();
function show(i){current=Math.max(0,Math.min(6,i));slides.forEach((s,n)=>s.classList.toggle('active',n===current));document.querySelector('#count').textContent=`${current+1} / 7`;const el=slides[current].querySelector('.chart');if(el){if(!drawn.has(el.id)){const f=figures[el.id];Plotly.newPlot(el,f.data,f.layout,{responsive:true,displayModeBar:false});drawn.add(el.id)}else Plotly.Plots.resize(el)}}
document.querySelector('#prev').onclick=()=>show(current-1);document.querySelector('#next').onclick=()=>show(current+1);document.querySelector('#full').onclick=()=>document.documentElement.requestFullscreen?.();document.addEventListener('keydown',e=>{if(['ArrowRight','PageDown',' '].includes(e.key)){e.preventDefault();show(current+1)}if(['ArrowLeft','PageUp'].includes(e.key))show(current-1)});show(0);
</script></html>'''.replace('PAYLOAD', json.dumps({k: json.loads(v.to_json()) for k, v in charts.items()}, ensure_ascii=False))
    (folder / 'practica6.html').write_text(html, encoding='utf-8')
    guide = '# Guion de la práctica 6\n\n' + '\n\n'.join(f'## {i + 1}. {title}\n\n' + '\n\n'.join(lines) for i, (title, lines, chart) in enumerate(slides))
    guide += """

## Apoyo para explicar la diapositiva 3: ejemplo paso a paso

Este ejemplo es inventado para explicar los algoritmos; no son cinco horas extraídas del dataset ni sus resultados reales. Omitimos los días y otras franjas para simplificar.

C = Cocina, M = Mañana, H = Climatización. Las cinco transacciones son:

| Hora | Ítems |
| --- | --- |
| 1 | C, M, H |
| 2 | C, M, H |
| 3 | C, H |
| 4 | M, H |
| 5 | C, M |

Con soporte mínimo de 60 %, un conjunto necesita aparecer en al menos 3 de las 5 horas.

### Apriori: generar, contar y podar

1. Contamos los ítems individuales: C = 4, M = 4 y H = 4. Todos tienen soporte 4/5 = 80 % y se conservan.
2. Formamos los pares CM, CH y MH. Cada uno aparece en 3 horas; su soporte es 3/5 = 60 %, por lo que todos son frecuentes.
3. Proponemos CMH. Sus tres pares son frecuentes, así que supera la poda y contamos sus apariciones. Solo aparece en las horas 1 y 2: 2/5 = 40 %. Se descarta y termina la búsqueda.
4. Para mostrar la poda: si añadimos Lavandería únicamente a la hora 1, su soporte sería 1/5 = 20 %. Apriori la elimina en el primer paso y evita contar cualquier par o conjunto mayor que la contenga. Ninguno puede aparecer más veces que Lavandería sola.

La propiedad Apriori permite podar por subconjuntos infrecuentes. Que todos los subconjuntos sean frecuentes no garantiza que el conjunto mayor lo sea: CMH lo ilustra.

### FP-Growth: construir y minar el árbol

1. Primera pasada: contamos los ítems y quitamos los que no llegan a 3 apariciones. C, M y H empatan con 4. Fijamos el desempate C, M, H para ordenar todas las transacciones de la misma manera.
2. Segunda pasada: insertamos las transacciones ordenadas, compartimos los prefijos e incrementamos los contadores de sus nodos. El árbol queda así:

```text
raíz
├── C:4
│   ├── M:3
│   │   └── H:2
│   └── H:1
└── M:1
    └── H:1
```

Los números cuentan transacciones que pasan por cada nodo; no son porcentajes. Por ejemplo, el camino C → M pasa por las horas 1, 2 y 5.

3. Para minar H, seguimos sus nodos y tomamos los prefijos con su multiplicidad: CM:2, C:1 y M:1. Esta es su base de patrones condicional.
4. En esa base, C suma 3 apariciones y M suma 3. Su árbol condicional tiene C:3 con un hijo M:2, y otra rama M:1 desde la raíz. Obtenemos CH y MH con soporte 3/5. CM junto con H solo tiene 2 apariciones, por lo que CMH no es frecuente.
5. Para M, la base condicional es C:3: obtenemos CM con soporte 3/5. Para C no hay prefijos. Junto con los ítems individuales, recuperamos los mismos seis conjuntos frecuentes que Apriori: C, M, H, CM, CH y MH.

FP-Growth busca mediante bases y árboles condicionales, sin enumerar candidatos como Apriori. Las dos pasadas se refieren a la base original; después trabaja recursivamente con esas estructuras.

### De los conjuntos frecuentes a una regla

Para C ⇒ H en el ejemplo: soporte = 3/5 = 60 %; confianza = 3/4 = 75 %; lift = 0.75/0.80 = 0.9375. Aunque pasa una confianza mínima de 60 %, se elimina al exigir lift > 1: H aparece en 80 % de todas las horas y solo en 75 % de las horas con C. Así se ve por qué la confianza sola no basta.

En los datos reales, Cocina + Mañana ⇒ Climatización tiene 659 horas conjuntas de 34,141; su antecedente aparece en 712 y Climatización en 16,757. Soporte = 659/34,141 = 1.93 %; confianza = 659/712 = 92.56 %; lift = (659/712)/(16,757/34,141) = 1.89. Esta regla sí supera soporte 1 %, confianza 60 % y lift > 1.

El ejemplo enseña el mecanismo. Las gráficas y tiempos de la presentación corresponden al dataset completo, con 15 ítems y ocho valores de soporte.
"""
    (folder / 'guion_practica6.md').write_text(guide, encoding='utf-8')
    (PROCESSED / 'hallazgos_practica6.md').write_text(guide, encoding='utf-8')
