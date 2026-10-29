"""Ejecutar con: python -m src.association.pipeline"""

import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules, fpgrowth
from mlxtend.preprocessing import TransactionEncoder

from src.cleaning.preprocessing import clean_data
from src.config import NUMERIC, PROCESSED, RAW, ROOT

ROOMS = dict(zip(NUMERIC[-3:], ['Cocina', 'Lavandería', 'Climatización']))
DAYS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
SUPPORTS = [.005, .01, .02, .05, .1, .2, .4, .8]


def make_hours(clean, threshold=100):
    # Una hora incompleta puede parecer una hora de poco consumo. La quitamos.
    data = clean.set_index('timestamp')
    groups = data.resample('h')
    hours = groups[NUMERIC].mean()
    hours['minutos_validos'] = groups.size()
    hours['minutos_imputados'] = groups['was_imputed'].sum()
    hours = hours.loc[hours['minutos_validos'] == 60].copy()
    for column in ROOMS:
        # Cada lectura es energía en Wh de un minuto. La suma da Wh por hora.
        hours[column + '_Wh'] = groups[column].sum(min_count=60).reindex(hours.index)
    hours['energia_global_kWh'] = groups['Global_active_power'].sum(min_count=60).reindex(hours.index) / 60
    hours['Dia_semana'] = [DAYS[d] for d in hours.index.dayofweek]
    hours['Tiempo_dia'] = pd.cut(hours.index.hour, [-1, 5, 10, 13, 18, 23],
                                  labels=['Madrugada', 'Mañana', 'Mediodía', 'Tarde', 'Noche']).astype(str)
    hours['Habitaciones_Activas'] = hours.apply(
        lambda row: [room for column, room in ROOMS.items() if row[column + '_Wh'] > threshold], axis=1)
    transactions = [row.Habitaciones_Activas + [row.Dia_semana, row.Tiempo_dia]
                    for row in hours.itertuples()]
    encoder = TransactionEncoder()
    basket = pd.DataFrame(encoder.fit_transform(transactions), columns=encoder.columns_, index=hours.index)
    return hours, basket


def compare_algorithms(basket):
    records = []
    selected = None
    for support in SUPPORTS:
        outputs = {}
        timings = {'Apriori': [], 'FP-Growth': []}
        # Alternamos el orden y tomamos la mediana de tres ejecuciones.
        for repeat in range(3):
            methods = [('Apriori', apriori), ('FP-Growth', fpgrowth)]
            if repeat % 2:
                methods.reverse()
            for name, method in methods:
                start = perf_counter()
                outputs[name] = method(basket, min_support=support, use_colnames=True)
                timings[name].append(perf_counter() - start)
        left = outputs['Apriori'].set_index('itemsets')['support']
        right = outputs['FP-Growth'].set_index('itemsets')['support']
        same = set(left.index) == set(right.index)
        if not same or not np.allclose(left.values, right.reindex(left.index).values, atol=1e-12, rtol=0):
            raise ValueError('Los algoritmos dieron resultados diferentes.')
        for name in timings:
            records.append(dict(min_support=support, algoritmo=name, itemsets=len(outputs[name]),
                                segundos_mediana=float(np.median(timings[name])),
                                segundos_1=timings[name][0], segundos_2=timings[name][1],
                                segundos_3=timings[name][2], coinciden=True))
        if support == .01:
            selected = outputs['Apriori']
        print(f'Soporte {support:.3f}: {len(left)} conjuntos frecuentes. Coinciden.', flush=True)
    return pd.DataFrame(records), selected


def readable_rules(rules, n):
    result = rules[['antecedents', 'consequents', 'antecedent support', 'consequent support',
                    'support', 'confidence', 'lift', 'leverage', 'conviction']].copy()
    result.columns = ['antecedente', 'consecuente', 'soporte_antecedente', 'soporte_consecuente',
                      'soporte', 'confianza', 'lift', 'leverage', 'conviction']
    for col in ['antecedente', 'consecuente']:
        result[col] = result[col].map(lambda x: ' + '.join(sorted(x)))
    result['horas_conjuntas'] = np.rint(result['soporte'] * n).astype(int)
    return result.sort_values(['lift', 'soporte', 'antecedente', 'consecuente'], ascending=[False, False, True, True])


