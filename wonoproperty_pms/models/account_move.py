# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountMoveProperty(models.Model):
    _inherit = 'account.move'

    property_unit_id = fields.Many2one('property.unit', string='Property')
