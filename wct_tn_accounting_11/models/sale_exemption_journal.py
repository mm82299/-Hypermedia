# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
#                   odoo, Open Source Management Solution                    #
#                   ###     PROOSOFT CLOUD     ###                    #
#                                 --2018--                                   #
#                                                                            #
##############################################################################


from odoo import models, fields, api, _,exceptions
import odoo.addons.decimal_precision as dp
from datetime import datetime


class sale_exemption_journal_line(models.Model):
    _name = 'sale.exemption.journal.line'

    name = fields.Char('Order Number')
    invoice_id = fields.Many2one('account.invoice','Invoice', ondelete="cascade")
    invoice_date = fields.Date('Invoice date',related='invoice_id.date_invoice', store=True)
    id_type = fields.Char('Type ID', default="1")
    vat = fields.Char('Vat', related='partner_id.vat', store=True)
    partner_id = fields.Many2one('res.partner','Partner',related='invoice_id.partner_id', store=True)
    address = fields.Char('Address', related='partner_id.street', store=True)
    exemption_certificate = fields.Many2one('exemption.certificate', string='Exemption Certificate',related='invoice_id.exemption_certificate_id', store=True)
    exemption_date_start = fields.Date(string='Start Date',related='exemption_certificate.start_date', store=True)

    vat_order = fields.Char('Vat order',related='invoice_id.vat_order', store=True)
    vat_order_date = fields.Date('Vat order date',related='invoice_id.date_vat_order', store=True)
    # amount_ht = fields.Monetary('Amount HT',related='invoice_id.amount_total', store=True)
    amount_ht = fields.Float('Total HT',digits=dp.get_precision('Account'),store=True, readonly=True, compute='_compute_total_ht')

    fodec_rate = fields.Char('FODEC rate',compute='_compute_amount_exempt', store=True)
    fodec_amount = fields.Float('FODEC amount',digits=dp.get_precision('Account'),store=True, readonly=True, compute='_compute_amount_exempt')

    dc_rate = fields.Char('DC rate',compute='_compute_amount_exempt', store=True)
    dc_amount = fields.Float('DC amount',digits=dp.get_precision('Account'),store=True, readonly=True, compute='_compute_amount_exempt')


    tax_rate = fields.Char('Tax rate',compute='_compute_amount_exempt', store=True)
    tax_amount = fields.Float('Tax amount',digits=dp.get_precision('Account'),store=True, readonly=True, compute='_compute_amount_exempt')

    journal_id = fields.Many2one('sale.exemption.journal','Journal', ondelete="set null")


    @api.one
    @api.depends('invoice_id')
    def _compute_total_ht(self):
        self.amount_ht = self.env['account.invoice'].search([('id','=',self.invoice_id.id)]).amount_total

    @api.one
    @api.depends('invoice_id')
    def _compute_amount_exempt(self):
        amount_tax_exempt = 0.0
        fodec_tax_exempt = 0.0
        fodec_rate = 0.0
        tax_rate = 0.0
        for line in self.invoice_id.invoice_line_ids:
            taxes = line.invoice_line_tax_ids.compute_all(
                (line.price_unit * (1.0 - (line.discount or 0.0) / 100.0)),line.currency_id,
                line.quantity, line.product_id, self.partner_id)['taxes']

            for tax in taxes:
                t = self.env['account.tax'].browse(tax['id'])
                if t.include_base_amount:
                    fodec_tax_exempt+= tax['amount']
                    fodec_rate = t.amount
                else:
                    amount_tax_exempt+= tax['amount']
                    tax_rate = t.amount
        self.tax_amount=amount_tax_exempt
        self.tax_rate=str(tax_rate * 100)
        self.fodec_amount=fodec_tax_exempt
        self.fodec_rate=str(fodec_rate * 100)