def run(input_path):
    PROCESSED.mkdir(parents=True, exist_ok=True)
    print('Limpiando las mediciones originales...', flush=True)
    clean, quality = clean_data(input_path)
    hours, basket = make_hours(clean)
    if hours.empty:
        raise ValueError('No hay horas completas para analizar.')
    sensitivity = []
    for threshold in [0, 50, 100, 200]:
        for column, room in ROOMS.items():
            sensitivity.append(dict(umbral_Wh=threshold, habitacion=room,
                                    soporte=float((hours[column + '_Wh'] > threshold).mean())))
    pd.DataFrame(sensitivity).to_csv(PROCESSED / 'sensibilidad_umbrales.csv', index=False)
    saved = hours.copy()
    saved['Habitaciones_Activas'] = saved['Habitaciones_Activas'].map(lambda x: json.dumps(x, ensure_ascii=False))
    saved.to_csv(PROCESSED / 'input_reglas_asociacion.csv', index_label='timestamp')
    basket.to_csv(PROCESSED / 'transacciones_reglas.csv', index_label='timestamp')
    comparison, itemsets = compare_algorithms(basket)
    comparison.to_csv(PROCESSED / 'comparacion_algoritmos.csv', index=False)
    export = itemsets.copy()
    export['itemsets'] = export['itemsets'].map(lambda x: ' + '.join(sorted(x)))
    export.to_csv(PROCESSED / 'itemsets_frecuentes.csv', index=False)
    rules = association_rules(itemsets, metric='confidence', min_threshold=.6)
    table = readable_rules(rules, len(hours))
    table.to_csv(PROCESSED / 'reglas_todas.csv', index=False)
    positive = table.loc[table.lift > 1].copy()
    positive.to_csv(PROCESSED / 'reglas_asociacion.csv', index=False)
    # Para explicar los resultados, buscamos reglas que terminen en una habitación.
    relevant = positive.loc[positive.consecuente.isin(ROOMS.values())].copy()
    relevant.to_csv(PROCESSED / 'reglas_habitaciones.csv', index=False)
    frequencies = basket.mean().sort_values(ascending=False)
    frequencies.rename('soporte').to_csv(PROCESSED / 'soporte_items.csv', index_label='item')
    # Revisamos las métricas contando las horas directamente, sin usar mlxtend.
    for rule in rules.itertuples():
        a = basket[list(rule.antecedents)].all(axis=1)
        b = basket[list(rule.consequents)].all(axis=1)
        support = (a & b).mean()
        assert np.isclose(support, rule.support)
        assert np.isclose(support / a.mean(), rule.confidence)
        assert np.isclose(support / (a.mean() * b.mean()), rule.lift)
    digest = hashlib.sha256()
    with input_path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    report = dict(quality=quality, horas_totales=int(clean.timestamp.dt.floor('h').nunique()),
                  horas_completas=len(hours), horas_con_imputacion=int((hours.minutos_imputados > 0).sum()),
                  inicio=str(hours.index.min()), fin=str(hours.index.max()), items=len(basket.columns),
                  umbral_Wh=100, min_support=.01, min_confidence=.6,
                  reglas_confianza=len(table), reglas_lift_positivo=len(positive),
                  reglas_habitaciones=len(relevant), sha256_original=digest.hexdigest(),
                  frecuencias=frequencies.to_dict())
    # El análisis describe todo el periodo. No estamos entrenando un pronóstico.
    report['sin_imputacion'] = int((hours.minutos_imputados == 0).sum())
    (PROCESSED / 'resultados_practica6.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    from src.association.presentation import create_outputs
    create_outputs(report, comparison, positive, relevant, pd.DataFrame(sensitivity))
    print(json.dumps({k: v for k, v in report.items() if k not in ['quality', 'frecuencias']}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Reglas de asociación del consumo por hora.')
    parser.add_argument('--input', type=Path, default=RAW / 'household_power_consumption.txt')
    args = parser.parse_args()
    run(args.input)
