# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    tds_account_id = fields.Many2one(string="Tax retainer account",
                                     comodel_name="account.account",)