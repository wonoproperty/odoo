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
    tenant_history_id = fields.Many2one('tenant.history', string='Owner History')
    amount_in_words = fields.Char(string="Amount In Words", compute='_amount_in_words')

    @api.onchange('property_expense_id')
    def onchange_property_expense(self):
        if self.property_expense_id:
            invoice_lines = [(5, 0, 0)]
            fiscal_position = self.fiscal_position_id
            accounts = self.property_expense_id.product_id.product_tmpl_id.get_product_accounts(
                fiscal_pos=fiscal_position)
            if self.is_sale_document(include_receipts=True):
                # Out invoice.
                account = accounts['income'] or self.account_id
            else:
                # In invoice.
                account = accounts['expense'] or self.account_id
            data = ({
                'price_unit': 0.0,
                'product_id': self.property_expense_id.product_id.id,
                'name': self.property_expense_id.name,
                'account_id': account.id,
            })
            invoice_lines.append((0, 0, data))
            self.invoice_line_ids = invoice_lines

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
        for rec in self:
            if rec.property_unit_id and rec.property_expense_id and rec.date_from and rec.date_to:
                invoices = rec.search([('property_unit_id', '=', rec.property_unit_id.id),
                                        ('property_expense_id', '=', rec.property_expense_id.id),
                                        ('id', '!=', rec.id)]).filtered(lambda x: x.date_from <= rec.date_from <= x.date_to
                                                                                  or x.date_from <= rec.date_to <= x.date_to)
                if invoices:
                    raise UserError(_('There is another invoice with this expense for this period'))
        return res
