from odoo.tests.common import TransactionCase


class TestConfiguratorSecurity(TransactionCase):
    def test_custom_acls_do_not_grant_permissions(self):
        for xmlid in (
            "product_configurator_attribute_price.access_product_template_attribute_value",
            "product_configurator_attribute_price.access_sale_order_line",
        ):
            access = self.env.ref(xmlid)
            self.assertFalse(access.perm_read)
            self.assertFalse(access.perm_write)
            self.assertFalse(access.perm_create)
            self.assertFalse(access.perm_unlink)

    def test_safe_formula_evaluation(self):
        model = self.env["product.template.attribute.value"]
        self.assertEqual(
            model._safe_eval(
                "((custom_value + 49) // 50 - 10) * 5",
                {"custom_value": 700, "price_so_far": 1000},
            ),
            20,
        )
        self.assertEqual(
            model._safe_eval(
                "price_so_far * 0.2",
                {"custom_value": 700, "price_so_far": 1000},
            ),
            200.0,
        )

    def test_unsafe_formula_is_rejected(self):
        model = self.env["product.template.attribute.value"]
        attacks = (
            "(1).__class__.__mro__",
            "__import__('os').system('id')",
            "custom_value.__class__",
        )
        for expression in attacks:
            with self.assertRaises(ValueError, msg=expression):
                model._safe_eval(
                    expression,
                    {"custom_value": 700, "price_so_far": 1000},
                )
