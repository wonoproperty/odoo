# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, Command


class PropertyTenantWizard(models.TransientModel):
    _name = 'property.tenant.wizard'
    _description = 'Property Tenant Wizard'

    current_tenant_id = fields.Many2one('res.partner', string='Current Tenant', required=True)
    current_date_start = fields.Date(string='Date Start')
    current_date_end = fields.Date(string='Date End')
    new_tenant_id = fields.Many2one('res.partner', string='New Tenant', required=True)
    new_date_start = fields.Date(string='Start of New Tenancy', required=True)
    property_unit_id = fields.Many2one('property.unit', string='Property Unit')

    def update_tenant(self):
        property_unit = self.property_unit_id
        invoices = property_unit.invoice_ids.filtered(lambda x: x.partner_id.id == self.current_tenant_id.id and
                                                                x.property_unit_id.id == property_unit.id)
        water_readings = property_unit.water_odometer_reading_ids.filtered(lambda x: x.tenant_id.id == self.current_tenant_id.id and
                                                                                     x.property_unit_id.id == property_unit.id)
        reading_vals = []
        for reading in water_readings:
            reading_vals.append(Command.create({
                'tenant_id': self.current_tenant_id.id,
                'property_unit_id': property_unit.id,
                'reading': reading.reading,
                'first_reading': reading.first_reading,
                'date': reading.date,
            }))
        property_unit.write({
            'tenant_ids': [
                Command.create({
                    'property_unit_id': property_unit.id,
                    'tenant_id': self.current_tenant_id.id,
                    'date_start': self.current_date_start,
                    'date_end': self.current_date_end,
                    'water_odometer_readings_ids': reading_vals,
                    'invoice_ids': invoices
                })],
            'tenant_id': self.new_tenant_id.id,
            'date_start': self.new_date_start,
        })
        property_unit.water_odometer_reading_ids.unlink()
        return {'type': 'ir.actions.act_window_close'}
