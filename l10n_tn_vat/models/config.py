# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    tds_account_id = fields.Many2one(string="Tax retainer account",
                                          comodel_name="account.account",
                                          related="company_id.tds_account_id")
