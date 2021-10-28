import base64
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import xlrd

    try:
        from xlrd import xlsx
    except ImportError:
        xlsx = None
except ImportError:
    xlrd = xlsx = None


class ImportPurchaseLineClasic(models.TransientModel):
    _name = "import.purchase.line.clasic"
    _description = "Import purchase line Clasic"


    data_file = fields.Binary(string="Archivo", required=True)
    filename = fields.Char("Archivo")
    has_header = fields.Boolean("Contiene Cabecera", default=True)
    purchase_id = fields.Many2one("purchase.order")

    @api.model
    def default_get(self, fields_list):
        defaults = super(ImportPurchaseLineClasic, self).default_get(fields_list)
        active_id = self.env.context.get("active_id", [])
        model = self.env.context.get("active_model", False)
        purchase = self.env[model].browse(active_id)
        if purchase.state != "draft":
            raise UserError(_("The order is in the %s state") % (purchase.state))
        defaults["purchase_id"] = purchase.id
        return defaults

    def do_import_clasic(self):
        decoded_data = base64.b64decode(self.data_file)
        book = xlrd.open_workbook(file_contents=decoded_data)
        sheet = book.sheet_by_index(0)
        table_values = []
        for row in list(map(sheet.row, range(sheet.nrows))):
            values = []
            for cell in row:
                if cell.ctype is xlrd.XL_CELL_NUMBER:
                    is_float = cell.value % 1 != 0.0
                    values.append(str(cell.value) if is_float else str(int(cell.value)))
                else:
                    values.append(cell.value)
            table_values.append(values)

        if not table_values:
            return
        if self.has_header:
            table_values.pop(0)

        lines = []
        for row in table_values:
            if len(row) == 6:
                product_code, product_name, quantity, price, tax, uom_name = row
            elif len(row) == 5:
                product_code, product_name, quantity, price, tax = row
                uom_name = False
            else:
                continue

            product_id = False
            quantity = float(quantity)

            domain = [("product_code", "=", product_code)]
            domain_igv = [("name", "=", tax), ("type_tax_use", "=", "purchase"),
                          ("company_id", "=", self.purchase_id.company_id.id)]

            supplierinfo = self.env["product.supplierinfo"].sudo().search(domain, limit=1)
            if not supplierinfo:
                raise UserError(_("Product %s not found") % product_code)
            else:
                if supplierinfo.product_id:
                    product_id = supplierinfo.product_id
                else:
                    product_id = supplierinfo.product_tmpl_id.product_variant_id

            product_uom = product_id.uom_po_id or product_id.uom_id
            if uom_name and uom_name != product_uom.name:
                uom = self.env["uom.uom"].serach([("name", "=", uom_name)], limit=1)
                if uom:
                    product_uom = uom

            if not tax:
                tax_id = False
            else:
                igvinfo = self.env["account.tax"].sudo().search(domain_igv, limit=1)
                if not igvinfo:
                    raise UserError(_("IGV NO ENCONTRADO O MAL ESCRITO %s") % tax)

                tax_id = [(6, 0, igvinfo.ids)]

            lines += [
                {
                    "order_id": self.purchase_id.id,
                    "product_id": product_id.id,
                    "name": product_name,
                    "product_qty": quantity,
                    "price_unit": price,
                    "product_uom": product_uom.id,
                    "taxes_id": tax_id,
                    "date_planned": self.purchase_id.date_order,
                }
            ]

        self.env["purchase.order.line"].create(lines)


class LinePurchase(models.Model):
    _inherit = 'purchase.order'

    def purchase_line(self):
        return {'type': 'ir.actions.act_window',
                'name': _('import line"'),
                'res_model': 'import.purchase.line.clasic',
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                }

