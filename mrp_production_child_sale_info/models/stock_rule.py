from odoo import api, models


class StockRule(models.Model):
    _inherit = "stock.rule"

    @api.model
    def _get_procurements_to_merge_groupby(self, procurement):
        # Preserve the originating sales line BEFORE native buy procurements
        # are merged, as well as when matching existing purchase lines.
        return super()._get_procurements_to_merge_groupby(procurement) + (
            procurement.values.get("mrp_component_sale_line_id") or False,
        )
