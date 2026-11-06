import base64
from urllib.parse import urlencode

from odoo.tests.common import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestNativeBoeDownload(HttpCase):
    def test_native_content_route_downloads_boe_bytes(self):
        contents = b"BOE regression export\r\n"
        wizard = self.env["l10n.es.aeat.report.export_to_boe"].create(
            {
                "name": "modelo_303.txt",
                "data": base64.b64encode(contents),
                "state": "get",
            }
        )
        self.authenticate("admin", "admin")
        response = self.url_open(
            "/web/content?"
            + urlencode(
                {
                    "model": wizard._name,
                    "id": wizard.id,
                    "field": "data",
                    "filename": wizard.name,
                    "download": "true",
                }
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, contents)
        self.assertIn("modelo_303.txt", response.headers["Content-Disposition"])
