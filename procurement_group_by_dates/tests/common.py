# -*- coding: utf-8 -*-
# Copyright 2017 SYLEAM Info Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date, timedelta
from odoo.tests import common


class ProcurementTransactionCase(common.TransactionCase):
    def setUp(self):
        super(ProcurementTransactionCase, self).setUp()

        self.warehouse = self.env.ref('stock.warehouse0')

        self.supplier = self.env['res.partner'].create({
            'name': 'Supplier',
            'supplier': True,
        })
        self.customer = self.env['res.partner'].create({
            'name': 'Customer',
            'customer': True,
        })
        self.calendar = self.env['resource.calendar'].create({
            'name': 'Calendar',
            'attendance_ids': [(0, 0, {
                'name': 'Monday morning',
                'dayofweek': '0',
                'hour_from': 8,
                'hour_to': 12,
            }), (0, 0, {
                'name': 'Monday afternoon',
                'dayofweek': '0',
                'hour_from': 14,
                'hour_to': 18,
            }), (0, 0, {
                'name': 'Tuesday morning',
                'dayofweek': '1',
                'hour_from': 8,
                'hour_to': 12,
            }), (0, 0, {
                'name': 'Tuesday afternoon',
                'dayofweek': '1',
                'hour_from': 14,
                'hour_to': 18,
            }), (0, 0, {
                'name': 'Wednesday morning',
                'dayofweek': '2',
                'hour_from': 8,
                'hour_to': 12,
            }), (0, 0, {
                'name': 'Wednesday afternoon',
                'dayofweek': '2',
                'hour_from': 14,
                'hour_to': 18,
            }), (0, 0, {
                'name': 'Thursday morning',
                'dayofweek': '3',
                'hour_from': 8,
                'hour_to': 12,
            }), (0, 0, {
                'name': 'Thursday afternoon',
                'dayofweek': '3',
                'hour_from': 14,
                'hour_to': 18,
            }), (0, 0, {
                'name': 'Friday morning',
                'dayofweek': '4',
                'hour_from': 8,
                'hour_to': 12,
            }), (0, 0, {
                'name': 'Friday afternoon',
                'dayofweek': '4',
                'hour_from': 14,
                'hour_to': 18,
            }), (0, 0, {
                'name': 'Saturday morning',
                'dayofweek': '5',
                'hour_from': 8,
                'hour_to': 12,
            }), (0, 0, {
                'name': 'Sunday morning',
                'dayofweek': '6',
                'hour_from': 8,
                'hour_to': 12,
            })]
        })
        self.purchase_calendar = self.env['resource.calendar'].create({
            'name': 'Purchase Calendar',
            'attendance_ids': [(0, 0, {
                'name': 'Monday morning',
                'dayofweek': '0',
                'hour_from': 8,
                'hour_to': 12,
            }), (0, 0, {
                'name': 'Tuesday morning',
                'dayofweek': '1',
                'hour_from': 8,
                'hour_to': 12,
            }), (0, 0, {
                'name': 'Wednesday morning',
                'dayofweek': '2',
                'hour_from': 8,
                'hour_to': 12,
            }), (0, 0, {
                'name': 'Thursday morning',
                'dayofweek': '3',
                'hour_from': 8,
                'hour_to': 12,
            }), (0, 0, {
                'name': 'Friday morning',
                'dayofweek': '4',
                'hour_from': 8,
                'hour_to': 12,
            }), (0, 0, {
                'name': 'Saturday morning',
                'dayofweek': '5',
                'hour_from': 8,
                'hour_to': 12,
            }), (0, 0, {
                'name': 'Sunday morning',
                'dayofweek': '6',
                'hour_from': 8,
                'hour_to': 12,
            })]
        })

    def create_product(
            self, name, horizon=0, regroupment=1,
            min_qty=0, max_qty=0):
        """ Create a product configured for the tests """
        product = self.env['product.product'].create({
            'name': name,
            'type': 'product',
            'seller_ids': [(0, 0, {
                'name': self.supplier.id,
            })]
        })
        self.env['stock.warehouse.orderpoint'].create({
            'product_id': product.id,
            'product_min_qty': min_qty,
            'product_max_qty': max_qty,
            'calendar_id': self.calendar.id,
            'purchase_calendar_id': self.purchase_calendar.id,
            'last_execution_date': date.today() - timedelta(days=1),
            'horizon_days': horizon,
            'regroupment_days': regroupment,
        })

        return product

    def create_move(
            self, product, move_date, quantity=1):
        """ Create a move to generate a need """

        return self.env['stock.move'].create({
            'name': product.name,
            'product_id': product.id,
            'product_uom_qty': quantity,
            'product_uom': product.uom_id.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'location_dest_id': self.customer.property_stock_customer.id,
            'date': move_date,
        })
