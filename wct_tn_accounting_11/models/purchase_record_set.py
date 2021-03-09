# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
#                   odoo, Open Source Management Solution                    #
#                   ###      PROOSOFT CLOUD    ###                    #
#                                 --2018--                                   #
#                                                                            #
##############################################################################


import re
from odoo.tools.translate import _

TRANS=[
    (u'é','e'),
    (u'è','e'),
    (u'à','a'),
    (u'ê','e'),
    (u'î','i'),
    (u'ï','i'),
    (u'â','a'),
    (u'ä','a'),
]

class record:
    def __init__(self, global_context_dict):
        for i in global_context_dict:
            global_context_dict[i] = global_context_dict[i] \
                    and tr(global_context_dict[i])
        self.fields = []
        self.global_values = global_context_dict
        self.pre = {
            'padding': '',
            'seg_num1': '01',
            'seg_num2': '02',
            'seg_num3': '03',
            'seg_num4': '04',
            'seg_num5': '05',
            'flag': '0',
            'zero4': '          '
        }
        self.post={'date_value_hdr': '000000', 'type_paiement': '0'}
        self.init_local_context()

    def init_local_context(self):
        """
        Must instanciate a fields list, field = (name,size)
        and update a local_values dict.
        """
        raise _('not implemented')

    def generate(self):
        res=''
        for field in self.fields :
            if self.pre.has_key(field[0]):
                value = self.pre[field[0]]
            elif self.global_values.has_key(field[0]):
                value = self.global_values[field[0]]
            elif self.post.has_key(field[0]):
                value = self.post[field[0]]
            else :
                pass
            try:
                res = res + c_ljust(value, field[1])
            except :
                pass
        return res

class record_df(record):
    def init_local_context(self):
        self.fields=[
            ('df', 2),
            ('vat', 7),
            ('vat_id', 1),
            ('vat_cat', 1),
            ('vat_num', 3),
            ('fiscal_year', 4),
            ('period', 2),

            ('order_num', 6),
            ('certificate', 30),
            ('vat_order', 13),

            ('vat_order_date', 8),
            ('partner_vat', 13),
            ('partner', 40),
            ('invoice', 30),
            ('invoice_date', 8),
            ('amount_ht', 15),
            ('tax_amount', 15),
            ('start', 1),
            ('subject', 320),
            ('end', 2),
            ('newline', 1)
        ]
        self.pre.update( {
            'newline': '\r\n',
        })

class record_ef(record):
    def init_local_context(self):
        self.fields=[
            ('ef', 2),
            ('vat', 7),
            ('vat_id', 1),
            ('vat_cat', 1),
            ('vat_num', 3),
            ('fiscal_year', 4),
            ('period', 2),

            ('company', 40),
            ('activity', 40),
            ('city', 40),
            ('street', 72),
            ('num', 4),
            ('zip', 4),
            ('newline', 1)
        ]
        self.pre.update( {
            'newline': '\r\n',
        })

class record_tf(record):
    def init_local_context(self):
        self.fields=[
            ('tf', 2),
            ('vat', 7),
            ('vat_id', 1),
            ('vat_cat', 1),
            ('vat_num', 3),
            ('fiscal_year', 4),
            ('period', 2),

            ('num_invoice', 6),
            ('reserved1', 142),
            ('total_ht', 15),
            ('total_tax', 15),
            ('newline', 1)
        ]
        self.pre.update( {
            'newline': '\r\n',
        })

def tr(string_in):
    try:
        string_in= string_in.decode('utf-8')
    except:
        # If exception => then just take the string as is
        pass
    for k in TRANS:
        string_in = string_in.replace(k[0],k[1])
    try:
        res= string_in.encode('ascii','replace')
    except:
        res = string_in
    return res







def c_ljust(s, size):
    """
    check before calling ljust
    """
    s= s or ''
    if len(s) > size:
        s= s[:size]
    s = s.decode('utf-8').encode('latin1','replace').ljust(size)
    return s
