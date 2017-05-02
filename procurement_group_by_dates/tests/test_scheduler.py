# -*- coding: utf-8 -*-
# Copyright 2017 SYLEAM Info Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date, timedelta
from odoo import fields
from .common import ProcurementTransactionCase


class TestScheduler(ProcurementTransactionCase):
    def setUp(self):
        super(TestScheduler, self).setUp()

    def _test_group_procurements_by_date(
            self, test_data):
        """
        Create moves with delays, and check created procurements
        """
        products = {}
        for product_name, product_data in test_data.items():
            # Create some products
            orderpoint_data = product_data['orderpoint']
            products[product_name] = self.create_product(
                product_name, horizon=orderpoint_data.get('horizon', 0),
                regroupment=orderpoint_data.get('regroupment', 1),
            )

            # Create some moves
            for data in product_data['moves']:
                move_date = date.today() + timedelta(days=data.get('delay', 0))
                move = self.create_move(
                    products[product_name], move_date,
                    quantity=data.get('quantity', 1))
                move.action_confirm()

        # Run the scheduler
        self.env['procurement.order'].run_scheduler()

        # Check created procurements
        for product_name, product_data in test_data.items():
            procurements = self.env['procurement.order'].search([
                ('product_id', '=', products[product_name].id),
            ], order='date_planned')

            # Check the procurements count (the list of results can be empty)
            self.assertEqual(len(procurements), len(product_data['results']))

            # Check the quantity of each procurement independently
            for procurement, results in zip(
                    procurements, product_data['results']):
                expected_date = date.today() + timedelta(
                    days=results['delay'])
                procurement_date = fields.Date.from_string(
                    procurement.date_planned)
                self.assertEqual(procurement.product_qty, results['quantity'])
                self.assertEqual(procurement_date, expected_date)

            # Check the last_execution_date of the orderpoint
            last_delay = product_data['last_execution_delay']
            last_date = fields.Date.from_string(
                products[product_name].orderpoint_ids.last_execution_date)
            self.assertEqual(
                last_date, date.today() + timedelta(days=last_delay))

    def test_standard_behaviour(self):
        self._test_group_procurements_by_date({
            'Product 1': {
                'orderpoint': {},
                'moves': [{'delay': 1}],
                'results': [
                    {'quantity': 1, 'delay': 0},
                ],
                'last_execution_delay': 1,
            },
            'Product 2': {
                'orderpoint': {},
                'moves': [{'delay': 1}],
                'results': [
                    {'quantity': 1, 'delay': 0},
                ],
                'last_execution_delay': 1,
            },
        })

    def test_high_horizon_behaviour(self):
        self._test_group_procurements_by_date({
            'Product 1': {
                'orderpoint': {'horizon': 90},
                'moves': [{}],
                'results': [
                    {'quantity': 1, 'delay': 0},
                ],
                'last_execution_delay': 1,
            },
            'Product 2': {
                'orderpoint': {'horizon': 90},
                'moves': [{'delay': 10}],
                'results': [
                    {'quantity': 1, 'delay': 10},
                ],
                'last_execution_delay': 11,
            },
        })

    def test_low_horizon_behaviour(self):
        self._test_group_procurements_by_date({
            'Product 1': {
                'orderpoint': {'horizon': 90},
                'moves': [{}],
                'results': [
                    {'quantity': 1, 'delay': 0},
                ],
                'last_execution_delay': 1,
            },
            'Product 2': {
                'orderpoint': {'horizon': 90},
                'moves': [{'delay': 100}],
                'results': [],
                # Yesterday because this is the default value defined in the
                # create_product method
                'last_execution_delay': -1,
            },
        })

    def test_one_group_high_regroupment(self):
        self._test_group_procurements_by_date({
            'Product 1': {
                'orderpoint': {'horizon': 90, 'regroupment': 50},
                'moves': [{}, {}, {}],
                'results': [
                    {'quantity': 3, 'delay': 0},
                ],
                'last_execution_delay': 50,
            },
        })

    def test_one_group_low_regroupment(self):
        self._test_group_procurements_by_date({
            'Product 1': {
                'orderpoint': {'horizon': 90, 'regroupment': 10},
                'moves': [{}, {}, {}],
                'results': [
                    {'quantity': 3, 'delay': 0},
                ],
                'last_execution_delay': 10,
            },
        })

    def test_two_groups_high_regroupment(self):
        self._test_group_procurements_by_date({
            'Product 1': {
                'orderpoint': {'horizon': 90, 'regroupment': 50},
                'moves': [{}, {'delay': 25}, {'delay': 75}],
                'results': [
                    {'quantity': 2, 'delay': 0},
                    {'quantity': 1, 'delay': 75},
                ],
                'last_execution_delay': 125,
            },
        })

    def test_two_groups_low_regroupment(self):
        self._test_group_procurements_by_date({
            'Product 1': {
                'orderpoint': {'horizon': 90, 'regroupment': 10},
                'moves': [{}, {'delay': 20}, {'delay': 25}],
                'results': [
                    {'quantity': 1, 'delay': 0},
                    {'quantity': 2, 'delay': 20},
                ],
                'last_execution_delay': 30,
            },
        })

    def test_several_products_groups_horizons(self):
        self._test_group_procurements_by_date({
            'Product 1': {
                'orderpoint': {'horizon': 90, 'regroupment': 14},
                'moves': [
                    # First group
                    {},
                    # Second group
                    {'delay': 20, 'quantity': 3},
                    {'delay': 25},
                    {'delay': 30, 'quantity': 10},
                    # Third group
                    {'delay': 40, 'quantity': 5},
                    {'delay': 50, 'quantity': 8},
                    # Fourth group
                    {'delay': 75, 'quantity': 2},
                ],
                'results': [
                    {'quantity': 1, 'delay': 0},
                    {'quantity': 14, 'delay': 20},
                    {'quantity': 13, 'delay': 40},
                    {'quantity': 2, 'delay': 75},
                ],
                'last_execution_delay': 89,
            },
            'Product 2': {
                'orderpoint': {'horizon': 50, 'regroupment': 28},
                'moves': [
                    # First group
                    {},
                    {'delay': 20, 'quantity': 3},
                    {'delay': 25},
                    # Second group
                    {'delay': 30, 'quantity': 10},
                    {'delay': 40, 'quantity': 5},
                    {'delay': 50, 'quantity': 8},
                    # Outside horizon
                    {'delay': 75, 'quantity': 2},
                ],
                'results': [
                    {'quantity': 5, 'delay': 0},
                    {'quantity': 23, 'delay': 30},
                ],
                'last_execution_delay': 58,
            },
            'Product 3': {
                'orderpoint': {'horizon': 90, 'regroupment': 7},
                'moves': [
                    # First group
                    {},
                    # Second group
                    {'delay': 20, 'quantity': 3},
                    {'delay': 25},
                    # Third group
                    {'delay': 30, 'quantity': 10},
                    # Fourth group
                    {'delay': 40, 'quantity': 5},
                    # Fith group
                    {'delay': 50, 'quantity': 8},
                    # Sixth group
                    {'delay': 75, 'quantity': 2},
                ],
                'results': [
                    {'quantity': 1, 'delay': 0},
                    {'quantity': 4, 'delay': 20},
                    {'quantity': 10, 'delay': 30},
                    {'quantity': 5, 'delay': 40},
                    {'quantity': 8, 'delay': 50},
                    {'quantity': 2, 'delay': 75},
                ],
                'last_execution_delay': 82,
            },
        })
