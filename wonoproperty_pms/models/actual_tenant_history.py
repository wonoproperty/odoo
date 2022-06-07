# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, Command


class ActualTenantHistory(models.Model):
    _name = 'actual.tenant.history'
    _description = 'Actual Tenant History'
    _order = 'date_start, id'

    property_unit_id = fields.Many2one('property.unit', string='Property Unit')
    tenant_id = fields.Many2one('res.partner', string='Tenant',)
    date_start = fields.Date(related='tenant_id.date_start', string='Date Start')
    date_end = fields.Date(related='tenant_id.date_end', string='Date End')
    current_active = fields.Boolean(string='Current Active')
