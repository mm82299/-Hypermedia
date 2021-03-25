# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
#                   odoo, Open Source Management Solution                    #
#                   ###     PROOSOFT CLOUD      ###                    #
#                                 --2018--                                   #
#                                                                            #
##############################################################################

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    vat_order = fields.Char('VAT Order')
    exemption_certificate_id = fields.Many2one('exemption.certificate', 'Exemption Certificate')
    date_invoice2 = fields.Date(compute='get_date_invoice')
    vat_exemption = fields.Boolean(string='VAT Exemption')
    date_vat_order = fields.Date('Vat Order Date')

    amount_tax_exempt = fields.Float(string='Tax', digits=dp.get_precision('Account'),store=True, readonly=True, compute='_compute_amount_exempt')


    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'currency_id', 'company_id')
    def _compute_amount_exempt(self):
        amount_tax_exempt = 0.0
        for line in self.invoice_line_ids:
            taxes = line.invoice_line_tax_ids.compute_all((line.price_unit * (1.0 - (line.discount or 0.0) / 100.0)), self.currency_id,line.quantity, line.product_id, self.partner_id)['taxes']
            for tax in taxes:
                amount_tax_exempt+= tax['amount']
        self.amount_tax_exempt=amount_tax_exempt

    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'currency_id', 'company_id')
    def _compute_amount(self):
        super(account_invoice, self)._compute_amount()
        if self.vat_exemption:
            self.amount_total = self.amount_total - self.amount_tax
            self.amount_tax = 0
    @api.one
    @api.depends('date_invoice')
    def get_date_invoice(self):
        self.date_invoice2 = self.date_invoice


    @api.multi
    def invoice_validate(self):
        res = super(account_invoice, self).invoice_validate()
        account_payment = self.env['account.payment'].search([('invoice_ids','=',self.id)])
        self.residual = self.amount_total
        self.amount_total_signed = self.amount_total
        self.residual_signed = self.amount_total
        return res

    @api.one
    @api.depends(
        'state', 'currency_id', 'invoice_line_ids.price_subtotal',
        'move_id.line_ids.amount_residual',
        'move_id.line_ids.currency_id')
    def _compute_residual(self):
        residual = 0.0
        residual_company_signed = 0.0
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        for line in self.sudo().move_id.line_ids:
            if line.account_id.internal_type in ('receivable', 'payable'):
                residual_company_signed += line.amount_residual
                if line.currency_id == self.currency_id:
                    residual += line.amount_residual_currency if line.currency_id else line.amount_residual
                else:
                    from_currency = (line.currency_id and line.currency_id.with_context(date=line.date)) or line.company_id.currency_id.with_context(date=line.date)
                    residual += from_currency.compute(line.amount_residual, self.currency_id)
        self.residual_company_signed = abs(residual_company_signed) * sign
        self.residual_signed = abs(residual) * sign
        self.residual = abs(residual)
        digits_rounding_precision = self.currency_id.rounding
        if float_is_zero(self.residual, precision_rounding=digits_rounding_precision):
            self.reconciled = True
        else:
            self.reconciled = False

    @api.multi
    def get_taxes_values(self):
        tax_grouped = super(account_invoice, self).get_taxes_values()
        if self.vat_exemption:
            tax_grouped = {}
        return tax_grouped


    @api.onchange('date_invoice2')
    def onchange_date_invoice(self):
        """
        we add new field date_invoice2 that copy the value of date_invoice to add a new onchange function based on date_invoice.
        we should do this on date_invoice if odoo support multi onchange function
        AUTHOR: Bejaoui souheil
        """
        partner = False
        if self.type == 'out_invoice':
            partner = self.partner_id
        elif self.type == 'in_invoice':
            partner = self.company_id.partner_id
        if partner and self.date_invoice:
            exemption_certificate_id = partner.get_certificate(self.date_invoice)[0]
            if exemption_certificate_id:
                self.exemption_certificate_id = exemption_certificate_id
                self.vat_exemption = True
            else:
                self.exemption_certificate_id = False
                self.vat_exemption = False
                self.vat_order = False
        else:
            self.exemption_certificate_id = False
            self.vat_exemption = False
            self.vat_order = False
        self._compute_amount()

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        """
        Surcharge the default onchange partner to get the certification exemption based on invoice date
        AUTHOR: Bejaoui SOUHEIL
        """
        partner = False
        values = super(account_invoice, self)._onchange_partner_id()
        if type == 'out_invoice':
            if self.partner_id:
                partner = self.env['res.partner'].browse(self.partner_id)
        elif type == 'in_invoice':
            partner = self.env['res.company'].browse(self.company_id).partner_id

        if partner:
            if self.date_invoice:
                exemption_certificate_id = partner.get_certificate(self.date_invoice)[0]
                if exemption_certificate_id:
                    values['value'].update({'vat_exemption':True, 'exemption_certificate_id':exemption_certificate_id[0].id,'vat_order':False})
                else:
                    values['value'].update({'vat_exemption':False, 'exemption_certificate_id':False,'vat_order':False})
            else:
                values['value'].update({'vat_exemption':False, 'exemption_certificate_id':False,'vat_order':False})
        return values

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        """ delete line of tax in case that debit = credit = 0
        Author: BEJAOUI SOUHEIL
        """
        res = []
        for move_line in move_lines:
            if move_line[2]['credit'] or move_line[2]['debit']:
                res.append(move_line)
        return res

    @api.one
    def write(self, vals):
        super(account_invoice, self).write(vals)
        res = False
        if self.type == 'out_invoice':
            res = self.env['sale.exemption.journal.line'].search([('invoice_id','=',self.id)])
        elif self.type == 'in_invoice':
            res = self.env['purchase.exemption.journal.line'].search([('invoice_id','=',self.id)])

        if self.state == 'open':
            if self.vat_exemption:
                if not res:
                    if self.type == 'out_invoice':
                        self.env['sale.exemption.journal.line'].create({'invoice_id' : self.id})
                    elif self.type == 'in_invoice':
                        self.env['purchase.exemption.journal.line'].create({'invoice_id' : self.id})

            else:
                if res:
                    res.unlink()
        elif self.state == 'cancel':
            if res:
                    res.unlink()
        return True

