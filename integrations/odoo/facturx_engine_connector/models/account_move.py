import requests
import base64
import logging
from odoo import models, fields, _, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_import_facturx_pdf(self):
        """
        Send the main PDF attachment to Factur-X Engine and fill the invoice.
        """
        self.ensure_one()
        
        # 1. Get Configuration
        config_url = self.env['ir.config_parameter'].sudo().get_param('facturx_engine.url')
        license_key = self.env['ir.config_parameter'].sudo().get_param('facturx_engine.key')
        
        if not config_url:
            raise UserError(_("Please configure Factur-X Engine URL in Settings."))

        # 2. Find PDF Attachment
        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'account.move'),
            ('res_id', '=', self.id),
            ('mimetype', '=', 'application/pdf')
        ], limit=1, order='create_date desc')

        if not attachment:
            raise UserError(_("No PDF attachment found on this invoice. Please upload one first."))

        # 3. Call API
        try:
            pdf_content = base64.b64decode(attachment.datas)
            files = {'file': ('invoice.pdf', pdf_content, 'application/pdf')}
            
            headers = {}
            if license_key:
                headers['X-LICENSE-KEY'] = license_key
            
            # Use 'extract' endpoint
            response = requests.post(f"{config_url}/v1/extract", files=files, headers=headers, timeout=10)
            
            if response.status_code != 200:
                error_msg = response.text
                raise UserError(_("Engine Error (%s): %s") % (response.status_code, error_msg))
                
            data = response.json()
            
        except requests.exceptions.ConnectionError:
            raise UserError(_("Could not connect to Factur-X Engine at %s. Is the Docker container running?") % config_url)
        except Exception as e:
            raise UserError(_("Extraction Failed: %s") % str(e))

        # 4. Apply Data to Odoo Invoice
        invoice_data = data.get('invoice_json')
        if not invoice_data:
            # Fallback if the engine returns flat data (Old versions or Pro with specific settings)
            invoice_data = data
            
        self._apply_facturx_data(invoice_data)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Invoice data imported successfully from Factur-X!'),
                'type': 'success',
                'sticky': False,
            }
        }

    def _apply_facturx_data(self, data):
        """
        Map JSON data from Engine to Odoo fields.
        This is a 'Best Effort' mapping.
        """
        vals = {}
        
        # --- Partner (Vendor) ---
        seller_name = data.get('seller', {}).get('name')
        seller_vat = data.get('seller', {}).get('vat_number')
        
        if seller_name:
            # Try to find partner by VAT first, then Name
            domain = []
            if seller_vat:
                domain = [('vat', '=', seller_vat)]
            else:
                domain = [('name', 'ilike', seller_name)]
                
            partner = self.env['res.partner'].search(domain, limit=1)
            if partner:
                vals['partner_id'] = partner.id
            else:
                # Optional: Create partner if not found? Risk of duplicates.
                # For now, just log warning
                _logger.warning(f"Factur-X: Partner '{seller_name}' (VAT: {seller_vat}) not found in Odoo.")

        # --- Dates ---
        def parse_facturx_date(d_str):
            if not d_str:
                return False
            # If already YYYY-MM-DD
            if '-' in d_str:
                return d_str
            # If YYYYMMDD
            if len(d_str) == 8:
                return f"{d_str[:4]}-{d_str[4:6]}-{d_str[6:8]}"
            return d_str

        if data.get('invoice_date'):
            vals['invoice_date'] = parse_facturx_date(data.get('invoice_date'))
        
        if data.get('due_date'):
            vals['invoice_date_due'] = parse_facturx_date(data.get('due_date'))

        # --- Ref ---
        if data.get('invoice_number'):
            vals['ref'] = data.get('invoice_number')

        # --- Lines ---
        line_commands = []
        
        # Odoo 16 requires an account_id on lines. Let's find a default one.
        # We try the default account on the journal, or the first 'expense' account found.
        default_account = self.journal_id.default_account_id
        if not default_account:
            default_account = self.env['account.account'].search([
                ('account_type', '=', 'expense'),
                ('company_id', '=', self.company_id.id)
            ], limit=1)
        
        if not default_account:
            # Last resort: any account
            default_account = self.env['account.account'].search([('company_id', '=', self.company_id.id)], limit=1)
        # Clear existing lines? Maybe dangerous. Let's append or assume empty.
        # self.invoice_line_ids.unlink() 
        
        line_items = data.get('line_items', [])
        if line_items:
            for item in line_items:
                line_vals = {
                    'name': item.get('description', item.get('name', 'Unknown Item')),
                    'quantity': float(item.get('quantity', 1.0)),
                    'price_unit': float(item.get('unit_price', 0.0)),
                    'account_id': default_account.id if default_account else False,
                }
                line_commands.append((0, 0, line_vals))
        else:
            # Fallback for 'Minimum' profile: Use totals to create a single summary line
            totals = data.get('totals', data.get('amounts', {}))
            net_amount = float(totals.get('net_amount', totals.get('tax_basis_total', 0.0)))
            if net_amount > 0:
                line_commands.append((0, 0, {
                    'name': _("Factur-X Import (Summary/Minimum Profile)"),
                    'quantity': 1.0,
                    'price_unit': net_amount,
                    'account_id': default_account.id if default_account else False,
                }))
            
        if line_commands:
            vals['invoice_line_ids'] = line_commands

        # Write changes
        self.write(vals)
