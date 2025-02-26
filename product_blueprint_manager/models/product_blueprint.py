from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import base64
import logging
from lxml import etree

_logger = logging.getLogger(__name__)

class ProductBlueprint(models.Model):
    _name = "product.blueprint"
    _description = "Product Blueprint"

    name = fields.Char("Nombre del Plano", required=True)
    file = fields.Binary("Archivo del Plano", required=True, attachment=True)
    product_id = fields.Many2one("product.template", string="Producto", required=True)
    formula_ids = fields.One2many("product.blueprint.formula", "blueprint_id", string="Fórmulas")

    @api.constrains("name", "product_id")
    def _check_unique_name_for_product(self):
        for rec in self:
            existing = self.env["product.blueprint"].search([
                ("name", "=", rec.name),
                ("product_id", "=", rec.product_id.id),
                ("id", "!=", rec.id)
            ])
            if existing:
                raise ValidationError("El nombre del plano debe ser único para cada producto.")

    @api.model_create_multi
    def create(self, vals):
        """Crear el plano y extraer las etiquetas una vez creado."""
        blueprint = super(ProductBlueprint, self).create(vals)
        if "file" in vals and vals["file"]:
            blueprint._extract_svg_formulas()
        return blueprint

    def write(self, vals):
        """Extraer las fórmulas después de escribir en el plano."""
        result = super(ProductBlueprint, self).write(vals)
        if "file" in vals and vals["file"]:
            self._extract_svg_formulas()
        return result

    def _extract_svg_formulas(self):
        """Extrae etiquetas <text> con class='odoo-formula' del archivo SVG, manejando espacios de nombres."""
        if not self.file:
            _logger.warning(f"[Blueprint] No hay archivo SVG para el plano '{self.name}'.")
            return []

        try:
            # Eliminar registros previos asociados al plano
            self.env["product.blueprint.formula.name"].search([("blueprint_id", "=", self.id)]).unlink()

            # Decodificar y analizar el archivo SVG
            svg_data = base64.b64decode(self.file)
            root = etree.fromstring(svg_data)

            # Detectar espacio de nombres (namespace)
            nsmap = {'svg': root.nsmap.get(None, 'http://www.w3.org/2000/svg')}
            _logger.debug(f"[Blueprint] Espacios de nombres detectados: {nsmap}")

            # Buscar etiquetas <text> con la clase 'odoo-formula' usando el namespace
            formulas = []
            for text_element in root.xpath("//svg:text[contains(@class, 'odoo-formula')]", namespaces=nsmap):
                formula_name = "".join(text_element.xpath(".//text()", namespaces=nsmap)).strip()

                if formula_name:
                    _logger.info(f"[Blueprint] Etiqueta detectada: '{formula_name}' en {etree.tostring(text_element).decode()}")
                    # Crear el registro con el ID válido del plano
                    self.env["product.blueprint.formula.name"].create({
                        "name": formula_name,
                        "blueprint_id": self.id
                    })
                    formulas.append(formula_name)
                else:
                    _logger.warning(f"[Blueprint] Etiqueta sin contenido en: {etree.tostring(text_element).decode()}")

            _logger.info(f"[Blueprint] Se encontraron {len(formulas)} etiquetas 'odoo-formula' para el plano '{self.name}'.")
            return formulas

        except Exception as e:
            _logger.exception(f"[Blueprint] Error al procesar el archivo SVG: {e}")
            raise ValidationError(f"Error al procesar el archivo SVG: {str(e)}")
