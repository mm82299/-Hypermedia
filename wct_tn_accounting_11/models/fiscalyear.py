# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
#                   odoo, Open Source Management Solution                    #
#                   ###      PROOSOFT CLOUD  	      ###                    #
#                                 --2018--                                   #
#                                                                            #
##############################################################################


from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp


class fiscalyear(models.Model):
    _name = 'fiscal.year'
    _description = 'Fiscal Year'

    name = fields.Char('Fiscal Year', required=True)
    code = fields.Char('Code', size=6, required=True)
    company_id = fields.Many2one('res.company', 'Company', required=True)
    date_start = fields.Date('Start Date', required=True)
    date_stop = fields.Date('End Date', required=True)
    # period_ids = fields.one2many('account.period', 'fiscalyear_id', 'Periods')
    state = fields.Selection([('draft','Open'), ('done','Closed')], 'Status', readonly=True, copy=False,default='draft')
    # end_journal_period_id = fields.many2one('account.journal.period', 'End of Year Entries Journal',readonly=True, copy=False)
