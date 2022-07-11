# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar
import math
import time
import json


class PropertyUnit(models.Model):
    _name = 'property.unit'
    _description = 'Property Unit'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _rec_name = 'complete_name'

    name = fields.Char(string='Name', required=True)
    property_id = fields.Many2one('property.property', string='Property')
    date_start = fields.Date(string='Date Start')
    date_end = fields.Date(string='Date End')
    tenant_id = fields.Many2one('res.partner', string='Current Owner')
    tenant_ids = fields.One2many('tenant.history', 'property_unit_id', string='Owner History')
    invoice_ids = fields.One2many('account.move', 'property_unit_id', string='Invoices')
    expense_ids = fields.One2many('unit.expense.line', 'property_unit_id', string='Expense Lines', copy=True)
    water_odometer_reading_ids = fields.One2many('water.odometer.reading', 'property_unit_id', string='Water Meter Readings')
    complete_name = fields.Char('Complete Name', compute='_compute_complete_name', recursive=True, store=True)
    invoice_count = fields.Integer(string='Invoice Count', compute='_get_invoiced')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self._default_currency_id(),
                                  required=True)
    loan_amount = fields.Monetary(string='Loan Amount')
    end_financier = fields.Many2one('financier.financier', string='End Financier',
                                    domain="[('financier_type', '=', 'financier')]")
    s_p_solicitor = fields.Many2one('financier.financier', string='S & P Solicitor',
                                    domain="[('financier_type', '=', 'solicitor')]")
    loan_solicitor = fields.Many2one('financier.financier', string='Loan Solicitor',
                                     domain="[('financier_type', '=', 'solicitor')]")
    date_purchase = fields.Date(string='Date of Purchase')
    s_p_amount = fields.Monetary(string='S & P Amount')
    actual_tenant_ids = fields.One2many('actual.tenant.history', 'property_unit_id', string='Tenant History')
    active = fields.Boolean('Active', default=True)

    def _default_currency_id(self):
        return self.env.user.company_id.currency_id

    @api.depends('name', 'property_id.name')
    def _compute_complete_name(self):
        for rec in self:
            if rec.property_id and rec.name:
                rec.complete_name = rec.property_id.name + ' / ' + rec.name

    def action_open_tenant_wizard(self):
        ctx = self.env.context.copy()
        ctx.update({
            'default_current_tenant_id': self.tenant_id.id,
            'default_property_unit_id': self.id,
            'default_current_date_start': self.date_start,
            'default_current_date_end': self.date_end
        })
        wizard_action = {
            'type': 'ir.actions.act_window',
            'res_model': 'property.tenant.wizard',
            'name': _('Update Owner'),
            'view_mode': 'form',
            'context': ctx,
            'target': 'new',
        }
        return wizard_action

    def action_open_actual_tenant_wizard(self):
        ctx = self.env.context.copy()
        current_active_tenant = self.actual_tenant_ids.filtered(lambda x: x.current_active)
        current_active = current_active_tenant.tenant_id.id if current_active_tenant else False
        ctx.update({
            'default_current_tenant_id': current_active,
            'default_property_unit_id': self.id,
            'default_current_date_start': current_active_tenant.date_start,
            'default_current_date_end': current_active_tenant.date_end
        })
        wizard_action = {
            'type': 'ir.actions.act_window',
            'res_model': 'actual.tenant.wizard',
            'name': _('Update Tenant'),
            'view_mode': 'form',
            'context': ctx,
            'target': 'new',
        }
        return wizard_action

    def action_create_invoice(self):
        for rec in self:
            if rec.expense_ids:
                for line in rec.expense_ids:
                    water_expense = self.env.ref('wonoproperty_pms.water_charges')
                    if line.expense_id.id != water_expense.id:
                        frequency = line.expense_frequency
                        last_invoice = sorted(self.invoice_ids.filtered(lambda x: x.property_expense_id.id == line.expense_id.id), key=lambda x: x.date_to, reverse=True)
                        invoice_date = rec.date_start if not last_invoice else last_invoice[0].date_to + relativedelta(days=1)
                        date_today = datetime.now().date()
                        date_end = rec.date_end
                        if date_today >= invoice_date:
                            # if not rec.date_end or invoice_date <= rec.date_end:
                            if frequency == 'quarterly':
                                current_quarter = math.ceil(invoice_date.month / 3.)
                                prefix = 'Q' + str(current_quarter)
                                current_quarter_start_month = (current_quarter * 3) - 2
                                current_quarter_end_month = current_quarter * 3
                                current_quarter_start_date = datetime(invoice_date.year, current_quarter_start_month, 1
                                                                      ).date()
                                current_quarter_end_date = datetime(invoice_date.year, current_quarter_end_month,
                                                                    calendar.monthrange(invoice_date.year,
                                                                                        current_quarter_end_month)[
                                                                        1]).date()
                                from_date = current_quarter_start_date
                                to_date = current_quarter_end_date
                                date_end = rec.date_end if rec.date_end and current_quarter_start_date <= rec.date_end <= current_quarter_end_date  else to_date
                                if invoice_date != from_date or date_end != to_date:
                                    from_date = invoice_date
                                    to_date = date_end
                                    remaining_days = (to_date - from_date).days
                                    total_days = (current_quarter_end_date - current_quarter_start_date).days
                                    amount = line.fixed_amount * remaining_days / total_days
                                else:
                                    amount = line.fixed_amount
                            elif frequency == 'monthly':
                                current_month = invoice_date.month
                                prefix = 'M' + str(current_month)
                                current_month_start_date = datetime(invoice_date.year, current_month, 1).date()
                                current_month_end_date = datetime(invoice_date.year, current_month, calendar.monthrange(
                                    invoice_date.year, current_month)[1]).date()
                                from_date = current_month_start_date
                                to_date = current_month_end_date
                                date_end = rec.date_end if rec.date_end and current_month_start_date <= rec.date_end <= current_month_end_date else to_date
                                if invoice_date != from_date or date_end != to_date:
                                    from_date = invoice_date
                                    to_date = date_end
                                    remaining_days = (to_date - from_date).days
                                    total_days = (current_month_end_date - current_month_start_date).days
                                    amount = line.fixed_amount * remaining_days / total_days
                                else:
                                    amount = line.fixed_amount
                            else:
                                current_year_start = datetime(invoice_date.year, 1, 1).date()
                                current_year_end = datetime(invoice_date.year, 12, 31).date()
                                prefix = 'Y' + str(current_year_start.year)
                                from_date = current_year_start
                                to_date = current_year_end
                                date_end = rec.date_end if rec.date_end and current_year_start <= rec.date_end <= current_year_end else to_date
                                if invoice_date != from_date or date_end != to_date:
                                    from_date = invoice_date
                                    to_date = date_end
                                    remaining_days = (to_date - from_date).days
                                    total_days = (current_year_end - current_year_start).days
                                    amount = line.fixed_amount * remaining_days / total_days
                                else:
                                    amount = line.fixed_amount
                            management_fee = self.env.ref('wonoproperty_pms.management_fee')
                            if line.expense_id.id != management_fee.id:
                                invoice_line_name = line.expense_id.name
                            else:
                                if frequency == 'quarterly':
                                    monthly_amount = amount / 3
                                elif frequency == 'monthly':
                                    monthly_amount = amount
                                else:
                                    monthly_amount = amount / 12
                                invoice_line_name = prefix + ' Management Fee (RM' + "{:.2f}".format(
                                    monthly_amount) + '/month)'
                            if invoice_date <= to_date:
                                account_move = self.env['account.move']
                                account_move.create({
                                    'move_type': 'out_invoice',
                                    'partner_id': rec.tenant_id,
                                    'invoice_date': invoice_date,
                                    'property_unit_id': rec.id,
                                    'date_from': from_date,
                                    'invoice_payment_term_id': rec.tenant_id.property_payment_term_id.id,
                                    'date_to': to_date,
                                    'property_expense_id': line.expense_id.id,
                                    'invoice_line_ids': [
                                        Command.create({
                                            'product_id': line.expense_id.product_id.id,
                                            'name': invoice_line_name,
                                            'price_unit': amount,
                                            'quantity': 1,
                                        })
                                    ]
                                })
                    else:
                        frequency = line.expense_frequency
                        last_invoice = sorted(
                            self.invoice_ids.filtered(lambda x: x.property_expense_id.id == line.expense_id.id),
                            key=lambda x: x.date_to, reverse=True)
                        date_today = datetime.now().date()
                        date_start = rec.date_start if not last_invoice else last_invoice[0].date_to + relativedelta(
                            days=1)
                        invoice_date = rec.date_start if not last_invoice else last_invoice[0].date_to + relativedelta(
                            days=1)
                        if frequency == 'quarterly':
                            current_quarter = math.ceil(invoice_date.month / 3.)
                            current_quarter_start_month = (current_quarter * 3) - 2
                            current_quarter_end_month = current_quarter * 3
                            current_quarter_start_date = datetime(invoice_date.year, current_quarter_start_month, 1
                                                                  ).date()
                            current_quarter_end_date = datetime(invoice_date.year, current_quarter_end_month,
                                                                calendar.monthrange(invoice_date.year,
                                                                                    current_quarter_end_month)[
                                                                    1]).date()
                            invoice_date = current_quarter_end_date + relativedelta(days=1)
                            from_date = current_quarter_start_date
                            to_date = current_quarter_end_date
                        elif frequency == 'monthly':
                            current_month = invoice_date.month
                            current_month_start_date = datetime(invoice_date.year, current_month, 1).date()
                            current_month_end_date = datetime(invoice_date.year, current_month, calendar.monthrange(
                                invoice_date.year, current_month)[1]).date()
                            from_date = current_month_start_date
                            to_date = current_month_end_date
                            invoice_date = current_month_end_date + relativedelta(days=1)
                        else:
                            current_year_start = datetime(invoice_date.year, 1, 1).date()
                            current_year_end = datetime(invoice_date.year, 12, 31).date()
                            from_date = current_year_start
                            to_date = current_year_end
                            invoice_date = current_year_end + relativedelta(days=1)
                        date_end = rec.date_end if rec.date_end else to_date
                        if date_start != from_date or date_end != to_date:
                            from_date = date_start
                            to_date = date_end
                        if date_today >= invoice_date:
                            if invoice_date <= to_date + relativedelta(days=1):
                                odometer = sorted(rec.water_odometer_reading_ids.filtered(
                                    lambda x: from_date <= x.date <= to_date and not x.first_reading),
                                    key=lambda x: x.date, reverse=True)
                                if odometer:
                                    prev_odometer = sorted(
                                        rec.water_odometer_reading_ids.filtered(lambda x: from_date >= x.date),
                                        key=lambda x: x.date, reverse=True)
                                    prev_odometer_reading = 0 if not prev_odometer else prev_odometer[0].reading
                                    total_amount = (odometer[
                                                        0].reading - prev_odometer_reading) * line.variable_amount
                                    minimum_amount = line.minimum_amount
                                    amount = total_amount if total_amount > minimum_amount else minimum_amount
                                    invoice_date = odometer[0].date + relativedelta(days=1)
                                    account_move = self.env['account.move']
                                    account_move.create({
                                        'move_type': 'out_invoice',
                                        'partner_id': rec.tenant_id,
                                        'invoice_date': invoice_date,
                                        'property_unit_id': rec.id,
                                        'date_from': from_date,
                                        'date_to': to_date,
                                        'invoice_payment_term_id': rec.tenant_id.property_payment_term_id.id,
                                        'property_expense_id': line.expense_id.id,
                                        'invoice_line_ids': [
                                            Command.create({
                                                'name': line.expense_id.name + ' (Minimum charge RM10.00 / Quarter) (Reading for quarter is ' + "{:.2f}".format(odometer[0].reading) + ' - ' + "{:.2f}".format(prev_odometer_reading) + ' = ' +
                                                        "{:.2f}".format(odometer[0].reading - prev_odometer_reading) + 'KL)',
                                                'product_id': line.expense_id.product_id.id,
                                                'price_unit': amount,
                                                'quantity': 1,
                                            })
                                        ]
                                    })

    @api.depends('invoice_ids')
    def _get_invoiced(self):
        for rec in self:
            rec['invoice_count'] = len(rec.invoice_ids.filtered(lambda x: x.partner_id.id == rec.tenant_id.id))

    def action_view_invoice(self):
        invoices = self.mapped('invoice_ids').filtered(lambda x: x.partner_id.id == self.tenant_id.id)
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_move_type': 'out_invoice',
            'default_partner_id': self.tenant_id.id,
            'default_property_unit_id': self.id,
            'default_invoice_payment_term_id': self.tenant_id.property_payment_term_id.id,
        }
        action['context'] = context
        return action

    @api.model
    def get_range_monthly(self, date_from, date_to):
        month_range = []
        if date_from.month == date_to.month and date_to.year == date_from.year:
            month_range.append((date_from, date_to))
        else:
            date_start = date_from
            date_end = date_start + relativedelta(months=1, day=1, days=-1)
            month_range.append((date_start, date_end))
            while date_end < date_to:
                date_start = date_end + relativedelta(days=1)
                date_end = date_start + relativedelta(months=1, day=1, days=-1)
                if date_end > date_to:
                    date_end = date_to
                month_range.append((date_start, date_end))
        return month_range

    @api.model
    def get_range_quarterly(self, date_from, date_to):
        month_range = []
        if date_from.month == date_to.month and date_to.year == date_from.year:
            month_range.append((date_from, date_to))
        else:
            date_start = date_from
            date_end = date_start + relativedelta(months=1, day=1, days=-1)
            month_range.append((date_start, date_end))
            while date_end < date_to:
                date_start = date_end + relativedelta(days=1)
                date_end = date_start + relativedelta(months=1, day=1, days=-1)
                if date_end > date_to:
                    date_end = date_to
                month_range.append((date_start, date_end))
        return month_range

    def send_report_email(self):
        for rec in self:
            email_template_id = self.env.ref('wonoproperty_pms.email_template_account_statement').id
            rec.with_context(force_send=True).message_post_with_template(
                email_template_id, email_layout_xmlid='mail.mail_notification_light')

    def print_statement(self):
        for rec in self:
            return rec.env.ref('wonoproperty_pms.report_account_statement').report_action(self)


