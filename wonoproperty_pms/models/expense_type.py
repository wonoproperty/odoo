# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ExpenseType(models.Model):
    _name = 'expense.type'
    _description = 'Expense Type'

    name = fields.Char(string='Name', required=True)
