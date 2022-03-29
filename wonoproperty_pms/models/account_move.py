# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


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
                rec.partner_id = rec.property_unit_id.tenant_id
                rec.invoice_payment_term_id = rec.partner_id.property_payment_term_id

    @api.model
    def create(self, vals):
        res = super(AccountMoveProperty, self).create(vals)
        if res.property_unit_id and res.property_expense_id and res.date_from and res.date_to:
            invoices = self.search([('property_unit_id', '=', res.property_unit_id.id),
                                    ('property_expense_id', '=', res.property_expense_id.id),
                                    ('id', '!=', res.id)]).filtered(lambda x: x.date_from <= res.date_from <= x.date_to
                                                                              or x.date_from <= res.date_to <= x.date_to)
            if invoices:
                raise UserError(_('There is another invoice with this expense for this period'))
        return res

    def write(self, vals):
        res = super(AccountMoveProperty, self).write(vals)
        if self.property_unit_id and self.property_expense_id and self.date_from and self.date_to:
            invoices = self.search([('property_unit_id', '=', self.property_unit_id.id),
                                    ('property_expense_id', '=', self.property_expense_id.id),
                                    ('id', '!=', self.id)]).filtered(lambda x: x.date_from <= self.date_from <= x.date_to
                                                                              or x.date_from <= self.date_to <= x.date_to)
            if invoices:
                raise UserError(_('There is another invoice with this expense for this period'))
        return res
