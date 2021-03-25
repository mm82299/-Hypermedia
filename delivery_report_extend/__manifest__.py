# Copyright 2019 Tecnativa S.L. - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Delivery Report Extend',
    'version': '11.0.1.0.2',
    'category': 'Sale',
    'author': 'Tecnativa,'
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/server-backend',
    'license': 'AGPL-3',
    'depends': [
        'stock',
    ],
    'data': [
        'views/stock_picking_view.xml',
        'views/report_deliveryslip.xml',
    ],
    'application': False,
    'installable': True,
}
