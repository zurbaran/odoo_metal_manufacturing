from odoo import models
import base64
import io
from PyPDF2 import PdfReader, PdfWriter

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_quotation_send(self):
        self.ensure_one()
        blueprint_attachments = sum((line.generate_blueprint_document() for line in self.order_line), [])
        
        main_report_pdf = io.BytesIO(self.env.ref('sale.action_report_saleorder')._render_qweb_pdf(self.id)[0])
        writer = PdfWriter()
        writer.append(PdfReader(main_report_pdf))

        for attachment_id in blueprint_attachments:
            attachment = self.env['ir.attachment'].browse(attachment_id)
            if attachment.datas:
                blueprint_pdf = io.BytesIO(base64.b64decode(attachment.datas))
                writer.append(PdfReader(blueprint_pdf))
        
        combined_pdf = io.BytesIO()
        writer.write(combined_pdf)
        combined_pdf.seek(0)

        final_attachment = self.env['ir.attachment'].create({
            'name': f"{self.name}_with_blueprints.pdf",
            'type': 'binary',
            'datas': base64.b64encode(combined_pdf.read()),
            'res_model': 'sale.order',
            'res_id': self.id,
        })
        return super().action_quotation_send()
