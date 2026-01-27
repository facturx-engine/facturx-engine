from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    facturx_engine_url = fields.Char(
        string="Factur-X Engine URL",
        config_parameter='facturx_engine.url',
        default='http://facturx-engine:8000',
        help="URL of the local Docker container (e.g. http://localhost:8000 or http://facturx-engine:8000)"
    )
    
    facturx_engine_key = fields.Char(
        string="License Key",
        config_parameter='facturx_engine.key',
        help="Pro License Key to unlock full extraction. Leave empty for Demo mode (masked data)."
    )
