# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountMoveProperty(models.Model):
    _inherit = 'account.move'

    property_unit_id = fields.Many2one('property.unit', string='Property')
    property_expense_id = fields.Many2one('unit.expense.line', string='Expense')
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')