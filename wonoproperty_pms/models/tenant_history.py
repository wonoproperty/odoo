# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar
import math


class TenantHistory(models.Model):
    _name = 'tenant.history'
    _description = 'Tenant History'

    property_unit_id = fields.Many2one('property.unit', string='Property Unit')
    tenant_id = fields.Many2one('res.partner', string='Current Tenant', required=True)
    date_start = fields.Date(string='Date Start', required=True)
    date_end = fields.Date(string='Date End')
    invoice_ids = fields.Many2many('account.move', string='Invoices')
    invoice_count = fields.Integer(string='Invoice Count', compute='_get_invoiced')
    water_odometer_readings_ids = fields.Many2many('water.odometer.reading.history', string='Water Odometer Readings')
    water_odometer_readings_count = fields.Integer(string='Water Odometer Readings Count', compute='_get_readings')
    currency_id = fields.Many2one('res.currency', string='Currency', required=True)
    loan_amount = fields.Monetary(string='Loan Amount')
    end_financier = fields.Many2one('financier.financier', string='End Financier',
                                    domain="[('financier_type', '=', 'financier')]")
    s_p_solicitor = fields.Many2one('financier.financier', string='S & P Solicitor',
                                    domain="[('financier_type', '=', 'solicitor')]")
    loan_solicitor = fields.Many2one('financier.financier', string='Loan Solicitor',
                                     domain="[('financier_type', '=', 'solicitor')]")
    date_purchase = fields.Date(string='Date of Purchase')
    s_p_amount = fields.Monetary(string='S & P Amount')

    @api.depends('invoice_ids')
    def _get_invoiced(self):
        for rec in self:
            rec['invoice_count'] = len(rec.invoice_ids.filtered(lambda x: x.partner_id.id == rec.tenant_id.id))

    @api.depends('water_odometer_readings_ids')
    def _get_readings(self):
        for rec in self:
            rec['water_odometer_readings_count'] = len(rec.water_odometer_readings_ids)

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

    def action_view_water_readings(self):
        water_odometer_readings_ids = self.mapped('water_odometer_readings_ids')
        action = self.env["ir.actions.actions"]._for_xml_id("wonoproperty_pms.water_odometer_reading_view_action")
        if len(water_odometer_readings_ids) > 1:
            action['domain'] = [('id', 'in', water_odometer_readings_ids.ids)]
        elif len(water_odometer_readings_ids) == 1:
            form_view = [(self.env.ref('wonoproperty_pms.water_odometer_reading_view_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = water_odometer_readings_ids.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action