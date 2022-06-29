# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class XLSXPrintWizard(models.TransientModel):
    _name = 'xlsx.print.wizard'
    _description = 'XLSX Print Wizard'

    xls_output = fields.Binary(string='Excel Output', readonly=True)
    name = fields.Char(string='File Name', help='Save report as .xls format', default='Aged Receivable.xlsx')
