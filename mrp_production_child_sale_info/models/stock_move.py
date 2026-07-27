from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _prepare_procurement_values(self):
        values = super()._prepare_procurement_values()
        self.ensure_one()

        parent_mo = self.raw_material_production_id
        if parent_mo and parent_mo.sale_line_id:
            values["sale_line_id"] = parent_mo.sale_line_id.id

        return values
