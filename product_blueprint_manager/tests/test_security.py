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
        partner = cls.env["res.partner"].create({"name": "Blueprint Security Partner"})
        cls.sale_order = cls.env["sale.order"].create({"partner_id": partner.id})

    def test_odoo19_privilege_structure(self):
        privilege = self.env.ref("product_blueprint_manager.privilege_product_blueprint")
        user_group = self.env.ref("product_blueprint_manager.group_product_blueprint_user")
        manager_group = self.env.ref("product_blueprint_manager.group_product_blueprint_manager")
        self.assertEqual(user_group.privilege_id, privilege)
        self.assertEqual(manager_group.privilege_id, privilege)
        self.assertIn(user_group, manager_group.implied_ids)

    def test_employee_has_no_blueprint_model_access(self):
        for model_name in _BLUEPRINT_MODELS:
            with self.subTest(model=model_name), self.assertRaises(AccessError):
                self.env[model_name].with_user(self.employee).check_access("read")

    def test_blueprint_user_is_read_only(self):
        for model_name in _BLUEPRINT_MODELS:
            model = self.env[model_name].with_user(self.blueprint_user)
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

        blueprint_fields = self.env["product.template"].with_user(
            self.blueprint_user
        ).fields_get()
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

    def test_sale_report_rpc_actions_require_blueprint_group(self):
        order = self.sale_order.with_user(self.employee)
        for method_name in (
            "action_print_blueprint",
            "action_print_purchase_blueprint",
        ):
            with self.subTest(method=method_name), self.assertRaises(AccessError):
                getattr(order, method_name)()

    def test_security_metadata_restricts_menus_and_actions(self):
        user_group = self.env.ref("product_blueprint_manager.group_product_blueprint_user")
        manager_group = self.env.ref(
            "product_blueprint_manager.group_product_blueprint_manager"
        )

        for xmlid in (
            "product_blueprint_manager.action_report_sale_order_blueprint",
            "product_blueprint_manager.action_report_purchase_order_blueprint",
        ):
            self.assertIn(user_group, self.env.ref(xmlid).group_ids)

        for xmlid in (
            "product_blueprint_manager.product_blueprint_action",
            "product_blueprint_manager.product_blueprint_formula_action",
        ):
            self.assertIn(manager_group, self.env.ref(xmlid).group_ids)

        menu_xmlids = (
            "product_blueprint_manager.menu_product_blueprints_root",
            "product_blueprint_manager.menu_product_blueprints",
            "product_blueprint_manager.menu_product_blueprint_formulas",
        )
        employee_visible = self.env["ir.ui.menu"].with_user(
            self.employee
        )._visible_menu_ids()
        manager_visible = self.env["ir.ui.menu"].with_user(
            self.blueprint_manager
        )._visible_menu_ids()
        for xmlid in menu_xmlids:
            menu = self.env.ref(xmlid)
            self.assertIn(manager_group, menu.group_ids)
            self.assertNotIn(menu.id, employee_visible)
            self.assertIn(menu.id, manager_visible)

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
