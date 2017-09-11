# -*- coding: utf-8 -*-
# Copyright 2017 SYLEAM Info Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta, datetime
from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class StockWarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    horizon_days = fields.Integer(
        string='Horizon', default=0,
        help='Maximum delay for newly created procurements, in days. '
        '0 to disable.')
    regroupment_days = fields.Integer(
        string='Regroupment', default=1,
        help='Maximum delay between procurement date and needs computation,'
        'in days.')

    @api.multi
    def _compute_next_need_date(self, previous_date=None):
        """
        Find the next date to compute the needs from this date
        """
        self.ensure_one()

        if previous_date is None:
            previous_date = self.last_execution_date or datetime.utcnow().strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        # Search the next move going out from the warehouse
        return fields.Date.from_string(self.env['stock.move'].search([
            ('state', 'not in', ('draft', 'cancel')),
            ('product_id', '=', self.product_id.id),
            ('date', '>=', previous_date),
            ('location_id', 'child_of', self.warehouse_id.lot_stock_id.id),
            '!', (
                'location_dest_id',
                'child_of',
                self.warehouse_id.lot_stock_id.id,
            ),
        ], order='date', limit=1).date)

    @api.multi
    def _compute_procurements_to_cancel(self, date):
        """ Return the date of the oldest procurement to cancel

        Get the procurements starting at given date minus regroupment_days
        """
        procurements = self.env['procurement.order']
        for orderpoint in self.filtered(lambda r: r.last_execution_date != False):
            first_date = fields.Datetime.from_string(
                orderpoint.last_execution_date) - \
                    timedelta(days=orderpoint.regroupment_days)

            procurements += self.env['procurement.order'].search([
                ('no_auto_cancel', '=', False),
                ('product_id', '=', orderpoint.product_id.id),
                ('date_planned', '>=', fields.Datetime.to_string(first_date)),
                ('state', 'not in', ('draft', 'cancel', 'done')),
            ])

        return procurements

    @api.multi
    def _prepare_procurement_values(self, product_qty, date=False, purchase_date=False, group=False):
        res = super(StockWarehouseOrderpoint, self)._prepare_procurement_values(product_qty, date=date, group=group)
        res.update({
            'no_auto_cancel': False,
        })
        return res
