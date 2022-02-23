# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class FinancierFinancier(models.Model):
    _name = 'financier.financier'
    _description = 'Financier'

    name = fields.Char(string='Name', required=True)
    financier_type = fields.Selection([('financier', 'Financier'),
                                       ('solicitor', 'Solicitor')], string='Type', required=True, default='financier')
