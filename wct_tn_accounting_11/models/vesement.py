##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-2014 Luis Falcon, Moldeo Interactive.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api, _
import time
from datetime import datetime
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
from .amount_to_text_fr import amount_to_text_fr


class account_vesement(models.Model):
    _name = "account.vesement"
    _description = 'Vesement'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    name = fields.Char('Reference', copy=False, readonly=True, select=True)
    date_vesement = fields.Date(string='Vesement Date', default=datetime.now().strftime('%Y-%m-%d'),
                                readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    date_from = fields.Date(string='Start Date', default=datetime.now().strftime('%Y-%m-%d'),
                            readonly=True, states={'draft': [('readonly', False)]})
    date_to = fields.Date(string='End Date', default=datetime.now().strftime('%Y-%m-%d'),
                          readonly=True, states={'draft': [('readonly', False)]})
    bank_target = fields.Many2one('res.partner.bank', 'Target Bank', readonly=True,
                                  states={'draft': [('readonly', False)]}, domain=[('company_id', '<>', False)])
    journal_id = fields.Many2one('account.journal', 'Journal', readonly=True, states={'draft': [('readonly', False)]},
                                 domain=[('type', '=', 'bank')])
    treasury_ids = fields.Many2many('account.treasury', 'account_vesement_treasury_rel', 'vesement_id', 'treasury_id',
                                    'Associated Document', domain="[('type_transaction', '=', 'receipt')]",
                                    readonly=True, states={'draft': [('readonly', False)]})
    amount = fields.Float(string='Total', digits=dp.get_precision('Account'), readonly=True, compute='_compute_amount')
    amount_in_word = fields.Char("Amount in Word")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    move_id = fields.Many2one('account.move', 'Account Entry', copy=False)
    move_ids = fields.One2many(related='move_id.line_ids', relation='account.move.line', string='Journal Items',
                               readonly=True)
    number = fields.Char('Number', required=1, readonly=True, states={'draft': [('readonly', False)]}, )
    note = fields.Text('Notes')
    state = fields.Selection([
        ('draft', 'Open'),
        ('valid', 'Validate'),
        ('cancel', 'Cancel'),
    ], 'State', required=True, readonly=True, select=1, default='draft', track_visibility='onchange')

    @api.one
    def _compute_amount(self):
        self.amount = sum(line.amount for line in self.treasury_ids)

    @api.one
    def button_draft(self):
        self.state = 'draft'

    @api.one
    def action_move_line_create(self):
        for vesement in self:
            if vesement.move_id:
                continue
            # Create the account move record.
            move = {
                'journal_id': vesement.journal_id.id,
                'date': vesement.date_vesement,
                'ref': vesement.name,
                'line_ids': [],

            }
            for line in vesement.treasury_ids:
                debit = {
                    'name': "Cheque[" + line.partner_id.name + "]N:[" + line.name + "]DV:" + line.clearing_date or '/',
                    'debit': line.amount,
                    'credit': 0,
                    'account_id': vesement.journal_id.default_debit_account_id.id,
                    'date': vesement.date_vesement,
                }
                move['line_ids'].append([0, False, debit])

            for line in vesement.treasury_ids:
                credit = {
                    'name': "Cheque[" + line.partner_id.name + "]N:[" + line.name + "]DV:" + line.clearing_date or '/',
                    'debit': 0,
                    'credit': line.amount,
                    'account_id': line.payment_id.journal_id.default_credit_account_id.id,
                    'date': vesement.date_vesement,
                }
                move['line_ids'].append([0, False, credit])

            self.move_id = self.env['account.move'].create(move)
            self.move_id.post()
            account_move_lines_to_reconcile = self.env['account.move.line']
            for treas in vesement.treasury_ids:
                account_move_lines_to_reconcile |= treas.payment_id.move_line_ids.filtered(
                lambda line: line.account_id.internal_type == 'liquidity')
            account_move_lines_to_reconcile |= self.move_id.line_ids.filtered(lambda line: line.credit > 0)
            account_move_lines_to_reconcile.reconcile()

    @api.multi
    def button_validate(self):
        if len(self.treasury_ids) == 0:
            raise UserError(_('no treasury line !'))
        for treasury in self.treasury_ids:
            if treasury.state != 'in_cash':
                raise UserError(_('Document number %s for %s is not in cash !') % (
                    treasury.name, treasury.partner_id.name))
            treasury.state = 'versed'
            treasury.bank_target = self.bank_target.id
        self.amount_in_word = amount_to_text_fr(self.amount, currency='Dinars')
        self.state = 'valid'
        self.action_move_line_create()

    @api.one
    def button_cancel(self):
        for treasury in self.treasury_ids:
            if treasury.state != 'versed':
                raise UserError(_('Document number %s for %s is not versed !') % (
                    treasury.name, treasury.partner_id.name))
            treasury.state = 'in_cash'
            treasury.bank_target = False
        #######################################
        self.refresh()
        self.move_ids.remove_move_reconcile()
        #######################################
        self.move_id.button_cancel()
        self.move_id.unlink()
        self.state = 'cancel'

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('account.vesement') or 'New'
        new_id = super(account_vesement, self).create(vals)
        new_id.message_post(body=_("Vesement created"))
        return new_id

    @api.multi
    def unlink(self):
        for vesement in self:
            if vesement.state != 'draft':
                raise UserError(_('You cannot delete this vesement !'))
        return super(account_vesement, self).unlink()

    @api.onchange('date_from', 'date_to')
    def onchange_date(self):
        if self.date_from and self.date_to:
            inv = self.env['account.treasury'].search([('state', '=', 'in_cash'),
                                                       ('clearing_date', '>=', self.date_from),
                                                       ('clearing_date', '<=', self.date_to),
                                                       ('type_transaction', '=', 'receipt'),
                                                       ('type.check', '=', True)])
            self.treasury_ids = [(6, 0, [x.id for x in inv])]

    @api.onchange('bank_target')
    def onchange_bank(self):
        self.journal_id = self.bank_target and self.bank_target.journal_id.id or False


class account_vesement_cash(models.Model):
    _name = "account.vesement.cash"
    _description = 'Cash Vesement'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    name = fields.Char('Reference', copy=False, readonly=True, select=True)
    date_vesement = fields.Date(string='Vesement Date', default=lambda *a: time.strftime('%Y-%m-%d'),
                                readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    journal_target = fields.Many2one('account.journal', 'Journal Target', readonly=True,
                                     states={'draft': [('readonly', False)]}, domain=[('type', '=', 'bank')])
    bank_target = fields.Many2one('res.partner.bank', 'Target Bank', readonly=True,
                                  states={'draft': [('readonly', False)]}, domain=[('company_id', '<>', False)])
    journal_source = fields.Many2one('account.journal', 'Journal Source', readonly=True,
                                     states={'draft': [('readonly', False)]}, domain=[('type', '=', 'cash')])
    amount = fields.Float(string='Total', digits=dp.get_precision('Account'), required=True, readonly=True,
                          states={'draft': [('readonly', False)]})
    amount_in_word = fields.Char("Amount in Word")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id, readonly=True,
                                 states={'draft': [('readonly', False)]})
    move_id = fields.Many2one('account.move', 'Account Entry', copy=False)
    move_ids = fields.One2many(related='move_id.line_ids', relation='account.move.line', string='Journal Items',
                               readonly=True)
    note = fields.Text('Notes')
    number = fields.Char('Number', required=1, readonly=True, states={'draft': [('readonly', False)]}, )
    account_id = fields.Many2one('account.account', 'Account', readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', 'Open'),
        ('valid', 'Validate'),
        ('cancel', 'Cancel'),
    ], 'State', required=True, readonly=True, select=1, default='draft', track_visibility='onchange')

    @api.onchange('bank_target')
    def onchange_bank(self):
        self.journal_id = self.bank_target and self.bank_target.journal_id.id or False

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('account.vesement.cash') or 'New'
        new_id = super(account_vesement_cash, self).create(vals)
        new_id.message_post(body=_("Vesement created"))
        return new_id

    @api.multi
    def unlink(self):
        for vesement in self:
            if vesement.state != 'draft':
                raise UserError(_('You cannot delete this cash vesement !'))
        return super(account_vesement_cash, self).unlink()

    @api.one
    def button_draft(self):
        self.state = 'draft'

    @api.one
    def action_move_line_create(self):
        vals = {
            'ref': self.name,
            'journal_id': self.journal_target.id,
            'narration': False,
            'date': self.date_vesement,
            'line_ids': [],
        }

        name = self.bank_target.acc_number
        if self.bank_target.bank_name:
            name = self.bank_target.bank_name
        move_line1 = {
            'name': "VERSEMENT [" + name + "] N:" + self.number or '/',
            'company_id': self.journal_target.company_id.id,
            'debit': 0,
            'credit': self.amount,
            'account_id': self.journal_source.default_debit_account_id.id,
            'date': self.date_vesement,
        }
        vals['line_ids'].append([0, False, move_line1])

        move_line2 = {
            'name': "VERSEMENT [" + name + "] N:" + self.number or '/',
            'company_id': self.journal_target.company_id.id,
            'debit': self.amount,
            'credit': 0,
            'account_id': self.journal_target.default_credit_account_id.id,
            'date': self.date_vesement,
        }
        vals['line_ids'].append([0, False, move_line2])
        self.move_id = self.env['account.move'].create(vals)
        self.move_id.post()

    @api.multi
    def button_validate(self):
        self.amount_in_word = amount_to_text_fr(self.amount, currency='Dinars')
        self.state = 'valid'
        self.action_move_line_create()
        return True

    @api.one
    def button_cancel(self):
        self.move_id.button_cancel()
        self.move_id.unlink()
        self.state = 'cancel'
        return True


