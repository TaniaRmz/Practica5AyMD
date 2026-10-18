"""Presentación local en HTML. Las cifras salen del procesamiento."""

from html import escape
import json

from plotly.offline import get_plotlyjs


def create_presentation(report, variance, weights, folder):
    folder.mkdir(parents=True, exist_ok=True)
    q, m, f = report["quality"], report["model"], report["findings"]
    removed = "; ".join(
        f"{x['variable']} por su relación con {x['related_to']} (r = {x['r']:.4f})"
        if x["r"] is not None else f"{x['variable']} por ser constante"
        for x in m["removed"]
    ) or "Ninguna variable alcanza el umbral"
    slides = [
        ("Consumo eléctrico doméstico", [
            "Práctica 5 · Almacenes y Minería de Datos",
            f"Dataset de UCI: {q['initial_rows']:,} mediciones de un hogar en Sceaux, Francia.",
            f"Periodo del archivo: {q['start'][:10]} a {q['end'][:10]}. Frecuencia de un minuto.",
            "Siete mediciones numéricas. Preparación para regresión y agrupamiento en prácticas posteriores.",
        ], None),
        ("Inspección y limpieza", [
            f"Se detectaron {q['exact_duplicates']:,} duplicados exactos y {q['invalid_dates']:,} fechas inválidas.",
            "Unimos fecha y hora, ordenamos los minutos y convertimos las mediciones a números.",
            "Tratamos signos de interrogación, celdas vacías, valores no numéricos y negativos como faltantes.",
            q["text_normalization"],
        ], None),
        ("Faltantes y orden temporal", [
            "Rellenamos hacia adelante hasta cinco minutos, usando solo el pasado. Evitamos inventar periodos largos.",
            f"Descartamos {q['dropped_incomplete_rows']:,} filas aún incompletas. Quedan {q['clean_rows']:,} filas y {q['imputed_rows']:,} tienen alguna imputación.",
            f"El corte del 80 % temporal es {q['cutoff'].replace('T', ' ')}. Reservamos el último bloque para evaluación futura.",
            "La energía del dashboard excluye potencia imputada. Las banderas permiten identificar estos registros.",
        ], None),
        ("Potencia según la hora", [f["hour"]], "hours"),
        ("Concentración del consumo", [f["concentration"],
            "La potencia indica la demanda de cada minuto. La energía suma potencia × duración, en kWh."], "concentration"),
        ("Comparación entre días", [f["day"],
            "Comparamos potencia media y exigimos al menos 95 % de cobertura diaria para reducir el efecto de los huecos."], "daily"),
        ("Normalización con z-score", [
            "Elegimos z-score porque las variables tienen escalas distintas y PCA depende de la varianza.",
            "A cada valor le restamos la media del entrenamiento y lo dividimos entre su desviación estándar.",
            "Los picos pueden ser consumos reales: los conservamos. Z-score no elimina su influencia ni los vuelve normales.",
            "Ajustamos los parámetros solo en entrenamiento y los aplicamos sin cambios al bloque posterior.",
        ], None),
        ("Redundancia con Pearson", [
            "Calculamos Pearson solo en entrenamiento y elegimos |r| ≥ 0.95 para detectar relaciones lineales muy fuertes.",
            "Conservamos la potencia activa primero por su utilidad al explicar el consumo.",
            "Variables eliminadas: " + removed + ".",
            "PCA usa las variables que quedan. Una correlación alta no establece una causa.",
        ], None),
        ("Componentes principales", [
            f"Retenemos {m['components_retained']} de {len(m['kept'])} componentes con {m['retained_variance']:.2%} de varianza del entrenamiento. Meta: al menos 95 %.",
            "PC1 resume demanda global y submedidores, con voltaje en sentido opuesto. PC2 contrasta potencia reactiva y lavandería con calentador y aire acondicionado.",
            "PC3 contrasta cocina y lavandería. PC4 combina potencia reactiva y calentador frente a cocina y lavandería. PC5 está dominado por voltaje.",
        ], "variance"),
        ("Conclusiones y alcance", [
            "La limpieza deja datos ordenados y conserva una señal para distinguir mediciones observadas e imputadas.",
            f"Pearson conserva {len(m['kept'])} variables y PCA resume su variación en {m['components_retained']} componentes.",
            "Los patrones describen un solo hogar. La cobertura y los picos influyen en la interpretación.",
            "El dataset queda preparado para modelos posteriores. Aquí todavía no entrenamos un predictor ni evaluamos su desempeño.",
        ], None),
    ]
    blocks = []
    markdown = "# Presentación de la práctica 5\n\n"
    for i, (title, paragraphs, chart) in enumerate(slides, 1):
        text = "".join(f"<p>{escape(p)}</p>" for p in paragraphs)
        chart_html = f'<div id="{chart}" class="chart"></div>' if chart else ""
        blocks.append(f'<section class="slide{" active" if i == 1 else ""}" aria-label="Diapositiva {i}">'
                      f'<div class="eyebrow">PRÁCTICA 05 · {i:02d}/10</div><h1>{escape(title)}</h1>'
                      f'<div class="content {"with-chart" if chart else ""}"><div>{text}</div>{chart_html}</div>'
                      '<footer>Fuente: UCI, Individual Household Electric Power Consumption · doi:10.24432/C58K54</footer></section>')
        markdown += f"## {i}. {title}\n\n" + "\n\n".join(paragraphs) + "\n\n"
    markdown += "## Pesos para explicar PCA\n\n" + "\n\n".join(report["component_notes"])
    (folder / "guion.md").write_text(markdown + "\n", encoding="utf-8")
    chart_data = {
        "hours": {"x": list(f["profile"]), "y": list(f["profile"].values())},
        "concentration": {"x": ["Minutos de mayor potencia", "Resto de minutos"],
                          "y": [100 * f["high_energy_fraction"], 100 * (1 - f["high_energy_fraction"])]},
        "daily": {"x": [r["date"] for r in f["daily"]], "y": [r["mean"] for r in f["daily"]]},
        "variance": {"x": variance["component"].tolist(), "y": (100 * variance["explained"]).tolist(),
                     "cumulative": (100 * variance["cumulative"]).tolist()},
    }
    html = '''<!doctype html><html lang="es"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Práctica 5 · Consumo eléctrico</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f6f8fa;color:#17324d;font-family:Arial,sans-serif}
.slide{display:none;min-height:100vh;padding:5vh 6vw 11vh}.slide.active{display:flex;flex-direction:column}
.eyebrow{font-size:16px;font-weight:bold;letter-spacing:2px;color:#087f8c;margin-bottom:24px}
h1{font-size:clamp(32px,4.2vw,58px);line-height:1.12;margin:0 0 25px;max-width:1100px}
p{font-size:clamp(18px,1.7vw,24px);line-height:1.4;max-width:1060px;margin:0 0 18px}
.content{flex:1}.with-chart{display:grid;grid-template-columns:42% 55%;gap:3%;align-items:center}
.chart{height:46vh;min-height:290px}footer{font-size:13px;color:#53677c;margin-top:28px}
nav{position:fixed;bottom:0;left:0;right:0;background:#17324d;color:white;display:flex;justify-content:center;align-items:center;gap:28px;padding:10px}
button{background:transparent;border:1px solid #9fb5c9;border-radius:5px;color:white;padding:9px 15px;cursor:pointer;font-size:16px}
button:disabled{opacity:.35;cursor:default}#position{min-width:60px;text-align:center}
@media(max-width:750px){.with-chart{display:block}.slide{padding-bottom:100px}.chart{height:35vh}p{font-size:19px}}
@media print{nav{display:none}.slide,.slide.active{display:block;min-height:0;height:100vh;page-break-after:always}body{background:white}}
</style>'''
    html += "".join(blocks)
    html += '<nav aria-label="Navegación"><button id="prev">Anterior</button><span id="position" aria-live="polite">1 / 10</span><button id="next">Siguiente</button><button id="full">Pantalla completa</button></nav>'
    html += "<script>" + get_plotlyjs() + "</script>"
    html += "<script>const data=" + json.dumps(chart_data, ensure_ascii=False) + ";"
    html += '''
const slides=[...document.querySelectorAll('.slide')];let current=0;const drawn=new Set();
const names={hours:['Hora del día','Potencia media (kW)'],concentration:['','Energía observada (%)'],daily:['Fecha, días con cobertura ≥95 %','Potencia media (kW)'],variance:['Componente','Varianza explicada (%)']};
function draw(){const box=slides[current].querySelector('.chart');if(!box)return;const id=box.id;
if(drawn.has(id)){Plotly.Plots.resize(box);return;}const d=data[id];
let traces=[{x:d.x,y:d.y,type:id==='daily'?'scatter':'bar',mode:'lines',marker:{color:'#087f8c'},line:{color:'#087f8c'},name:'Por componente'}];
if(id==='variance')traces.push({x:d.x,y:d.cumulative,type:'scatter',mode:'lines+markers',name:'Acumulada',line:{color:'#d07824'}});
Plotly.newPlot(box,traces,{paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',font:{family:'Arial',size:16,color:'#17324d'},margin:{t:25,l:65,r:20,b:65},showlegend:id==='variance',legend:{orientation:'h',y:1.2},xaxis:{title:names[id][0]},yaxis:{title:names[id][1]}},{responsive:true,displayModeBar:false});drawn.add(id);}
function show(i){current=Math.max(0,Math.min(slides.length-1,i));slides.forEach((s,n)=>s.classList.toggle('active',n===current));
document.querySelector('#position').textContent=`${current+1} / ${slides.length}`;document.querySelector('#prev').disabled=current===0;document.querySelector('#next').disabled=current===slides.length-1;draw();}
document.querySelector('#prev').onclick=()=>show(current-1);document.querySelector('#next').onclick=()=>show(current+1);
document.querySelector('#full').onclick=()=>{if(!document.fullscreenElement)document.documentElement.requestFullscreen?.();else document.exitFullscreen?.();};
document.addEventListener('keydown',e=>{if(['ArrowRight','PageDown',' '].includes(e.key)){e.preventDefault();show(current+1);}if(['ArrowLeft','PageUp'].includes(e.key)){e.preventDefault();show(current-1);}if(e.key==='Home')show(0);if(e.key==='End')show(slides.length-1);});show(0);
</script></html>'''
    (folder / "practica5.html").write_text(html, encoding="utf-8")
