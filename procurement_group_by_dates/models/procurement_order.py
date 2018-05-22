# -*- coding: utf-8 -*-
# Copyright 2017 SYLEAM Info Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta
from odoo import api, fields, models


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    no_auto_cancel = fields.Boolean(
        default=True,
        help='Check this box to keep this procurement confirmed when a need '
        'on the related product is changed.'
    )

    @api.model
    def _procurement_from_orderpoint_get_grouping_key(self, orderpoint_ids):
        """
        Each product will have different date so it's not possible to have a grouping.
        To avoid grouping, we add the id of the nomenclature.
        """
        orderpoint = self.env['stock.warehouse.orderpoint'].browse(
            orderpoint_ids)
        orderpoint._compute_procurements_to_cancel()

        return super(
            ProcurementOrder, self
        )._procurement_from_orderpoint_get_grouping_key(orderpoint_ids) + (
            orderpoint.id,)

    @api.model
    def _procurement_from_orderpoint_get_groups(self, orderpoint_ids):
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
        # Find the first need date
        next_date = orderpoint._compute_next_need_date()

        # For each need before horizon :
        # - Add a group
        # - Recompute the next need date to compute
        while next_date is not None and next_date <= horizon_date:
            regroupment_date = next_date + \
                timedelta(orderpoint.regroupment_days)
            groups.append({
                'to_date': regroupment_date,
                'procurement_values': {
                    'group': False,
                    'date': next_date,
                    'purchase_date': next_date,
                },
            })
            next_date = orderpoint._compute_next_need_date(
                fields.Date.to_string(regroupment_date + timedelta(days=1)))

        # If we have not future needs, we compute the needs for the stock.
        if not groups:
            return super(
                ProcurementOrder, self
            )._procurement_from_orderpoint_get_groups(orderpoint_ids)

        return groups

    @api.model
    def _procurement_from_orderpoint_post_process(self, orderpoint_ids):
        """
        By default all procurements are not run, new procurements are only seen at the end.
        When we have multiple dates for the same product,
        it will not consider previously created procurements in the stock as they are not confirmed.
        It will create too many needs. To correct this, we execute the needs.
        """
        self.env['stock.warehouse.orderpoint'].browse(
            orderpoint_ids).mapped('procurement_ids').filtered(
                lambda r: r.state == 'confirmed'
        ).run()

        return super(
            ProcurementOrder, self
        )._procurement_from_orderpoint_post_process(orderpoint_ids)

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
                orderpoint.sudo().last_execution_date = procurement.date_planned \
                    if not orderpoint.last_execution_date else min(
                        orderpoint.last_execution_date,
                        procurement.date_planned)
