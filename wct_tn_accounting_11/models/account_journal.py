# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
#                   odoo, Open Source Management Solution                    #
#                   ###     PROOSOFT CLOUD      ###                    #
#                                 --2018--                                   #
#                                                                            #
##############################################################################

from odoo import models, fields

class account_journal(models.Model):
    _inherit = 'account.journal'

    bank_ids = fields.Many2many('res.bank', 'account_journal_res_bank_rel', string='Allowed source bank',
                                help="Chose allowed source banks for treasury document. All banks are allowed if no bank is chosen.")
    temporary_bank_journal = fields.Boolean('Temporary Bank Journal',
                                            help="This journal will be your default temporary bank journal.")
    is_payment = fields.Boolean('Is Payment')
    document_type = fields.Many2one('account.treasury.type', 'Document Type')
