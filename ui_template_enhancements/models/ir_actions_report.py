from odoo import api, models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    @api.model
    def _ute_apply_compact_external_paperformat(self):
        """Apply the compact paper format to installed address-bearing reports."""
        paperformat = self.env.ref(
            "ui_template_enhancements.paperformat_ute_external_compact"
        )

        report_xmlids = (
            "account.account_invoices",
            "account.account_invoices_without_payment",
            "l10n_es_aeat_mod347.347_partner",
            "purchase.action_report_purchase_order",
            "purchase.report_purchase_quotation",
            "sale.action_report_pro_forma_invoice",
            "product_blueprint_manager.action_report_sale_order_blueprint",
            "sale_pdf_quote_builder.action_report_saleorder_raw",
            "sale.action_report_saleorder",
            "stock.action_report_delivery",
            "stock.action_report_picking",
        )

        for xmlid in report_xmlids:
            action = self.env.ref(xmlid, raise_if_not_found=False)
            if action and action._name == "ir.actions.report":
                action.sudo().write({"paperformat_id": paperformat.id})

        return True
