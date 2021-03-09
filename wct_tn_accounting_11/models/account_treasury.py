# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
#                   odoo, Open Source Management Solution                    #
#                   ###      PROOSOFT CLOUD  ###                    #
#                                 --2018--                                   #
#                                                                            #
##############################################################################

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from datetime import date
from odoo.exceptions import UserError

class treasury_document_type(models.Model):
    _name = 'account.treasury.type'
    _description = "Treasury Document Type"

    name = fields.Char('Name', size=64, required=True)
    check = fields.Boolean('Check')
    treaty = fields.Boolean('Treaty')
    letter_of_credit = fields.Boolean('Letter of credit',
                                      help='This checkbox used to define letter of credit document type.')


class treasury_document(models.Model):
    _name = 'account.treasury'
    _order = 'clearing_date'
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = "Treasury Document"

    @api.model
    def _employee_get(self):
        ids = self.env['hr.employee'].search([('user_id', '=', self._uid)])
        if ids:
            return ids[0]
        return False

    @api.model
    def _compute_transaction_type(self):
        if self.partner_id:
            if self.partner_id.costumer:
                self.type_transaction='receipt'
            else:
                self.type_transaction='payment'

    name = fields.Char('Document ID', size=64, index=1, required=True, readonly=True,
                       states={'in_cash': [('readonly', False)]})
    partner_id = fields.Many2one('res.partner', 'Partner', required=True, readonly=True,
                                 states={'in_cash': [('readonly', False)]},
                                 help='Partner who made the pay with this document.')
    holder = fields.Char('Holder', size=128, required=True, readonly=True, states={'in_cash': [('readonly', False)]},
                         help='Holder who made the pay with this document.')
    user_id = fields.Many2one('res.users', 'Possessor', required=True, readonly=True,
                              states={'in_cash': [('readonly', False)]},
                              help='User who receive this document.', default=lambda self: self.env.user)
    cashier_id = fields.Many2one('hr.employee', 'Cashier', readonly=True, default=_employee_get)
    partner_steed = fields.Boolean('Partner Steed', default=True)
    steed_id = fields.Many2one('hr.employee', 'Steed')
    company_id = fields.Many2one('res.company', 'Company', required=True, readonly=True,
                                 states={'in_cash': [('readonly', False)]},
                                 help='Company related to this treasury', default=lambda self: self.env.user.company_id)
    amount = fields.Monetary(string='Amount', digits=dp.get_precision('Account'), required=True, readonly=True,
                          states={'in_cash': [('readonly', False)]}, help='Value of the Treasure', currency_field='currency_id')
    value = fields.Monetary(string='Value', digits=dp.get_precision('Account'), compute="_compute_value",
                           help='Value of the Treasure', currency_field='currency_id')

    reception_date = fields.Date('Reception Date', required=True, readonly=True,
                                 states={'in_cash': [('readonly', False)]},default=date.today())
    clearing_date = fields.Date('Clearing Date', readonly=True, states={'in_cash': [('readonly', False)]},default=date.today())


    bank_source = fields.Many2one('res.bank', 'Source Bank', required=True, readonly=True,
                                  states={'in_cash': [('readonly', False)]})
    journal_target = fields.Many2one('account.journal', 'Journal Target')
    journal_id = fields.Many2one('account.journal', 'Journal', domain="[('type','=','bank')]")
    type = fields.Many2one('account.treasury.type', 'Document Type', required=True, index=1, readonly=True,
                           states={'in_cash': [('readonly', False)]})
    state = fields.Selection([
        ('in_cash', 'In Cash'),
        # ('valid', 'Valid'), #valide
        ('versed', 'Versed'), #liquidé
        ('paid', 'Paid'), # paier
        ('notice', 'Notice'), #préavis
        ('cancel', 'Cancelled'),
    ], 'State', required=True, readonly=True, index=1, default='in_cash', track_visibility='onchange')
    note = fields.Text('Notes')
    payment_id = fields.Many2one('account.payment', 'Associated Payment', ondelete='cascade')
    type_transaction = fields.Selection([('receipt', 'Receipt'), ('payment', 'Payment')], 'Transaction Type',
                                        required=True, readonly=True, states={'in_cash': [('readonly', False)]},default=_compute_transaction_type)
    statement_id = fields.Many2one('account.bank.statement.line', ondelete='cascade')
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, related='company_id.currency_id',
                                  store=True)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        print("test")
        type_transaction=''
        if not self.partner_id:
            return {}
        if self.partner_id.customer:
            type_transaction = 'receipt'
        else:
            type_transaction = 'payment'
        amount=0
        if self.payment_id:
            amount=self.payment_id.amount
        return {'value': {'holder': self.partner_id.display_name, 'type_transaction': type_transaction, 'amount': amount}}

    @api.multi
    def unlink(self):
        for treasury in self:
            if treasury.state != 'in_cash':
                raise UserError(_('You cannot delete this Document !'))
        return super(treasury_document, self).unlink()


    @api.one
    @api.depends('type_transaction', 'amount')
    def _compute_value(self):
        if self.type_transaction=='payment':
            self.value = - self.amount
        else:
            self.value = self.amount

    @api.one
    def account_move_get(self, date):
        if self.bank_target.journal_id.sequence_id:
            if not self.bank_target.journal_id.sequence_id.active:
                raise UserError(_('Please activate the sequence of selected journal !'))
            name = self.bank_target.journal_id.sequence_id.next_by_id()
        else:
            raise UserError(_('Please define a sequence on the journal.'))

        move = {
            'name': name,
            'journal_id': self.bank_target.journal_id.id,
            'date': date,
            'ref': name,
        }
        return move

    @api.one
    def first_move_line_get(self, move_id, account_id):
        move_line = {
            'name': '/',
            'debit': self.amount,
            'credit': 0,
            'account_id': account_id,
            'partner_id': self.partner_id.id,
            'move_id': move_id.id,
            'journal_id': self.bank_target.journal_id.id,
            'date': move_id.date,
            'date_maturity': move_id.date
        }
        return self.env['account.move.line'].create(move_line)

    @api.one
    def treasury_move_line_create(self, move_id):
        move_line = {
            'name': '/',
            'debit': 0,
            'credit': self.amount,
            'account_id': self.bank_target.journal_id.default_credit_account_id.id,
            'partner_id': self.partner_id.id,
            'move_id': move_id.id,
            'journal_id': self.bank_target.journal_id.id,
            'date': move_id.date,
            'date_maturity': move_id.date
        }
        self.env['account.move.line'].create(move_line)

    @api.one
    def action_move_line_create(self, account_id, date):
        move_pool = self.env['account.move']
        # Create the account move record.
        move_id = move_pool.create(self.account_move_get(date)[0])
        # Create the first line of the vesement
        self.first_move_line_get(move_id, account_id)
        self.treasury_move_line_create(move_id)

    @api.one
    def action_rejected(self, account_id, date):
        self.action_move_line_create(account_id, date)
        self.state = 'rejected'

    @api.multi
    def button_rejected(self):
        dummy, view_id = self.env['ir.model.data'].get_object_reference('treasury_extend',
                                                                        'view_account_treasury_rejected_form')

        return {
            'name': _("Document Treasury Rejected"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.treasury.rejected',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
        }

class account_payment(models.Model):
    _inherit = 'account.payment'

    @api.multi
    def unlink(self):
        for rec in self:
            rec.move_name = ''
        return super(account_payment, self).unlink()

    journal_type = fields.Selection(related='journal_id.type', string='Journal type')
    check_ids = fields.One2many('account.treasury', 'payment_id', string='List of Checks')
    temporary_bank_journal = fields.Boolean(related='journal_id.temporary_bank_journal')
    document_type = fields.Many2one('account.treasury.type', 'Document Type')


    @api.onchange('partner_id')
    @api.depends('partner_id')
    def onchange_partner_id(self):
        if self.temporary_bank_journal:
            for cheque in self.check_ids:
                    cheque.holder = self.partner_id and self.partner_id.name


    @api.multi
    def cancel(self):
        super(account_payment, self).cancel()
        if self.journal_id.temporary_bank_journal:
            treasury_id = self.env['account.treasury'].search([('payment_id', '=', self.id)])
            if treasury_id.state not in ('versed', 'cancel','paid'):
                treasury_id.unlink()
            else:
                raise UserError(_('You cannot delete this document because tresory document is not valid or cancel!'))

    @api.one
    @api.constrains('amount','check_ids')
    def _check_total_checks(self):
        amount=0.0
        for c in self.check_ids:
            amount+=c.amount
        if self.amount < amount:
            raise UserError(_('The payment amount must be equal to checks total amount.'))

    def _create_payment_entry(self, amount):
        if self.check_ids:
            total_amount=0.0
            for c in self.check_ids:
                total_amount += c.amount
            if abs(amount) != total_amount:
                raise UserError(_('The payment amount must be equal to checks total amount. %f, %f')% (total_amount, amount))
            print("new traitement")
            aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
            invoice_currency = False
            if self.invoice_ids and all([x.currency_id == self.invoice_ids[0].currency_id for x in self.invoice_ids]):
                # if all the invoices selected share the same currency, record the paiement in that currency too
                invoice_currency = self.invoice_ids[0].currency_id
            move = self.env['account.move'].create(self._get_move_vals())
            counterpart_aml = aml_obj
            checks = []
            for chk in self.check_ids:
                print("processing chk number ",chk.name)
                debit, credit, amount_currency, currency_id = aml_obj.with_context(
                    date=self.payment_date).compute_amount_fields(chk.amount*(amount>0 or -1), self.currency_id, self.company_id.currency_id,
                                                                  invoice_currency)

                # Write line corresponding to invoice payment
                counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
                # counterpart_aml_dict_inv=
                counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.invoice_ids))
                counterpart_aml_dict.update({'currency_id': currency_id})
                counterpart_aml = aml_obj.create(counterpart_aml_dict)


                # Reconcile with the invoices
                if self.payment_difference_handling == 'reconcile' and self.payment_difference:
                    writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
                    amount_currency_wo, currency_id = aml_obj.with_context(
                        date=self.payment_date).compute_amount_fields(self.payment_difference, self.currency_id,
                                                                      self.company_id.currency_id, invoice_currency)[2:]
                    # the writeoff debit and credit must be computed from the invoice residual in company currency
                    # minus the payment amount in company currency, and not from the payment difference in the payment currency
                    # to avoid loss of precision during the currency rate computations. See revision 20935462a0cabeb45480ce70114ff2f4e91eaf79 for a detailed example.
                    total_residual_company_signed = sum(invoice.residual_company_signed for invoice in self.invoice_ids)
                    total_payment_company_signed = self.currency_id.with_context(date=self.payment_date).compute(
                        chk.amount*(amount>0 or -1), self.company_id.currency_id)
                    if self.invoice_ids[0].type in ['in_invoice', 'out_refund']:
                        amount_wo = total_payment_company_signed - total_residual_company_signed
                    else:
                        amount_wo = total_residual_company_signed - total_payment_company_signed
                    # Align the sign of the secondary currency writeoff amount with the sign of the writeoff
                    # amount in the company currency
                    if amount_wo > 0:
                        debit_wo = amount_wo
                        credit_wo = 0.0
                        amount_currency_wo = abs(amount_currency_wo)
                    else:
                        debit_wo = 0.0
                        credit_wo = -amount_wo
                        amount_currency_wo = -abs(amount_currency_wo)
                    writeoff_line['name'] = self.writeoff_label
                    writeoff_line['account_id'] = self.writeoff_account_id.id
                    writeoff_line['debit'] = debit_wo
                    writeoff_line['credit'] = credit_wo
                    writeoff_line['amount_currency'] = amount_currency_wo
                    writeoff_line['currency_id'] = currency_id
                    writeoff_line = aml_obj.create(writeoff_line)
                    if counterpart_aml['debit'] or (writeoff_line['credit'] and not counterpart_aml['credit']):
                        counterpart_aml['debit'] += credit_wo - debit_wo
                    if counterpart_aml['credit'] or (writeoff_line['debit'] and not counterpart_aml['debit']):
                        counterpart_aml['credit'] += debit_wo - credit_wo
                    counterpart_aml['amount_currency'] -= amount_currency_wo
                    print("processing counterpart_aml ", counterpart_aml)

                checks.append(counterpart_aml)
                if not self.currency_id.is_zero(chk.amount*(amount>0 or -1)):
                    if not self.currency_id != self.company_id.currency_id:
                        amount_currency = 0
                    liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id,
                                                                         False)
                    liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-(chk.amount*(amount>0 or -1))))
                    aml_obj.create(liquidity_aml_dict)
                    print("processing liquidity_aml_dict ", liquidity_aml_dict)



                # validate the payment
            move.post()

            # reconcile the invoice receivable/payable line(s) with the payment
            for check in checks:
                print(check)
                self.invoice_ids.register_payment(check)


            return move

        else:
            return super(account_payment, self)._create_payment_entry(amount)


