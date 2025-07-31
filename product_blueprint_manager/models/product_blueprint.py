import base64
import logging

from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ProductBlueprint(models.Model):
    _name = "product.blueprint"
    _description = "Product Blueprint"

    name = fields.Char("Nombre del Plano", required=True)
    file = fields.Binary(
        "Archivo del Plano",
        required=True,
        attachment=True,
    )
    product_id = fields.Many2one(
        "product.template",
        string="Producto",
        required=True,
    )
    formula_ids = fields.One2many(
        "product.blueprint.formula", "blueprint_id", string="Fórmulas"
    )

    type_blueprint = fields.Selection(
        [
            ("manufacturing", "Orden de Fabricación"),
            ("purchase", "Orden de Compra"),
        ],
        string="Tipo de Plano",
        default="manufacturing",
        required=True,
        help=(
            "Determina si el plano se utiliza para una orden de fabricación o "
            "para una orden de compra."
        ),
    )

    attribute_filter_id = fields.Many2one(
        "product.attribute",
        string="Atributo Condicional",
        help=(
            "Atributo del producto que se debe usar para condicionar "
            "este plano. "
            "Si no se define, el plano siempre aplica."
        ),
    )

    attribute_value_ids = fields.Many2many(
        "product.attribute.value",
        string="Valores que activan este plano",
        domain="[('attribute_id', '=', attribute_filter_id)]",
        help=(
            "Valores del atributo que deben estar presentes para que "
            "este plano se aplique."
        ),
    )

    def _extract_svg_formulas(self):
        """Busca fórmulas en el SVG y las registra si son nuevas."""
        for blueprint in self:
            if not blueprint.file:
                _logger.warning(
                    f"[Blueprint] El plano '{blueprint.name}' "
                    "no tiene archivo SVG adjunto."
                )
                continue

            try:
                content = base64.b64decode(blueprint.file)
                tree = etree.fromstring(
                    content, parser=etree.XMLParser(remove_blank_text=True)
                )

                formula_nodes = tree.xpath("//*[@class='odoo-formula']")
                _logger.debug(
                    "[Blueprint] Se encontraron "
                    f"{len(formula_nodes)} nodos con clase 'odoo-formula'"
                )

                for node in formula_nodes:
                    formula_name = self._extract_formula_name_from_node(node)
                    element_id = node.get("id")

                    _logger.debug(
                        "[Blueprint] Nodo analizado - fórmula: "
                        f"'{formula_name}' ID nodo: '{element_id}'"
                    )
                    if not formula_name:
                        _logger.info(
                            "[Blueprint] Nodo omitido - no se pudo "
                            "determinar un nombre de fórmula"
                        )
                        continue
                    if not element_id:
                        _logger.warning(
                            "[Blueprint] Nodo sin ID detectado. "
                            f"Se omite fórmula '{formula_name}'"
                        )
                        continue

                    (
                        fill_color,
                        font_size,
                        font_family,
                    ) = self._extract_style_from_node_or_children(node)
                    _logger.debug(
                        "[Blueprint] Estilos detectados para '"
                        f"{formula_name}': "
                        f"fill={fill_color}, size={font_size}, "
                        f"font={font_family}"
                    )

                    existing = self.env["product.blueprint.formula.name"].search(
                        [
                            ("name", "=", formula_name),
                            ("svg_element_id", "=", element_id),
                            ("blueprint_id", "=", blueprint.id),
                        ],
                        limit=1,
                    )

                    if not existing:
                        _logger.info(
                            "[Blueprint] Creando nueva fórmula: '"
                            f"{formula_name}' "
                            f"con ID='{element_id}', "
                            f"color={fill_color}, tamaño={font_size}"
                        )
                        self.env["product.blueprint.formula.name"].create(
                            {
                                "name": formula_name,
                                "svg_element_id": element_id,
                                "blueprint_id": blueprint.id,
                                "fill_color": fill_color,
                                "font_size": font_size,
                            }
                        )
                    else:
                        _logger.debug(
                            "[Blueprint] Fórmula ya existente: '"
                            f"{formula_name}' "
                            f"con ID='{element_id}', se omite creación."
                        )

            except Exception as e:
                _logger.exception("[Blueprint] Error al procesar el archivo SVG")
                raise UserError(f"Error al procesar el archivo SVG: {e}") from e

    def _extract_formula_name_from_node(self, node):
        """
        Intenta determinar el nombre visual de la fórmula desde
        diferentes fuentes visibles,
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

        _logger.debug(
            "[Blueprint] No se encontró texto visible en el nodo "
            "ni en sus descendientes."
        )
        return None

    def _extract_style_from_node_or_children(self, node):
        """
        Busca atributos de estilo como fill, font-size y font-family en el nodo
        o sus hijos. Si no están definidos como atributos directos, intenta
        extraerlos del atributo 'style'.
        """

        def extract_from_style(style_str):
            style_map = {}
            for part in style_str.split(";"):
                if ":" in part:
                    key, val = part.split(":", 1)
                    style_map[key.strip()] = val.strip()
            return (
                style_map.get("fill"),
                style_map.get("font-size"),
                style_map.get("font-family"),
            )

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
                    fill_style, size_style, family_style = extract_from_style(
                        style_attr
                    )
                    fill = fill or fill_style
                    size = size or size_style
                    family = family or family_style

            fill = fill or child.get("fill")
            size = size or child.get("font-size")
            family = family or child.get("font-family")

        _logger.debug(
            f"[Blueprint] Estilos finales extraídos: fill={fill}, "
            f"font-size={size}, font-family={family}"
        )

        return (fill or "#000000", size or "12px", family or "Arial")

    @api.constrains("name", "product_id")
    def _check_unique_name_for_product(self):
        for rec in self:
            existing = self.env["product.blueprint"].search(
                [
                    ("name", "=", rec.name),
                    ("product_id", "=", rec.product_id.id),
                    ("id", "!=", rec.id),
                ]
            )
            if existing:
                _logger.warning(
                    "[Blueprint] Ya existe un plano con nombre '"
                    f"{rec.name}' "
                    f"para el producto ID {rec.product_id.id}"
                )
                raise ValidationError(
                    _("El nombre del plano debe ser único para cada producto.")
                )

    @api.model_create_multi
    def create(self, vals_list):
        blueprints = super().create(vals_list)
        for blueprint in blueprints:
            _logger.info(f"[Blueprint] Creado blueprint '{blueprint.name}'")
            _logger.debug(
                "[Blueprint] Intentando extraer fórmulas "
                "inmediatamente después de la creación..."
            )
            blueprint._extract_svg_formulas()
        return blueprints

    def write(self, vals):
        _logger.info(f"[Blueprint] Modificación del blueprint '{self.name}'")
        result = super().write(vals)
        _logger.debug(
            "[Blueprint] Intentando extraer fórmulas después de la " "modificación..."
        )
        self._extract_svg_formulas()
        return result
