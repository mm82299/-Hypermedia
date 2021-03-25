# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
#                   odoo, Open Source Management Solution                    #
#                   ###     PROOSOFT CLOUD      ###                    #
#                                 --2018--                                   #
#                                                                            #
##############################################################################


{
    'name': 'Tunisia - Accounting 11.0',
    'version': '1.0',
    'author': 'proosoft',
    'website': 'http://www.proosoft.com',
    'summary': 'Manage Chart of Accounts and Taxes template for companies in Tunisia with odoo 11.0',
    'category': 'Localization/Account Charts',
    'description': """
This is the base module to manage Chart of Accounts and Taxes template for companies in Tunisia.
=================================================================================================
Ce Module charge le modèle du plan de comptes standard Tunisien et permet de générer les états
comptables aux normes tunisiennes.""",

    'depends': ['base_iban', 'base_vat', 'account', 'account_cancel', 'sale', 'sale_management', 'hr', 'purchase', 'document' ],
    'data': [
        'security/ir.model.access.csv',
        'data/tn_pcg_taxes.xml',
        'data/plan_comptable_general.xml',
        'data/tn_tax.xml',
        'data/tn_fiscal_templates.xml',
        'data/account_chart_template.yml',
        'data/res_bank_data.xml',
        # 'data/data.xml',
        'data/vesement_sequence.xml',
        'data/treasury_type_data.xml',
        'views/report_invoice.xml',
        'views/res_partner_view.xml',
        'views/wct_account.xml',
        'views/account_stamp_tax.xml',
        'views/treasury_view.xml',
        'views/exchange_document.xml',
        'views/vesement_view.xml',
        'views/account_journal.xml',
        'reports/withholding_report.xml',
        'views/account_invoice.xml',
        'views/purchase_exemption_journal.xml',
        'views/sale_exemption_journal.xml',
        'views/account_withholding_tax_views.xml',
        'views/account_withholding_views.xml',
        'report/report_cash_vesement.xml',
        'report/vesement_report_views.xml',
        'report/report_check_vesement.xml',
        'report/report_traite_vesement.xml',
    ],
    'images': [
        'static/description/wct.png',
    ],
    'test': [],
    'demo_xml': [],
    'active': True,
    'installable': True,
    'application': True,

}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
