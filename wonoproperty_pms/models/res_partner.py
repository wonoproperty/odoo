# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, Command


class ResPartner(models.Model):
    _inherit = 'res.partner'

    property_unit_ids = fields.One2many('property.unit', 'tenant_id', string='Rooms')
    property_unit_count = fields.Integer(string='Property Unit Count', compute='_get_properties')
    contact_type = fields.Selection([('owner', 'Owner'),
                                     ('tenant', 'Tenant')], string='Contact Type')
    date_start = fields.Date(string='Date Start')
    date_end = fields.Date(string='Date End')
    tenancy_agreement = fields.Char(string='Tenancy Agreement')

    @api.depends('property_unit_ids')
    def _get_properties(self):
        for rec in self:
            rec['property_unit_count'] = len(rec.property_unit_ids)

    def action_view_property_unit(self):
        room_ids = self.mapped('property_unit_ids')
        action = self.env["ir.actions.actions"]._for_xml_id("wonoproperty_pms.property_unit_view_action")
        if len(room_ids) > 1:
            action['domain'] = [('id', 'in', room_ids.ids)]
        elif len(room_ids) == 1:
            form_view = [(self.env.ref('wonoproperty_pms.property_unit_view_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = room_ids.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
