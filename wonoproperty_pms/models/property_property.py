# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PropertyProperty(models.Model):
    _name = 'property.property'
    _description = 'Property'

    name = fields.Char(string='Name', required=True)
    owner_id = fields.Many2one('res.partner', string='Property Owner', required=True)
    unit_ids = fields.One2many('property.unit', 'property_id', string='Units')

    def create_invoices(self):
        for unit in self.unit_ids:
            unit.action_create_invoice()
