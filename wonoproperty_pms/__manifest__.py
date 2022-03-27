# -*- coding: utf-8 -*-
{
    'name': 'WonoProperty PMS',
    'summary': 'Add custom Property Management System for WonoProperty',
    'description': 'Add custom Property Management System for WonoProperty',
    'author': 'Maurice Jansz',
    'category': 'Property Management',
    'version': '1.0.7',
    'depends': ['account'],
    'data': [
        'data/expense_type_data.xml',
        'views/property_property_views.xml',
        'views/property_unit_views.xml',
        'wizard/property_tenant_wizard_views.xml',
        'views/expense_type_views.xml',
        'views/account_move_views.xml',
        'views/water_odometer_reading_views.xml',
        'views/res_partner_views.xml',
        'views/financier_financier_views.xml',
        'views/report_invoice_views.xml',
        'security/ir.model.access.csv'
    ],
    'demo': [],
    'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            'wonoproperty_pms/static/src/**/*',
        ],
    },
}
