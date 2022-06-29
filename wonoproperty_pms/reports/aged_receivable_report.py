# -*- coding: utf-8 -*-
import base64
import io
from odoo import api, fields, models, _
import xlsxwriter
import json
from datetime import datetime


class AgedReceivableReport(models.Model):
    _name = 'aged.receivable.report'
    _description = 'Aged Receivable Report'

    def generate_excel_report(self, date):
        # create worksheet formatting

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        format_header = workbook.add_format({'font_size': 18, 'bold': True, 'border': 1, 'align': 'Center'})
        table_header = workbook.add_format({'font_size': 12, 'bold': True})
        table_header_bottom = workbook.add_format({'font_size': 12, 'bold': True, 'bottom': 1})
        table_header_top = workbook.add_format({'font_size': 12, 'bold': True, 'top': 1})
        table_body = workbook.add_format({'font_size': 12})
        table_body1 = workbook.add_format({'font_size': 12, 'align': 'right', 'bold': True})
        table_date = workbook.add_format({'font_size': 12, 'num_format': 'dd-mm-yyyy'})
        table_acc = workbook.add_format({'font_size': 12, 'num_format': '#,##0.00_);[Red](#,##0.00)'})
        table_acc_total = workbook.add_format({'font_size': 12, 'num_format': '#,##0.00_);[Red](#,##0.00)',
                                               'bold': True, 'top': 1})

        data = self.env['property.unit'].search([]).mapped('invoice_ids').filtered(lambda x:
                                                                                   x.invoice_date_due <= date and
                                                                                   x.state == 'posted')
        property_units = data.mapped('property_unit_id')
        collapsed = workbook.add_worksheet('Collapsed')
        expanded = workbook.add_worksheet('Expanded')
        expanded.set_column('A:A', 100)
        expanded.set_column('B:B', 15)
        expanded.set_column('C:H', 18)
        collapsed.set_column('A:A', 100)
        collapsed.set_column('B:B', 15)
        collapsed.set_column('C:H', 18)
        expanded_row = 0
        collapsed_row = 0
        for unit in property_units:
            expanded.write(expanded_row, 0, unit.name, table_header)

            collapsed.write(collapsed_row, 0, unit.name, table_header)

            expanded_row += 1

            collapsed_row += 1

            date_in_text = date.strftime('%d/%m/%Y')

            expanded.write(expanded_row, 0, _('Aged Receivable'), table_header_bottom)
            expanded.write(expanded_row, 1, _('Due Date'), table_header_bottom)
            expanded.write(expanded_row, 2, _('As of: ' + date_in_text), table_header_bottom)
            expanded.write(expanded_row, 3, _('14 Days'), table_header_bottom)
            expanded.write(expanded_row, 4, _('30 Days'), table_header_bottom)
            expanded.write(expanded_row, 5, _('60 Days'), table_header_bottom)
            expanded.write(expanded_row, 6, _('90 Days and Older'), table_header_bottom)
            expanded.write(expanded_row, 7, _('Total'), table_header_bottom)

            collapsed.write(collapsed_row, 0, _('Aged Receivable'), table_header_bottom)
            collapsed.write(collapsed_row, 1, _('Due Date'), table_header_bottom)
            collapsed.write(collapsed_row, 2, _('As of: ' + date_in_text), table_header_bottom)
            collapsed.write(collapsed_row, 3, _('14 Days'), table_header_bottom)
            collapsed.write(collapsed_row, 4, _('30 Days'), table_header_bottom)
            collapsed.write(collapsed_row, 5, _('60 Days'), table_header_bottom)
            collapsed.write(collapsed_row, 6, _('90 Days and Older'), table_header_bottom)
            collapsed.write(collapsed_row, 7, _('Total'), table_header_bottom)

            expanded_row += 1
            collapsed_row += 1

            lines = []
            AccountMove = self.env['account.move']
            final_total = 0.0
            total_ninty = 0.0
            total_sixty = 0.0
            total_thirty = 0.0
            total_fourteen = 0.0
            total_current = 0.0
            for invoice in unit.invoice_ids.filtered(lambda x: x.partner_id == unit.tenant_id and x.date <= date
                                                     and x.state == 'posted'):
                lines.append(invoice.id)
                invoice_payments = json.loads(invoice.invoice_payments_widget)
                journal_entries = AccountMove.search([('payment_id', '!=', False)])
                if invoice_payments:
                    for payment in invoice_payments['content']:
                        display_name = payment['ref']
                        journal_entry = journal_entries.filtered(lambda x: x.display_name == display_name)
                        lines.append(journal_entry.id)
                        lines.append(invoice.id)
                        invoice_payments = json.loads(invoice.invoice_payments_widget)
                        journal_entries = AccountMove.search([('payment_id', '!=', False)])
                        if invoice_payments:
                            for payment in invoice_payments['content']:
                                display_name = payment['ref']
                                journal_entry = journal_entries.filtered(lambda x: x.display_name == display_name)
                                lines.append(journal_entry.id)
            moves = AccountMove.search([('id', 'in', lines)])
            total = 0.0
            ninty = 0.0
            sixty = 0.0
            thirty = 0.0
            fourteen = 0.0
            current = 0.0
            for invoice in moves:
                date_diff = (date - invoice.date).days
                if invoice.move_type == 'out_invoice':
                    sign = 1
                elif invoice.payment_id:
                    sign = -1
                else:
                    sign = -1
                total += sign * invoice.amount_total
                if date_diff >= 90:
                    ninty += sign * invoice.amount_total
                elif date_diff >= 60:
                    sixty += sign * invoice.amount_total
                elif date_diff >= 30:
                    thirty += sign * invoice.amount_total
                elif date_diff >= 14:
                    fourteen += sign * invoice.amount_total
                else:
                    current += sign * invoice.amount_total
            expanded.write(expanded_row, 0, unit.tenant_id.name, table_header)
            expanded.write(expanded_row, 1, '', table_acc)
            expanded.write(expanded_row, 2, current, table_acc)
            expanded.write(expanded_row, 3, fourteen, table_acc)
            expanded.write(expanded_row, 4, thirty, table_acc)
            expanded.write(expanded_row, 5, sixty, table_acc)
            expanded.write(expanded_row, 6, ninty, table_acc)
            expanded.write(expanded_row, 7, total, table_acc)

            collapsed.write(collapsed_row, 0, unit.tenant_id.name, table_header)
            collapsed.write(collapsed_row, 1, '', table_acc)
            collapsed.write(collapsed_row, 2, current, table_acc)
            collapsed.write(collapsed_row, 3, fourteen, table_acc)
            collapsed.write(collapsed_row, 4, thirty, table_acc)
            collapsed.write(collapsed_row, 5, sixty, table_acc)
            collapsed.write(collapsed_row, 6, ninty, table_acc)
            collapsed.write(collapsed_row, 7, total, table_acc)

            expanded_row += 1
            collapsed_row += 1

            for invoice in moves:
                if invoice.move_type == 'out_invoice':
                    sign = 1
                elif invoice.payment_id:
                    sign = -1
                else:
                    sign = -1
                date_diff = (date - invoice.date).days
                expanded.write(expanded_row, 0, invoice.name, table_body)
                expanded.write(expanded_row, 1, invoice.invoice_date_due if invoice.invoice_date_due else '', table_date)
                expanded.write(expanded_row, 2, sign * invoice.amount_total if 0 <= date_diff <= 13 else 0.0, table_acc)
                expanded.write(expanded_row, 3, sign * invoice.amount_total if 14 <= date_diff <= 29 else 0.0, table_acc)
                expanded.write(expanded_row, 4, sign * invoice.amount_total if 30 <= date_diff <= 59 else 0.0, table_acc)
                expanded.write(expanded_row, 5, sign * invoice.amount_total if 60 <= date_diff <= 89 else 0.0, table_acc)
                expanded.write(expanded_row, 6, sign * invoice.amount_total if 90 <= date_diff else 0.0, table_acc)
                expanded.write(expanded_row, 7, sign * invoice.amount_total, table_acc)
                expanded_row += 1
            final_total += total
            total_ninty += ninty
            total_sixty += sixty
            total_thirty += thirty
            total_fourteen += fourteen
            total_current += current
            for owner in unit.tenant_ids:
                expanded_row += 1

                lines = []
                AccountMove = self.env['account.move']
                for invoice in owner.invoice_ids.filtered(lambda x: x.partner_id == owner.tenant_id and x.date <= date
                                                                    and x.state == 'posted'):
                    lines.append(invoice.id)
                    invoice_payments = json.loads(invoice.invoice_payments_widget)
                    journal_entries = AccountMove.search([('payment_id', '!=', False)])
                    if invoice_payments:
                        for payment in invoice_payments['content']:
                            display_name = payment['ref']
                            journal_entry = journal_entries.filtered(lambda x: x.display_name == display_name)
                            lines.append(journal_entry.id)
                            lines.append(invoice.id)
                            invoice_payments = json.loads(invoice.invoice_payments_widget)
                            journal_entries = AccountMove.search([('payment_id', '!=', False)])
                            if invoice_payments:
                                for payment in invoice_payments['content']:
                                    display_name = payment['ref']
                                    journal_entry = journal_entries.filtered(lambda x: x.display_name == display_name)
                                    lines.append(journal_entry.id)
                moves = AccountMove.search([('id', 'in', lines)])
                total = 0.0
                ninty = 0.0
                sixty = 0.0
                thirty = 0.0
                fourteen = 0.0
                current = 0.0
                for invoice in moves:
                    date_diff = (date - invoice.date).days
                    if invoice.move_type == 'out_invoice':
                        sign = 1
                    elif invoice.payment_id:
                        sign = -1
                    else:
                        sign = -1
                    total += sign * invoice.amount_total
                    if date_diff >= 90:
                        ninty += sign * invoice.amount_total
                    elif date_diff >= 60:
                        sixty += sign * invoice.amount_total
                    elif date_diff >= 30:
                        thirty += sign * invoice.amount_total
                    elif date_diff >= 14:
                        fourteen += sign * invoice.amount_total
                    else:
                        current += sign * invoice.amount_total

                expanded.write(expanded_row, 0, owner.tenant_id.name, table_header)
                expanded.write(expanded_row, 1, '', table_acc)
                expanded.write(expanded_row, 2, current, table_acc)
                expanded.write(expanded_row, 3, fourteen, table_acc)
                expanded.write(expanded_row, 4, thirty, table_acc)
                expanded.write(expanded_row, 5, sixty, table_acc)
                expanded.write(expanded_row, 6, ninty, table_acc)
                expanded.write(expanded_row, 7, total, table_acc)

                collapsed.write(collapsed_row, 0, owner.tenant_id.name, table_header)
                collapsed.write(collapsed_row, 1, '', table_acc)
                collapsed.write(collapsed_row, 2, current, table_acc)
                collapsed.write(collapsed_row, 3, fourteen, table_acc)
                collapsed.write(collapsed_row, 4, thirty, table_acc)
                collapsed.write(collapsed_row, 5, sixty, table_acc)
                collapsed.write(collapsed_row, 6, ninty, table_acc)
                collapsed.write(collapsed_row, 7, total, table_acc)

                expanded_row += 1
                collapsed_row += 1

                for invoice in moves:
                    if invoice.move_type == 'out_invoice':
                        sign = 1
                    elif invoice.payment_id:
                        sign = -1
                    else:
                        sign = -1
                    date_diff = (date - invoice.date).days
                    expanded.write(expanded_row, 0, invoice.name, table_body)
                    expanded.write(expanded_row, 1, invoice.invoice_date_due if invoice.invoice_date_due else '', table_date)
                    expanded.write(expanded_row, 2, sign * invoice.amount_total if 0 <= date_diff <= 13 else 0.0, table_acc)
                    expanded.write(expanded_row, 3, sign * invoice.amount_total if 14 <= date_diff <= 29 else 0.0, table_acc)
                    expanded.write(expanded_row, 4, sign * invoice.amount_total if 30 <= date_diff <= 59 else 0.0, table_acc)
                    expanded.write(expanded_row, 5, sign * invoice.amount_total if 60 <= date_diff <= 89 else 0.0, table_acc)
                    expanded.write(expanded_row, 6, sign * invoice.amount_total if 90 <= date_diff else 0.0, table_acc)
                    expanded.write(expanded_row, 7, sign * invoice.amount_total, table_acc)
                    expanded_row += 1

                final_total += total
                total_ninty += ninty
                total_sixty += sixty
                total_thirty += thirty
                total_fourteen += fourteen
                total_current += current

            expanded_row += 1

            expanded.write(expanded_row, 0, 'Total', table_header_top)
            expanded.write(expanded_row, 1, '', table_acc_total)
            expanded.write(expanded_row, 2, total_current, table_acc_total)
            expanded.write(expanded_row, 3, total_fourteen, table_acc_total)
            expanded.write(expanded_row, 4, total_thirty, table_acc_total)
            expanded.write(expanded_row, 5, total_sixty, table_acc_total)
            expanded.write(expanded_row, 6, total_ninty, table_acc_total)
            expanded.write(expanded_row, 7, final_total, table_acc_total)

            collapsed.write(collapsed_row, 0, 'Total', table_header_top)
            collapsed.write(collapsed_row, 1, '', table_acc_total)
            collapsed.write(collapsed_row, 2, total_current, table_acc_total)
            collapsed.write(collapsed_row, 3, total_fourteen, table_acc_total)
            collapsed.write(collapsed_row, 4, total_thirty, table_acc_total)
            collapsed.write(collapsed_row, 5, total_sixty, table_acc_total)
            collapsed.write(collapsed_row, 6, total_ninty, table_acc_total)
            collapsed.write(collapsed_row, 7, final_total, table_acc_total)

            expanded_row += 2
            collapsed_row += 2

        workbook.close()

        # create attach_id and send it to the wizard
        attach_id = self.env['xlsx.print.wizard'].create({
            'name': _('Aged Receivable.xlsx'),
            'xls_output': base64.encodebytes(output.getvalue())
        })
        return attach_id