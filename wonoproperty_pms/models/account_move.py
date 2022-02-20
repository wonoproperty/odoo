# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountMoveProperty(models.Model):
    _inherit = 'account.move'

    property_unit_id = fields.Many2one('property.unit', string='Property')
    property_expense_id = fields.Many2one('expense.type', string='Expense')
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    tenant_history_id = fields.Many2one('tenant.history', string='Tenant History')
