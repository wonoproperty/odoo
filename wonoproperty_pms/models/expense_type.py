# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ExpenseType(models.Model):
    _name = 'expense.type'
    _description = 'Expense Type'

    name = fields.Char(string='Name', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