class UnitExpenseLine(models.Model):
    _name = 'unit.expense.line'
    _description = 'Unit Expense Lines'

    property_unit_id = fields.Many2one('property.unit', string='Property')
    expense_id = fields.Many2one('expense.type', string='Expense Type', required=True)
    expense_frequency = fields.Selection([('monthly', 'Monthly'),
                                          ('quarterly', 'Quarterly'),
                                          ('yearly', 'Yearly')], string='Frequency', required=True)
    minimum_amount = fields.Float(string='Minimum Amount')
    fixed_amount = fields.Float(string='Fixed Amount')
    variable_amount = fields.Float(string='Variable Amount')


class PropertyUnitAccountStatement(models.AbstractModel):
    _name = 'report.wonoproperty_pms.report_account_statement'
    _description = 'Property Unit Account Statement'

    def _get_report_values(self, docids, data=None):
        docs = self.env['property.unit'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'property_unit',
            'docs': docs,
            'time': time,
            'get_current_company': self._get_current_company,
            'get_invoice_lines': self._get_invoice_lines,
            'get_aging_line': self._get_aging_line
        }

    def _get_current_company(self):
        company = self.env.company[0]
        return company

    def _get_invoice_lines(self, rec):
        lines = []
        AccountMove = self.env['account.move']
        for invoice in rec.invoice_ids.filtered(lambda x: x.state == 'posted'):
            lines.append(invoice.id)
            invoice_payments = json.loads(invoice.invoice_payments_widget)
            journal_entries = AccountMove.search([('payment_id', '!=', False)])
            if invoice_payments:
                for payment in invoice_payments['content']:
                    display_name = payment['ref']
                    journal_entry = journal_entries.filtered(lambda x: x.display_name == display_name)
                    lines.append(journal_entry.id)
        moves = AccountMove.search([('id', 'in', lines)], order='date asc')
        return moves

    def _get_aging_line(self, rec):
        date_today = datetime.now().date()
        total = 0.0
        ninty = 0.0
        sixty = 0.0
        thirty = 0.0
        twenty_eight = 0.0
        fourteen = 0.0
        current = 0.0
        currency = self.env.company.currency_id
        for invoice in rec.invoice_ids.filtered(lambda x: x.state == 'posted' and x.amount_residual > 0.0):
            date_diff = (date_today - invoice.invoice_date_due).days
            total += invoice.amount_residual
            if date_diff >= 90:
                ninty += invoice.amount_residual
            elif date_diff >= 60:
                sixty += invoice.amount_residual
            elif date_diff >= 30:
                thirty += invoice.amount_residual
            elif date_diff >= 28:
                twenty_eight += invoice.amount_residual
            elif date_diff >= 14:
                fourteen += invoice.amount_residual
            else:
                current += invoice.amount_residual
        return [currency, current, fourteen, twenty_eight, thirty, sixty, ninty, total]