class account_vesement_traite(models.Model):
    _name = "account.vesement.traite"
    _description = 'Vesement traite'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    name = fields.Char('Reference', copy=False, readonly=True, select=True)
    date_vesement = fields.Date(string='Vesement Date', default=datetime.now().strftime('%Y-%m-%d'),
                                readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    date_from = fields.Date(string='Start Date', default=datetime.now().strftime('%Y-%m-%d'),
                            readonly=True, states={'draft': [('readonly', False)]})
    date_to = fields.Date(string='End Date', default=datetime.now().strftime('%Y-%m-%d'),
                          readonly=True, states={'draft': [('readonly', False)]})
    bank_target = fields.Many2one('res.partner.bank', 'Target Bank', readonly=True,
                                  states={'draft': [('readonly', False)]},
                                  domain=[('company_id', '<>', False)])
    journal_id = fields.Many2one('account.journal', 'Journal', readonly=True, states={'draft': [('readonly', False)]},
                                 domain=[('type', '=', 'bank')])
    treasury_ids = fields.Many2many('account.treasury', 'account_vesement_traite_treasury_rel', 'vesement_id', 'treasury_id',
                                    'Associated Document', domain="[('type_transaction', '=', 'receipt')]",
                                    readonly=True, states={'draft': [('readonly', False)]})
    amount = fields.Float(string='Total', digits=dp.get_precision('Account'), readonly=True, compute='_compute_amount')
    amount_in_word = fields.Char("Amount in Word")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    move_id = fields.Many2one('account.move', 'Account Entry', copy=False)
    move_ids = fields.One2many(related='move_id.line_ids', relation='account.move.line', string='Journal Items',
                               readonly=True)
    note = fields.Text('Notes')
    number = fields.Char('Number', required=1, readonly=True, states={'draft': [('readonly', False)]})
    expected = fields.Boolean('Expected effect')
    state = fields.Selection([
        ('draft', 'Open'),
        ('valid', 'Validate'),
        ('cancel', 'Cancel'),
    ], 'State', required=True, readonly=True, select=1, default='draft', track_visibility='onchange')

    @api.one
    def _compute_amount(self):
        self.amount = sum(line.amount for line in self.treasury_ids)

    @api.one
    def button_draft(self):
        self.state = 'draft'

    @api.one
    def action_move_line_create(self):
        vals = {
            'ref': self.name,
            'journal_id': self.bank_target.journal_id.id,
            'narration': False,
            'date': self.date_vesement,
            'line_ids': [],
        }

        name = self.bank_target.acc_number
        if self.bank_target.bank_name:
            name = self.bank_target.bank_name
        move_line1 = {
            'name': "VERSEMENT [" + name + "] N:" + self.number or '/',
            'company_id': self.bank_target.journal_id.company_id.id,
            'debit': 0,
            'credit': self.amount,
            'account_id': self.journal_id.default_debit_account_id.id,
            'date': self.date_vesement,
        }
        vals['line_ids'].append([0, False, move_line1])

        move_line2 = {
            'name': "VERSEMENT [" + name + "] N:" + self.number or '/',
            'company_id': self.bank_target.journal_id.company_id.id,
            'debit': self.amount,
            'credit': 0,
            'account_id': self.bank_target.journal_id.default_credit_account_id.id,
            'date': self.date_vesement,
        }
        vals['line_ids'].append([0, False, move_line2])
        self.move_id = self.env['account.move'].create(vals)
        self.move_id.post()

    @api.multi
    def button_validate(self):
        if len(self.treasury_ids) == 0:
            raise UserError(_('no treasury line !'))
        for treasury in self.treasury_ids:
            if treasury.state != 'in_cash':
                raise UserError(_('Document number %s for %s is not in cash !') % (
                    treasury.name, treasury.partner_id.name))
            treasury.state = 'versed'
            treasury.bank_target = self.bank_target.id
        self.state = 'valid'
        self.action_move_line_create()
        self.amount_in_word = amount_to_text_fr(self.amount, currency='Dinars')

    @api.one
    def button_cancel(self):
        for treasury in self.treasury_ids:
            if treasury.state != 'versed':
                raise UserError(_('Document number %s for %s is not versed !') % (
                    treasury.name, treasury.partner_id.name))
            treasury.state = 'in_cash'
            treasury.bank_target = False
        #######################################
        self.refresh()
        self.move_ids.remove_move_reconcile()
        #######################################
        self.move_id.button_cancel()
        self.move_id.unlink()
        self.state = 'cancel'

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('account.vesement.traite') or 'New'
        new_id = super(account_vesement_traite, self).create(vals)
        new_id.message_post(body=_("Vesement created"))
        return new_id

    @api.multi
    def unlink(self):
        for vesement in self:
            if vesement.state != 'draft':
                raise UserError(_('You cannot delete this vesement !'))
        return super(account_vesement_traite, self).unlink()

    @api.onchange('date_from', 'date_to')
    def onchange_date(self):
        if not self.date_from or not self.date_to:
            self.treasury_ids = []
        else:
            inv = self.env['account.treasury'].search([('state', '=', 'in_cash'),
                                                       ('clearing_date', '>=', self.date_from),
                                                       ('clearing_date', '<=', self.date_to),
                                                       ('type_transaction', '=', 'receipt'),
                                                       ('type.treaty', '=', True)])

            self.treasury_ids = [(6, 0, [x.id for x in inv])]

    @api.onchange('bank_target')
    def onchange_bank(self):
        self.journal_id = self.bank_target and self.bank_target.journal_id.id or False


class account_withdrawal_cash(models.Model):
    _name = "account.withdrawal.cash"
    _description = 'Cash Withdrawal'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    name = fields.Char('Reference', copy=False, readonly=True, select=True)
    date_withdrawal = fields.Date(string='Withdrawal Date', default=lambda *a: time.strftime('%Y-%m-%d'),
                                  readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    journal_target = fields.Many2one('account.journal', 'Journal Target', readonly=True,
                                     states={'draft': [('readonly', False)]}, domain=[('type', '=', 'cash')])
    number = fields.Char('Number', required=1, readonly=True, states={'draft': [('readonly', False)]}, )
    bank_source = fields.Many2one('res.partner.bank', 'Target Bank', readonly=True,
                                  states={'draft': [('readonly', False)]}, domain=[('company_id', '<>', False)])
    journal_source = fields.Many2one('account.journal', 'Journal Source', readonly=True,
                                     states={'draft': [('readonly', False)]}, domain=[('type', '=', 'bank')])
    account_id = fields.Many2one('account.account', 'Account', readonly=True, states={'draft': [('readonly', False)]})
    amount = fields.Float(string='Total', digits=dp.get_precision('Account'), required=True, readonly=True,
                          states={'draft': [('readonly', False)]})
    amount_in_word = fields.Char("Amount in Word")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id, readonly=True,
                                 states={'draft': [('readonly', False)]})
    move_id = fields.Many2one('account.move', 'Account Entry', copy=False)
    move_ids = fields.One2many(related='move_id.line_ids', relation='account.move.line', string='Journal Items',
                               readonly=True)
    note = fields.Text('Notes')
    state = fields.Selection([
        ('draft', 'Open'),
        ('valid', 'Validate'),
        ('cancel', 'Cancel'),
    ], 'State', required=True, readonly=True, select=1, default='draft', track_visibility='onchange')

    @api.onchange('bank_source')
    def onchange_bank(self):
        self.journal_source = self.bank_source and self.bank_source.journal_id.id or False

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('account.withdrawal') or 'New'
        new_id = super(account_withdrawal_cash, self).create(vals)
        new_id.message_post(body=_("Withdrawal created"))
        return new_id

    @api.multi
    def unlink(self):
        for withdrawal in self:
            if withdrawal.state != 'draft':
                raise UserError(_('You cannot delete this cash withdrawal !'))
        return super(account_withdrawal_cash, self).unlink()

    @api.one
    def button_draft(self):
        self.state = 'draft'

    @api.one
    def account_move_get(self, withdrawal):
        if withdrawal.journal_source.sequence_id:
            if not withdrawal.journal_source.sequence_id.active:
                raise UserError(_('Please activate the sequence of selected journal !'))
            name = withdrawal.journal_source.sequence_id.next_by_id()
        else:
            raise UserError(_('Please define a sequence on the journal.'))

        move = {
            'name': name,
            'journal_id': withdrawal.journal_source.id,
            'date': withdrawal.date_withdrawal,
            'ref': name,
        }
        return move

    @api.one
    def first_move_line_get(self, withdrawal, move_id):
        move_line = {
            'name': "Retrait [" + withdrawal.bank_source.bank_name + "] N:" + withdrawal.number or '/',
            'debit': 0,
            'credit': withdrawal.amount,
            'account_id': withdrawal.journal_source.default_debit_account_id.id,
            'move_id': move_id.id,
            'journal_id': withdrawal.journal_source.id,
            'date': withdrawal.date_withdrawal,
            'date_maturity': withdrawal.date_withdrawal
        }
        line = self.env['account.move.line'].create(move_line)
        return line

    @api.one
    def withdrawal_move_line_create(self, withdrawal, move_id):
        move_line = {
            'name': "Retrait [" + withdrawal.bank_source.bank_name + "] N:" + withdrawal.number or '/',
            'debit': withdrawal.amount,
            'credit': 0,
            'account_id': withdrawal.journal_target.default_credit_account_id.id,
            'move_id': move_id.id,
            'journal_id': withdrawal.journal_source.id,
            'date': withdrawal.date_withdrawal,
            'date_maturity': withdrawal.date_withdrawal
        }
        return self.env['account.move.line'].create(move_line)

    @api.one
    def inter_move_line_create(self, withdrawal, move_id):
        move_line = {
            'name': "Retrait [" + withdrawal.bank_source.bank_name + "] N:" + withdrawal.number or '/',
            'debit': withdrawal.amount,
            'credit': 0,
            'account_id': withdrawal.account_id.id,
            'move_id': move_id.id,
            'journal_id': withdrawal.journal_source.id,
            'date': withdrawal.date_withdrawal,
            'date_maturity': withdrawal.date_withdrawal
        }
        self.env['account.move.line'].create(move_line)
        move_line.update({'debit': 0, 'credit': withdrawal.amount})
        self.env['account.move.line'].create(move_line)
        return True

    @api.one
    def action_move_line_create(self):
        move_pool = self.env['account.move']
        for withdrawal in self:
            if withdrawal.move_id:
                continue
            # Create the account move record.
            move_id = move_pool.create(self.account_move_get(withdrawal)[0])
            withdrawal.move_id = move_id
            # Create the first line of the withdrawal
            self.first_move_line_get(withdrawal, move_id)
            if self.account_id:
                self.inter_move_line_create(withdrawal, move_id)
            self.withdrawal_move_line_create(withdrawal, move_id)

    @api.multi
    def button_validate(self):
        self.amount_in_word = amount_to_text_fr(self.amount, lang='fr', currency='Dinars')
        self.state = 'valid'
        self.action_move_line_create()

    @api.one
    def button_cancel(self):
        self.move_id.button_cancel()
        self.move_id.unlink()
        self.state = 'cancel'
