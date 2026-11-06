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

    def test_real_sale_creates_child_mo_and_component_purchase(self):
        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.env.company.id)], limit=1
        )
        mto = self.env.ref("stock.route_warehouse0_mto")
        mto.active = True
        manufacture = warehouse.manufacture_pull_id.route_id
        buy = self.env.ref("purchase_stock.route_warehouse0_buy")
        vendor = self.env["res.partner"].create({"name": "Component vendor"})

        def product(name, routes):
            return self.env["product.product"].create(
                {
                    "name": name,
                    "is_storable": True,
                    "route_ids": [Command.set(routes.ids)],
                }
            )

        parent = product("MTO assembly", mto | manufacture)
        child = product("MTO subassembly", mto | manufacture)
        bought = product("MTO purchased component", mto | buy)
        material = product("Raw material", self.env["stock.route"])
        bought.seller_ids = [Command.create({"partner_id": vendor.id, "price": 1})]
        self.env["mrp.bom"].create(
            {
                "product_tmpl_id": parent.product_tmpl_id.id,
                "product_qty": 1,
                "bom_line_ids": [
                    Command.create({"product_id": p.id, "product_qty": 1})
                    for p in (child, bought)
                ],
            }
        )
        self.env["mrp.bom"].create(
            {
                "product_tmpl_id": child.product_tmpl_id.id,
                "product_qty": 1,
                "bom_line_ids": [
                    Command.create({"product_id": material.id, "product_qty": 1})
                ],
            }
        )
        order = self.env["sale.order"].create(
            {
                "partner_id": self.env["res.partner"]
                .create({"name": "MTO customer"})
                .id,
                "warehouse_id": warehouse.id,
                "order_line": [
                    Command.create({"product_id": parent.id, "product_uom_qty": 1})
                ],
            }
        )
        order.action_confirm()
        productions = self.env["mrp.production"].search(
            [("product_id", "in", (parent | child).ids)]
        )
        self.assertEqual(len(productions), 2)
        self.assertEqual(productions.sale_line_id, order.order_line)
        for production in productions:
            self.assertIn(order, production.reference_ids.sale_ids)
        purchase_line = self.env["purchase.order.line"].search(
            [("product_id", "=", bought.id)]
        )
        self.assertEqual(len(purchase_line), 1)
        self.assertIn(order, purchase_line.order_id.reference_ids.sale_ids)
        self.assertEqual(purchase_line.sale_line_id, order.order_line)
        # A second sale must not reuse the component line of the first sale.
        second = order.copy()
        second.action_confirm()
        purchase_lines = self.env["purchase.order.line"].search(
            [("product_id", "=", bought.id)]
        )
        self.assertEqual(len(purchase_lines), 2)
        self.assertEqual(
            purchase_lines.sale_line_id, order.order_line | second.order_line
        )
        self.assertTrue(all(line.product_qty == 1 for line in purchase_lines))
        # Confirm two sales together too: buy procurements must remain separate
        # even before _find_candidate() is called.
        third, fourth = order.copy(), order.copy()
        (third | fourth).action_confirm()
        purchase_lines = self.env["purchase.order.line"].search(
            [("product_id", "=", bought.id)]
        )
        self.assertEqual(len(purchase_lines), 4)
        self.assertEqual(
            set(purchase_lines.sale_line_id.ids),
            set((order | second | third | fourth).order_line.ids),
        )
        self.assertTrue(all(line.product_qty == 1 for line in purchase_lines))
        # Ordinary MTO sale of the same SKU uses native 19.0 linking and must
        # not merge into a component line of one of the manufactured sales.
        direct = order.copy()
        direct.order_line.product_id = bought
        direct.action_confirm()
        native_line = (
            self.env["purchase.order.line"].search([("product_id", "=", bought.id)])
            - purchase_lines
        )
        self.assertEqual(len(native_line), 1)
        self.assertFalse(native_line.sale_line_id)
        self.assertIn(direct, native_line.order_id.reference_ids.sale_ids)
        # Keep Odoo 19's receipt semantics: raw-material receipts must not count
        # as delivery of the sold finished product.
        purchase_lines.order_id.button_confirm()
        receipts = purchase_lines.move_ids
        self.assertTrue(receipts)
        self.assertFalse(receipts.sale_line_id)
        self.assertEqual(order.order_line.qty_delivered, 0)
        self.assertEqual(second.order_line.qty_delivered, 0)
