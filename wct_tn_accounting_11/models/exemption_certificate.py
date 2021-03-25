# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
#                   odoo, Open Source Management Solution                    #
#                   ###     PROOSOFT CLOUD    ###                    #
#                                 --2018--                                   #
#                                                                            #
##############################################################################


from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from datetime import datetime

class exemption_certificate(models.Model):
    _name = 'exemption.certificate'
    _description = 'Exemption Certificate'


    name = fields.Char('Number', required=True)
    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date')
    certificate = fields.Binary(string='Certificate')
    partner_id = fields.Many2one('res.partner','Partner')

class res_partner(models.Model):
    _inherit = 'res.partner'

    exemption_certificate_ids = fields.One2many('exemption.certificate', 'partner_id','Exemption Certificate')
    vat_exemption = fields.Boolean(string="VAT Exemption", compute='_is_vat_exemption')

    @api.one
    @api.depends('exemption_certificate_ids')
    def _is_vat_exemption(self):
        vat_exemption = False
        today = datetime.today()
        for certificate in self.exemption_certificate_ids:
            if not certificate.end_date:
                if today >= datetime.strptime(certificate.start_date, '%Y-%m-%d'):
                    vat_exemption = True
                    break
            elif today <= datetime.strptime(certificate.end_date, '%Y-%m-%d') and today >= datetime.strptime(certificate.start_date, '%Y-%m-%d'):
                vat_exemption = True
                break
        self.vat_exemption = vat_exemption

    @api.one
    def get_certificate(self, date):
        vat_exemption = False
        date = datetime.strptime(date[:10], '%Y-%m-%d')
        for certificate in self.exemption_certificate_ids:
            if not certificate.end_date:
                if date >= datetime.strptime(certificate.start_date, '%Y-%m-%d'):
                    vat_exemption = certificate
                    break
            elif date <= datetime.strptime(certificate.end_date, '%Y-%m-%d') and date >= datetime.strptime(certificate.start_date, '%Y-%m-%d'):
                vat_exemption = certificate
                break
        return vat_exemption

