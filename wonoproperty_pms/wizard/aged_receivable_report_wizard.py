# -*- coding: utf-8 -*-
import base64
import io
from odoo import api, fields, models, _
import xlsxwriter
from datetime import datetime


class AgedReceivableReportWizard(models.Model):
    _name = 'aged.receivable.report.wizard'
    _description = 'Aged Receivable Report Wizard'

    date = fields.Date(string='As At Date', required=True, default=datetime.now().date())

    def print_report_xls(self):
        # take attach_id from generate_excel_report and open new wizard
        attach_id = self.env['aged.receivable.report'].generate_excel_report(self.date)
        return {
            'context': self.env.context,
            'view_mode': 'form',
            'res_model': 'xlsx.print.wizard',
            'res_id': attach_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }

