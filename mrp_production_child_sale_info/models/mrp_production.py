from odoo import Command, api, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    @api.model_create_multi
    def create(self, vals_list):
        productions = super().create(vals_list)
        for production in productions:
            if production.sale_line_id:
                production.reference_ids.write(
                    {"sale_ids": [Command.link(production.sale_line_id.order_id.id)]}
                )
        return productions
