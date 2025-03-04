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
        _logger.info(f"[Blueprint] Creando blueprint '{blueprint.name}'")

        # FORZAMOS la extracción de fórmulas
        _logger.info(f"[Blueprint] Intentando extraer fórmulas inmediatamente después de la creación...")
        blueprint._extract_svg_formulas()

        return blueprint

    def write(self, vals):
        """Extraer las fórmulas después de escribir en el plano."""
        _logger.info(f"[Blueprint] Modificando blueprint '{self.name}'")
        result = super(ProductBlueprint, self).write(vals)

        # FORZAMOS la extracción de fórmulas
        _logger.info(f"[Blueprint] Intentando extraer fórmulas después de la modificación...")
        self._extract_svg_formulas()

        return result

    def _extract_svg_formulas(self):
        """
        Extrae los trayectos <path> con class='odoo-formula' y las evalúa como fórmulas.
        """
        _logger.info(f"[Blueprint] Iniciando extracción de fórmulas para '{self.name}'")
        if not self.file:
            _logger.info(f"[Blueprint] No hay archivo SVG para el plano '{self.name}'.")
            return []

        try:
            # Eliminar registros previos de fórmulas asociadas al plano
            self.env["product.blueprint.formula.name"].search([("blueprint_id", "=", self.id)]).unlink()

            # Decodificar el archivo SVG desde base64
            svg_data = base64.b64decode(self.file)
            root = etree.fromstring(svg_data)

            # Obtener namespaces (importante para XML con `xmlns`)
            nsmap = {'svg': root.nsmap.get(None, 'http://www.w3.org/2000/svg')}
            _logger.info(f"[Blueprint] Namespace detectado: {nsmap}")

            formulas = []
            found_any = False

            # Buscar todos los elementos <path> con class="odoo-formula"
            paths = root.xpath(".//svg:path[contains(@class, 'odoo-formula')]", namespaces=nsmap)
            _logger.info(f"[Blueprint] Se encontraron {len(paths)} trayectos con 'odoo-formula' en el plano.")

            for path in paths:
                formula_text = path.get("aria-label", "").strip()  # Extraer la fórmula original
                path_id = path.get("id", "sin ID")  # Identificar el elemento
                #path_d = path.get("d", "").strip()  # Coordenadas del trayecto

                _logger.info(f"[Blueprint] Encontrado trayecto con ID={path_id} y fórmula='{formula_text}'")

                if formula_text:
                    found_any = True
                    self.env["product.blueprint.formula.name"].create({
                        "name": formula_text,
                        "blueprint_id": self.id
                    })
                    formulas.append({"id": path_id, "formula": formula_text})#, "path": path_d})

            if not found_any:
                _logger.info(f"[Blueprint] NO se encontraron fórmulas en el plano '{self.name}'.")
            else:
                _logger.info(f"[Blueprint] Se extrajeron {len(formulas)} fórmulas de '{self.name}'.")

            return formulas

        except Exception as e:
            _logger.info(f"[Blueprint] Error al procesar el archivo SVG: {e}")
            raise ValidationError(f"Error al procesar el archivo SVG: {str(e)}")
