from odoo import models, fields, api, exceptions, _

import logging
_logger = logging.getLogger(__name__)

class account_invoice(models.Model):

    _inherit = 'account.invoice'
    
    @api.onchange('purchase_id')
    def purchase_order_change(self):
        res = super(account_invoice, self).purchase_order_change()
        print ("res",res)
        return 
    
    def _prepare_invoice_line_from_po_line(self, line):
        res = super(account_invoice, self)._prepare_invoice_line_from_po_line(line=line)
        print ("res ================================",res)
        return res
    
    @api.multi
    def get_taxes_values(self):
        fpos = self.fiscal_position_id
        self.invoice_line_tax_ids = fpos.map_tax(self.account_id.tax_ids, partner=self.partner_id).ids
        print ("Cal.........................",self._context, self.fiscal_position_id, self.fiscal_position_id.stamp_tax_id)
        tax_grouped = super(account_invoice, self).get_taxes_values()
        if self.fiscal_position_id and self.fiscal_position_id.stamp_tax_id:
            # for line in self.invoice_line_tax_ids:
            #     _logger.info(('line tax='))
                tax = self.fiscal_position_id.stamp_tax_id
                val = {
                    'invoice_id': self.id,
                    'name': tax.name,
                    'tax_id': tax.id,
                    'amount': tax.amount,
                    'manual': True,
                    'sequence': 20,
                    'account_analytic_id': tax['analytic'] and line.account_analytic_id.id or False,
                    'account_id': self.type in ('out_invoice', 'in_invoice') and tax.account_id.id or tax.refund_account_id.id,
                }

                # If the taxes generate moves on the same financial account as the invoice line,
                # propagate the analytic account from the invoice line to the tax line.
                # This is necessary in situations were (part of) the taxes cannot be reclaimed,
                # to ensure the tax move is allocated to the proper analytic account.
                # if not val.get('account_analytic_id') and line.account_analytic_id and val['account_id'] == line.account_id.id:
                #     val['account_analytic_id'] = line.account_analytic_id.id
                key_search = tax.id

                if any(line.invoice_line_tax_ids for line in self.invoice_line_ids) and not self.tax_line_ids and key_search not in tax_grouped:
                    tax_grouped[key_search] = val
        active_model = self._context.get('active_model')
        active_id = self._context.get('active_id')
        if active_model == 'purchase.order':
            if self.partner_id and self.partner_id.property_account_position_id and self.partner_id.property_account_position_id.stamp_tax_id:
                tax = self.partner_id.property_account_position_id.stamp_tax_id
                val = {
                    'invoice_id': self.id,
                    'name': tax.name,
                    'tax_id': tax.id,
                    'amount': tax.amount,
                    'manual': True,
                    'sequence': 20,
                    'account_analytic_id': tax['analytic'] and line.account_analytic_id.id or False,
                    'account_id': self.type in ('out_invoice', 'in_invoice') and tax.account_id.id or tax.refund_account_id.id,
                }
                key_search = tax.id
                if any(line.invoice_line_tax_ids for line in self.invoice_line_ids) and not self.tax_line_ids and key_search not in tax_grouped:
                    tax_grouped[key_search] = val
        return tax_grouped