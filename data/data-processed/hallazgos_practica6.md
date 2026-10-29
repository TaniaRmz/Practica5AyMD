# Guion de la práctica 6

## 1. Reglas de asociación del consumo eléctrico

Práctica 6 · Almacenes y Minería de Datos

Buscamos actividades que coinciden durante una hora en un hogar.

Dataset de UCI: 2,075,259 mediciones por minuto. Periodo 2006-12-16 a 2010-11-26.

Continuamos el proyecto de la práctica 5 y reutilizamos su limpieza.

## 2. Una hora como transacción

Analizamos 34,141 horas con 60 minutos válidos. 56 horas incluyen algún minuto rellenado.

Sumamos los Wh de cada submedidor. Una habitación está activa cuando supera 100 Wh en la hora.

Comparamos 0, 50, 100 y 200 Wh. Elegimos 100 Wh para reducir actividad pequeña o de fondo. Puede omitir usos breves.

Madrugada 00–05, mañana 06–10, mediodía 11–13, tarde 14–18, noche 19–23. Añadimos el día de la semana.

## 3. Apriori y FP-Growth

Ejemplo didáctico: CMH, CMH, CH, MH, CM. C = Cocina; M = Mañana; H = Climatización. Soporte mínimo: 3 de 5 horas.

Apriori: cada ítem aparece 4 veces; cada par, 3. Probamos CMH: aparece 2 veces y se descarta. Si un subconjunto es infrecuente, podamos sus extensiones.

FP-Growth: ordenamos C → M → H y compartimos prefijos en un árbol. En los prefijos de H, C y M aparecen 3 veces cada uno; juntos, 2. Recuperamos CH y MH.

Coinciden los conjuntos y sus soportes en los ocho umbrales. Con soporte 0.5 % hay 166 conjuntos. Con 80 % hay 0.

Un soporte bajo conserva patrones menos frecuentes y aumenta la búsqueda. Uno alto pierde actividades poco comunes.

## 4. Comparación de tiempos

Medimos solo la búsqueda de conjuntos frecuentes sobre la misma tabla.

Alternamos el orden de los algoritmos y usamos la mediana de tres repeticiones por soporte.

Apriori fue más rápido en los ocho soportes. Con 1 %, tardó 0.0508 s frente a 0.0730 s de FP-Growth. Hay solo 15 ítems.

## 5. Soporte, confianza y lift

Soporte: proporción de horas con ambas partes de la regla. Confianza: proporción con el resultado entre las horas con el antecedente.

Lift: confianza dividida entre la frecuencia habitual del resultado. Un valor mayor que 1 indica asociación positiva.

Usamos soporte mínimo 1 % (al menos 342 horas) y confianza 60 % (seis de cada diez casos).

Conservamos 31 reglas con lift > 1. Son umbrales exploratorios, no valores universales.

## 6. Reglas con habitaciones como resultado

Cocina + Mañana ⇒ Climatización. Soporte 1.93%, confianza 92.56%, lift 1.89. Coinciden en 659 horas. El resultado aparece en 49.08% de todas las horas.

Lavandería + Mañana ⇒ Climatización. Soporte 1.04%, confianza 88.50%, lift 1.80. Coinciden en 354 horas. El resultado aparece en 49.08% de todas las horas.

Cocina + Lavandería ⇒ Climatización. Soporte 1.84%, confianza 85.09%, lift 1.73. Coinciden en 628 horas. El resultado aparece en 49.08% de todas las horas.

Estas reglas señalan coincidencias de climatización con otras actividades. No significan que la cocina encienda el calentador.

## 7. Utilidad y límites

Las coincidencias ayudan a ubicar horarios para revisar hábitos y uso simultáneo de aparatos.

Podrían orientar cambios de horario. Para afirmar ahorro hay que medir energía y considerar la tarifa.

Describimos un hogar durante el periodo analizado. Las reglas no demuestran causalidad ni orden temporal. Tampoco validan un pronóstico.

Climatización reúne calentador y aire acondicionado. Lavandería incluye refrigerador. No podemos distinguir cada aparato.

Fuente: Hebrail y Berard, UCI. DOI 10.24432/C58K54. Métodos: Apriori, FP-Growth y mlxtend.

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
