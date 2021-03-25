# -*- encoding: utf-8 -*-
##############################################################################
#
#    ODOO, Open Source Management Solution    
#    Copyright (C) 2004-2017 NEXTMA (http://nextma.com). All Rights Reserved
#    
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

from odoo import fields, api, models, _
from .convertion import trad


class StockPicking(models.Model):

    _inherit = "stock.picking"



    @api.multi
    @api.depends('sale_id.amount_total')
    def get_amount_letter(self):
        # import pdb;pdb.set_trace()
        amount = self.env.ref('base.main_company').currency_id.amount_to_text(self.sale_id.amount_total)
        return 10
        

    Nom_du_hauffeur = fields.Char(string='Nom du Chauffeur', translate=True)
    immatriculation_camion = fields.Char(string='immatriculation camion', translate=True)
    date_de_Livraison = fields.Date(string="Date de Livraison", required=False)
