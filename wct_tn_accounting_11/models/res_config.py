# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
#                   odoo, Open Source Management Solution                    #
#                   ###     PROOSOFT CLOUD     ###                    		 #
#                                 --2018--                                   #
#                                                                            #
##############################################################################


from odoo import models, fields, api, exceptions, _

#Add a checkbox to the accounting configuration
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_accounting_withholding_tax = fields.Boolean('Allow the withholding tax',
            help='This allows you to use the withholding tax')
    module_treasury = fields.Boolean('Treasury document on payment',
                                     help='This allows you to use treasury document on payment')
    module_treasury_pos = fields.Boolean('Treasury document on point of sale',
            help='This allows you to use treasury document on point of sale')
