import base64

from odoo.tests.common import TransactionCase, tagged


@tagged("-at_install", "post_install")
class TestBlueprintGeneration(TransactionCase):
    def test_attachment_generated(self):
        template = self.env["product.template"].create(
            {"name": "Blueprint Generation Product"}
        )
        svg = b'<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50"></svg>'
        blueprint = self.env["product.blueprint"].create(
            {
                "name": "Generated Blueprint",
                "product_id": template.id,
                "type_blueprint": "manufacturing",
                "file": base64.b64encode(svg),
            }
        )
        partner = self.env["res.partner"].create({"name": "Blueprint Generation Partner"})
        order = self.env["sale.order"].create({"partner_id": partner.id})
        line = self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": template.product_variant_id.id,
                "product_uom_qty": 1,
            }
        )

        generated = line._get_evaluated_blueprint()

        self.assertEqual(len(generated), 1)
        self.assertEqual(generated[0]["blueprint_name"], blueprint.name)
        self.assertTrue(generated[0]["png_base64"])

        attachment = self.env["ir.attachment"].browse(generated[0]["attachment_id"])
        self.assertTrue(attachment.exists())
        self.assertEqual(attachment.res_model, "sale.order.line")
        self.assertEqual(attachment.res_id, line.id)
        self.assertEqual(attachment.mimetype, "image/svg+xml")
        self.assertTrue(attachment.datas)
