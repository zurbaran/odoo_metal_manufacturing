import base64
import json

from odoo import fields
from odoo.tests.common import HttpCase, tagged
from odoo.tools import file_open


@tagged("post_install", "-at_install")
class TestActualBoeExport(HttpCase):
    def test_actual_mod130_export_and_download_without_patch(self):
        self.assertFalse(
            self.env["ir.module.module"].search_count(
                [
                    ("name", "=", "web_binary_boe_download_fix"),
                    ("state", "=", "installed"),
                ]
            )
        )
        report = self.env["l10n.es.aeat.mod130.report"].create(
            {
                "name": "9990000000130",
                "company_id": self.env.company.id,
                "company_vat": "12345678Z",
                "contact_name": "BOE Test owner",
                "contact_phone": "911234455",
                "statement_type": "N",
                "support_type": "T",
                "year": 2026,
                "period_type": "1T",
                "date_start": "2026-01-01",
                "date_end": "2026-03-31",
                "export_config_id": self.env.ref(
                    "l10n_es_aeat_mod130.aeat_mod130_export_config"
                ).id,
            }
        )
        wizard = self.env["l10n.es.aeat.report.export_to_boe"].create({})
        expected = wizard._export_config(report, report.export_config_id)
        self.assertTrue(expected.startswith(b"<T130"))
        self.assertGreater(len(expected), 100)
        fixture = {
            "action": {
                "type": "ir.actions.act_window",
                "name": "Actual BOE export",
                "res_model": wizard._name,
                "res_id": wizard.id,
                "target": "new",
                "views": [[self.env.ref("l10n_es_aeat.wizard_aeat_export").id, "form"]],
                "context": {
                    "active_model": report._name,
                    "active_id": report.id,
                    "active_ids": report.ids,
                },
            },
            "model": wizard._name,
            "id": wizard.id,
            "filename": f"130_report_{fields.Date.today()}.txt",
            "expected": base64.b64encode(expected).decode(),
        }
        self.env.ref("base.user_admin").tour_enabled = False
        with file_open(
            "boe_native_check/tests/browser_actual_boe.js", "r"
        ) as browser_code:
            self.browser_js(
                "/odoo?debug=assets",
                "const fixture = " + json.dumps(fixture) + ";" + browser_code.read(),
                ready=(
                    "odoo.isReady === true && Boolean("
                    "odoo.__WOWL_DEBUG__.root.env.services.action.currentController)"
                ),
                login="admin",
                timeout=90,
            )
