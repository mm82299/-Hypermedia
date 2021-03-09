# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
#                   odoo, Open Source Management Solution                    #
#                   ###     PROOSOFT CLOUD     ###                    #
#                                 --2018--                                   #
#                                                                            #
##############################################################################


import logging
_logger = logging.getLogger(__name__)

try:
    import vatnumber
except ImportError:
    _logger.warning("VAT validation partially unavailable because the `vatnumber` Python library cannot be found. "
                                          "Install it to support more countries, for example with `easy_install vatnumber`.")
    vatnumber = None

from odoo import models

_ref_vat = {
    'at': 'ATU12345675',
    'be': 'BE0477472701',
    'bg': 'BG1234567892',
    'ch': 'CHE-123.456.788 TVA or CH TVA 123456', #Swiss by Yannick Vaucher @ Camptocamp
    'cy': 'CY12345678F',
    'cz': 'CZ12345679',
    'de': 'DE123456788',
    'dk': 'DK12345674',
    'ee': 'EE123456780',
    'el': 'EL12345670',
    'es': 'ESA12345674',
    'fi': 'FI12345671',
    'fr': 'FR32123456789',
    'gb': 'GB123456782',
    'gr': 'GR12345670',
    'hu': 'HU12345676',
    'hr': 'HR01234567896', # Croatia, contributed by Milan Tribuson
    'ie': 'IE1234567FA',
    'it': 'IT12345670017',
    'lt': 'LT123456715',
    'lu': 'LU12345613',
    'lv': 'LV41234567891',
    'mt': 'MT12345634',
    'mx': 'MXABC123456T1B',
    'nl': 'NL123456782B90',
    'no': 'NO123456785',
    'pe': 'PER10254824220 or PED10254824220',
    'pl': 'PL1234567883',
    'pt': 'PT123456789',
    'ro': 'RO1234567897',
    'se': 'SE123456789701',
    'si': 'SI12345679',
    'sk': 'SK0012345675',
    'tn': 'TN 1234567ABC000'
}
caractere_vat = {
    1: 'a',
    2: 'b',
    3: 'c',
    4: 'd',
    5: 'e',
    6: 'f',
    7: 'g',
    8: 'h',
    9: 'j',
    10: 'k',
    11: 'l',
    12: 'm',
    13: 'n',
    14: 'p',
    15: 'q',
    16: 'r',
    17: 's',
    18: 't',
    19: 'v',
    20: 'w',
    21: 'x',
    22: 'y',
    23: 'z'
}
class res_partner(models.Model):
    _inherit = 'res.partner'

    def check_vat_tn(self, vat):
        '''
        Check Tunisian VAT number.
        '''
        total = 0
        x = 7
        c = 0
        try:
            if len(vat) != 13:
                for n in vat[:7]:
                    c += 1
                    if not n.isnumeric():
                        vat = vat.rjust(len(vat) + (8-c), '0')
                        break

            for n in vat[:7]:
                total += int(n) * x
                x -= 1
            reste = (total % 23) + 1
            if vat[7:8].upper() == caractere_vat[reste].upper():
                return True
            else:
                return False
        except:
            return False

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
