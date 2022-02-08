# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PropertyUnit(models.Model):
    _name = 'property.unit'
    _description = 'Property Unit'
    _rec_name = 'complete_name'

    name = fields.Char(string='Name', required=True)
    property_id = fields.Many2one('property.property', string='Property')
    date_start = fields.Date(string='Date Start')
    tenant_id = fields.Many2one('res.partner', string='Current Tenant')
    tenant_ids = fields.One2many('tenant.history', 'property_unit_id', string='Tenant History')
    invoice_ids = fields.One2many('account.move', 'property_unit_id', string='Invoices')
    expense_ids = fields.One2many('unit.expense.line', 'property_unit_id', string='Expense Lines')
    water_odometer_reading_ids = fields.One2many('water.odometer.reading', 'property_unit_id', string='Expense Lines')
    complete_name = fields.Char('Complete Name', compute='_compute_complete_name', recursive=True, store=True)

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
            'default_current_date_start': self.date_start
        })
        wizard_action = {
            'type': 'ir.actions.act_window',
            'res_model': 'property.tenant.wizard',
            'name': _('Accrual Sale Orders'),
            'view_mode': 'form',
            'context': ctx,
            'target': 'new',
        }
        return wizard_action


class TenantHistory(models.Model):
    _name = 'tenant.history'
    _description = 'Tenant History'

    property_unit_id = fields.Many2one('property.unit', string='Property')
    tenant_id = fields.Many2one('res.partner', string='Current Tenant', required=True)
    date_start = fields.Date(string='Date Start', required=True)
    date_end = fields.Date(string='Date End')


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


class WaterOdometerReading(models.Model):
    _name = 'water.odometer.reading'
    _description = 'Water Odometer Reading'

    property_unit_id = fields.Many2one('property.unit', string='Property')
    date = fields.Date(string='Date', required=True)
    reading = fields.Float(string='Reading')

    @api.model
    def create(self, vals_list):
        res = super(WaterOdometerReading, self).create(vals_list)
        meter_readings = res.search([('property_unit_id', '=', res.property_unit_id.id),
                                     ('id', '!=', res.id)], order="date desc")
        if len(meter_readings) > 0:
            prev_reading = meter_readings[0].reading
            if prev_reading:
                if res.reading < prev_reading:
                    raise UserError(_('Reading must be higher than previous reading of %s', str(prev_reading)))
        return res

    def write(self, vals):
        res = super(WaterOdometerReading, self).write(vals)
        meter_readings = self.search([('property_unit_id', '=', self.property_unit_id.id),
                                      ('id', '!=', self.id)], order="date desc")
        if len(meter_readings) > 0:
            prev_reading = meter_readings[0].reading
            if prev_reading:
                if self.reading < prev_reading:
                    raise UserError(_('Reading must be higher than previous reading of %s', str(prev_reading)))
        return res
