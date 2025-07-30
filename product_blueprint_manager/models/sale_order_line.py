import ast
import base64
import logging
import math

import cairosvg
from lxml import etree
from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    blueprint_custom_values = fields.Char(
        compute="_compute_blueprint_custom_values",
    )

    blueprint_attachment_id = fields.Many2one(
        "ir.attachment", string="Blueprint Attachment"
    )

    @api.depends("product_id", "product_custom_attribute_value_ids")
    def _compute_blueprint_custom_values(self):
        hook = self.env["product.blueprint.hook"]
        for line in self:
            _logger.debug(
                f"[Blueprint] Capturando valores para la línea de pedido {line.id}"
            )
            blueprint_custom_values = hook.get_attribute_values_for_blueprint(line)
            line.blueprint_custom_values = str(blueprint_custom_values)

    def _extract_formula_name_from_svg_element(self, elem):
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
        _logger.debug(
            f"[Blueprint] Generando SVG evaluado para el blueprint '{blueprint.name}'"
        )

        if not blueprint.file:
            raise ValidationError(_("No hay archivo SVG en el blueprint."))

        try:
            svg_data = base64.b64decode(blueprint.file)
            root = etree.fromstring(svg_data)

            style_element = etree.Element("style")
            style_element.text = """
                .formula-eval-error {
                    font-style: italic;
                    text-decoration: underline;
                }
            """
            root.insert(0, style_element)

            nsmap = {"svg": root.nsmap.get(None, "http://www.w3.org/2000/svg")}
            _logger.debug(f"[Blueprint] Espacios de nombres detectados: {nsmap}")

            elements = root.xpath(
                ".//*[@class and contains(@class, 'odoo-formula')]", namespaces=nsmap
            )
            _logger.debug(
                f"[Blueprint] Se encontraron {len(elements)} elementos con fórmulas."
            )

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
                            f"[Blueprint] Sustituyendo '{formula_name}' →\
                                  '{rounded_value}' en ID={elem_id}"
                        )

                        # === 🔧 NUEVA LÓGICA DE ESTILOS ===
                        # 1. Extraer estilo original
                        style = elem.get("style", "")
                        font_size = None
                        fill_color = None
                        _logger.debug(
                            f"[Blueprint][STYLE] Nodo ID={elem_id}\
                                  fórmula='{formula_name}' - style='{style}'"
                        )

                        for attr in style.split(";"):
                            if "font-size" in attr:
                                font_size = attr.split(":")[1].strip()
                            elif "fill" in attr:
                                fill_color = attr.split(":")[1].strip()

                        # 2. Complementar con atributos directos si faltan
                        if not fill_color and elem.get("fill"):
                            fill_color = elem.get("fill")
                            _logger.debug(
                                f"[Blueprint][STYLE] Nodo ID={elem_id}\
                                      fill directo='{fill_color}'"
                            )
                        if not font_size and elem.get("font-size"):
                            font_size = elem.get("font-size")
                            _logger.debug(
                                f"[Blueprint][STYLE] Nodo ID={elem_id} font-size\
                                      directo='{font_size}'"
                            )

                        # 3. Aplicar estilos desde la fórmula (si están definidos)
                        formula_filtered = blueprint.formula_ids.filtered(
                            lambda f, elem_id=elem_id: f.name
                            and f.name.svg_element_id == elem_id
                        )
                        if not formula_filtered:
                            _logger.warning(
                                f"[Blueprint] No se encontró fórmula con ID\
                                      SVG '{elem_id}' para '{formula_name}'"
                            )
                        formula_obj = formula_filtered[0] if formula_filtered else None
                        if formula_obj:
                            _logger.debug(
                                f"[Blueprint] Usando estilo configurado para\
                                      '{formula_name}': fill={formula_obj.fill_color},\
                                        font_size={formula_obj.font_size}"
                            )
                            font_size = formula_obj.font_size or font_size
                            fill_color = formula_obj.fill_color or fill_color

                        # 4. Defaults si siguen vacíos
                        font_size = font_size or "12px"
                        fill_color = fill_color or "#000000"

                        final_style = f"fill:{fill_color}; font-size:{font_size};"
                        _logger.debug(
                            f"[Blueprint][STYLE] Nodo ID={elem_id} estilo aplicado\
                                  final='{final_style}'"
                        )

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
                                    f"[Blueprint] No se pudo obtener la posición\
                                          de {elem_id}, usando (0,0)"
                                )

                        text_element = etree.Element(
                            "text",
                            {
                                "x": x,
                                "y": y,
                                "style": final_style,
                                "transform": transform,
                            },
                        )
                        text_element.text = rounded_value
                        elem.getparent().replace(elem, text_element)

                    else:
                        _logger.warning(
                            f"[Blueprint] Valor de fórmula '{formula_name}' es 'error'.\
                                  No se reemplaza. Se marca el nodo."
                        )

                        existing_class = elem.get("class", "")
                        elem.set(
                            "class", f"{existing_class} formula-eval-error".strip()
                        )

                        x = elem.get("x", "0")
                        y = elem.get("y", "0")
                        try:
                            x_float = float(x)
                            y_float = float(y)
                        except Exception:
                            x_float = 0
                            y_float = 0

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
                    _logger.debug(
                        f"[Blueprint] No hay fórmula configurada para '{formula_name}'\
                            , se mantiene sin cambios en el SVG."
                    )

            new_svg_data = etree.tostring(
                root, pretty_print=True, encoding="utf-8"
            ).decode("utf-8")

            # Guardar adjunto SVG
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

            # Convertir a PNG
            png_output = cairosvg.svg2png(bytestring=new_svg_data.encode("utf-8"))
            png_base64 = base64.b64encode(png_output).decode("utf-8")

            _logger.debug(
                f"[Blueprint] Adjunto creado: ID={attachment.id}, Nombre=\
                    {attachment.name}, Res_model={attachment.res_model},\
                          Res_id={attachment.res_id}"
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

        hook = self.env["product.blueprint.hook"]
        attribute_values = hook.get_attribute_values_for_blueprint(sale_order_line)
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
        self.ensure_one()
        _logger.info(
            f"[Blueprint] Generando planos evaluados para línea {self.id}\
                  (Producto: {self.product_id.name})"
        )

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

        if not self.product_id or not self.product_id.product_tmpl_id.blueprint_ids:
            _logger.warning(
                f"[Blueprint] No hay blueprints para el producto {self.product_id.name}"
            )
            return []

        evaluated_svgs = []

        for blueprint in self.product_id.product_tmpl_id.blueprint_ids:
            if blueprint.type_blueprint != type_blueprint:
                continue

            if blueprint.attribute_filter_id:
                blueprint_value_names = blueprint.attribute_value_ids.mapped("name")
                selected_names = []

                for v in self.product_custom_attribute_value_ids:
                    if (
                        v.custom_product_template_attribute_value_id
                        and v.custom_product_template_attribute_value_id.attribute_id
                        == blueprint.attribute_filter_id
                    ):
                        selected_names.append(v.name)
                for v in self.product_no_variant_attribute_value_ids:
                    if v.attribute_id == blueprint.attribute_filter_id:
                        selected_names.append(v.name)
                for v in self.product_template_attribute_value_ids:
                    if v.attribute_id == blueprint.attribute_filter_id:
                        selected_names.append(v.name)

                if not any(name in blueprint_value_names for name in selected_names):
                    continue

            _logger.debug(f"[Blueprint] Evaluando plano: {blueprint.name}")
            variables = self._get_evaluated_variables(self)
            evaluated_values = {}
            for formula in blueprint.formula_ids:
                if formula.name and formula.formula_expression:
                    formula_key = formula.name.name
                    evaluated_values[formula_key] = self.safe_evaluate_formula(
                        formula.formula_expression, variables
                    )

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
