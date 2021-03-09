# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
#                   odoo, Open Source Management Solution                    #
#                   ###      PROOSOFT CLOUD      ###                    #
#                                 --2018--                                   #
#                                                                            #
##############################################################################


import base64
from odoo import models, fields, api, _
from odoo.tools.translate import _
from . import purchase_record_set
from odoo.exceptions import UserError, ValidationError

def _create_journal(self, data):
    v = {}
    dta = ''
    declar_obj = self.env['purchase.exemption.journal']
    attachment_obj = self.env['ir.attachment']
    # if context is None:
    #     context = {}

    declar = declar_obj.browse(data)
    if not declar.fiscal_year_id.company_id.partner_id.vat:
        raise ValidationError(_('Company vat'),_('Set your company vat first.'))
    for pline in declar.line_ids:
        if not pline.partner_id.vat:
            raise ValidationError(_('Partner vat'),_('Set vat for the partner %s.')% pline.partner_id.name)
        if not pline.partner_id.street:
            raise ValidationError(_('Partner address'),_('Set address for the partner %s.')% pline.partner_id.name)
    vat = declar.fiscal_year_id.company_id.partner_id.vat[3:]

    def date_format(s):
        s = str(s)
        s = s[8:11]+s[5:7]+s[:4]
        return s

    v['ef']= str('EF')
    v['vat']= str(vat[:7])
    v['vat_id']= str(vat[7])
    v['vat_cat']= str(vat[9])
    v['vat_num']= str(vat[10:])
    v['fiscal_year']= str(declar.fiscal_year_id.code)
    v['period']= str(declar.period)
    v['company']= str(declar.fiscal_year_id.company_id.name).ljust(40, ' ')
    v['activity']= str(declar.fiscal_year_id.company_id.name).ljust(40, ' ')
    v['city']= str(declar.fiscal_year_id.company_id.city and declar.fiscal_year_id.company_id.city or '').ljust(40, ' ')
    v['street']= str(declar.fiscal_year_id.company_id.street and declar.fiscal_year_id.company_id.street or '').ljust(72, ' ')
    v['num']= str(declar.fiscal_year_id.company_id.state_id and declar.fiscal_year_id.company_id.state_id.code or '').ljust(4, ' ')
    v['zip']= str(declar.fiscal_year_id.company_id.zip and declar.fiscal_year_id.company_id.zip or '').ljust(4, ' ')

    record_type = purchase_record_set.record_ef
    dta_line = record_type(v).generate()
    dta = dta + dta_line
    v= {}

    for pline in declar.line_ids:

        v['df']= str('DF')
        v['vat']= str(vat[:7])
        v['vat_id']= str(vat[7])
        v['vat_cat']= str(vat[9])
        v['vat_num']= str(vat[10:])
        v['fiscal_year']= str(declar.fiscal_year_id.code)
        v['period']= str(declar.period)

        v['order_num']= str(pline.name).zfill(6)
        v['certificate']= str(pline.exemption_certificate.name).ljust(30, ' ')
        v['vat_order']= str(pline.vat_order).ljust(13, ' ')
        v['vat_order_date']= str(date_format(pline.vat_order_date))
        v['partner_vat']= str(pline.partner_id.vat[3:]).ljust(13, ' ')
        v['partner']= str(pline.partner_id.name).ljust(40, ' ')
        v['invoice']= str(pline.invoice_id.number).ljust(30, ' ')
        v['invoice_date']= str(date_format(pline.invoice_date))
        v['amount_ht']= str(int(pline.amount_ht * 1000)).zfill(15)
        v['tax_amount']= str(int(pline.tax_amount * 1000)).zfill(15)
        v['start']= '<'
        v['subject']= str(pline.subject and pline.subject or '' ).ljust(320, ' ')
        v['end']= '/>'

        record_type = purchase_record_set.record_df
        dta_line = record_type(v).generate()
        dta = dta + dta_line
    v= {}

    v['tf']= str('TF')
    v['vat']= str(vat[:7])
    v['vat_id']= str(vat[7])
    v['vat_cat']= str(vat[9])
    v['vat_num']= str(vat[10:])
    v['fiscal_year']= str(declar.fiscal_year_id.code)
    v['period']= str(declar.period)
    v['num_invoice']= str(declar.num_invoice).zfill(6)
    v['reserved1']= str('').ljust(142, ' ')
    v['total_ht']= str(int(declar.total_ht * 1000)).zfill(15)
    v['total_tax']= str(int(declar.total_tax * 1000)).zfill(15)

    record_type = purchase_record_set.record_tf
    dta_line = record_type(v).generate()
    dta = dta + dta_line

    dta_data = base64.encodestring(dta)
    print("yesss")
    print(dta_data)
    attachment_obj.create({
        'name': declar.name,
        'datas': dta_data,
        'datas_fname': '%s.txt'%declar.name,
        'res_model': 'purchase.exemption.journal',
        'res_id': data,
        })
    return dta_data

class create_purchase_exemption_declar(models.Model):
    _inherit="purchase.exemption.journal"

    @api.one
    def button_confirm(self):
        # if not context:
        #     context = {}
        # if isinstance(self._ids, list):
        #     req_id = self._ids[0]
        # else:
        #     req_id = self._ids
        # current = self.browse(req_id)
        # data = {}
        #
        # data['id'] = self._ids[0]
        # dta_file = _create_journal(self, cr, uid, data, context)
        _create_journal(self, self.id)
        # self.write({'state':'valid'})
        self.state = 'valid'
        return True

# create_purchase_exemption_declar()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
