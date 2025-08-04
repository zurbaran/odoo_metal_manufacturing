from odoo.tests.common import TransactionCase, tagged


@tagged("-at_install", "post_install")
class TestBlueprintReport(TransactionCase):
    def test_action_print_blueprint(self):
        order = self.env["sale.order"].create(
            {"partner_id": self.env.ref("base.res_partner_1").id}
        )
        action = order.action_print_blueprint()
        self.assertIn("report_name", action)
        self.assertIn("blueprint_fabrication_report", action["report_name"])
