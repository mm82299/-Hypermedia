# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
#                   odoo, Open Source Management Solution                    #
#                   ###      PROOSOFT CLOUD      ###                    #
#                                 --2018--                                   #
#                                                                            #
##############################################################################


from odoo import models, fields, api, _,exceptions
import odoo.addons.decimal_precision as dp


class purchase_exemption_journal_line(models.Model):
    _name = 'purchase.exemption.journal.line'

    name = fields.Char('Order Number')
    exemption_certificate = fields.Many2one('exemption.certificate', string='Exemption Certificate',related='invoice_id.exemption_certificate_id', store=True)
    vat_order = fields.Char('Vat order',related='invoice_id.vat_order', store=True)
    vat_order_date = fields.Date('Vat order date',related='invoice_id.date_vat_order', store=True)
    vat = fields.Char('Vat', related='partner_id.vat', store=True)
    partner_id = fields.Many2one('res.partner','Partner',related='invoice_id.partner_id', store=True)
    invoice_id = fields.Many2one('account.invoice','Invoice', ondelete="cascade")
    invoice_date = fields.Date('Invoice date',related='invoice_id.date_invoice', store=True)
    # amount_ht = fields.Monetary('Amount HT',related='invoice_id.amount_total', store=True)
    amount_ht = fields.Float('Total HT',digits=dp.get_precision('Account'),store=True, readonly=True, compute='_compute_total_ht')
    tax_amount = fields.Float('Tax amount',related='invoice_id.amount_tax_exempt', store=True)
    subject = fields.Char('Subject')
    journal_id = fields.Many2one('purchase.exemption.journal','Journal', ondelete="set null")

    @api.one
    @api.depends('invoice_id')
    def _compute_total_ht(self):
        self.amount_ht = self.env['account.invoice'].search([('id','=',self.invoice_id.id)]).amount_total

class purchase_exemption_journal(models.Model):
    _name = 'purchase.exemption.journal'
    _inherit = ['mail.thread']
    _description = "Purchase Exemption Journal"

    name = fields.Char('File name',store=True,track_visibility='always',compute='_get_name2')
    line_ids = fields.One2many('purchase.exemption.journal.line','journal_id', string='Lines',compute='_get_name2')
    total_ht = fields.Float('Total HT',digits=dp.get_precision('Account'),store=True, readonly=True, compute='_compute_total')
    total_tax = fields.Float('Total TAX',digits=dp.get_precision('Account'),store=True, readonly=True, compute='_compute_total')
    num_invoice = fields.Integer('Invoice number',store=True, readonly=True, compute='_compute_total')
    period = fields.Selection([
            ('T1','T1'),
            ('T2','T2'),
            ('T3','T3'),
            ('T4','T4'),
        ], string='Quarter',track_visibility='onchange', default='T1')
    fiscal_year_id = fields.Many2one('fiscal.year','Fiscal year', ondelete="cascade")
    state = fields.Selection([
            ('draft','Draft'),
            ('valid','Valid'),
        ], string='State', default='draft',track_visibility='onchange')

    # @api.one
    @api.depends('fiscal_year_id','period')
    def _get_name2(self):
        if self.fiscal_year_id:
            self.name = 'BCD'+'_'+self.period+'_'+self.fiscal_year_id.code[2:]
            # self.name = 'BCD'+'_'+self.period+'_'+self.fiscal_year_id
        else:
            self.name= ''

        if self.fiscal_year_id:
            year = self.fiscal_year_id.date_start[:4]
            # year = self.fiscal_year_id
            if self.period == 'T1':
                start_date = '01-01-'+year
                end_date = '31-03-'+year
            elif self.period == 'T2':
                start_date = '01-04-'+year
                end_date = '30-06-'+year
            elif self.period == 'T3':
                start_date = '01-06-'+year
                end_date = '30-09-'+year
            elif self.period == 'T4':
                start_date = '01-10-'+year
                end_date = '31-12-'+year
            res = self.env['purchase.exemption.journal.line'].search([
                ('vat_order_date','>=',start_date),
                ('vat_order_date','<=',end_date),
                ])
            lines = []
            i = 1
            for r in res:
                r.name = str(i)
                r.write({'name':str(i)})
                lines.append(r.id)
                i+=1
            self.line_ids = [(6, 0, lines)]


    @api.one
    @api.depends('line_ids')
    def _compute_total(self):
        total_ht = 0.0
        total_tax = 0.0
        i = 0
        for line in self.line_ids:
            total_ht += line.amount_ht
            total_tax += line.tax_amount
            i += 1
        self.total_ht = total_ht
        self.total_tax = total_tax
        self.num_invoice = i


    # @api.one
    @api.onchange('fiscal_year_id','period')
    def onchange_date(self):
        if self.fiscal_year_id:
            year = self.fiscal_year_id.date_start[:4]
            # year = self.fiscal_year_id
            if self.period == 'T1':
                start_date = '01-01-'+year
                end_date = '31-03-'+year
            elif self.period == 'T2':
                start_date = '01-04-'+year
                end_date = '30-06-'+year
            elif self.period == 'T3':
                start_date = '01-06-'+year
                end_date = '30-09-'+year
            elif self.period == 'T4':
                start_date = '01-10-'+year
                end_date = '31-12-'+year
            res = self.env['purchase.exemption.journal.line'].search([
                ('vat_order_date','>=',start_date),
                ('vat_order_date','<=',end_date),
                ])
            lines = []
            i = 1
            for r in res:
                r.name = str(i)
                r.write({'name':str(i)})
                lines.append(r.id)
                i+=1
            self.line_ids = [(6, 0, lines)]

    @api.one
    def button_confirm(self):
        self.state = 'valid'

    @api.one
    def button_draft(self):
        self.state = 'draft'
        files = self.env['ir.attachment'].search([('res_model','=', 'purchase.exemption.journal'),('res_id','=', self.id), ])
        files.unlink()

    @api.one
    def unlink(self):
        if self.state == 'valid':
            raise exceptions.ValidationError(_("You can't delete an exemption journal in valid state!"))
        else:
            super(purchase_exemption_journal, self).unlink()
