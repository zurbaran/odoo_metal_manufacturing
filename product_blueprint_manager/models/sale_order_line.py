import ast
import base64
import logging
import math

import cairosvg  # pyright: ignore[reportMissingImports]
from lxml import etree
from markupsafe import Markup

from odoo import _, api, fields, models  # pyright: ignore[reportMissingImports]
from odoo.exceptions import ValidationError  # pyright: ignore[reportMissingImports]

# ---------------------------------------------------------------------------
# Extensión de `sale.order.line` para la gestión de planos SVG con fórmulas.
#
# Funciones principales de este módulo:
# - Capturar atributos (estándar, no_variant y custom) de la línea de venta
#   y proyectarlos como variables numéricas para las fórmulas de plano.
# - Evaluar expresiones matemáticas de forma controlada y segura, usando sólo
#   variables y funciones permitidas (módulo `math`).
# - Procesar el SVG del plano, localizar los nodos con class "odoo-formula"
#   y sustituirlos por nodos <text> "limpios" con los valores evaluados.
# - Generar adjuntos SVG evaluados y PNG (vía CairoSVG) para su inclusión en
#   reportes QWeb (presupuesto, plano de compra, MO, etc.).
# - Exponer utilidades para mostrar, en los reportes, las variables usadas y
#   un resumen de los atributos seleccionados en la línea.
# ---------------------------------------------------------------------------

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    # Campo técnico para guardar, en texto, el dict de variables que se usan
    # en las fórmulas del plano. Se recalcula cada vez que cambian los atributos.
    blueprint_custom_values = fields.Char(
        compute="_compute_blueprint_custom_values",
    )

    # Último adjunto SVG generado y evaluado para la línea (no es necesario
    # para el flujo, pero puede ser útil para inspección/debug).
    blueprint_attachment_id = fields.Many2one(
        "ir.attachment", string="Blueprint Attachment"
    )

    @api.depends(
        "product_id",
        "product_no_variant_attribute_value_ids",
        "product_template_attribute_value_ids",
        # el campo custom es opcional: solo si existe
        # no lo ponemos en depends para no crear dependencia dura
    )
    def _compute_blueprint_custom_values(self):
        """Calcula un resumen con las variables disponibles para las fórmulas
        del blueprint en esta línea."""
        for line in self:
            _logger.debug(
                f"[Blueprint] Capturando valores para la línea de pedido {line.id}"
            )
            blueprint_custom_values = line._get_blueprint_attribute_values()
            # Se guarda en texto para consumo sencillo (ej. en otros modelos/vistas)
            line.blueprint_custom_values = str(blueprint_custom_values)

    def _extract_formula_name_from_svg_element(self, elem):
        """Intenta extraer el nombre de la fórmula a partir del nodo SVG.

        Busca texto en:
          - elem.text
          - aria-label / aria-text
          - descendientes
        y limpia llaves '{{ }}' para quedarse con el nombre de la variable.
        """
        candidates = [
            elem.text,
            elem.get("aria-label"),
            elem.get("aria-text"),
        ]
        for child in elem.iterdescendants():
            if child.text:
                candidates.append(child.text)
            if child.get("aria-label"):
                candidates.append(child.get("aria-label"))
            if child.get("aria-text"):
                candidates.append(child.get("aria-text"))

        for candidate in candidates:
            if candidate and candidate.strip():
                cleaned = candidate.replace("{{", "").replace("}}", "").strip()
                _logger.debug(
                    f"[Blueprint] Nombre de fórmula detectado en SVG: '{cleaned}'"
                )
                return cleaned

        _logger.debug(
            "[Blueprint] No se pudo determinar un nombre de fórmula para un nodo SVG."
        )
        return None

    def _generate_evaluated_blueprint_svg(self, blueprint, evaluated_variables):
        """Genera el SVG evaluado para un blueprint concreto.

        - Carga el SVG original del blueprint.
        - Localiza los nodos con class 'odoo-formula'.
        - Sustituye las fórmulas por los valores evaluados.
        - Normaliza estilo y font-size para evitar emborronamientos.
        - Crea un adjunto SVG y un PNG (vía CairoSVG) para incrustar en el PDF.
        """
        _logger.debug(
            f"[Blueprint] Generando SVG evaluado para el blueprint '{blueprint.name}'"
        )

        if not blueprint.file:
            raise ValidationError(_("No hay archivo SVG en el blueprint."))

        try:
            # Decodificar el archivo SVG del blueprint
            svg_data = base64.b64decode(blueprint.file)
            root = etree.fromstring(svg_data)

            # Limpiar posibles hints de renderizado que causan problemas
            style_attr = root.get("style")
            if style_attr:
                # Opcional: limpiar solo las pistas de render que nos perjudican
                parts = [
                    p
                    for p in style_attr.split(";")
                    if not p.strip().startswith(("image-rendering", "text-rendering"))
                ]
                if parts:
                    root.set("style", ";".join(parts))
                else:
                    root.attrib.pop("style", None)

            # Estilo inyectado para marcar errores de evaluación de fórmulas
            style_element = etree.Element("style")
            style_element.text = """
                .formula-eval-error {
                    font-style: italic;
                    text-decoration: underline;
                }
            """
            root.insert(0, style_element)

            # Namespaces del SVG
            nsmap = {"svg": root.nsmap.get(None, "http://www.w3.org/2000/svg")}
            _logger.debug(f"[Blueprint] Espacios de nombres detectados: {nsmap}")

            # Nodos que representan fórmulas (class contiene 'odoo-formula')
            elements = root.xpath(
                ".//*[@class and contains(@class, 'odoo-formula')]", namespaces=nsmap
            )
            _logger.debug(
                f"[Blueprint] Se encontraron {len(elements)} elementos con fórmulas."
            )

            # ------------------------------------------------------------------
            # Cálculo del font-size "de referencia" del plano
            # ------------------------------------------------------------------

            def _parse_font_size(value):
                """Devuelve el valor numérico del font-size (en px) si se puede.

                Ejemplos soportados:
                  - '12px'  → 12.0
                  - '10pt'  → 10.0  (no convertimos unidades, solo el número)
                  - '8.5'   → 8.5
                Si no se puede parsear, devuelve None.
                """
                if not value:
                    return None
                v = value.strip()
                num = ""
                for ch in v:
                    if ch.isdigit() or ch in ".,-":
                        num += ch
                    else:
                        break
                if not num:
                    return None
                try:
                    return float(num.replace(",", "."))
                except Exception:
                    return None

            # Buscamos <text> que NO sean fórmulas para estimar el tamaño
            # de fuente típico del plano (así evitamos números gigantes).
            text_nodes = root.xpath(".//svg:text", namespaces=nsmap)
            formula_ids = {e.get("id") for e in elements}  # noqa: F841
            size_values = []

            for t in text_nodes:
                # Saltar textos que también son 'odoo-formula'
                cls = t.get("class", "")
                if "odoo-formula" in cls:
                    continue
                # Font-size desde style o atributo directo
                style = t.get("style", "")
                font_size_candidate = None
                for attr in style.split(";"):
                    kv = attr.split(":", 1)
                    if len(kv) != 2:
                        continue
                    k = kv[0].strip()
                    v = kv[1].strip()
                    if k == "font-size":
                        font_size_candidate = v
                        break
                if not font_size_candidate and t.get("font-size"):
                    font_size_candidate = t.get("font-size")
                if font_size_candidate:
                    parsed = _parse_font_size(font_size_candidate)
                    if parsed:
                        size_values.append(parsed)

            if size_values:
                avg_size = sum(size_values) / len(size_values)
                # Redondeamos a entero para algo estable tipo "10px", "12px", etc.
                default_font_size = f"{int(round(avg_size))}px"
            else:
                default_font_size = "12px"

            default_font_size_numeric = _parse_font_size(default_font_size)
            _logger.debug(
                "[Blueprint][STYLE] font-size de referencia calculado: %s \
                    (numérico=%s)",
                default_font_size,
                default_font_size_numeric,
            )

            # ------------------------------------------------------------------
            # Helper para construir un nodo <text> limpio y legible
            # ------------------------------------------------------------------
            def _build_clean_text_node(elem, elem_id, text_value):
                """Convierte cualquier nodo SVG (text, path, etc.) en un <text>
                con estilo y posición coherentes para que el valor se vea nítido.
                """
                # 1) Extraer estilo original del nodo de origen
                style = elem.get("style", "")
                font_size = None
                fill_color = None
                font_size_source = "svg"  # por defecto asumimos que viene del SVG
                _logger.debug(
                    f"[Blueprint][STYLE] Nodo ID={elem_id} fórmula='{text_value}' \
                         - style='{style}'"
                )

                for attr in style.split(";"):
                    kv = attr.split(":", 1)
                    if len(kv) != 2:
                        continue
                    k = kv[0].strip()
                    v = kv[1].strip()
                    if k == "font-size":
                        font_size = v
                    elif k == "fill":
                        fill_color = v

                # 2) Complementar con atributos directos si faltan
                if not fill_color and elem.get("fill"):
                    fill_color = elem.get("fill")
                    _logger.debug(
                        f"[Blueprint][STYLE] Nodo ID={elem_id} fill \
                            directo='{fill_color}'"
                    )
                if not font_size and elem.get("font-size"):
                    font_size = elem.get("font-size")
                    _logger.debug(
                        f"[Blueprint][STYLE] Nodo ID={elem_id} font-size \
                            directo='{font_size}'"
                    )

                # 3) Aplicar estilos desde la fórmula (si están definidos)
                formula_filtered = blueprint.formula_ids.filtered(
                    lambda f, _elem_id=elem_id: f.name
                    and f.name.svg_element_id == _elem_id
                )
                formula_obj = formula_filtered[0] if formula_filtered else None
                if formula_obj:
                    _logger.debug(
                        f"[Blueprint] Usando estilo configurado para '{text_value}': "
                        f"fill={formula_obj.fill_color}, \
                        font_size={formula_obj.font_size}"
                    )
                    if formula_obj.font_size:
                        font_size = formula_obj.font_size
                        font_size_source = "formula"
                    if formula_obj.fill_color:
                        fill_color = formula_obj.fill_color

                # 4) Defaults si siguen vacíos
                if not font_size:
                    font_size = default_font_size
                    font_size_source = "default"
                if not fill_color:
                    fill_color = "#000000"

                # Normalizar font-size desproporcionados (ej. valores enormes
                # arrastrados desde CorelDraw/Inkscape) SOLO si NO vienen de
                # una configuración explícita de la fórmula.
                parsed_font_size = _parse_font_size(font_size)
                if (
                    font_size_source != "formula"
                    and parsed_font_size
                    and default_font_size_numeric
                    and parsed_font_size > default_font_size_numeric * 3
                ):
                    _logger.debug(
                        "[Blueprint][STYLE] Nodo ID=%s font-size=%s demasiado grande "
                        "(fuente: %s). Normalizando a valor de referencia %s.",
                        elem_id,
                        font_size,
                        font_size_source,
                        default_font_size,
                    )
                    font_size = default_font_size

                # Nos aseguramos de que tenga unidad 'px' si no la trae
                if isinstance(font_size, str) and not font_size.strip().endswith("px"):
                    # Si es algo como '12', lo convertimos a '12px'
                    numeric_fs = _parse_font_size(font_size)
                    if numeric_fs is not None:
                        font_size = f"{int(round(numeric_fs))}px"
                    else:
                        # fallback por si el parse falla
                        font_size = default_font_size

                final_style = f"fill:{fill_color}; font-size:{font_size};"
                _logger.debug(
                    f"[Blueprint][STYLE] Nodo ID={elem_id} estilo aplicado \
                        final='{final_style}'"
                )

                # 5) Posición: usamos x/y o, si es un path, el primer punto del 'd'
                transform = elem.get("transform", "")
                x = elem.get("x", "0")
                y = elem.get("y", "0")
                if elem.tag.endswith("path") and "d" in elem.attrib:
                    try:
                        path_commands = elem.attrib["d"].split(" ")
                        x = (
                            path_commands[1].split(",")[0]
                            if len(path_commands) > 1
                            else "0"
                        )
                        y = (
                            path_commands[1].split(",")[1]
                            if len(path_commands) > 1
                            else "0"
                        )
                    except Exception:
                        _logger.debug(
                            f"[Blueprint] No se pudo obtener la posición \
                                de {elem_id}, usando (0,0)"
                        )

                # Construimos el nodo <text> limpio con el valor evaluado
                text_element = etree.Element(
                    "text",
                    {
                        "x": x,
                        "y": y,
                        "style": final_style,
                        "transform": transform,
                    },
                )
                text_element.text = str(text_value)
                return text_element

            # ------------------------------------------------------------------
            # Sustitución de fórmulas y normalización de textos
            # ------------------------------------------------------------------
            for elem in elements:
                formula_name = self._extract_formula_name_from_svg_element(elem)
                elem_id = elem.get("id", "sin ID")

                if formula_name in evaluated_variables:
                    evaluated_value = evaluated_variables[formula_name]
                    try:
                        rounded_value = str(round(float(evaluated_value)))
                    except ValueError:
                        rounded_value = str(evaluated_value)

                    if rounded_value.lower() != "error":
                        _logger.debug(
                            f"[Blueprint] Sustituyendo '{formula_name}' → \
                                '{rounded_value}' en ID={elem_id}"
                        )
                        text_element = _build_clean_text_node(
                            elem, elem_id, rounded_value
                        )
                        elem.getparent().replace(elem, text_element)
                    else:
                        # Caso en el que la fórmula devuelve 'Error'
                        _logger.warning(
                            f"[Blueprint] Valor de fórmula '{formula_name}' \
                                es 'error'. "
                            "No se reemplaza. Se marca el nodo."
                        )

                        existing_class = elem.get("class", "")
                        elem.set(
                            "class",
                            f"{existing_class} formula-eval-error".strip(),
                        )

                        x = elem.get("x", "0")
                        y = elem.get("y", "0")
                        try:
                            x_float = float(x)
                            y_float = float(y)
                        except Exception:
                            x_float = 0
                            y_float = 0

                        # Añadimos un "!" rojo cerca como aviso visual
                        warning_text = etree.Element(
                            "text",
                            {
                                "x": str(x_float + 10),
                                "y": str(y_float),
                                "fill": "red",
                                "font-size": "10px",
                                "font-weight": "bold",
                            },
                        )
                        warning_text.text = "!"
                        elem.getparent().append(warning_text)
                else:
                    # No hay fórmula configurada para este nodo, pero igualmente
                    # normalizamos el texto para que no se vea borroso en PNG/PDF.
                    if formula_name:
                        display_text = formula_name
                    else:
                        # fallback: primer texto encontrado en el nodo
                        texts = []
                        if elem.text and elem.text.strip():
                            texts.append(elem.text.strip())
                        for child in elem.iterdescendants():
                            if child.text and child.text.strip():
                                texts.append(child.text.strip())
                        display_text = texts[0] if texts else ""

                    _logger.debug(
                        f"[Blueprint] Nodo ID={elem_id} sin fórmula configurada "
                        f"('{formula_name}'), normalizando estilo."
                    )
                    text_element = _build_clean_text_node(elem, elem_id, display_text)
                    elem.getparent().replace(elem, text_element)

            # Serializamos el SVG resultante (ya evaluado y normalizado)
            new_svg_data = etree.tostring(
                root, pretty_print=True, encoding="utf-8"
            ).decode("utf-8")

            # Guardar adjunto SVG evaluado
            attachment = self.env["ir.attachment"].create(
                {
                    "name": f"blueprint_{blueprint.id}_line_{self.id}_evaluated.svg",
                    "type": "binary",
                    "datas": base64.b64encode(new_svg_data.encode("utf-8")),
                    "res_model": "sale.order.line",
                    "res_id": self.id,
                    "mimetype": "image/svg+xml",
                }
            )

            # Convertir a PNG (mantengo tu dpi=300 para mejorar nitidez en PDF)
            png_output = cairosvg.svg2png(
                bytestring=new_svg_data.encode("utf-8"),
                dpi=300,
            )
            png_base64 = base64.b64encode(png_output).decode("utf-8")

            _logger.debug(
                f"[Blueprint] Adjunto creado: ID={attachment.id}, \
                    Nombre={attachment.name}, "
                f"Res_model={attachment.res_model}, Res_id={attachment.res_id}"
            )

            return {
                "attachment_id": attachment.id,
                "svg_markup": Markup(new_svg_data),
                "png_base64": png_base64,
            }

        except Exception as e:
            _logger.exception("[Blueprint] Error en la evaluación del plano")
            raise ValidationError(f"Error procesando el SVG: {e}") from e

    def safe_evaluate_formula(self, expression, variables):
        """
        Evalúa de manera segura la fórmula usando solo las variables permitidas.

        Args:
            expression (str): La expresión matemática a evaluar (ej. "mmA * 2").
            variables (dict): Diccionario con los valores de las variables
            (ej. {"mmA": 1500}).

        Returns:
            str: Resultado de la evaluación o 'Error' si ocurre un problema.
        """
        _logger.debug(
            f"[Blueprint] Evaluando expresión: '{expression}' con variables:\
                  {variables}"
        )

        try:
            # Crear entorno seguro con funciones matemáticas permitidas
            allowed_names = {
                k: v for k, v in math.__dict__.items() if not k.startswith("__")
            }
            allowed_names.update(variables)

            # Analizar la expresión de forma segura
            tree = ast.parse(expression, mode="eval")
            compiled = compile(tree, "<string>", "eval")

            # Se evalúa en un entorno sin __builtins__ para evitar accesos peligrosos
            result = eval(compiled, {"__builtins__": {}}, allowed_names)

            _logger.debug(f"[Blueprint] Resultado de la evaluación: {result}")
            return str(result)

        except Exception:
            _logger.exception(f"[Blueprint] Error al evaluar la fórmula '{expression}'")
            return "Error"

    def _get_evaluated_variables(self, sale_order_line):
        """
        Devuelve un diccionario con los nombres de las variables personalizadas
        y sus valores correspondientes.

        Args:
            sale_order_line (recordset): La línea de pedido de venta.

        Returns:
            dict: Un diccionario con las variables evaluadas.
        """
        _logger.debug(
            f"[Blueprint] Iniciando la captura de variables evaluadas para la línea\
            de venta ID: {sale_order_line.id}"
        )

        # Atributos (custom + estándar) proyectados a variables para fórmulas
        attribute_values = sale_order_line._get_blueprint_attribute_values()
        _logger.debug(f"[Blueprint] Atributos capturados: {attribute_values}")

        variable_mapping = {}

        if (
            not sale_order_line.product_id
            or not sale_order_line.product_id.product_tmpl_id
        ):
            _logger.warning(
                f"[Blueprint] Producto o plantilla no encontrados para\
                      línea {sale_order_line.id}."
            )
            return {}

        # Recorremos todas las fórmulas definidas en la plantilla de producto
        # y extraemos sólo las variables listadas en available_attributes.
        for formula in sale_order_line.product_id.product_tmpl_id.formula_ids:
            if not formula.formula_expression or not formula.available_attributes:
                continue

            for attribute_name in formula.available_attributes.split(","):
                attribute_name = attribute_name.strip()
                if attribute_name in attribute_values:
                    try:
                        variable_mapping[attribute_name] = float(
                            attribute_values[attribute_name]
                        )
                    except ValueError:
                        variable_mapping[attribute_name] = attribute_values[
                            attribute_name
                        ]

        return variable_mapping

    def _get_evaluated_blueprint(self, type_blueprint="manufacturing"):
        """Genera todos los planos evaluados para la línea (por tipo de plano).

        - Limpia adjuntos antiguos de esta línea.
        - Filtra los blueprints según tipo (fabricación / compra).
        - Aplica condiciones de atributos.
        - Evalúa las fórmulas y genera SVG + PNG.
        """
        self.ensure_one()
        _logger.info(
            f"[Blueprint] Generando planos evaluados para línea {self.id}\
                  (Producto: {self.product_id.name})"
        )

        # Limpiar adjuntos SVG anteriores asociados a esta línea
        old_attachments = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "sale.order.line"),
                ("res_id", "=", self.id),
                ("name", "ilike", f"blueprint_%_line_{self.id}_evaluated.svg"),
            ]
        )
        if old_attachments:
            _logger.debug(
                f"[Blueprint] Se eliminarán {len(old_attachments)} adjuntos antiguos"
            )
            old_attachments.unlink()

        # Si el producto no tiene planos, no hacemos nada
        if not self.product_id or not self.product_id.product_tmpl_id.blueprint_ids:
            _logger.warning(
                f"[Blueprint] No hay blueprints para el producto {self.product_id.name}"
            )
            return []

        # Mapa de atributos seleccionados (para aplicar condiciones de plano)
        attribute_values = {}

        # a) variantes / dinámicos
        for v in self.product_template_attribute_value_ids:
            attribute_values.setdefault(v.attribute_id.id, set()).add(v.name)
        # b) no_variant
        for v in self.product_no_variant_attribute_value_ids:
            attribute_values.setdefault(v.attribute_id.id, set()).add(v.name)
        # c) custom (opcional)
        if "product_custom_attribute_value_ids" in self._fields:
            for cav in self.product_custom_attribute_value_ids:
                ptav = getattr(cav, "custom_product_template_attribute_value_id", False)
                if ptav:
                    attr = ptav.attribute_id
                    attribute_values.setdefault(attr.id, set()).add(ptav.name)

        evaluated_svgs = []

        # Recorremos todos los planos configurados en la plantilla
        for blueprint in self.product_id.product_tmpl_id.blueprint_ids:
            if blueprint.type_blueprint != type_blueprint:
                continue

            # Aplicar condiciones de atributos (blueprint_condition_ids)
            skip_blueprint = False
            for condition in blueprint.blueprint_condition_ids:
                required = set(condition.value_ids.mapped("name"))
                selected = attribute_values.get(condition.attribute_id.id, set())
                if required and selected.isdisjoint(required):
                    _logger.debug(
                        "[Blueprint] → Saltando plano %s por no cumplir "
                        "condición del atributo %s",
                        blueprint.name,
                        condition.attribute_id and condition.attribute_id.name or "-",
                    )
                    skip_blueprint = True
                    break

            if skip_blueprint:
                continue

            _logger.debug(f"[Blueprint] Evaluando plano: {blueprint.name}")

            # Variables disponibles para las fórmulas de este plano
            variables = self._get_evaluated_variables(self)
            evaluated_values = {}
            for formula in blueprint.formula_ids:
                if formula.name and formula.formula_expression:
                    formula_key = formula.name.name
                    evaluated_values[formula_key] = self.safe_evaluate_formula(
                        formula.formula_expression, variables
                    )

            # Generar SVG evaluado + PNG para este blueprint
            result = self._generate_evaluated_blueprint_svg(blueprint, evaluated_values)
            evaluated_svgs.append(
                {
                    "attachment_id": result["attachment_id"],
                    "markup": result["svg_markup"],
                    "png_base64": result["png_base64"],
                    "blueprint_name": blueprint.name,
                }
            )

        if not evaluated_svgs:
            _logger.warning(
                f"[Blueprint] No se generó ningún SVG evaluado para línea {self.id}"
            )

        return evaluated_svgs

    def _get_blueprint_attribute_values(self):
        """
        Devuelve un dict con los valores de variables para las fórmulas del blueprint,
        igual que hacía el antiguo hook pero sin usar ningún modelo externo.

        Claves del dict: nombres de variables (mmA, mmB, etc.).
        Valores: normalmente enteros (medidas), si se pueden convertir.
        """
        self.ensure_one()
        result = {}

        _logger.debug(
            "[Blueprint][ATTR] Iniciando extracción de variables para fórmulas. "
            "Linea ID: %s, Producto: %s",
            self.id,
            getattr(self, "product_id", False) and self.product_id.display_name or "-",
        )

        # --- Atributos personalizados (custom) (opcional) ---
        # Cada valor custom con ptav.is_custom=True define una variable (ptav.name)
        if "product_custom_attribute_value_ids" in self._fields:
            for val in self.product_custom_attribute_value_ids:
                ptav = val.custom_product_template_attribute_value_id
                if ptav and ptav.is_custom:
                    var_name = ptav.name
                    _logger.debug(
                        "[Blueprint][ATTR] Encontrado atributo personalizado: %s "
                        "(is_custom) → variable '%s'",
                        ptav.display_name,
                        var_name,
                    )
                    if val.custom_value is not None:
                        try:
                            int_value = int(val.custom_value)
                            result[var_name] = int_value
                            _logger.info(
                                "[Blueprint][ATTR] Variable '%s' definida por "
                                "custom_value: %s (valor crudo: %r)",
                                var_name,
                                int_value,
                                val.custom_value,
                            )
                        except Exception as e:
                            _logger.warning(
                                "[Blueprint][ATTR] No se pudo convertir custom_value "
                                "'%r' a int para variable '%s' (Error: %s)",
                                val.custom_value,
                                var_name,
                                e,
                            )
                    else:
                        _logger.debug(
                            "[Blueprint][ATTR] custom_value es None para variable "
                            "'%s' (atributo: %s)",
                            var_name,
                            ptav.display_name,
                        )

        # --- Atributos estándar proyectados como variable, si el atributo tiene
        #     algún valor is_custom (para obtener el "alias" de variable) ---
        std_values = (
            self.product_template_attribute_value_ids
            + self.product_no_variant_attribute_value_ids
        ).filtered(lambda v: not v.is_custom)

        for val in std_values:
            attr = val.attribute_id
            custom_vals = attr.value_ids.filtered(lambda v: v.is_custom)
            if not custom_vals:
                _logger.debug(
                    "[Blueprint][ATTR] Atributo '%s' (%s) ignorado: "
                    "no tiene valores is_custom.",
                    attr.display_name,
                    attr.name,
                )
                continue  # Este atributo no tiene variable asociada
            var_name = custom_vals[0].name
            if var_name in result:
                _logger.debug(
                    "[Blueprint][ATTR] Variable '%s' ya fue definida previamente, "
                    "se omite atributo estándar '%s'.",
                    var_name,
                    attr.display_name,
                )
                continue
            try:
                # Si el nombre del valor es un número (por ejemplo '1500' mmAltura)
                int_value = int(val.name)
                result[var_name] = int_value
                _logger.info(
                    "[Blueprint][ATTR] Variable '%s' definida a partir de "
                    "valor estándar: %s (valor: %s)",
                    var_name,
                    int_value,
                    val.display_name,
                )
            except ValueError as e:
                _logger.info(
                    "[Blueprint][ATTR] Valor estándar '%s' para atributo '%s' "
                    "no es convertible a int (ignorado). Error: %s",
                    val.name,
                    attr.display_name,
                    e,
                )

        _logger.debug(
            "[Blueprint][ATTR] Resultado final de variables extraídas para "
            "línea %s: %r",
            self.id,
            result,
        )

        return result

    def _get_blueprint_display_attributes(self):
        """Devuelve lista de dicts [{'attr': 'Color', 'value': 'Blanco'}, ...]
        sin depender del módulo externo.

        Se usa para mostrar, en el plano, un resumen de los atributos seleccionados.
        """
        self.ensure_one()
        items = []

        # variantes / dinámicos
        for v in self.product_template_attribute_value_ids:
            items.append({"attr": v.attribute_id.name, "value": v.name})

        # no_variant
        for v in self.product_no_variant_attribute_value_ids:
            items.append({"attr": v.attribute_id.name, "value": v.name})

        # custom (si existe)
        if "product_custom_attribute_value_ids" in self._fields:
            for cav in self.product_custom_attribute_value_ids:
                ptav = getattr(cav, "custom_product_template_attribute_value_id", False)
                if ptav:
                    label = ptav.name
                    val = getattr(cav, "custom_value", None)
                    shown = f"{label}: {val}" if val not in (None, False, "") else label
                    items.append({"attr": ptav.attribute_id.name, "value": shown})

        return items
