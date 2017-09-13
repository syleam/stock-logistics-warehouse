# -*- coding: utf-8 -*-
# Copyright 2017 SYLEAM Info Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def action_confirm(self):
        res = super(StockMove, self).action_confirm()

        self.cancel_future_needs()

        return res

    @api.multi
    def action_cancel(self):
        res = super(StockMove, self).action_cancel()

        self.cancel_future_needs()

        return res

    @api.multi
    def cancel_future_needs(self):
        """ Cancel the procurements that come after the modified need

        This is called when an old need has been modified or added.
        In this case, we cancel all running procurements, then update the
        last_execution_date field to let the scheduler recompute all these
        needs during the next run.
        """
        for move in self:
            for orderpoint in move.product_id.mapped('orderpoint_ids'):
                orderpoint.last_execution_date = move.date \
                        if not orderpoint.last_execution_date else min(
                            orderpoint.last_execution_date,
                            move.date)
                orderpoint.cancel_procurements = True
