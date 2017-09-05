# -*- coding: utf-8 -*-
# Copyright 2017 SYLEAM Info Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'procurement_group_by_dates',
    'version': '10.0.1.0.0',
    'category': 'Custom',
    'summary': 'Groups created procurements by dates',
    'author': 'SYLEAM, Odoo Community Association (OCA)',
    'website': 'http://www.Syleam.fr/',
    'depends': [
        'stock_calendar',
    ],
    'data': [
        # 'security/ir.model.access.csv',
        'views/stock_warehouse_orderpoint.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
