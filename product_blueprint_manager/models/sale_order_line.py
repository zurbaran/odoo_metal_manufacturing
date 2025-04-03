from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import base64
from lxml import etree
import logging
import ast
import math
import tempfile
import subprocess
import uuid
import os
from markupsafe import Markup
import cairosvg

_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    blueprint_custom_values = fields.Char(
        compute="_capture_blueprint_custom_values",
        string="Blueprint Custom Values",
    )

    blueprint_attachment_id = fields.Many2one("ir.attachment", string="Blueprint Attachment")

    @api.depends("product_id", "product_custom_attribute_value_ids")
    def _capture_blueprint_custom_values(self):
        hook = self.env["product.blueprint.hook"]
        for line in self:
            _logger.info(f"[Blueprint] Capturando valores para la línea de pedido {line.id}")
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
                _logger.debug(f"[Blueprint] Nombre de fórmula detectado en SVG: '{cleaned}'")
                return cleaned

        _logger.debug("[Blueprint] No se pudo determinar un nombre de fórmula para un nodo SVG.")
        return None

    def _generate_evaluated_blueprint_svg(self, blueprint, evaluated_variables):
        _logger.info(f"[Blueprint] Generando SVG evaluado para el blueprint '{blueprint.name}'")

        if not blueprint.file:
            raise ValidationError("No hay archivo SVG en el blueprint.")

        try:
            svg_data = base64.b64decode(blueprint.file)
            root = etree.fromstring(svg_data)

            nsmap = {'svg': root.nsmap.get(None, 'http://www.w3.org/2000/svg')}
            _logger.info(f"[Blueprint] Espacios de nombres detectados: {nsmap}")

            elements = root.xpath(".//*[@class and contains(@class, 'odoo-formula')]", namespaces=nsmap)
            _logger.info(f"[Blueprint] Se encontraron {len(elements)} elementos con fórmulas.")

            for elem in elements:
                formula_name = self._extract_formula_name_from_svg_element(elem)
                elem_id = elem.get("id", "sin ID")

                if formula_name in evaluated_variables:
                    evaluated_value = evaluated_variables[formula_name]
                    try:
                        rounded_value = str(round(float(evaluated_value)))
                    except ValueError:
                        rounded_value = str(evaluated_value)
                    _logger.info(f"[Blueprint] Sustituyendo '{formula_name}' → '{rounded_value}' en ID={elem_id}")

                    # Extraer estilo original
                    style = elem.get("style", "")
                    font_size = "12px"
                    fill_color = None

                    for attr in style.split(";"):
                        if "font-size" in attr:
                            font_size = attr.split(":")[1].strip()
                        elif "fill" in attr:
                            fill_color = attr.split(":")[1].strip()

                    # Buscar atributos directos si no estaban en style
                    if not fill_color and elem.get("fill"):
                        fill_color = elem.get("fill")
                    if elem.get("font-size"):
                        font_size = elem.get("font-size")

                    # Estilo final: usar valores configurados si existen
                    final_style = ""
                    formula_filtered = blueprint.formula_ids.filtered(lambda f: f.name.name == formula_name)
                    formula_obj = formula_filtered[0] if formula_filtered else None
                    if formula_obj:
                        _logger.info(f"[Blueprint] Usando estilo configurado para '{formula_name}': fill={formula_obj.fill_color}, font_size={formula_obj.font_size}")
                        font_size = formula_obj.font_size or font_size
                        fill_color = formula_obj.fill_color or fill_color

                    # Estilo final: solo lo necesario
                    final_style = f"fill:{fill_color}; font-size:{font_size};"

                    # Posición
                    transform = elem.get("transform", "")
                    x, y = "0", "0"
                    if elem.tag.endswith("path") and "d" in elem.attrib:
                        try:
                            path_commands = elem.attrib["d"].split(" ")
                            x = path_commands[1].split(",")[0] if len(path_commands) > 1 else "0"
                            y = path_commands[1].split(",")[1] if len(path_commands) > 1 else "0"
                        except Exception:
                            _logger.info(f"[Blueprint] No se pudo obtener la posición de {elem_id}, usando (0,0)")
                    else:
                        x = elem.get("x", "0")
                        y = elem.get("y", "0")

                    # Crear nuevo nodo <text>
                    text_element = etree.Element("text", {
                        "x": x,
                        "y": y,
                        "style": final_style,
                        "transform": transform
                    })
                    text_element.text = rounded_value
                    elem.getparent().replace(elem, text_element)
                else:
                    _logger.info(f"[Blueprint] No hay fórmula configurada para '{formula_name}', se mantiene sin cambios en el SVG.")

            new_svg_data = etree.tostring(root, pretty_print=True, encoding="utf-8").decode("utf-8")
            new_svg_base64 = base64.b64encode(new_svg_data.encode("utf-8"))

            # Guardar adjunto SVG
            attachment = self.env["ir.attachment"].create({
                'name': f"blueprint_{blueprint.id}_line_{self.id}_evaluated.svg",
                'type': 'binary',
                'datas': base64.b64encode(new_svg_data.encode("utf-8")),
                'res_model': 'sale.order.line',
                'res_id': self.id,
                'mimetype': 'image/svg+xml',
            })

            # Convertir a PNG
            png_output = cairosvg.svg2png(bytestring=new_svg_data.encode("utf-8"))
            png_base64 = base64.b64encode(png_output).decode("utf-8")

            _logger.info(f"[Blueprint] Adjunto creado: ID={attachment.id}, Nombre={attachment.name}, Res_model={attachment.res_model}, Res_id={attachment.res_id}")

            return {
                'attachment_id': attachment.id,
                'svg_markup': Markup(new_svg_data),
                'png_base64': png_base64,
            }

        except Exception as e:
            _logger.exception(f"[Blueprint] Error en la evaluación del plano")
            raise ValidationError(f"Error procesando el SVG: {str(e)}")

    def safe_evaluate_formula(self, expression, variables):
        """
        Evalúa de manera segura la fórmula usando solo las variables permitidas.

        Args:
            expression (str): La expresión matemática a evaluar (ej. "mmA * 2").
            variables (dict): Diccionario con los valores de las variables (ej. {"mmA": 1500}).

        Returns:
            str: Resultado de la evaluación o 'Error' si ocurre un problema.
        """
        _logger.info(f"[Blueprint] Evaluando expresión: '{expression}' con variables: {variables}")

        try:
            # Crear entorno seguro con funciones matemáticas permitidas
            allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
            allowed_names.update(variables)

            # Analizar la expresión de forma segura
            tree = ast.parse(expression, mode='eval')
            compiled = compile(tree, "<string>", "eval")

            result = eval(compiled, {"__builtins__": {}}, allowed_names)

            _logger.info(f"[Blueprint] Resultado de la evaluación: {result}")
            return str(result)

        except Exception as e:
            _logger.exception(f"[Blueprint] Error al evaluar la fórmula '{expression}'")
            return "Error"

    def _get_evaluated_variables(self, sale_order_line):
        """
        Devuelve un diccionario con los nombres de las variables personalizadas y sus valores correspondientes.

        Args:
            sale_order_line (recordset): La línea de pedido de venta.

        Returns:
            dict: Un diccionario con las variables evaluadas.
        """
        _logger.info(
            f"[Blueprint] Iniciando la captura de variables evaluadas para la línea de venta ID: {sale_order_line.id}, Producto: {sale_order_line.product_id.name if sale_order_line.product_id else 'Ninguno'}"
        )

        hook = self.env["product.blueprint.hook"]
        attribute_values = hook.get_attribute_values_for_blueprint(sale_order_line)
        _logger.info(
            f"[Blueprint] Atributos capturados para la línea {sale_order_line.id}: {attribute_values}"
        )

        variable_mapping = {}

        if (
            not sale_order_line.product_id
            or not sale_order_line.product_id.product_tmpl_id
        ):
            _logger.info(
                f"[Blueprint] Producto o plantilla de producto no encontrado para la línea {sale_order_line.id}."
            )
            return {}

        formula_count = len(sale_order_line.product_id.product_tmpl_id.formula_ids)
        _logger.info(
            f"[Blueprint] Se encontraron {formula_count} fórmula(s) para el producto '{sale_order_line.product_id.name}'."
        )

        for formula in sale_order_line.product_id.product_tmpl_id.formula_ids:
            _logger.info(
                f"[Blueprint] Procesando fórmula: '{formula.name}' para el blueprint '{formula.blueprint_id.name or 'N/A'}'"
            )

            if not formula.formula_expression:
                _logger.info(
                    f"[Blueprint] Fórmula sin expresión para '{formula.name}' en la línea {sale_order_line.id}."
                )
                continue

            if not formula.available_attributes:
                _logger.info(
                    f"[Blueprint] La fórmula '{formula.name}' no tiene atributos disponibles definidos."
                )
                continue

            _logger.info(
                f"[Blueprint] Atributos disponibles para la fórmula '{formula.name}': {formula.available_attributes}"
            )

            for attribute_name in formula.available_attributes.split(","):
                attribute_name = attribute_name.strip()
                if attribute_name in attribute_values:
                    try:
                        variable_mapping[attribute_name] = float(
                            attribute_values[attribute_name]
                        )
                        _logger.info(
                            f"[Blueprint] Atributo '{attribute_name}' encontrado con valor: {variable_mapping[attribute_name]}"
                        )
                    except ValueError:
                        variable_mapping[attribute_name] = attribute_values[
                            attribute_name
                        ]
                        _logger.info(
                            f"[Blueprint] Atributo '{attribute_name}' no es un número. Se usará como cadena: '{attribute_values[attribute_name]}'"
                        )
                else:
                    _logger.info(
                        f"[Blueprint] Atributo '{attribute_name}' no encontrado en los valores de atributos para la línea {sale_order_line.id}."
                    )

        if not variable_mapping:
            _logger.info(
                f"[Blueprint] No se mapearon variables para la línea {sale_order_line.id}."
            )
        else:
            _logger.info(
                f"[Blueprint] Variables mapeadas para la línea {sale_order_line.id}: {variable_mapping}"
            )

        _logger.info(
            f"[Blueprint] Finalizada la captura de variables para la línea {sale_order_line.id}."
        )
        return variable_mapping

        """Genera los planos evaluados para esta línea de pedido (puede ser 0, 1 o varios)."""
    def _get_evaluated_blueprint(self, type_blueprint="manufacturing"):
        self.ensure_one()

        _logger.info(f"[Blueprint] Iniciando generación de planos evaluados para la línea {self.id} (Producto: {self.product_id.name})")

        # Paso 1: Limpiar adjuntos anteriores
        old_attachments = self.env["ir.attachment"].search([
            ("res_model", "=", "sale.order.line"),
            ("res_id", "=", self.id),
            ("name", "ilike", f"blueprint_%_line_{self.id}_evaluated.svg"),
        ])
        if old_attachments:
            _logger.info(f"[Blueprint] Eliminando {len(old_attachments)} adjuntos antiguos para la línea {self.id}")
            old_attachments.unlink()

        if not self.product_id or not self.product_id.product_tmpl_id.blueprint_ids:
            _logger.info(f"[Blueprint] No hay blueprints configurados para el producto {self.product_id.name}")
            return []

        evaluated_svgs = []

        for blueprint in self.product_id.product_tmpl_id.blueprint_ids:
            if blueprint.type_blueprint != type_blueprint:
                _logger.info(f"[Blueprint] Plano '{blueprint.name}' descartado por tipo no coincidente: {blueprint.type_blueprint}")
                continue

            if blueprint.attribute_filter_id:
                blueprint_value_ids = blueprint.attribute_value_ids.ids
                blueprint_value_names = blueprint.attribute_value_ids.mapped("name")
                _logger.info(f"[Blueprint] Plano '{blueprint.name}' tiene filtro de atributo '{blueprint.attribute_filter_id.name}'")
                _logger.info(f"[Blueprint] Valores esperados (IDs): {blueprint_value_ids}")
                _logger.info(f"[Blueprint] Valores esperados (Nombres): {blueprint_value_names}")

                # Recoger valores seleccionados por separado (evitando mezcla de modelos)
                selected_ids_all = []
                selected_names_all = []

                for v in self.product_custom_attribute_value_ids:
                    if (
                        hasattr(v, 'custom_product_template_attribute_value_id') and
                        v.custom_product_template_attribute_value_id and
                        v.custom_product_template_attribute_value_id.attribute_id == blueprint.attribute_filter_id
                    ):
                        selected_ids_all.append(v.custom_product_template_attribute_value_id.product_attribute_value_id.id)
                        selected_names_all.append(v.name)

                for v in self.product_no_variant_attribute_value_ids:
                    if v.attribute_id == blueprint.attribute_filter_id:
                        selected_ids_all.append(v.id)
                        selected_names_all.append(v.name)

                for v in self.product_template_attribute_value_ids:
                    if v.attribute_id == blueprint.attribute_filter_id:
                        selected_ids_all.append(v.id)
                        selected_names_all.append(v.name)

                _logger.info(f"[Blueprint] Valores seleccionados en línea (IDs): {selected_ids_all}")
                _logger.info(f"[Blueprint] Valores seleccionados en línea (Nombres): {selected_names_all}")

                coincide_por_id = any(val_id in blueprint_value_ids for val_id in selected_ids_all)
                coincide_por_nombre = any(name in blueprint_value_names for name in selected_names_all)

                if not coincide_por_id and not coincide_por_nombre:
                    _logger.info(f"[Blueprint] Plano '{blueprint.name}' descartado por no coincidir valor de atributo '{blueprint.attribute_filter_id.name}'")
                    continue
                else:
                    _logger.info(f"[Blueprint] Plano '{blueprint.name}' aceptado por coincidencia de atributo condicional")

            _logger.info(f"[Blueprint] Procesando plano: {blueprint.name} (ID: {blueprint.id})")

            variables = self._get_evaluated_variables(self)
            _logger.info(f"[Blueprint] Variables obtenidas para evaluación: {variables}")

            evaluated_values = {}
            for formula in blueprint.formula_ids:
                if formula.name and formula.formula_expression:
                    formula_key = formula.name.name
                    evaluated_values[formula_key] = self.safe_evaluate_formula(
                        formula.formula_expression, variables
                    )
                    _logger.info(f"[Blueprint] Fórmula '{formula_key}' → '{evaluated_values[formula_key]}'")

            _logger.info(f"[Blueprint] Resultados evaluados finales para el plano '{blueprint.name}': {evaluated_values}")

            result = self._generate_evaluated_blueprint_svg(blueprint, evaluated_values)
            attachment_id = result['attachment_id']
            svg_markup = result['svg_markup']

            evaluated_svgs.append({
                'attachment_id': attachment_id,
                'markup': svg_markup,
                'png_base64': result['png_base64'],
            })

        if not evaluated_svgs:
            _logger.info(f"[Blueprint] No se generó ningún SVG evaluado para la línea {self.id}")

        return evaluated_svgs