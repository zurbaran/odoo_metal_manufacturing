import base64
import json
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

    def test_native_binary_component_download_in_browser(self):
        contents = b"BOE browser regression export\r\n"
        wizard = self.env["l10n.es.aeat.report.export_to_boe"].create(
            {
                "name": "modelo_303.txt",
                "data": base64.b64encode(contents),
                "state": "get",
            }
        )
        values = {
            "model": wizard._name,
            "id": wizard.id,
            "filename": wizard.name,
            "content": contents.decode(),
            "base64": base64.b64encode(contents).decode(),
            "size": str(len(contents)) + " b",
        }
        self.browser_js(
            "/odoo?debug=assets",
            "const fixture = "
            + json.dumps(values)
            + ";"
            + r"""
            (async () => {
                const { BinaryField } = odoo.loader.modules.get(
                    "@web/views/fields/binary/binary_field");
                const { downloadFile } = odoo.loader.modules.get(
                    "@web/core/network/download");
                const field = Object.create(BinaryField.prototype);
                field.props = {
                    name: "data", fileNameField: "name",
                    record: { resModel: fixture.model, resId: fixture.id,
                        data: { data: fixture.size, name: fixture.filename } },
                };
                const originalOpen = XMLHttpRequest.prototype.open;
                const originalSend = XMLHttpRequest.prototype.send;
                const responses = [];
                XMLHttpRequest.prototype.open = function(method, url, ...args) {
                    this.boeTest = { method, url: String(url) };
                    return originalOpen.call(this, method, url, ...args);
                };
                XMLHttpRequest.prototype.send = function(body) {
                    if (this.boeTest?.url.startsWith("/web/content")) {
                        this.addEventListener("load", () => {
                            responses.push({
                                ...this.boeTest, status: this.status,
                                blob: this.response,
                                header: this.getResponseHeader(
                                    "Content-Disposition") });
                        }, { once: true });
                    }
                    return originalSend.call(this, body);
                };
                try {
                    // The native handler must work for a bin_size placeholder
                    // as well as a base64 value, through the real HTTP endpoint.
                    await field.onFileDownload();
                    field.props.record.data.data = fixture.base64;
                    await field.onFileDownload();
                    // Verify the old helper too: a URL-only call does use GET.
                    await downloadFile(
                        `/web/content/${fixture.model}/${fixture.id}/data/` +
                        `${fixture.filename}?download=true`);
                    // Let all load event listeners finish after the XHR promise.
                    await new Promise(resolve => setTimeout(resolve, 0));
                    if (responses.length !== 3) {
                        throw new Error("Expected three binary requests");
                    }
                    if (responses[0].method !== "POST" ||
                        responses[1].method !== "POST" ||
                        responses[2].method !== "GET") {
                        throw new Error("Unexpected download methods");
                    }
                    for (const response of responses) {
                        if (response.status !== 200) {
                            throw new Error("HTTP status " + response.status);
                        }
                        if (await response.blob.text() !== fixture.content) {
                            throw new Error("Wrong BOE bytes");
                        }
                        if (!response.header.includes(fixture.filename)) {
                            throw new Error("Wrong filename");
                        }
                    }
                    console.log("test successful");
                } finally {
                    XMLHttpRequest.prototype.open = originalOpen;
                    XMLHttpRequest.prototype.send = originalSend;
                }
            })().catch(error => console.error(error));
            """,
            ready="odoo.isReady === true",
            login="admin",
            timeout=60,
        )
