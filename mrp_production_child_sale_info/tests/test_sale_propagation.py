from odoo import Command
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSalePropagation(TransactionCase):
    def test_child_procurement_and_reference(self):
        partner = self.env["res.partner"].create({"name": "MRP customer"})
        product = self.env["product.product"].create(
            {"name": "Assembly", "type": "consu"}
        )
        component = self.env["product.product"].create(
            {"name": "Component", "type": "consu"}
        )
        order = self.env["sale.order"].create({"partner_id": partner.id})
        line = self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": product.id,
                "product_uom_qty": 1,
            }
        )
        production = self.env["mrp.production"].create(
            {
                "product_id": product.id,
                "product_qty": 1,
                "sale_line_id": line.id,
                "move_raw_ids": [
                    Command.create(
                        {
                            "product_id": component.id,
                            "product_uom": component.uom_id.id,
                            "product_uom_qty": 1,
                            "location_id": self.env.ref(
                                "stock.stock_location_stock"
                            ).id,
                            "location_dest_id": product.property_stock_production.id,
                        }
                    )
                ],
            }
        )
        self.assertIn(order, production.reference_ids.sale_ids)
        values = production.move_raw_ids._prepare_procurement_values()
        self.assertEqual(values["sale_line_id"], line.id)
        # sale_mrp natively copies this value to a child MO.
        child = self.env["mrp.production"].create(
            {
                "product_id": component.id,
                "product_qty": 1,
                "sale_line_id": values["sale_line_id"],
            }
        )
        self.assertEqual(child.sale_line_id, line)
        self.assertIn(order, child.reference_ids.sale_ids)

    def test_production_without_sale(self):
        product = self.env["product.product"].create({"name": "Stock assembly"})
        production = self.env["mrp.production"].create(
            {
                "product_id": product.id,
                "product_qty": 1,
            }
        )
        self.assertFalse(production.reference_ids.sale_ids)
