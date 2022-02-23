# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar
import math


class PropertyUnit(models.Model):
    _name = 'property.unit'
    _description = 'Property Unit'
    _rec_name = 'complete_name'

    name = fields.Char(string='Name', required=True)
    property_id = fields.Many2one('property.property', string='Property')
    date_start = fields.Date(string='Date Start')
    date_end = fields.Date(string='Date End')
    tenant_id = fields.Many2one('res.partner', string='Current Tenant')
    tenant_ids = fields.One2many('tenant.history', 'property_unit_id', string='Tenant History')
    invoice_ids = fields.One2many('account.move', 'property_unit_id', string='Invoices')
    expense_ids = fields.One2many('unit.expense.line', 'property_unit_id', string='Expense Lines', copy=True)
    water_odometer_reading_ids = fields.One2many('water.odometer.reading', 'property_unit_id', string='Water Odometer Readings')
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
                            if invoice_date <= to_date:
                                account_move = self.env['account.move']
                                account_move.create({
                                    'move_type': 'out_invoice',
                                    'partner_id': rec.tenant_id,
                                    'invoice_date': invoice_date,
                                    'property_unit_id': rec.id,
                                    'date_from': from_date,
                                    'date_to': to_date,
                                    'property_expense_id': line.expense_id.id,
                                    'invoice_line_ids': [
                                        Command.create({
                                            'product_id': line.expense_id.product_id.id,
                                            'name': line.expense_id.name,
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
                                    amount = total_amount
                                    invoice_date = odometer[0].date + relativedelta(days=1)
                                    account_move = self.env['account.move']
                                    account_move.create({
                                        'move_type': 'out_invoice',
                                        'partner_id': rec.tenant_id,
                                        'invoice_date': invoice_date,
                                        'property_unit_id': rec.id,
                                        'date_from': from_date,
                                        'date_to': to_date,
                                        'property_expense_id': line.expense_id.id,
                                        'invoice_line_ids': [
                                            Command.create({
                                                'name': line.expense_id.name + ' (Reading for month is ' + "{:.2f}".format(odometer[0].reading) + ' - ' + "{:.2f}".format(prev_odometer_reading) + ' = ' +
                                                        "{:.2f}".format(odometer[0].reading - prev_odometer_reading) + ')',
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


class UnitExpenseLine(models.Model):
    _name = 'unit.expense.line'
    _description = 'Unit Expense Lines'

    property_unit_id = fields.Many2one('property.unit', string='Property')
    expense_id = fields.Many2one('expense.type', string='Expense Type', required=True)
    expense_frequency = fields.Selection([('monthly', 'Monthly'),
                                          ('quarterly', 'Quarterly'),
                                          ('yearly', 'Yearly')], string='Frequency', required=True)
    fixed_amount = fields.Float(string='Fixed Amount')
    variable_amount = fields.Float(string='Variable Amount')
