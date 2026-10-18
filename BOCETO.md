# Boceto del dashboard para revisar en equipo

## Propósito

Explorar cuándo cambia la demanda eléctrica de este hogar y revisar cómo queda el dataset después de limpiarlo y reducir sus dimensiones.

## Distribución

```text
Título: Consumo eléctrico en casa

Barra lateral                 Vista de Consumo
-----------------------       -------------------------------------------
Rango de fechas               Energía | Potencia media | Pico | Cobertura
Agrupar día/semana/mes         -------------------------------------------
                              Potencia media en el tiempo
                              -------------------------------------------
                              Perfil por hora | Distribución de potencia
                              -------------------------------------------
                              Tabla por periodo y descarga

Pestañas adicionales: Calidad de datos / Pearson / PCA / Datos
```

## Preguntas que orientan las vistas

1. ¿En qué horas se observa mayor demanda media?
2. ¿Qué parte de la energía se concentra en los minutos de mayor potencia?
3. ¿Qué diferencias hay entre días con suficiente cobertura?
4. ¿Qué variables aportan información parecida y cómo se resume su variación con PCA?

## Justificación de las vistas

La línea muestra cambios temporales. El perfil por hora permite comparar horarios. El histograma muestra si predominan consumos bajos o si hay muchos picos. La tabla permite comprobar los valores. La cobertura acompaña los KPIs porque los datos faltantes pueden afectar las comparaciones.

Pearson y PCA tienen pestañas propias para explicar la preparación de los datos sin mezclar los valores estandarizados con las unidades físicas del consumo.
