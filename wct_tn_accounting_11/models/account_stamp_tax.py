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

class account_invoice(models.Model):
    _inherit = 'res.partner'

    have_stamp_tax = fields.Boolean(string="Have a stamp tax", default=True)

class account_invoice(models.Model):
    _inherit = 'account.invoice'

    stamp_tax = fields.Monetary(string="Tax Stamp", readonly=True, compute='_compute_amount', store=True, digits=dp.get_precision('Account'))
    amount_discount = fields.Monetary(string='Remise', store=True,compute='_compute_amount',digits=dp.get_precision('Account'))
    amount_total_afdiscount = fields.Monetary(string='Total Aprés Remise', store=True,compute='_compute_amount',digits=dp.get_precision('Account'))
    group_invoice_stamp_tax = fields.Boolean(string='Apply stamp tax', help="Apply stamp tax on invoice total")
    fodec_tax = fields.Monetary(string="Fodec Tax", readonly=True, compute='_compute_amount', store=True, digits=dp.get_precision('Account'))



    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'group_invoice_stamp_tax')
    def _compute_amount(self):
        super(account_invoice, self)._compute_amount()
        self.amount_discount = sum((line.quantity * line.price_unit * line.discount)/100 for line in self.invoice_line_ids)
        self.stamp_tax = 0
        type = 'sale'
        if self.type == 'in_invoice':
            type = 'purchase'
        if self.group_invoice_stamp_tax and self.type in ('in_invoice', 'out_invoice'):
            self.stamp_tax = self.env['account.tax'].search([('is_stamp_tax', '=', 1), ('type_tax_use', 'in', ['all', type])], limit=1).amount
        if self.group_invoice_stamp_tax:
            self.amount_untaxed =self.amount_untaxed + self.amount_discount
            self.amount_total = self.amount_untaxed + self.amount_tax - self.amount_discount
            self.amount_total_afdiscount=self.amount_untaxed - self.amount_discount
        tax_grouped = self.get_taxes_values()
        self.amount_tax_exempt=self.amount_tax_exempt-self.fodec_tax



    @api.onchange('invoice_line_ids', 'group_invoice_stamp_tax')
    def _onchange_invoice_line_ids(self):
        super(account_invoice, self)._onchange_invoice_line_ids()

    @api.constrains('partner_id')
    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        super(account_invoice, self)._onchange_partner_id()
        self.group_invoice_stamp_tax = self.partner_id.have_stamp_tax

    @api.multi
    def get_taxes_values(self):
        taxes = super(account_invoice, self).get_taxes_values()
        if self.group_invoice_stamp_tax and self.type in ('in_invoice', 'out_invoice'):
            ttype = 'sale'
            if self.type == 'in_invoice':
                ttype = 'purchase'
            obj_stamp_tax = self.env['account.tax'].search([('is_stamp_tax', '=', 1), ('type_tax_use', 'in', ['all', ttype])], limit=1)
            if obj_stamp_tax:
                key = str(obj_stamp_tax.id) + '-' + str(obj_stamp_tax.account_id.id)
                taxes[key] = {
                    'invoice_id': self.id,
                    'name': 'timbre',
                    'tax_id': obj_stamp_tax[0].id,
                    'amount': obj_stamp_tax[0].amount,
                    'sequence': obj_stamp_tax[0].sequence,
                    'tax_amount': obj_stamp_tax[0].amount,
                    'account_id': obj_stamp_tax[0].account_id.id,
                    'is_stamp_tax': True,
                    'manual': False,
                }
            else:
                return {'warning': {'title': _('Error!'), 'message': _('You have to configure a stamp tax before.')}}
        # dummy write on self to trigger recomputations
        return taxes

class account_tax_template(models.Model):
    _inherit = 'account.tax.template'

    is_stamp_tax = fields.Boolean(string="Is stamp tax")

class account_tax(models.Model):
    _inherit = 'account.tax'

    is_stamp_tax = fields.Boolean(string="Is stamp tax")

    @api.onchange('is_stamp_tax')
    def set_default_apply(self):
        self.type = 'fixed'

    @api.multi
    def toggle_stamp(self):
        """ Inverse the value of the field ``active`` on the records in ``self``. """
        for record in self:
            record.is_stamp_tax = not record.is_stamp_tax

class account_invoice_tax(models.Model):
    _inherit = 'account.invoice.tax'

    is_stamp_tax = fields.Boolean(string="Is stamp tax",default=False)

