from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
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

    def _extract_svg_formulas(self):
        """Busca fórmulas en el SVG y las registra si son nuevas."""
        for blueprint in self:
            if not blueprint.file:
                _logger.warning(f"[Blueprint] El plano '{blueprint.name}' no tiene archivo SVG adjunto.")
                continue

            try:
                content = base64.b64decode(blueprint.file)
                tree = etree.fromstring(content, parser=etree.XMLParser(remove_blank_text=True))

                formula_nodes = tree.xpath("//*[@class='odoo-formula']")
                _logger.info(f"[Blueprint] Se encontraron {len(formula_nodes)} nodos con clase 'odoo-formula'")

                for node in formula_nodes:
                    formula_name = self._extract_formula_name_from_node(node)
                    _logger.info(f"[Blueprint] Nodo analizado - fórmula: '{formula_name}'")
                    if not formula_name:
                        _logger.warning("[Blueprint] Nodo omitido - no se pudo determinar un nombre de fórmula")
                        continue

                    fill_color, font_size, font_family = self._extract_style_from_node_or_children(node)
                    _logger.info(f"[Blueprint] Estilos detectados para '{formula_name}': fill={fill_color}, size={font_size}, font={font_family}")

                    existing = self.env["product.blueprint.formula.name"].search([
                        ("name", "=", formula_name),
                        ("blueprint_id", "=", blueprint.id),
                    ], limit=1)

                    if not existing:
                        _logger.info(f"[Blueprint] Creando nueva fórmula: '{formula_name}' con color={fill_color}, tamaño={font_size}")
                        self.env["product.blueprint.formula.name"].create({
                            "name": formula_name,
                            "blueprint_id": blueprint.id,
                            "fill_color": fill_color,
                            "font_size": font_size,
                        })
                    else:
                        _logger.info(f"[Blueprint] Fórmula ya existente: '{formula_name}', se omite creación.")

            except Exception as e:
                _logger.warning("[Blueprint] Error al procesar el archivo SVG: %s", e)
                raise UserError("Error al procesar el archivo SVG: %s" % e)

    def _extract_formula_name_from_node(self, node):
        """
        Intenta determinar el nombre visual de la fórmula desde diferentes fuentes visibles,
        incluyendo nodos anidados como <tspan>.
        """
        candidates = [
            node.text,
            node.get("aria-label"),
            node.get("aria-text"),
        ]

        for child in node.iterdescendants():
            if child.text:
                candidates.append(child.text)
            if child.get("aria-label"):
                candidates.append(child.get("aria-label"))
            if child.get("aria-text"):
                candidates.append(child.get("aria-text"))

        for candidate in candidates:
            if candidate and candidate.strip():
                cleaned = candidate.replace("{{", "").replace("}}", "").strip()
                _logger.debug(f"[Blueprint] Texto de fórmula encontrado: '{cleaned}'")
                return cleaned

        _logger.debug("[Blueprint] No se encontró texto visible en el nodo ni en sus descendientes.")
        return None

    def _extract_style_from_node_or_children(self, node):
        """
        Busca atributos de estilo como fill, font-size y font-family en el nodo o sus hijos.
        Si no están definidos como atributos directos, intenta extraerlos del atributo 'style'.
        """
        def extract_from_style(style_str):
            style_map = {}
            for part in style_str.split(';'):
                if ':' in part:
                    key, val = part.split(':', 1)
                    style_map[key.strip()] = val.strip()
            return style_map.get('fill'), style_map.get('font-size'), style_map.get('font-family')

        fill = node.get("fill")
        size = node.get("font-size")
        family = node.get("font-family")

        if not fill or not size or not family:
            style_attr = node.get("style")
            if style_attr:
                fill_style, size_style, family_style = extract_from_style(style_attr)
                fill = fill or fill_style
                size = size or size_style
                family = family or family_style

        for child in node.iterdescendants():
            if not fill or not size or not family:
                style_attr = child.get("style")
                if style_attr:
                    fill_style, size_style, family_style = extract_from_style(style_attr)
                    fill = fill or fill_style
                    size = size or size_style
                    family = family or family_style

            fill = fill or child.get("fill")
            size = size or child.get("font-size")
            family = family or child.get("font-family")

        _logger.debug(f"[Blueprint] Estilos finales extraídos: fill={fill}, font-size={size}, font-family={family}")

        return (
            fill or "#000000",
            size or "12px",
            family or "Arial"
        )

    @api.constrains("name", "product_id")
    def _check_unique_name_for_product(self):
        for rec in self:
            existing = self.env["product.blueprint"].search([
                ("name", "=", rec.name),
                ("product_id", "=", rec.product_id.id),
                ("id", "!=", rec.id)
            ])
            if existing:
                _logger.warning(f"[Blueprint] Ya existe un plano con nombre '{rec.name}' para el producto ID {rec.product_id.id}")
                raise ValidationError("El nombre del plano debe ser único para cada producto.")

    @api.model_create_multi
    def create(self, vals):
        blueprint = super(ProductBlueprint, self).create(vals)
        _logger.info(f"[Blueprint] Creando blueprint '{blueprint.name}'")
        _logger.info(f"[Blueprint] Intentando extraer fórmulas inmediatamente después de la creación...")
        blueprint._extract_svg_formulas()
        return blueprint

    def write(self, vals):
        _logger.info(f"[Blueprint] Modificando blueprint '{self.name}'")
        result = super(ProductBlueprint, self).write(vals)
        _logger.info(f"[Blueprint] Intentando extraer fórmulas después de la modificación...")
        self._extract_svg_formulas()
        return result
