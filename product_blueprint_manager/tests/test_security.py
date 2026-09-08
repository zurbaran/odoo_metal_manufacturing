from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, new_test_user


_BLUEPRINT_MODELS = (
    "product.blueprint",
    "product.blueprint.formula",
    "product.blueprint.formula.name",
    "product.blueprint.condition",
)


class TestBlueprintSecurity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = new_test_user(
            cls.env,
            login="blueprint_employee",
            groups="base.group_user",
        )
        cls.blueprint_user = new_test_user(
            cls.env,
            login="blueprint_user",
            groups="product_blueprint_manager.group_product_blueprint_user",
        )
        cls.blueprint_manager = new_test_user(
            cls.env,
            login="blueprint_manager",
            groups="product_blueprint_manager.group_product_blueprint_manager",
        )
        cls.product_template = cls.env["product.template"].create(
            {"name": "Blueprint Security Product"}
        )

    def test_employee_has_no_blueprint_model_access(self):
        for model_name in _BLUEPRINT_MODELS:
            with self.subTest(model=model_name), self.assertRaises(AccessError):
                self.env[model_name].with_user(self.employee).check_access("read")

    def test_blueprint_user_is_read_only(self):
        for model_name in _BLUEPRINT_MODELS:
            model = self.env[model_name].with_user(self.blueprint_user)
            with self.subTest(model=model_name, operation="read"):
                model.check_access("read")
            for operation in ("write", "create", "unlink"):
                with self.subTest(model=model_name, operation=operation), self.assertRaises(
                    AccessError
                ):
                    model.check_access(operation)

    def test_blueprint_manager_has_full_access(self):
        for model_name in _BLUEPRINT_MODELS:
            model = self.env[model_name].with_user(self.blueprint_manager)
            for operation in ("read", "write", "create", "unlink"):
                with self.subTest(model=model_name, operation=operation):
                    model.check_access(operation)

    def test_employee_cannot_discover_blueprint_product_fields(self):
        employee_fields = self.env["product.template"].with_user(self.employee).fields_get()
        self.assertNotIn("blueprint_ids", employee_fields)
        self.assertNotIn("formula_ids", employee_fields)

        blueprint_fields = (
            self.env["product.template"].with_user(self.blueprint_user).fields_get()
        )
        self.assertIn("blueprint_ids", blueprint_fields)
        self.assertIn("formula_ids", blueprint_fields)

    def test_public_product_helpers_require_blueprint_group(self):
        product = self.product_template.with_user(self.employee)
        with self.assertRaises(AccessError):
            product.get_custom_attribute_values()
        with self.assertRaises(AccessError):
            product.generate_blueprint_report()

        blueprint_product = self.product_template.with_user(self.blueprint_user)
        self.assertEqual(blueprint_product.get_custom_attribute_values(), {})
        self.assertFalse(blueprint_product.generate_blueprint_report())

    def test_safe_formula_evaluation(self):
        line_model = self.env["sale.order.line"]
        self.assertEqual(
            line_model.safe_evaluate_formula(
                "math.ceil(mmB / 50) * 50",
                {"mmB": 1234},
            ),
            "1250",
        )
        self.assertEqual(
            line_model.safe_evaluate_formula(
                "5 if mmA > 1000 else 0",
                {"mmA": 1500},
            ),
            "5",
        )

    def test_unsafe_formula_is_rejected(self):
        line_model = self.env["sale.order.line"]
        attacks = (
            "(1).__class__.__mro__",
            "__import__('os').system('id')",
            "mmA.__class__",
        )
        for expression in attacks:
            self.assertEqual(
                line_model.safe_evaluate_formula(expression, {"mmA": 10}),
                "Error",
                expression,
            )
