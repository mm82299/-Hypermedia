# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
#                   odoo, Open Source Management Solution                    #
#                   ###      PROOSOFT CLOUD      ###                    #
#                                 --2018--                                   #
#                                                                            #
##############################################################################


from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from datetime import datetime

class purchase_order(models.Model):
    _inherit = 'purchase.order'

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the PO.
        """
        for order in self:
            val = val1 = 0.0
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                val1 += line.price_subtotal
                exemption_certificate = order.company_id.partner_id.get_certificate(order.date_order)[0]
                if not exemption_certificate:
                    val += line.price_tax
            order.update({
                'amount_untaxed': order.currency_id.round(val1),
                'amount_tax': order.currency_id.round(val),
                'amount_total': order.currency_id.round(val) + order.currency_id.round(val1),
            })

    # @api.depends('order_line.price_total')
    # def _amount_all(self):
    #     res = {}
    #     # cur_obj=self.pool.get('res.currency')
    #     company_id = self.env.user.company_id
    #     currency = company_id.currency_id
    #     for order in self:
    #         res[order.id] = {
    #             'amount_untaxed': 0.0,
    #             'amount_tax': 0.0,
    #             'amount_total': 0.0,
    #         }
    #         val = val1 = 0.0
    #         cur = order.currency_id
    #         for line in order.order_line:
    #            val1 += line.price_subtotal
    #            exemption_certificate = order.company_id.partner_id.get_certificate(order.date_order)[0]
    #            if not exemption_certificate:
    #                # for c in self.env['account.tax'].compute_all2(line.taxes_id.amount, line.price_unit, line.product_qty, line.product_id, order.partner_id)['taxes']:
    #                for c in self.env['account.tax'].compute_all(line.price_unit, line.order_id.currency_id, line.product_qty, line.product_id, order.partner_id)['taxes']:
    #                    val += c.get('amount', 0.0)
    #
    #         print(val)
    #         print(val1)
    #         res[order.id]['amount_tax']=currency.round(val)
    #         res[order.id]['amount_untaxed']=currency.round(val1)
    #         res[order.id]['amount_total']=res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
    #         print(res[order.id]['amount_total'])
    #     return res




    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all', track_visibility='always')
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all')


