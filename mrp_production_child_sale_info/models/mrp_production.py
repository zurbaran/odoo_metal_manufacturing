from odoo import api, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    @api.model_create_multi
    def create(self, vals_list):
        productions = super().create(vals_list)
        for production in productions:
            if (
                production.sale_line_id
                and production.procurement_group_id
                and not production.procurement_group_id.sale_id
            ):
                production.procurement_group_id.sale_id = (
                    production.sale_line_id.order_id
                )
        return productions
