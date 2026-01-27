{
    'name': 'Factur-X Engine Connector',
    'version': '1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Import Factur-X/ZUGFeRD invoices using Local Engine',
    'description': """
Factur-X Engine Connector
=========================
This module allows you to import Supplier Invoices (Vendor Bills) from PDF files 
containing Factur-X / ZUGFeRD metadata.

It connects to your local "Factur-X Engine" Docker container to perform 
safe and reliable data extraction without relying on Cloud OCR services.

Features:
- Import PDF invoice -> Auto-fill Odoo Bill
- 100% Privacy (Data stays on your server)
- Support for EN16931 and ZUGFeRD standards
    """,
    'author': 'Factur-X Engine Team',
    'website': 'https://facturx-engine.lemonsqueezy.com',
    'license': 'OPL-1',
    'depends': ['account', 'base_setup'],
    'data': [
        'views/res_config_settings_views.xml',
        'views/account_move_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