class sale_exemption_journal(models.Model):
    _name = 'sale.exemption.journal'
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = "sale Exemption Journal"

    name = fields.Char('File name',store=True,track_visibility='always',compute='_get_name')
    line_ids = fields.One2many('sale.exemption.journal.line','journal_id', string='Lines',compute='_get_name')

    period = fields.Selection([
            ('T1','T1'),
            ('T2','T2'),
            ('T3','T3'),
            ('T4','T4'),
        ], string='Quarter',track_visibility='onchange', default='T1', required=True)

    fiscal_year_id = fields.Many2one('fiscal.year','Fiscal year', ondelete="cascade", required=True)



    state = fields.Selection([
            ('draft','Draft'),
            ('valid','Valid'),
        ], string='State', default='draft',track_visibility='onchange')

    total_ht = fields.Float('Total HT',digits=dp.get_precision('Account'),store=True, readonly=True, compute='_compute_total')
    total_fodec = fields.Float('Total Fodec',digits=dp.get_precision('Account'),store=True, readonly=True, compute='_compute_total')
    total_dc = fields.Float('Total DC',digits=dp.get_precision('Account'),store=True, readonly=True, compute='_compute_total')
    total_tax = fields.Float('Total TAX',digits=dp.get_precision('Account'),store=True, readonly=True, compute='_compute_total')
    num_invoice = fields.Integer('Invoice number',store=True, readonly=True, compute='_compute_total')

    @api.one
    @api.depends('fiscal_year_id','period')
    def _get_name(self):
        if self.fiscal_year_id:
            self.name = 'BCD'+'_'+self.period+'_'+self.fiscal_year_id.code[2:]
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
            res = self.env['sale.exemption.journal.line'].search([
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
            # self.name = 'BCD'+'_'+self.period+'_'+self.fiscal_year_id
        else:
            self.name= ''

        # if self.fiscal_year_id:
        #     year = self.fiscal_year_id.date_start[:4]
        #     # year = self.fiscal_year_id
        #     if self.period == 'T1':
        #         start_date = '01-01-'+year
        #         end_date = '31-03-'+year
        #     elif self.period == 'T2':
        #         start_date = '01-04-'+year
        #         end_date = '30-06-'+year
        #     elif self.period == 'T3':
        #         start_date = '01-06-'+year
        #         end_date = '30-09-'+year
        #     elif self.period == 'T4':
        #         start_date = '01-10-'+year
        #         end_date = '31-12-'+year
        #     res = self.env['sale.exemption.journal.line'].search([
        #         ('vat_order_date','>=',start_date),
        #         ('vat_order_date','<=',end_date),
        #         ])
        #     lines = []
        #     i = 1
        #     for r in res:
        #         r.name = str(i)
        #         r.write({'name':str(i)})
        #         lines.append(r.id)
        #         i+=1
        #     self.line_ids = [(6, 0, lines)]


    @api.one
    @api.depends('line_ids')
    def _compute_total(self):
        total_ht = 0.0
        total_fodec = 0.0
        total_dc = 0.0
        total_tax = 0.0
        i = 0
        for line in self.line_ids:
            total_ht += line.amount_ht
            total_fodec += line.fodec_amount
            total_dc += line.dc_amount
            total_tax += line.tax_amount
            i += 1

        self.total_ht = total_ht
        self.total_fodec = total_fodec
        self.total_dc = total_dc
        self.total_tax = total_tax
        self.num_invoice = i

    # @api.one
    @api.onchange('fiscal_year_id','period')
    def onchange_date(self):
        if self.fiscal_year_id:
            year = self.fiscal_year_id.date_start[:4]
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
            res = self.env['sale.exemption.journal.line'].search([
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
        files = self.env['ir.attachment'].search([('res_model','=', 'sale.exemption.journal'),('res_id','=', self.id), ])
        files.unlink()

    @api.one
    def unlink(self):
        if self.state == 'valid':
            raise exceptions.ValidationError(_("You can't delete an exemption journal in valid state!"))
        else:
            super(sale_exemption_journal, self).unlink()
