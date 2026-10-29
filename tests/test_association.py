"""Casos pequeños donde conocemos el resultado."""
import unittest
import numpy as np
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules, fpgrowth
from src.association.pipeline import make_hours
from src.config import NUMERIC


class AssociationTests(unittest.TestCase):
    def test_complete_hours_and_energy(self):
        data = pd.DataFrame({name: np.ones(121) for name in NUMERIC})
        data['timestamp'] = pd.date_range('2024-01-01', periods=121, freq='min')
        data['was_imputed'] = False
        # 2 Wh por minuto suman 120 Wh en cada hora completa.
        data['Sub_metering_1'] = 2
        hours, basket = make_hours(data)
        self.assertEqual(len(hours), 2)
        self.assertEqual(hours.iloc[0]['Sub_metering_1_Wh'], 120)
        self.assertEqual(hours.iloc[0]['energia_global_kWh'], 1)
        self.assertTrue(basket.Cocina.all())
        self.assertNotIn('Lavandería', basket.columns)
        self.assertTrue(basket.Lunes.all())
        self.assertTrue(basket.Madrugada.all())
        self.assertEqual(basket.sum(axis=1).tolist(), [3, 3])

    def test_known_rule(self):
        basket = pd.DataFrame({'A': [True, True, False, False],
                               'B': [True, True, True, False]})
        for method in [apriori, fpgrowth]:
            found = method(basket, min_support=.5, use_colnames=True)
            rules = association_rules(found, metric='confidence', min_threshold=.6)
            rule = rules.loc[rules.antecedents == frozenset({'A'})].iloc[0]
            self.assertAlmostEqual(rule.support, .5)
            self.assertAlmostEqual(rule.confidence, 1)
            self.assertAlmostEqual(rule.lift, 4 / 3)


if __name__ == '__main__':
    unittest.main()