class account_invoice_tax(models.Model):
    _inherit = "account.invoice.tax"

    @api.v8
    def compute(self, invoice):
        """
        if the invoice is exempted don't return taxes
        Author: BEJAOUI SOUHEIL
        """
        tax_grouped = super(account_invoice_tax, self).compute(invoice)
        if invoice.vat_exemption:
            tax_grouped = {}
        return tax_grouped


class account_payment(models.Model):
    _inherit = "account.payment"

    @api.onchange('journal_id')
    def _onchange_journal(self):
        self.document_type = self.journal_id.document_type.id
        return super(account_payment, self)._onchange_journal()

    @api.onchange('amount', 'currency_id')
    def _onchange_amount(self):
        jrnl_filters = self._compute_journal_domain_and_types()
        journal_types = jrnl_filters['journal_types']
        domain_on_types = [('type', 'in', list(journal_types)), ('is_payment', '=', True)]

        journal_domain = jrnl_filters['domain'] + domain_on_types
        default_journal_id = self.env.context.get('default_journal_id')
        if not default_journal_id:
            if self.journal_id.type not in journal_types:
                self.journal_id = self.env['account.journal'].search(domain_on_types, limit=1)
        else:
            journal_domain = journal_domain.append(('id', '=', default_journal_id))

        return {'domain': {'journal_id': journal_domain}}

    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        if not self.invoice_ids:
            # Set default partner type for the payment type
            if self.payment_type == 'inbound':
                self.partner_type = 'customer'
            elif self.payment_type == 'outbound':
                self.partner_type = 'supplier'
            else:
                self.partner_type = False
        # Set payment method domain
        res = self._onchange_journal()
        if not res.get('domain', {}):
            res['domain'] = {}
        jrnl_filters = self._compute_journal_domain_and_types()
        journal_types = jrnl_filters['journal_types']
        journal_types.update(['bank', 'cash'])
        res['domain']['journal_id'] = jrnl_filters['domain'] + [('type', 'in', list(journal_types)), ('is_payment', '=', True)]
        return res

    @api.one
    @api.depends('invoice_ids', 'amount', 'payment_date', 'currency_id')
    def _compute_payment_difference(self):
        if len(self.invoice_ids) == 0:
            return
        if self.invoice_ids[0].type in ['in_invoice', 'out_refund']:
            self.payment_difference = self.amount - self._compute_total_invoices_amount()
        else:
            self.payment_difference = self._compute_total_invoices_amount() - self.amount


class account_abstract_payment(models.AbstractModel):
    _inherit = "account.abstract.payment"


    def _compute_total_invoices_amount(self):
        """ Compute the sum of the residual of invoices, expressed in the payment currency """
        payment_currency = self.currency_id or self.journal_id.currency_id or self.journal_id.company_id.currency_id
       # invoices = self._get_invoices() Not Implemented in odoo11

        for  inv in self.invoice_ids:
            if inv.vat_exemption:
                total = inv.amount_total
                inv.residual = 0
            else:
                if all(inv.currency_id == payment_currency for inv in self.invoice_ids):
                    total = sum(self.invoice_ids.mapped('residual_signed'))
                else:
                    total = 0
                    for inv in self.invoice_ids:
                        if inv.company_currency_id != payment_currency:
                            total += inv.company_currency_id.with_context(date=self.payment_date).compute(inv.residual_company_signed, payment_currency)
                        else:
                            total += inv.residual_company_signed
        return abs(total)
