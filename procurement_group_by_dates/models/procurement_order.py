# -*- coding: utf-8 -*-
# Copyright 2017 SYLEAM Info Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta
from odoo import api, fields, models


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    no_auto_cancel = fields.Boolean(default=True,
        help='Check this box to keep this procurement confirmed when a need '
        'on the related product is changed.')

    @api.model
    def _procurement_from_orderpoint_get_grouping_key(self, orderpoint_ids):
        # FIXME : Adapt this when Odoo has fixed the new API conversion
        orderpoint = self.env['stock.warehouse.orderpoint'].browse(
            orderpoint_ids)

        return super(
            ProcurementOrder, self
        )._procurement_from_orderpoint_get_grouping_key(orderpoint_ids) + (
            orderpoint.id,)

    @api.model
    def _procurement_from_orderpoint_get_groups(self, orderpoint_ids):
        # FIXME : Adapt this when Odoo has fixed the new API conversion
        orderpoint = self.env['stock.warehouse.orderpoint'].browse(
            orderpoint_ids)

        if not orderpoint.horizon_days:
            return super(
                ProcurementOrder, self
            )._procurement_from_orderpoint_get_groups(orderpoint_ids)

        # An horizon is defined
        # Group by intervals depending on regroupment_days field
        groups = []
        horizon_date = datetime.now().date() + \
            timedelta(days=orderpoint.horizon_days)
        # TODO Find the first need date
        next_date = orderpoint._compute_next_need_date()

        # For each need before horizon :
        # - Add a group
        # - Recompute the next need date to compute
        while next_date is not None and next_date <= horizon_date:
            regroupment_date = next_date + \
                timedelta(orderpoint.regroupment_days)
            groups.append({
                'from_date': next_date,
                'to_date': regroupment_date,
                'procurement_values': {
                    'group': False,
                    'date': next_date,
                    'purchase_date': next_date,
                },
            })
            next_date = orderpoint._compute_next_need_date(
                fields.Date.to_string(regroupment_date + timedelta(days=1)))

        return groups

    @api.model
    def _procurement_from_orderpoint_post_process(self, orderpoint_ids):
        # FIXME : Adapt this when Odoo has fixed the new API conversion
        orderpoints = self.env['stock.warehouse.orderpoint'].browse(
            orderpoint_ids)
        all_groups = {}
        dates = {}

        for orderpoint in orderpoints:
            groups = self._procurement_from_orderpoint_get_groups(
                orderpoint.ids)

            if groups:
                # There are groups : Some needs have been treated
                all_groups[orderpoint] = groups
            else:
                # No group : Nothing has been done, save the date
                dates[orderpoint] = orderpoint.last_execution_date

        res = super(
            ProcurementOrder, self
        )._procurement_from_orderpoint_post_process(orderpoint_ids)

        # Call _procurement_from_orderpoint_get_groups to get right dates
        for orderpoint, groups in all_groups.iteritems():
            if groups and groups[-1]['to_date']:
                last_date = groups[-1]['to_date']
                orderpoint.last_execution_date = last_date

        # Restore saved dates
        for orderpoint, saved_date in dates.iteritems():
            orderpoint.last_execution_date = saved_date

        return res

    @api.multi
    def cancel(self):
        self.update_orderpoints_last_execution_date()
        return super(ProcurementOrder, self).cancel()

    @api.multi
    def update_orderpoints_last_execution_date(self):
        """ Change the last_execution_date of all orderpoints

        The new date written on each orderpoint must be changed when the
        procurement's state change implies modifications in computed virtual
        quantities. If the date already written is lower than the move's date,
        no change must be done.
        """
        for procurement in self:
            for orderpoint in procurement.product_id.mapped('orderpoint_ids'):
                orderpoint.last_execution_date = procurement.date_planned \
                    if not orderpoint.last_execution_date else min(
                        orderpoint.last_execution_date,
                        procurement.date_planned)
