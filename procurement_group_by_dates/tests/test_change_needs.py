# -*- coding: utf-8 -*-
# Copyright 2017 SYLEAM Info Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date, timedelta
from odoo import fields
from .common import ProcurementTransactionCase


class TestChangeNeeds(ProcurementTransactionCase):
    def setUp(self):
        super(TestChangeNeeds, self).setUp()

    def check_orderpoint_last_date(self, orderpoint, delay):
        """ Check the last_execution_date of the orderpoint compared to delay
        """
        product_date = fields.Date.from_string(orderpoint.last_execution_date)
        self.assertEqual(product_date, date.today() + timedelta(days=delay))

    def test_new_move(self):
        """ Creating a new move shouldn't update the needs

        The last_execution_date shouldn't be updated, and no procurement
        should be cancelled
        """
        # Create some products
        product1 = self.create_product('Product 1', horizon=90, regroupment=7)
        product2 = self.create_product('Product 2', horizon=90, regroupment=10)

        # Create some moves
        product1_move1 = self.create_move(
            product1, date.today() + timedelta(days=0), quantity=1)
        product1_move2 = self.create_move(
            product1, date.today() + timedelta(days=5), quantity=1)
        product2_move1 = self.create_move(
            product2, date.today() + timedelta(days=2), quantity=1)

        (product1_move1 + product1_move2 + product2_move1).action_confirm()

        # Run the scheduler
        self.env['procurement.order'].run_scheduler()

        # Check orderpoints' dates
        self.check_orderpoint_last_date(product1.orderpoint_ids, 7)
        self.check_orderpoint_last_date(product2.orderpoint_ids, 12)

        # Create a new move
        product2_move1 = self.create_move(
            product2, date.today() + timedelta(days=4), quantity=1)

        # Orderpoints' dates should not have been changed
        self.check_orderpoint_last_date(product1.orderpoint_ids, 7)
        self.check_orderpoint_last_date(product2.orderpoint_ids, 12)

    def test_cancel_move(self):
        """ Cancelling a move should update the needs

        The last_execution_date should be updated, but no procurement
        should be cancelled
        """
        # Create some products
        product1 = self.create_product('Product 1', horizon=90, regroupment=7)
        product2 = self.create_product('Product 2', horizon=90, regroupment=10)

        # Create some moves
        product1_move1 = self.create_move(
            product1, date.today() + timedelta(days=0), quantity=1)
        product1_move2 = self.create_move(
            product1, date.today() + timedelta(days=4), quantity=1)
        product2_move1 = self.create_move(
            product2, date.today() + timedelta(days=2), quantity=1)

        (product1_move1 + product1_move2 + product2_move1).action_confirm()

        # Run the scheduler
        self.env['procurement.order'].run_scheduler()

        # Check orderpoints' dates
        self.check_orderpoint_last_date(product1.orderpoint_ids, 7)
        self.check_orderpoint_last_date(product2.orderpoint_ids, 12)

        # Cancel a move used by the scheduler
        product1_move1.action_cancel()

        # The orderpoint linked to the cancelled move should have been modified
        # The other orderpoint should be left unchanged
        self.check_orderpoint_last_date(product1.orderpoint_ids, 0)
        self.check_orderpoint_last_date(product2.orderpoint_ids, 12)

        # Re-run the scheduler
        self.env['procurement.order'].run_scheduler()

        # Check that the cancelled move has been ignored here, but the
        # last_execution_date has been changed according to the remaining
        # confirmed moves
        self.check_orderpoint_last_date(product1.orderpoint_ids, 11)
        self.check_orderpoint_last_date(product2.orderpoint_ids, 12)

    def test_confirm_move(self):
        """ Confirming a move should update the needs

        The last_execution_date should be updated, but no procurement
        should be cancelled
        """
        # Create some products
        product1 = self.create_product('Product 1', horizon=90, regroupment=7)
        product2 = self.create_product('Product 2', horizon=90, regroupment=10)

        # Create some moves
        product1_move1 = self.create_move(
            product1, date.today() + timedelta(days=0), quantity=1)
        product1_move2 = self.create_move(
            product1, date.today() + timedelta(days=5), quantity=1)
        product2_move1 = self.create_move(
            product2, date.today() + timedelta(days=2), quantity=1)

        (product1_move1 + product1_move2 + product2_move1).action_confirm()

        # Create a new move
        product2_move2 = self.create_move(
            product2, date.today() + timedelta(days=4), quantity=1)

        # Run the scheduler
        self.env['procurement.order'].run_scheduler()

        # Check orderpoints' dates
        self.check_orderpoint_last_date(product1.orderpoint_ids, 7)
        self.check_orderpoint_last_date(product2.orderpoint_ids, 12)

        # Confirm the draft move
        product2_move2.action_confirm()

        # The product1 orderpoint's last_execution_date should be put on the
        # oldest cancelled need date
        # The other orderpoint should be left unchanged
        self.check_orderpoint_last_date(product1.orderpoint_ids, 7)
        self.check_orderpoint_last_date(product2.orderpoint_ids, 2)

        # Run the scheduler
        self.env['procurement.order'].run_scheduler()

        # Check orderpoints' dates
        self.check_orderpoint_last_date(product1.orderpoint_ids, 7)
        self.check_orderpoint_last_date(product2.orderpoint_ids, 12)

    def test_done_move(self):
        """ Terminating new move shouldn't update the needs

        The last_execution_date shouldn't be updated, and no procurement
        should be cancelled
        """
        # Create some products
        product1 = self.create_product('Product 1', horizon=90, regroupment=7)
        product2 = self.create_product('Product 2', horizon=90, regroupment=10)

        # Create some moves
        product1_move1 = self.create_move(
            product1, date.today() + timedelta(days=0), quantity=1)
        product1_move2 = self.create_move(
            product1, date.today() + timedelta(days=5), quantity=1)
        product2_move1 = self.create_move(
            product2, date.today() + timedelta(days=2), quantity=1)

        (product1_move1 + product1_move2 + product2_move1).action_confirm()

        # Run the scheduler
        self.env['procurement.order'].run_scheduler()

        # Check orderpoints' dates
        self.check_orderpoint_last_date(product1.orderpoint_ids, 7)
        self.check_orderpoint_last_date(product2.orderpoint_ids, 12)

        # Terminate one of the existing moves
        product1_move1.action_done()

        # Orderpoints' dates should not have been changed
        self.check_orderpoint_last_date(product1.orderpoint_ids, 7)
        self.check_orderpoint_last_date(product2.orderpoint_ids, 12)

    def test_cancel_move_without_cancel(self):
        """ Cancelling a move shouldn't update the needs without cancel """
        # Create some products
        product1 = self.create_product('Product 1', horizon=90, regroupment=7)
        product2 = self.create_product('Product 2', horizon=90, regroupment=10)

        # Create some moves
        product1_move1 = self.create_move(
            product1, date.today() + timedelta(days=0), quantity=1)
        product1_move2 = self.create_move(
            product1, date.today() + timedelta(days=4), quantity=1)
        product2_move1 = self.create_move(
            product2, date.today() + timedelta(days=2), quantity=1)

        (product1_move1 + product1_move2 + product2_move1).action_confirm()

        # Run the scheduler
        self.env['procurement.order'].run_scheduler()

        # Check orderpoints' dates
        self.check_orderpoint_last_date(product1.orderpoint_ids, 7)
        self.check_orderpoint_last_date(product2.orderpoint_ids, 12)

        # Retrieve product1's procurement to forbid auto-cancel
        self.env['procurement.order'].search([
            ('product_id', '=', product1.id),
        ]).no_auto_cancel = True

        # Cancel a move used by the scheduler
        product1_move1.action_cancel()

        # No procurement has been cancelled, no last_execution_date changed
        self.check_orderpoint_last_date(product1.orderpoint_ids, 7)
        self.check_orderpoint_last_date(product2.orderpoint_ids, 12)

        # Re-run the scheduler
        self.env['procurement.order'].run_scheduler()

        # Nothing new happened
        self.check_orderpoint_last_date(product1.orderpoint_ids, 7)
        self.check_orderpoint_last_date(product2.orderpoint_ids, 12)

    def test_confirm_move_without_cancel(self):
        """ Confirming a move shouldn't update the needs without cancel """
        # Create some products
        product1 = self.create_product('Product 1', horizon=90, regroupment=7)
        product2 = self.create_product('Product 2', horizon=90, regroupment=10)

        # Create some moves
        product1_move1 = self.create_move(
            product1, date.today() + timedelta(days=0), quantity=1)
        product1_move2 = self.create_move(
            product1, date.today() + timedelta(days=5), quantity=1)
        product2_move1 = self.create_move(
            product2, date.today() + timedelta(days=2), quantity=1)

        (product1_move1 + product1_move2 + product2_move1).action_confirm()

        # Create a new move
        product2_move2 = self.create_move(
            product2, date.today() + timedelta(days=4), quantity=1)

        # Run the scheduler
        self.env['procurement.order'].run_scheduler()

        # Check orderpoints' dates
        self.check_orderpoint_last_date(product1.orderpoint_ids, 7)
        self.check_orderpoint_last_date(product2.orderpoint_ids, 12)

        # Retrieve product2's procurement to forbid auto-cancel
        self.env['procurement.order'].search([
            ('product_id', '=', product2.id),
        ]).no_auto_cancel = True

        # Confirm the draft move
        product2_move2.action_confirm()

        # No procurement has been cancelled, no last_execution_date changed
        self.check_orderpoint_last_date(product1.orderpoint_ids, 7)
        self.check_orderpoint_last_date(product2.orderpoint_ids, 12)

        # Run the scheduler
        self.env['procurement.order'].run_scheduler()

        # Nothing new happened
        self.check_orderpoint_last_date(product1.orderpoint_ids, 7)
        self.check_orderpoint_last_date(product2.orderpoint_ids, 12)
