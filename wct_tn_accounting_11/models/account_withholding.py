# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
#                   odoo, Open Source Management Solution                    #
#                   ###      PROOSOFT CLOUD      ###                    #
#                                 --2018--                                   #
#                                                                            #
##############################################################################


from odoo import models, fields, api
import odoo.addons.decimal_precision as dp
from datetime import date

class AccountWithholdingTax(models.Model):
    _name = 'account.withholding.tax'

    name = fields.Char(string='Tax Name', required=True)

    rate = fields.Float(string='Rate', required=True, digits=dp.get_precision('Discount'))

    account_id = fields.Many2one('account.account', domain=[('deprecated', '=', False)], string='Tax Account',
                                 ondelete='restrict', required=True)
    refund_account_id = fields.Many2one('account.account', domain=[('deprecated', '=', False)],
                                        string='Tax Account on Refunds', ondelete='restrict', required=True)

class AccountWithholding(models.Model):
    _name = 'account.withholding'

    def _set_name(self):
        return self.env['ir.sequence'].next_by_code('account.withholding')

    name = fields.Char(default=_set_name)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done')
    ], string='Withholding Tax Status', default='draft', readonly=True)

    type = fields.Selection([
        ('out_withholding', 'Customer Withholding'),
        ('in_withholding', 'Vendor Withholding')
    ], readonly=True)

    date = fields.Date(string='Date', default=fields.Date.context_today, required=True)

    @api.model
    def _default_journal_id(self):
        return self.env['account.journal'].search([('type', '=', 'general')], limit=1)

    journal_id = fields.Many2one('account.journal', string='Journal', default=_default_journal_id, required=True)

    partner_id = fields.Many2one('res.partner', required=True)

    account_invoice_ids = fields.One2many('account.invoice', inverse_name='withholding_id', string='Invoices')

    account_withholding_tax_ids = fields.Many2many('account.withholding.tax', string='Withholding Type', required=True)

    # @api.model
    # def _default_currency(self):
    #     journal = self._default_journal_id()
    #     return journal.currency_id or journal.company_id.currency_id or self.env.user.company_id.currency_id
    #
    # currency_id = fields.Many2one('res.currency', string='Currency',
    #                               required=True, readonly=True, states={'draft': [('readonly', False)]},
    #                               default=_default_currency)

    company_id = fields.Many2one('res.company', string='Company', change_default=True,
                                 required=True, readonly=True, states={'draft': [('readonly', False)]},
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'account.withholding'))

    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency",
                                          readonly=True)

    @api.one
    def _compute_currency_id(self):
        self.currency_id = self.journal_id.company_id.currency_id

    currency_id = fields.Many2one('res.currency', compute='_compute_currency_id')

    amount = fields.Monetary(string='Withholding Tax', compute='_compute_amount',digits=dp.get_precision('Product Price'))

    account_move_id = fields.Many2one('account.move')

    @api.onchange('partner_id')
    def _partner_id_onchange(self):
        for invoice in self.account_invoice_ids:
            invoice.write({'withholding_id': False})
        self.account_invoice_ids = []

    @api.depends('account_invoice_ids', 'account_withholding_tax_ids')
    @api.onchange('account_invoice_ids', 'account_withholding_tax_ids')
    def _compute_amount(self):
        for record in self:
            sum = 0.0
            for tax in record.account_withholding_tax_ids:
                invoice_sum = 0.0
                for invoice in record.account_invoice_ids:
                    invoice_sum += invoice.residual_signed
                    #invoice_sum += invoice.amount_total
                #sum += (invoice_sum * 0.01 * tax.rate)
                sum += round((invoice_sum * tax.rate) / 100, 3)
            record.amount = sum

    @api.one
    def button_validate_withholding(self):
        today = date.today()

        vals = {
            'ref': self.name,
            'journal_id': self.journal_id.id,
            'narration': False,
            'date': today,
            'partner_id': self.partner_id.id,
            'line_ids': [],
        }
        # vals for move
        partner_account_id = self.type == 'in_withholding' and self.partner_id.property_account_payable_id.id or self.partner_id.property_account_receivable_id.id
        debit = self.type == 'in_withholding' and self.amount or 0.0
        credit = self.type == 'out_withholding' and self.amount or 0.0

        partner = {'name': self.name,
                 'journal_id': self.journal_id.id,
                 'company_id': self.journal_id.company_id.id,
                 'credit': credit,
                 'debit': debit,
                 'date': today,
                 'partner_id': self.partner_id.id,
                 'account_id': partner_account_id}
        vals['line_ids'].append([0, False, partner])

        for l in self.account_withholding_tax_ids:
            invoice_sum = 0.0
            for invoice in self.account_invoice_ids:
                #invoice_sum += invoice.amount_total
                invoice_sum += invoice.residual_signed
            deb = self.type == 'in_withholding' and round((invoice_sum * l.rate) / 100, 3) or 0.0

            cred = self.type == 'out_withholding' and round((invoice_sum * l.rate) / 100, 3) or 0.0

            withholding = {'name': self.name,
                  'journal_id': self.journal_id.id,
                  'company_id': self.journal_id.company_id.id,
                  'credit': deb,
                  'debit': cred,
                  'date': today,
                  'partner_id': self.partner_id.id,
                  'account_id': l.account_id.id}
            vals['line_ids'].append([0, False, withholding])


        self.account_move_id = self.env['account.move'].create(vals)
        counterpart_aml = self.account_move_id.line_ids.filtered(lambda r: r.account_id.internal_type in ('payable','receivable'))
        self.account_invoice_ids.register_payment(counterpart_aml)
        self.state = 'done'

    @api.one
    def button_reset_to_draft_withholding(self):
        self.account_move_id.button_cancel()
        self.account_move_id.line_ids.unlink()
        self.account_move_id.unlink()
        self.state = 'draft'

    @api.multi
    def button_account_move(self):
        return {
            'name': 'Journal Items',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'res_id': self.account_move_id.id,
        }


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    withholding_id = fields.Many2one('account.withholding', string='Withholding Tax')   
