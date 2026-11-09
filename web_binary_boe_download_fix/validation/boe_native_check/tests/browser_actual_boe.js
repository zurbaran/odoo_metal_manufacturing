/* global odoo */
(async () => {
            const wait = async (selector) => {
                for (let i = 0; i < 500; i++) {
                    const el = document.querySelector(selector);
                    if (el) return el;
                    await new Promise(resolve => setTimeout(resolve, 20));
                }
                throw new Error('Missing UI element: ' + selector);
            };
            const originalOpen = XMLHttpRequest.prototype.open;
            const originalSend = XMLHttpRequest.prototype.send;
            let resolveDownload;
            const received = new Promise(resolve => resolveDownload = resolve);
            XMLHttpRequest.prototype.open = function(method, url, ...args) {
                this.boeRequest = { method, url: String(url) };
                return originalOpen.call(this, method, url, ...args);
            };
            XMLHttpRequest.prototype.send = function(body) {
                if (this.boeRequest?.url.startsWith('/web/content')) {
                    const data = body instanceof FormData ? Object.fromEntries(body.entries()) : null;
                    this.addEventListener('load', async () => {
                        const bytes = new Uint8Array(await this.response.arrayBuffer());
                        const encoded = btoa(Array.from(bytes, b => String.fromCharCode(b)).join(''));
                        resolveDownload({ ...this.boeRequest, data, encoded,
                            status: this.status, header: this.getResponseHeader('Content-Disposition') });
                    }, { once: true });
                }
                return originalSend.call(this, body);
            };
            try {
                await odoo.__WOWL_DEBUG__.root.env.services.action.doAction(fixture.action);
                const exportButton = await wait('button[name="action_get_file"]');
                exportButton.click();
                const link = await wait('.o_field_widget[name="data"] a.o_form_uri');
                if (!link.textContent.includes(fixture.filename)) {
                    throw new Error('The real wizard did not load its filename: ' + link.textContent);
                }
                link.click();
                const result = await Promise.race([received, new Promise((_, reject) =>
                    setTimeout(() => reject(new Error('No actual download request')), 15000))]);
                if (result.method !== 'POST' || result.status !== 200) {
                    throw new Error('Native download failed: ' + JSON.stringify(result));
                }
                if (result.data.model !== fixture.model || result.data.id !== String(fixture.id) ||
                    result.data.field !== 'data' || result.data.filename !== fixture.filename) {
                    throw new Error('Wrong native request parameters: ' + JSON.stringify(result.data));
                }
                if (result.encoded !== fixture.expected) throw new Error('Actual BOE bytes differ');
                if (!result.header.includes(fixture.filename)) throw new Error('Wrong response filename');
                console.log('test successful');
            } finally {
                XMLHttpRequest.prototype.open = originalOpen;
                XMLHttpRequest.prototype.send = originalSend;
            }
        })().catch(error => console.error(error));
