# -*- coding: utf-8 -*-
from odoo import http

# class L10nTnVat(http.Controller):
#     @http.route('/l10n_tn_vat/l10n_tn_vat/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/l10n_tn_vat/l10n_tn_vat/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('l10n_tn_vat.listing', {
#             'root': '/l10n_tn_vat/l10n_tn_vat',
#             'objects': http.request.env['l10n_tn_vat.l10n_tn_vat'].search([]),
#         })

#     @http.route('/l10n_tn_vat/l10n_tn_vat/objects/<model("l10n_tn_vat.l10n_tn_vat"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('l10n_tn_vat.object', {
#             'object': obj
#         })