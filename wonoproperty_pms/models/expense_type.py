# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ExpenseType(models.Model):
    _name = 'expense.type'
    _description = 'Expense Type'

    name = fields.Char(string='Name', required=True)
    
    def unlink(self):
        expense_lines = self.env['unit.expense.line'].search([('expense_id', '=', self.id)])
        if expense_lines:
            raise UserError(_('Unable to delete expense type already used in units'))
        return super(ExpenseType, self).unlink()
