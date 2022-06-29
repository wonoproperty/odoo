# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, Command


class ActualTenantWizard(models.TransientModel):
    _name = 'actual.tenant.wizard'
    _description = 'Actual Owner Wizard'

    current_tenant_id = fields.Many2one('res.partner', string='Current Tenant')
    current_date_start = fields.Date(string='Date Start')
    current_date_end = fields.Date(string='Date End')
    new_tenant_id = fields.Many2one('res.partner', string='New Tenant', required=True)
    new_date_start = fields.Date(string='Start of New Tenancy', required=True)
    property_unit_id = fields.Many2one('property.unit', string='Property Unit')

    def update_tenant(self):
        property_unit = self.property_unit_id
        active_line = property_unit.actual_tenant_ids.filtered(lambda x: x.current_active)
        active_line.tenant_id.date_end = self.current_date_end
        active_line.current_active = False
        self.new_tenant_id.date_start = self.new_date_start
        property_unit.write({
            'actual_tenant_ids': [
                Command.create({
                    'property_unit_id': property_unit.id,
                    'tenant_id': self.new_tenant_id.id,
                    'current_active': True
                })],
        })
        return {'type': 'ir.actions.act_window_close'}
