from odoo import models
import base64
import io
from PyPDF2 import PdfReader, PdfWriter
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_quotation_send(self):
        """Override the action_quotation_send method to attach blueprint documents to the quotation."""
        self.ensure_one()
        _logger.info(f"[Blueprint] Enviando presupuesto: {self.name}")
        blueprint_attachments = []
        for line in self.order_line:
            _logger.info(f"[Blueprint] Procesando línea de pedido: {line.id} para adjuntar blueprints")
            _logger.info(f"[Blueprint] Variables pasadas para la evaluación del blueprint '{blueprint.name}' en modo 'final': {variables}")
            attachments = line.generate_blueprint_document()
            if attachments:
                blueprint_attachments.extend(attachments)
                _logger.info(f"[Blueprint] Adjuntos añadidos: {len(attachments)}")
            else:
                _logger.info(f"[Blueprint] No se encontraron adjuntos para la linea: {line.id}")

        main_report_pdf = io.BytesIO(self.env.ref('sale.action_report_saleorder')._render_qweb_pdf(self.id)[0])
        writer = PdfWriter()
        try:
            writer.append(PdfReader(main_report_pdf))
        except Exception as e:
            _logger.info(f"[Blueprint] Error al leer el PDF principal: {e}")
            return super().action_quotation_send() #Si falla el pdf principal enviamos el original

        for attachment_id in blueprint_attachments:
            try:
                attachment = self.env['ir.attachment'].browse(attachment_id)
                if attachment.datas:
                    blueprint_pdf = io.BytesIO(base64.b64decode(attachment.datas))
                    writer.append(PdfReader(blueprint_pdf))
            except Exception as e:
                _logger.info(f"[Blueprint] Error al procesar un adjunto: {e}")

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
        _logger.info(f"[Blueprint] Archivo combinado creado: {final_attachment.name}")
        return super().action_quotation_send()
    
    # Método action_confirm incompleto, se removió del código original.
