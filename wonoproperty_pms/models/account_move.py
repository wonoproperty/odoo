# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountMoveProperty(models.Model):
    _inherit = 'account.move'

    def _amount_in_words(self):
        for rec in self:
            rec.amount_in_words = str(rec.currency_id.amount_to_text(rec.amount_total))

    property_unit_id = fields.Many2one('property.unit', string='Property')
    property_expense_id = fields.Many2one('expense.type', string='Expense')
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    tenant_history_id = fields.Many2one('tenant.history', string='Tenant History')
    amount_in_words = fields.Char(string="Amount In Words", compute='_amount_in_words')

    @api.onchange('property_unit_id')
    def onchange_property_unit(self):
        for rec in self:
            if rec.property_unit_id:
                rec['partner_id'] = rec.property_unit_id.tenant_id
                rec['invoice_payment_term_id'] = rec.partner_id.property_payment_term_id

