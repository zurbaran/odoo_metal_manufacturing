from odoo import Command
from odoo.tests.common import TransactionCase, tagged


@tagged("-at_install", "post_install")
class TestBlueprintReport(TransactionCase):
    def test_action_print_blueprint(self):
        partner = self.env["res.partner"].create({"name": "Blueprint Report Partner"})
        order = self.env["sale.order"].create({"partner_id": partner.id})

        action = order.action_print_blueprint()
        report_action = action.get("context", {}).get("report_action") or action

        self.assertEqual(
            report_action.get("report_name"),
            "product_blueprint_manager.report_sale_order_blueprint",
        )
        self.assertEqual(report_action.get("report_type"), "qweb-pdf")

    def test_mrp_blueprint_uses_odoo19_stock_reference(self):
        partner = self.env["res.partner"].create({"name": "MRP blueprint partner"})
        order = self.env["sale.order"].create({"partner_id": partner.id})
        product = self.env["product.product"].create({"name": "Blueprint assembly"})
        production = self.env["mrp.production"].create(
            {
                "product_id": product.id,
                "product_qty": 1,
            }
        )
        production.reference_ids.write({"sale_ids": [Command.link(order.id)]})
        self.assertFalse(production.move_dest_ids)
        self.assertEqual(
            production.action_print_blueprint_mrp(), order.action_print_blueprint()
        )
