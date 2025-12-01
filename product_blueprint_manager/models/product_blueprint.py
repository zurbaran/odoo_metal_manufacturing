"""Módulo de gestión de planos de producto (SVG) con fórmulas dinámicas.

Este modelo se encarga de:
- Almacenar los planos SVG asociados a una plantilla de producto.
- Higienizar el contenido SVG (estilos globales problemáticos, namespaces).
- Detectar automáticamente las fórmulas (class="odoo-formula") presentes en el SVG.
- Registrar etiquetas de fórmula y estilos visuales en modelos auxiliares.
- Controlar unicidad de nombre de plano por producto.
"""

import base64
import logging

from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ProductBlueprint(models.Model):
    _name = "product.blueprint"
    _description = "Product Blueprint"

    # Nombre legible del plano (por ejemplo “Plano Vista Frontal”).
    # Debe ser único por producto
    # (se valida más abajo en _check_unique_name_for_product).
    name = fields.Char("Nombre del Plano", required=True)

    # Archivo SVG bruto del plano.
    # - Se almacena en base64.
    # - Se higieniza antes de guardar (ver _sanitize_svg_content).
    file = fields.Binary(
        "Archivo del Plano",
        required=True,
        attachment=True,
    )

    # Producto (plantilla) al que está asociado este plano.
    # Un producto puede tener varios planos (vistas, tipos, etc.).
    product_id = fields.Many2one(
        "product.template",
        string="Producto",
        required=True,
    )

    # Fórmulas asociadas a este plano.
    # Cada fórmula está ligada a una etiqueta detectada en el SVG
    # (modelo product.blueprint.formula + product.blueprint.formula.name).
    formula_ids = fields.One2many(
        "product.blueprint.formula", "blueprint_id", string="Fórmulas"
    )

    # Tipo de plano: Fabricación o Compra.
    # Esto permite reutilizar el mismo producto para distintos contextos
    # (plano de fábrica vs plano para proveedor).
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

    # Condiciones de atributos que deben cumplirse para que este plano se aplique.
    # Por ejemplo:
    # - Vidrio = Transparente
    # - Color = Blanco
    # Si alguna condición no se cumple, el plano se ignora para esa línea de venta.
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
        # Si no hay nodo raíz, no se puede hacer nada.
        if root is None:
            return

        # Nombre solo para logging; no altera la lógica.
        # Si no se pasa blueprint_name, se intenta usar el id del nodo <svg>.
        bp_label = blueprint_name or root.get("id") or "SVG sin nombre"

        # Limpieza de estilos globales en el nodo raíz <svg>.
        # Algunos programas de diseño exportan pistas de renderizado que
        # degradan la nitidez (sobre todo al convertir a PNG/PDF).
        style_attr = root.get("style")
        if style_attr:
            parts_in = style_attr.split(";")
            parts_out = []
            removed = []
            for p in parts_in:
                p_stripped = p.strip()
                if not p_stripped:
                    # Saltar entradas vacías generadas por ";;" o similares.
                    continue
                # Tomamos la parte izquierda antes de ":" (nombre de propiedad CSS).
                key = p_stripped.split(":", 1)[0].strip().lower()
                # Quitamos únicamente estos hints globales de renderizado
                # para no interferir con otros estilos válidos.
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
                # Si todavía hay estilos útiles, los dejamos.
                root.set("style", ";".join(parts_out))
            else:
                # Si no queda nada útil, eliminamos el atributo style del <svg>
                root.attrib.pop("style", None)

        # Aviso si el namespace principal no es el estándar SVG.
        # No lo modificamos porque puede venir de herramientas externas
        # que dependan de ese namespace, pero dejamos constancia en el log.
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
        # Si no hay archivo, no hay nada que limpiar.
        if not file_b64:
            return file_b64

        try:
            # Decodificar base64 → bytes XML
            raw = base64.b64decode(file_b64)
        except Exception:
            # Si no se puede decodificar, registramos el error y devolvemos
            # el contenido original tal cual para no romper el flujo.
            _logger.exception(
                "[Blueprint] No se pudo decodificar el archivo SVG de '%s' "
                "para higienizarlo.",
                blueprint_name or "desconocido",
            )
            return file_b64

        try:
            # Parser de XML con eliminación de textos en blanco redundantes
            # para evitar nodos de texto “ruido” que dificulten el análisis.
            parser = etree.XMLParser(remove_blank_text=True)
            root = etree.fromstring(raw, parser=parser)
        except Exception:
            # Si el SVG no es parseable, registramos el error y seguimos
            # con el contenido original.
            _logger.exception(
                "[Blueprint] No se pudo parsear el SVG de '%s' para "
                "higienizarlo. Se almacena sin cambios.",
                blueprint_name or "desconocido",
            )
            return file_b64

        # Limpieza ligera del nodo raíz (estilos globales, etc.).
        self._sanitize_svg_root(root, blueprint_name=blueprint_name)

        # Serializamos de nuevo el SVG higienizado.
        sanitized_bytes = etree.tostring(
            root,
            pretty_print=True,
            encoding="utf-8",
        )
        sanitized_b64 = base64.b64encode(sanitized_bytes)

        # Respetar el tipo original (str/bytes) para no sorprender al ORM.
        # Algunos campos binarios pueden llegar como str, otros como bytes.
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
        # Procesar cada blueprint del recordset.
        for blueprint in self:
            if not blueprint.file:
                # Caso en el que el registro existe pero todavía no tiene archivo.
                _logger.warning(
                    f"[Blueprint] El plano '{blueprint.name}' "
                    "no tiene archivo SVG adjunto."
                )
                continue

            try:
                # Decodificar SVG guardado en base64.
                content = base64.b64decode(blueprint.file)
                # Cargar árbol XML del SVG (sin espacios en blanco molestos).
                tree = etree.fromstring(
                    content, parser=etree.XMLParser(remove_blank_text=True)
                )

                # Aplicamos la misma higiene de nodo raíz que usamos al guardar.
                # Esto hace que la detección de fórmulas vea el mismo SVG
                # “sano” que luego usará la evaluación.
                self._sanitize_svg_root(tree, blueprint_name=blueprint.name)

                # Localizar todos los nodos que tengan exactamente class="odoo-formula".
                # Si se necesitan clases múltiples, se podría cambiar a contains().
                formula_nodes = tree.xpath("//*[@class='odoo-formula']")
                _logger.debug(
                    "[Blueprint] Se encontraron "
                    f"{len(formula_nodes)} nodos con clase 'odoo-formula'"
                )

                # Recorrer cada nodo candidato a fórmula.
                for node in formula_nodes:
                    # Nombre lógico/visible de la fórmula, extraído del nodo.
                    formula_name = self._extract_formula_name_from_node(node)
                    # ID del elemento SVG (clave para que sea único).
                    element_id = node.get("id")

                    _logger.debug(
                        "[Blueprint] Nodo analizado - fórmula: "
                        f"'{formula_name}' ID nodo: '{element_id}'"
                    )
                    # Sin nombre de fórmula no se puede mapear
                    #  contra atributos → se omite.
                    if not formula_name:
                        _logger.info(
                            "[Blueprint] Nodo omitido - no se pudo "
                            "determinar un nombre de fórmula"
                        )
                        continue
                    # Sin ID de nodo no se puede garantizar unicidad dentro del SVG.
                    if not element_id:
                        _logger.warning(
                            "[Blueprint] Nodo sin ID detectado. "
                            f"Se omite fórmula '{formula_name}'"
                        )
                        continue

                    # Extraer estilo visual del nodo (o de sus hijos).
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

                    # Comprobar si ya existe un registro de fórmula con ese
                    # nombre + id de nodo + blueprint, para no duplicar.
                    existing = self.env["product.blueprint.formula.name"].search(
                        [
                            ("name", "=", formula_name),
                            ("svg_element_id", "=", element_id),
                            ("blueprint_id", "=", blueprint.id),
                        ],
                        limit=1,
                    )

                    if not existing:
                        # Crear nueva etiqueta de fórmula reutilizable en el plano.
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
                        # Si ya existe, se deja tal cual; esto permite reprocesar
                        # el SVG sin crear registros duplicados.
                        _logger.debug(
                            "[Blueprint] Fórmula ya existente: '"
                            f"{formula_name}' "
                            f"con ID='{element_id}', se omite creación."
                        )

            except Exception as e:
                # Cualquier error en el proceso de análisis del SVG se escapa
                # como UserError para mostrar un mensaje amigable al usuario.
                _logger.exception("[Blueprint] Error al procesar el archivo SVG")
                raise UserError(f"Error al procesar el archivo SVG: {e}") from e

    def _extract_formula_name_from_node(self, node):
        """
        Determina el nombre visual de la fórmula desde el nodo SVG.

        Revisa diferentes fuentes visibles (texto directo, aria-*, descendientes)
        y limpia las llaves '{{ }}' para obtener el nombre de variable.
        """
        # Candidatos a texto significativo:
        # - texto directo del nodo,
        # - atributos accesibles (aria-label, aria-text),
        # - textos de descendientes.
        candidates = [
            node.text,
            node.get("aria-label"),
            node.get("aria-text"),
        ]

        # Incluir texto de nodos hijos por si el editor anida <tspan> u otros.
        for child in node.iterdescendants():
            if child.text:
                candidates.append(child.text)
            if child.get("aria-label"):
                candidates.append(child.get("aria-label"))
            if child.get("aria-text"):
                candidates.append(child.get("aria-text"))

        # Nos quedamos con el primer texto no vacío, limpiando "{{ }}" si existen.
        for candidate in candidates:
            if candidate and candidate.strip():
                cleaned = candidate.replace("{{", "").replace("}}", "").strip()
                _logger.debug(f"[Blueprint] Texto de fórmula encontrado: '{cleaned}'")
                return cleaned

        # Si no se ha encontrado nada, se devuelve None y el nodo se ignora.
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
            """Convierte un string CSS en un pequeño dict de propiedades.

            Ejemplo:
                'fill:#000;font-size:12px' → {'fill': '#000', 'font-size': '12px'}
            """
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

        # Intentar primero con atributos directos en el nodo.
        fill = node.get("fill")
        size = node.get("font-size")
        family = node.get("font-family")

        # Si falta alguno, intentar extraerlo del atributo style.
        if not fill or not size or not family:
            style_attr = node.get("style")
            if style_attr:
                fill_style, size_style, family_style = extract_from_style(style_attr)
                fill = fill or fill_style
                size = size or size_style
                family = family or family_style

        # Si todavía faltan datos, mirar en los descendientes (por ejemplo,
        # cuando el texto está dentro de <tspan> o nodos anidados con su propio estilo).
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

            # Como último recurso, mirar atributos directos del descendiente.
            fill = fill or child.get("fill")
            size = size or child.get("font-size")
            family = family or child.get("font-family")

        _logger.debug(
            f"[Blueprint] Estilos finales extraídos: fill={fill}, "
            f"font-size={size}, font-family={family}"
        )

        # Devolver siempre valores definidos para evitar problemas visuales:
        # - fill: color del texto (negro por defecto).
        # - font-size: tamaño base de texto (12px).
        # - font-family: tipografía de fallback (Arial).
        return (fill or "#000000", size or "12px", family or "Arial")

    # -------------------------------------------------------------------------
    # Restricciones y hooks de create/write
    # -------------------------------------------------------------------------

    @api.constrains("name", "product_id")
    def _check_unique_name_for_product(self):
        """Garantiza que para un mismo producto no se repitan nombres de plano."""
        for rec in self:
            # Buscar otros planos del mismo producto con el mismo nombre.
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
                # Lanzar error de validación para bloquear el guardado.
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
        # Preprocesar todos los registros en el batch.
        for vals in vals_list:
            if vals.get("file"):
                # Higienizar SVG antes de guardarlo en base de datos.
                vals["file"] = self._sanitize_svg_content(
                    vals["file"],
                    blueprint_name=vals.get("name"),
                )

        # Crear registros normalmente.
        blueprints = super().create(vals_list)
        # Y, una vez creados, intentar extraer las fórmulas automáticamente.
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
        # Si se cambia el archivo SVG, lo higienizamos antes de guardar.
        if vals.get("file"):
            vals["file"] = self._sanitize_svg_content(
                vals["file"],
                blueprint_name=self.name,
            )

        _logger.info(f"[Blueprint] Modificación del blueprint '{self.name}'")
        # Guardar cambios en el registro (o registros).
        result = super().write(vals)
        _logger.debug(
            "[Blueprint] Intentando extraer fórmulas después de la " "modificación..."
        )
        # Recalcular fórmulas a partir del nuevo contenido del SVG.
        self._extract_svg_formulas()
        return result
