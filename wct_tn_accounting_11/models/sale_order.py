# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
#                   odoo, Open Source Management Solution                    #
#                   ###     PROOSOFT CLOUD      ###                    #
#                                 --2018--                                   #
#                                                                            #
##############################################################################

from odoo import models, fields, api, _

class sale_order(models.Model):
    _inherit = 'sale.order'

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                exemption_certificate = order.partner_id.get_certificate(order.date_order)[0]
                if not exemption_certificate:
                    amount_tax += line.price_tax
            order.update({
                'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
                'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
            })


    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all', track_visibility='always')
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all')

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        inv = super(sale_order, self).action_invoice_create(grouped, final)
        for invoice in self.env['account.invoice'].browse(inv):
            invoice.group_invoice_stamp_tax = invoice.partner_id.have_stamp_tax
            invoice.compute_taxes()
        return inv

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    @api.multi
    def _create_invoice(self, order, so_line, amount):
        inv = super(SaleAdvancePaymentInv, self)._create_invoice(order, so_line, amount)
        inv.group_invoice_stamp_tax = inv.partner_id.have_stamp_tax
        return inv
