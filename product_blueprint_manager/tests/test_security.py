from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, new_test_user


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

    def test_employee_has_no_blueprint_model_access(self):
        with self.assertRaises(AccessError):
            self.env["product.blueprint"].with_user(self.employee).check_access("read")

    def test_blueprint_user_is_read_only(self):
        model = self.env["product.blueprint"].with_user(self.blueprint_user)
        model.check_access("read")
        with self.assertRaises(AccessError):
            model.check_access("write")
        with self.assertRaises(AccessError):
            model.check_access("create")
        with self.assertRaises(AccessError):
            model.check_access("unlink")

    def test_blueprint_manager_has_full_access(self):
        model = self.env["product.blueprint"].with_user(self.blueprint_manager)
        for operation in ("read", "write", "create", "unlink"):
            model.check_access(operation)

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
