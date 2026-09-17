from lxml import html

from odoo.tests.common import TransactionCase


class TestSaleOrderReportAddresses(TransactionCase):
    """Regression tests for the Odoo 19 address blocks in the report."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env["res.partner"].create(
            {
                "name": "Blueprint Customer",
                "street": "Customer Street 101",
            }
        )
        cls.invoice_address = cls.env["res.partner"].create(
            {
                "name": "Blueprint Invoice",
                "street": "Invoice Street 202",
                "parent_id": cls.customer.id,
                "type": "invoice",
            }
        )
        cls.shipping_address = cls.env["res.partner"].create(
            {
                "name": "Blueprint Shipping",
                "street": "Shipping Street 303",
                "parent_id": cls.customer.id,
                "type": "delivery",
            }
        )
        cls.alternate_contact = cls.env["res.partner"].create(
            {
                "name": "Blueprint Alternate Contact",
                "street": "Alternate Street 404",
                "parent_id": cls.customer.id,
                "type": "contact",
            }
        )
        product = cls.env["product.product"].create(
            {"name": "Blueprint address test product"}
        )
        cls.order = cls.env["sale.order"].create(
            {
                "partner_id": cls.customer.id,
                "partner_invoice_id": cls.customer.id,
                "partner_shipping_id": cls.customer.id,
            }
        )
        cls.line = cls.env["sale.order.line"].create(
            {
                "order_id": cls.order.id,
                "product_id": product.id,
                "product_uom_qty": 1,
            }
        )

    def _render_address_text(self):
        rendered = self.env["ir.qweb"]._render(
            "product_blueprint_manager.report_sale_order_blueprint_page",
            {
                "doc": self.order,
                "line": self.line,
                "line_index": 0,
                "blueprint": {"blueprint_name": "Address regression blueprint"},
            },
        )
        return " ".join(html.fromstring(rendered).text_content().split())

    def test_same_customer_invoice_and_shipping_address(self):
        report_text = self._render_address_text()

        self.assertIn("Customer Street 101", report_text)
        self.assertNotIn("Invoicing Address", report_text)
        self.assertNotIn("Invoicing and Shipping Address", report_text)
        self.assertNotIn("Shipping Address", report_text)

    def test_combined_invoice_and_shipping_address(self):
        self.order.write(
            {
                "partner_invoice_id": self.invoice_address.id,
                "partner_shipping_id": self.invoice_address.id,
            }
        )

        report_text = self._render_address_text()

        self.assertIn("Customer Street 101", report_text)
        self.assertIn("Invoicing and Shipping Address", report_text)
        self.assertIn("Invoice Street 202", report_text)
        self.assertNotIn("Shipping Street 303", report_text)

    def test_alternate_contact_with_separate_invoice_and_shipping(self):
        self.order.write(
            {
                "partner_id": self.alternate_contact.id,
                "partner_invoice_id": self.invoice_address.id,
                "partner_shipping_id": self.shipping_address.id,
            }
        )

        report_text = self._render_address_text()

        self.assertIn("Blueprint Alternate Contact", report_text)
        self.assertIn("Invoicing Address", report_text)
        self.assertIn("Invoice Street 202", report_text)
        self.assertIn("Shipping Address", report_text)
        self.assertIn("Shipping Street 303", report_text)

    def test_shipping_block_only_when_invoice_is_primary_address(self):
        self.order.write(
            {
                "partner_id": self.invoice_address.id,
                "partner_invoice_id": self.invoice_address.id,
                "partner_shipping_id": self.shipping_address.id,
            }
        )

        report_text = self._render_address_text()

        self.assertNotIn("Invoicing Address", report_text)
        self.assertIn("Shipping Address", report_text)
        self.assertIn("Shipping Street 303", report_text)

    def test_invoice_block_only_when_shipping_is_primary_address(self):
        self.order.write(
            {
                "partner_id": self.shipping_address.id,
                "partner_invoice_id": self.invoice_address.id,
                "partner_shipping_id": self.shipping_address.id,
            }
        )

        report_text = self._render_address_text()

        self.assertIn("Invoicing Address", report_text)
        self.assertIn("Invoice Street 202", report_text)
        self.assertNotIn("Shipping Address", report_text)
