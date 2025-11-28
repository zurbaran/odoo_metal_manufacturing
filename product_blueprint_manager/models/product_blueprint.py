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

    blueprint_condition_ids = fields.One2many(
        "product.blueprint.condition",
        "blueprint_id",
        string="Conditions",
    )

    # -------------------------------------------------------------------------
    # Funciones de higiene / limpieza del SVG
    # -------------------------------------------------------------------------

    def _sanitize_svg_root(self, root, blueprint_name=None):
        """Aplica reglas de limpieza e higiene al nodo raíz del SVG.

        - Elimina estilos globales problemáticos (image/text/shape-rendering)
          que afectan a la nitidez del render en PNG/PDF.
        - Está pensada para ser idempotente (se puede llamar varias veces sin
          que se vaya “comiendo” más cosas cada vez).
        """
        if root is None:
            return

        # Nombre solo para logging; no altera la lógica
        bp_label = blueprint_name or root.get("id") or "SVG sin nombre"

        style_attr = root.get("style")
        if style_attr:
            parts_in = style_attr.split(";")
            parts_out = []
            removed = []
            for p in parts_in:
                p_stripped = p.strip()
                if not p_stripped:
                    continue
                key = p_stripped.split(":", 1)[0].strip().lower()
                # Quitamos únicamente estos hints globales de renderizado
                if key in (
                    "image-rendering",
                    "text-rendering",
                    "shape-rendering",
                ):
                    removed.append(p_stripped)
                    continue
                parts_out.append(p_stripped)

            if removed:
                _logger.debug(
                    "[Blueprint] Limpieza de estilos globales en '%s': %s",
                    bp_label,
                    ", ".join(removed),
                )

            if parts_out:
                root.set("style", ";".join(parts_out))
            else:
                # Si no queda nada útil, eliminamos el atributo style del <svg>
                root.attrib.pop("style", None)

        # Aviso si el namespace principal no es el estándar SVG.
        # No lo modificamos porque puede venir de herramientas externas.
        ns = root.nsmap.get(None)
        if ns and ns != "http://www.w3.org/2000/svg":
            _logger.warning(
                "[Blueprint] SVG '%s' con namespace no estándar: %s",
                bp_label,
                ns,
            )

    def _sanitize_svg_content(self, file_b64, blueprint_name=None):
        """Recibe un SVG en base64 y devuelve una versión higienizada.

        Flujo:
        - Decodifica el contenido base64.
        - Aplica _sanitize_svg_root al nodo <svg>.
        - Re-serializa el SVG y lo vuelve a codificar en base64.

        Si algo falla, devuelve el contenido original sin modificar.
        """
        if not file_b64:
            return file_b64

        try:
            raw = base64.b64decode(file_b64)
        except Exception:
            _logger.exception(
                "[Blueprint] No se pudo decodificar el archivo SVG de '%s' "
                "para higienizarlo.",
                blueprint_name or "desconocido",
            )
            return file_b64

        try:
            parser = etree.XMLParser(remove_blank_text=True)
            root = etree.fromstring(raw, parser=parser)
        except Exception:
            _logger.exception(
                "[Blueprint] No se pudo parsear el SVG de '%s' para "
                "higienizarlo. Se almacena sin cambios.",
                blueprint_name or "desconocido",
            )
            return file_b64

        # Limpieza ligera del nodo raíz (estilos globales, etc.)
        self._sanitize_svg_root(root, blueprint_name=blueprint_name)

        sanitized_bytes = etree.tostring(
            root,
            pretty_print=True,
            encoding="utf-8",
        )
        sanitized_b64 = base64.b64encode(sanitized_bytes)

        # Respetar el tipo original (str/bytes) para no sorprender al ORM
        if isinstance(file_b64, str):
            return sanitized_b64.decode()
        return sanitized_b64

    # -------------------------------------------------------------------------
    # Detección y registro de fórmulas en el SVG
    # -------------------------------------------------------------------------

    def _extract_svg_formulas(self):
        """Busca fórmulas en el SVG y las registra si son nuevas.

        A partir del archivo SVG asociado al blueprint:
        - Aplica una limpieza ligera del nodo raíz (higiene base).
        - Localiza nodos con class='odoo-formula'.
        - Extrae nombre visible, id de nodo y estilos básicos (fill/font-size).
        - Crea (si no existen) los registros product.blueprint.formula.name.
        """
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

                # Aplicamos la misma higiene de nodo raíz que usamos al guardar.
                # Esto hace que la detección de fórmulas vea el mismo SVG
                # “sano” que luego usará la evaluación.
                self._sanitize_svg_root(tree, blueprint_name=blueprint.name)

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
        Determina el nombre visual de la fórmula desde el nodo SVG.

        Revisa diferentes fuentes visibles (texto directo, aria-*, descendientes)
        y limpia las llaves '{{ }}' para obtener el nombre de variable.
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

        Prioriza:
          - Atributos directos del nodo.
          - Atributo 'style' del nodo.
          - Atributos/estilos de los descendientes.

        Si no encuentra nada, devuelve valores razonables por defecto
        (negro, 12px, Arial) para garantizar que el texto sea legible.
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

    # -------------------------------------------------------------------------
    # Restricciones y hooks de create/write
    # -------------------------------------------------------------------------

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
        """
        Crea blueprints higienizando previamente el SVG subido.

        Antes de llamar a super().create():
          - Para cada vals que incluya 'file', se limpia el SVG en memoria y
            se deja listo para extracción de fórmulas y evaluación.

        Después:
          - Se ejecuta la extracción de fórmulas para cada blueprint creado.
        """
        for vals in vals_list:
            if vals.get("file"):
                vals["file"] = self._sanitize_svg_content(
                    vals["file"],
                    blueprint_name=vals.get("name"),
                )

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
        """
        Actualiza blueprints higienizando el SVG si se ha modificado.

        Si en vals viene una nueva versión de 'file', se aplica la misma
        higiene que en create() antes de guardar.
        A continuación se recalculan las fórmulas del plano.
        """
        if vals.get("file"):
            vals["file"] = self._sanitize_svg_content(
                vals["file"],
                blueprint_name=self.name,
            )

        _logger.info(f"[Blueprint] Modificación del blueprint '{self.name}'")
        result = super().write(vals)
        _logger.debug(
            "[Blueprint] Intentando extraer fórmulas después de la " "modificación..."
        )
        self._extract_svg_formulas()
        return result