class account_register_payments(models.TransientModel):
    _inherit = "account.register.payments"

    journal_type = fields.Selection(related='journal_id.type', string='Journal type')
    check_ids = fields.One2many('account.treasury', 'payment_id', string='List of Checks')
    temporary_bank_journal = fields.Boolean(related='journal_id.temporary_bank_journal')
    document_type = fields.Many2one('account.treasury.type', 'Document Type')



    @api.multi
    def create_payments(self):
        '''Create payments according to the invoices.
        Having invoices with different commercial_partner_id or different type (Vendor bills with customer invoices)
        leads to multiple payments.
        In case of all the invoices are related to the same commercial_partner_id and have the same type,
        only one payment will be created.

        :return: The ir.actions.act_window to show created payments.
        '''
        Payment = self.env['account.payment']
        payments = Payment
        for payment_vals in self.get_payments_vals():
            payments += Payment.create(payment_vals)
        for check in self.check_ids:
            if(len(payments)==1):
                check.payment_id=payments
            else:
                raise UserError(_('We Cannot do this operation.'))
        payments.post()
        return {
            'name': _('Payments'),
            'domain': [('id', 'in', payments.ids), ('state', '=', 'posted')],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.payment',
            'view_id': False,
            'type': 'ir.actions.act_window',
        }




class account_bank_statement_line(models.Model):
    _inherit = 'account.bank.statement.line'

    check_number = fields.Char(string='Check number')
