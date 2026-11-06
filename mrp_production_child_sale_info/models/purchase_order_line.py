from odoo import api, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    @api.model
    def _prepare_purchase_order_line_from_procurement(
        self,
        product_id,
        product_qty,
        product_uom,
        location_dest_id,
        name,
        origin,
        company_id,
        values,
        po,
    ):
        result = super()._prepare_purchase_order_line_from_procurement(
            product_id,
            product_qty,
            product_uom,
            location_dest_id,
            name,
            origin,
            company_id,
            values,
            po,
        )
        # sale_purchase_stock 19 only fills sale_line_id for dropshipping.
        # Restore the 18.0 traceability for components of sale-linked MOs.
        if values.get("mrp_component_sale_line_id"):
            result["sale_line_id"] = values["mrp_component_sale_line_id"]
        return result

    def _find_candidate(
        self,
        product_id,
        product_qty,
        product_uom,
        location_id,
        name,
        origin,
        company_id,
        values,
    ):
        lines = self
        sale_line_id = values.get("mrp_component_sale_line_id")
        if sale_line_id:
            lines = lines.filtered(lambda line: line.sale_line_id.id == sale_line_id)
        elif values.get("move_dest_ids"):
            # An ordinary stock replenishment must not consume a component
            # purchase line which is attributed to a particular sales line.
            lines = lines.filtered(lambda line: not line.sale_line_id)
        return super(PurchaseOrderLine, lines)._find_candidate(
            product_id,
            product_qty,
            product_uom,
            location_id,
            name,
            origin,
            company_id,
            values,
        )
