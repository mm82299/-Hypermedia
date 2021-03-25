# -*- coding: utf-8 -*-

from odoo import models, fields, api

import logging
_logger = logging.getLogger(__name__)

class account_fiscal_position(models.Model):

    _inherit = 'account.fiscal.position'

    stamp_tax_id = fields.Many2one(string="Fiscal Stamp", comodel_name="account.tax")
