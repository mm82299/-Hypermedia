# -*- coding: utf-8 -*-

from odoo import api, models, _
from datetime import datetime
from odoo.exceptions import ValidationError


class withholding(models.AbstractModel):
    _name = 'report.wct_tn_accounting_11.withholding_report'
    _wrapped_report_class = None

    def tax_id(self, vat):
        if not vat:
            return ''
        vat_country, vat_number = vat[:2].lower(), vat[2:].replace(' ', '')
        print("'''''''''''''''''''''''''''''''''''''",vat_number)
        print("'''''''''''''''''''''''''''''''''''''",vat_number[:8].upper())
        return vat_number[:8].upper()

    def tva_code(self, vat):
        if not vat:
            return ''
        vat_country, vat_number = vat[:2].lower(), vat[2:].replace(' ', '')
        return vat_number[8:9].upper()

    def categ_code(self, vat):
        if not vat:
            return ''
        vat_country, vat_number = vat[:2].lower(), vat[2:].replace(' ', '')
        return vat_number[9:10].upper()


    def retenue_line(self, obj, w):
     
        for line in obj.account_invoice_ids:
            number=line.number
            date_inv=line.date_invoice
            
        return number,date_inv
 
        
        return vat_number[9:10].upper()

    def etb_num(self, vat):
        if not vat:
            return ''
        vat_country, vat_number = vat[:2].lower(), vat[2:].replace(' ', '')
        res = vat_number[10:].upper()
        if len(res) == 3:
            return res
        return '000'

    def compute_withholdin_amount(self, obj, w):
        invoice_sum = 0.0
        for invoice in obj.account_invoice_ids:
            invoice_sum += invoice.amount_total
        return (invoice_sum * 0.01 * w.rate)

    def data(self, ids):
        res = self.env['account.withholding'].browse(ids)
        data = {}
        withholding_tab = {}
        withholding_ids = []
        amount_total = 0.0
        withholding_total = 0.0
        net_amount_total = 0.0
        if len(res) == 1:
            amount_total = 0.0
            for line in res.account_invoice_ids:
                amount_total += line.amount_total
            date_start = False
            date_stop = res.account_move_id.date
            partner = res.account_move_id.company_id
            suplier = res.partner_id
            type = res.type
            for w in res.account_withholding_tax_ids:
                if w.name not in withholding_tab:
                    withholding_tab[w.name] = {
                        'amount': sum(inv.amount_total for inv in res.account_invoice_ids),
                        'withholding': self.compute_withholdin_amount(res, w),
                        'net_amount': amount_total - self.compute_withholdin_amount(res, w)
                    }
                    withholding_ids.append(w.id)
                else:
                    withholding_tab[w.name]['amount'] = sum(inv.amount_total for inv in res.account_invoice_ids)
                    withholding_tab[w.name]['withholding'] += self.compute_withholdin_amount(res, w)
                    withholding_tab[w.name]['net_amount'] -= self.compute_withholdin_amount(res, w)
                withholding_total += self.compute_withholdin_amount(res, w)

            net_amount_total += amount_total - withholding_total

        withholding_ids = self.env['account.withholding.tax'].search([('id', 'not in', withholding_ids)])

        withholdings = []
        for w in withholding_ids:
            withholdings.append(w.name)

        data['partner'] = partner
        if date_start:
            data['date_start'] = datetime.strptime(date_start, '%Y-%m-%d')
        else:
            data['date_start'] = date_start
        data['date_stop'] = datetime.strptime(date_stop, '%Y-%m-%d')
        data['suplier'] = suplier
        data['type'] = type
        data['withholding_tab'] = withholding_tab
        data['withholdings'] = withholdings
        data['net_amount'] = net_amount_total
        data['withholding'] = withholding_total
        data['amount'] = amount_total

        if not partner.vat:
            raise ValidationError(_("You must define the vat number for your company"))
        if not suplier.vat and not suplier.ref:
            raise ValidationError(_("You must define the vat or the cin number for your partner"))
        return data

    def get_report_values(self, docids, data=None):
        docs = self.env['account.withholding'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'account.withholding',
            'docs': docs,
            'data': self.data(docids),
            'tax_id': self.tax_id,
            'tva_code': self.tva_code,
            'categ_code': self.categ_code,
            'etb_num': self.etb_num
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
