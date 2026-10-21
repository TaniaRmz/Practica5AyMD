# Práctica 5: consumo eléctrico doméstico

Preparamos una serie de tiempo de consumo eléctrico para usarla en modelos de prácticas posteriores. El proyecto incluye limpieza, normalización con z-score, selección de variables con Pearson, PCA y un dashboard en Streamlit. La presentación tiene 10 diapositivas y se abre en el navegador.

## Dataset

Usamos **Individual Household Electric Power Consumption**, de Georges Hebrail y Alice Berard, disponible en [UCI](https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption), DOI [10.24432/C58K54](https://doi.org/10.24432/C58K54), licencia CC BY 4.0.

La fuente describe 2,075,259 registros de un hogar de Sceaux, Francia, entre diciembre de 2006 y noviembre de 2010. Son mediciones por minuto de potencia activa (kW), potencia reactiva (kVAR), voltaje (V), intensidad (A) y tres submedidores (Wh por minuto), además de fecha y hora. El archivo usa `;` como separador y contiene valores faltantes. Es un dataset multivariado y temporal, asociado a regresión y agrupamiento.

Los submedidores corresponden a cocina, lavandería y calentador/aire acondicionado. No representan por sí solos toda la energía del hogar.

## Cómo ejecutarlo

Se recomienda **Python 3.11 o 3.12** para instalar las versiones de `requirements.txt`.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

En Windows, activa el entorno con `.venv\Scripts\activate`.

1. Descarga y descomprime el dataset de UCI.
2. Coloca `household_power_consumption.txt` en `data/data-raw/`.
3. Desde la carpeta del proyecto, ejecuta:

```bash
python -m src.pipeline
python -m streamlit run visualization/app.py
```

Si el TXT está en la raíz del proyecto, el programa lo copia a `data/data-raw/`. También acepta una ruta con `python -m src.pipeline --input /ruta/household_power_consumption.txt`. Nunca modifica el contenido original. El procesamiento puede tardar unos minutos y necesita memoria para trabajar con más de dos millones de filas.

En esta computadora se puede usar el entorno de Anaconda ya instalado:

```bash
/opt/anaconda3/bin/python -m src.pipeline
/opt/anaconda3/bin/python -m streamlit run visualization/app.py
```

Para ver la presentación, abre `presentacion/practica5.html`. Funciona sin internet, incluye las gráficas y se controla con los botones o las flechas. `presentacion/guion.md` contiene el texto editable para preparar la exposición. Las cifras y los archivos de presentación se regeneran al procesar el dataset.

## Carpetas

```text
data/
  data-raw/             # Archivo original
  data-processed/       # Dataset preparado y resultados
src/
  cleaning/             # Limpieza, z-score, Pearson y PCA
  visualization/        # Carga, métricas y gráficas
  config.py
  pipeline.py           # Ejecuta el procesamiento
  presentation.py       # Genera las diapositivas con los resultados
visualization/
  app.py                # Entrada del dashboard
presentacion/
  practica5.html
  guion.md
tests/
README.md
requirements.txt
```

Seguimos la separación que pide el paso 7 del PDF: la entrada del dashboard está en `visualization/` y las funciones auxiliares en `src/`.

## Decisiones del proceso

### Inspección y limpieza

- Registramos filas, columnas, tipos detectados, faltantes, periodo temporal y estadísticos antes de rellenar datos. Todo queda en `data/data-processed/results.json`.
- Quitamos espacios de fecha y hora y las convertimos con formato día/mes/año. No hay categorías de texto libre que requieran unificar mayúsculas o acentos.
- Convertimos las siete mediciones a números. Tratamos `?`, celdas vacías, conversiones fallidas, infinitos y valores negativos como faltantes.
- Eliminamos duplicados exactos. Si hay dos mediciones diferentes del mismo minuto, el programa se detiene para revisarlas en lugar de escoger una sin criterio.
- Ordenamos por fecha y agregamos los minutos ausentes a la cuadrícula temporal. Rellenamos hacia adelante un máximo de cinco minutos por columna. Es un criterio sencillo para huecos cortos: usa solo observaciones anteriores y puede suavizar cambios bruscos. Los primeros cinco minutos de un hueco largo también se rellenan; el resto se descarta si sigue incompleto.
- Guardamos `was_imputed` para marcar filas con alguna imputación y `power_observed` para saber si la potencia activa era observada. No eliminamos automáticamente los picos altos porque pueden ser consumo real.

### Orden temporal y z-score

Separamos aproximadamente el primer 80 % de los minutos originales válidos y únicos para entrenamiento, y dejamos el último 20 % para evaluación futura. El corte se fija antes de eliminar filas incompletas, por eso el porcentaje final puede cambiar un poco. Un relleno al inicio del bloque posterior puede usar el último dato anterior, que ya pertenece al pasado.

Elegimos **z-score** porque las mediciones tienen unidades y escalas distintas y PCA usa la varianza. Ajustamos media y desviación estándar solo con entrenamiento, después transformamos todas las filas con esos mismos parámetros. Z-score no elimina valores atípicos ni convierte las distribuciones en normales. No evaluamos todavía ningún modelo predictivo.

### Pearson

Calculamos las correlaciones solo con entrenamiento. Usamos **|r| ≥ 0.95** como criterio de relación lineal muy fuerte. Recorremos las variables en el orden del archivo y quitamos una si tiene alta correlación con alguna ya conservada. Priorizamos `Global_active_power` por su interpretación y utilidad para el dashboard. También quitamos columnas constantes, si las hubiera.

El umbral es una decisión del proyecto, no una regla universal. El orden de las columnas influye en la selección. Las variables eliminadas y sus correlaciones quedan en `results.json`. La correlación no implica causalidad.

### PCA

Aplicamos PCA a las variables estandarizadas que quedaron después de Pearson. Se ajusta solo con entrenamiento. Retenemos el menor número de componentes que acumula **al menos 95 % de la varianza** de ese bloque, apoyándonos en la gráfica de varianza explicada.

`weights.csv` guarda los coeficientes de cada variable estandarizada en cada componente, llamados pesos o loadings en esta práctica. Los mayores valores absolutos indican mayor participación. El signo completo de un componente puede invertirse sin cambiar la solución. Los pesos no son las correlaciones variable-componente. El dashboard muestra la tabla y los pesos principales de cada componente retenido.

La proyección PC1-PC2 muestra hasta 6,000 filas distribuidas en el tiempo, solo para aligerar la visualización. El ajuste y la transformación usan **todas las filas limpias** de sus bloques. No hacemos el ejercicio opcional de reducción de numerosidad ni afirmamos que la proyección pruebe la existencia de grupos.

### Dataset preparado

`prepared.parquet` contiene fecha y hora, partición temporal, banderas de imputación, las variables conservadas en z-score y los componentes retenidos. Las variables redundantes no están en este archivo. `results.json` conserva las medias, escalas, centro y coeficientes de PCA, así como las decisiones y los resultados de calidad. Los CSV acompañantes permiten revisar Pearson, varianza y pesos.

El dashboard lee el dataset preparado. Para mostrar las unidades físicas, deshace el z-score en memoria con los parámetros guardados. No necesita volver a leer ni modificar el TXT original.

## Dashboard y boceto

La propuesta está en `BOCETO.md`, 
- **Consumo:** energía observada, potencia media y máxima, cobertura, evolución temporal, perfil por hora, distribución y tabla agregada. Filtros por fecha y agregación diaria, semanal o mensual.
- **Calidad de datos:** cambios de la limpieza y separación temporal.
- **Pearson:** mapa de calor, variables descartadas y criterio.
- **PCA:** varianza explicada, pesos y proyección en dos dimensiones.
- **Datos:** consulta de valores físicos o estandarizados y descarga limitada.

Los filtros de fecha afectan Consumo y Datos. Las otras pestañas describen el procesamiento completo y se indican como tales. En la agregación semanal, las fechas corresponden al cierre de semana en lunes, según `W-MON` de pandas.

**Unidades:** la potencia media se expresa en kW. Para calcular energía en kWh sumamos `Global_active_power / 60`, porque cada lectura representa un minuto. Solo incluimos potencia observada de las filas que sobreviven a la limpieza. La cobertura usa esos minutos sobre los minutos esperados del rango, limitado al inicio y final del archivo. No estimamos la energía de huecos ni presentamos la suma como consumo completo cuando falta cobertura.

## Resultados y exposición

Al ejecutar el dataset completo se obtuvieron **2,049,436 filas preparadas**, con 156 filas que tienen alguna imputación. No se encontraron duplicados exactos ni fechas inválidas. Se eliminó `Global_intensity` por su correlación de **0.99895** con potencia activa. PCA conservó **5 de 6 componentes**, con **97.27 %** de la varianza del entrenamiento.

La potencia media por hora fue mayor a las **20:00 (1.90 kW)** y menor a las **04:00 (0.44 kW)**. Los minutos por encima o iguales al percentil 90 de potencia acumularon **32.2 % de la energía observada**. Son resultados del periodo completo, no conclusiones para todos los hogares.

Los resultados calculados están en `data/data-processed/hallazgos.md`. Las tres vistas de hallazgos comparan horas, concentración de energía en minutos de mayor potencia y días con al menos 95 % de cobertura. Son resultados descriptivos de un hogar, no causas ni predicciones.



## Comprobaciones

```bash
python -m unittest discover -s tests -v
```

Se comprueba que modificar el bloque futuro no cambie el ajuste del entrenamiento, que el relleno use el pasado y respete su límite, y que la energía convierta correctamente los minutos y excluya la potencia imputada.

## Referencias

- [Dataset y descripción de variables en UCI](https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption).
- [StandardScaler, scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html).
- [PCA, scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html).
- [Documentación de Streamlit](https://docs.streamlit.io/).
