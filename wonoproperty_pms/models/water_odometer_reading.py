# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError


class WaterOdometerReading(models.Model):
    _name = 'water.odometer.reading'
    _description = 'Water Odometer Reading'
    _order = 'date'

    property_unit_id = fields.Many2one('property.unit', string='Property')
    tenant_id = fields.Many2one('res.partner', string='Tenant')
    date = fields.Date(string='Date', required=True)
    reading = fields.Float(string='Reading')
    invoiced = fields.Boolean(string='Invoiced')
    first_reading = fields.Boolean(string='First Reading')

    @api.model
    def create(self, vals_list):
        res = super(WaterOdometerReading, self).create(vals_list)
        meter_readings = res.search([('property_unit_id', '=', res.property_unit_id.id),
                                     ('id', '!=', res.id)], order="date desc")
        if not res.tenant_id:
            res.tenant_id = res.property_unit_id.tenant_id
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
        if not self.tenant_id:
            self.tenant_id = self.property_unit_id.tenant_id
        if len(meter_readings) > 0:
            prev_reading = meter_readings[0].reading
            if prev_reading:
                if self.reading < prev_reading:
                    raise UserError(_('Reading must be higher than previous reading of %s', str(prev_reading)))
        return res


class WaterOdometerReadingHistory(models.Model):
    _name = 'water.odometer.reading.history'
    _description = 'Water Odometer Reading'
    _order = 'date'

    property_unit_id = fields.Many2one('property.unit', string='Property Unit')
    tenant_id = fields.Many2one('res.partner', string='Tenant')
    date = fields.Date(string='Date', required=True)
    reading = fields.Float(string='Reading')
    invoiced = fields.Boolean(string='Invoiced')
    first_reading = fields.Boolean(string='First Reading')

    @api.model
    def create(self, vals_list):
        res = super(WaterOdometerReadingHistory, self).create(vals_list)
        meter_readings = res.search([('property_unit_id', '=', res.property_unit_id.id),
                                     ('id', '!=', res.id)], order="date desc")
        if len(meter_readings) > 0:
            prev_reading = meter_readings[0].reading
            if prev_reading:
                if res.reading < prev_reading:
                    raise UserError(_('Reading must be higher than previous reading of %s', str(prev_reading)))
        return res

    def write(self, vals):
        res = super(WaterOdometerReadingHistory, self).write(vals)
        meter_readings = self.search([('property_unit_id', '=', self.property_unit_id.id),
                                      ('id', '!=', self.id)], order="date desc")
        if len(meter_readings) > 0:
            prev_reading = meter_readings[0].reading
            if prev_reading:
                if self.reading < prev_reading:
                    raise UserError(_('Reading must be higher than previous reading of %s', str(prev_reading)))
        return res
