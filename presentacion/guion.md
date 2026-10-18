# Presentación de la práctica 5

## 1. Consumo eléctrico doméstico

Práctica 5 · Almacenes y Minería de Datos

Dataset de UCI: 2,075,259 mediciones de un hogar en Sceaux, Francia.

Periodo del archivo: 2006-12-16 a 2010-11-26. Frecuencia de un minuto.

Siete mediciones numéricas. Preparación para regresión y agrupamiento en prácticas posteriores.

## 2. Inspección y limpieza

Se detectaron 0 duplicados exactos y 0 fechas inválidas.

Unimos fecha y hora, ordenamos los minutos y convertimos las mediciones a números.

Tratamos signos de interrogación, celdas vacías, valores no numéricos y negativos como faltantes.

Se quitaron espacios de fecha y hora. No hay categorías de texto libres que necesiten cambios de mayúsculas o acentos.

## 3. Faltantes y orden temporal

Rellenamos hacia adelante hasta cinco minutos, usando solo el pasado. Evitamos inventar periodos largos.

Descartamos 25,823 filas aún incompletas. Quedan 2,049,436 filas y 156 tienen alguna imputación.

El corte del 80 % temporal es 2010-02-11 15:31:00. Reservamos el último bloque para evaluación futura.

La energía del dashboard excluye potencia imputada. Las banderas permiten identificar estos registros.

## 4. Potencia según la hora

La hora con mayor potencia media es 20:00 (1.90 kW). La menor corresponde a 04:00 (0.44 kW). La comparación usa solo lecturas observadas y puede cambiar por diferencias de cobertura.

## 5. Concentración del consumo

Los minutos con potencia de al menos 2.470 kW (percentil 90) representan 10.0% de las lecturas observadas y 32.2% de su energía. Los empates pueden superar el 10 % de los minutos.

La potencia indica la demanda de cada minuto. La energía suma potencia × duración, en kWh.

## 6. Comparación entre días

Entre los días con al menos 95 % de cobertura, 2006-12-23 tiene la mayor potencia media: 3.31 kW. Esto describe un día de este hogar, sin explicar la causa.

Comparamos potencia media y exigimos al menos 95 % de cobertura diaria para reducir el efecto de los huecos.

## 7. Normalización con z-score

Elegimos z-score porque las variables tienen escalas distintas y PCA depende de la varianza.

A cada valor le restamos la media del entrenamiento y lo dividimos entre su desviación estándar.

Los picos pueden ser consumos reales: los conservamos. Z-score no elimina su influencia ni los vuelve normales.

Ajustamos los parámetros solo en entrenamiento y los aplicamos sin cambios al bloque posterior.

## 8. Redundancia con Pearson

Calculamos Pearson solo en entrenamiento y elegimos |r| ≥ 0.95 para detectar relaciones lineales muy fuertes.

Conservamos la potencia activa primero por su utilidad al explicar el consumo.

Variables eliminadas: Global_intensity por su relación con Global_active_power (r = 0.9990).

PCA usa las variables que quedan. Una correlación alta no establece una causa.

## 9. Componentes principales

Retenemos 5 de 6 componentes con 97.27% de varianza del entrenamiento. Meta: al menos 95 %.

PC1 resume demanda global y submedidores, con voltaje en sentido opuesto. PC2 contrasta potencia reactiva y lavandería con calentador y aire acondicionado.

PC3 contrasta cocina y lavandería. PC4 combina potencia reactiva y calentador frente a cocina y lavandería. PC5 está dominado por voltaje.

## 10. Conclusiones y alcance

La limpieza deja datos ordenados y conserva una señal para distinguir mediciones observadas e imputadas.

Pearson conserva 6 variables y PCA resume su variación en 5 componentes.

Los patrones describen un solo hogar. La cobertura y los picos influyen en la interpretación.

El dataset queda preparado para modelos posteriores. Aquí todavía no entrenamos un predictor ni evaluamos su desempeño.

## Pesos para explicar PCA

PC1: los mayores pesos corresponden a Global_active_power (+0.61), Sub_metering_3 (+0.43), Voltage (-0.38). Contrapone las variaciones de Potencia activa (kW), Cocina (Wh por minuto), Lavandería (Wh por minuto), Calentador y aire acondicionado (Wh por minuto) frente a Voltaje (V). Esta lectura describe el eje, sin establecer causas.

PC2: los mayores pesos corresponden a Global_reactive_power (+0.68), Sub_metering_2 (+0.51), Sub_metering_3 (-0.50). Contrapone las variaciones de Potencia reactiva (kVAR), Lavandería (Wh por minuto) frente a Calentador y aire acondicionado (Wh por minuto). Esta lectura describe el eje, sin establecer causas.

PC3: los mayores pesos corresponden a Sub_metering_1 (+0.73), Sub_metering_2 (-0.58), Global_reactive_power (+0.27). Contrapone las variaciones de Cocina (Wh por minuto) frente a Lavandería (Wh por minuto). Esta lectura describe el eje, sin establecer causas.

PC4: los mayores pesos corresponden a Global_reactive_power (+0.63), Sub_metering_1 (-0.46), Sub_metering_2 (-0.44). Contrapone las variaciones de Potencia reactiva (kVAR), Calentador y aire acondicionado (Wh por minuto) frente a Cocina (Wh por minuto), Lavandería (Wh por minuto). Esta lectura describe el eje, sin establecer causas.

PC5: los mayores pesos corresponden a Voltage (+0.90), Sub_metering_3 (+0.31), Global_active_power (+0.23). Resume principalmente variaciones conjuntas de Voltaje (V), Calentador y aire acondicionado (Wh por minuto). Esta lectura describe el eje, sin establecer causas.
