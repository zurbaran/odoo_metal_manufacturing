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

    def _generate_evaluated_blueprint_svg(self, blueprint, evaluated_variables):
        """
        Evalúa las fórmulas en el plano y genera un nuevo SVG con textos en lugar de trayectorias.
        """
        _logger.info(f"[Blueprint] Generando SVG evaluado para el blueprint '{blueprint.name}'")

        if not blueprint.file:
            raise ValidationError("No hay archivo SVG en el blueprint.")

        try:
            # Decodificar SVG desde base64
            svg_data = base64.b64decode(blueprint.file)
            root = etree.fromstring(svg_data)

            nsmap = {'svg': root.nsmap.get(None, 'http://www.w3.org/2000/svg')}
            _logger.info(f"[Blueprint] Espacios de nombres detectados: {nsmap}")

            # NO necesitamos formula_mapping aquí.  Usamos evaluated_variables directamente.

            # Buscar todos los elementos <path> con class="odoo-formula"
            paths = root.xpath(".//svg:path[contains(@class, 'odoo-formula')]", namespaces=nsmap)
            _logger.info(f"[Blueprint] Se encontraron {len(paths)} trayectos con fórmulas.")

            for path in paths:
                formula_name = path.get("aria-label", "").strip()  # Identificador del path
                path_id = path.get("id", "sin ID")

                if formula_name in evaluated_variables: # Usamos evaluated_variables
                    evaluated_value = evaluated_variables[formula_name] # Usamos evaluated_variables

                    # APLICAR REDONDEO AQUÍ:
                    try:
                        rounded_value = str(round(float(evaluated_value)))  # Convertir a float, redondear, volver a string
                    except ValueError:
                        rounded_value = str(evaluated_value) #Si no se puede convertir a float, no redondeamos
                    _logger.info(f"[Blueprint] Sustituyendo '{formula_name}' → '{rounded_value}' en ID={path_id}")


                    # Extraer información visual del path
                    transform = path.get("transform", "")
                    style = path.get("style", "")

                    # Extraer tamaño de fuente y color
                    font_size = "12px"
                    fill_color = "black"
                    for style_attr in style.split(";"):
                        if "font-size" in style_attr:
                            font_size = style_attr.split(":")[1].strip()
                        elif "fill" in style_attr:
                            fill_color = style_attr.split(":")[1].strip()

                    # IMPORTANTE: Extraer la posición correcta
                    x, y = "0", "0"
                    if "d" in path.attrib:
                        try:
                            path_commands = path.attrib["d"].split(" ")
                            x = path_commands[1].split(",")[0] if len(path_commands) > 1 else "0"
                            y = path_commands[1].split(",")[1] if len(path_commands) > 1 else "0"
                        except Exception:
                            _logger.info(f"[Blueprint] No se pudo obtener la posición de {path_id}, usando (0,0)")

                    # Crear un nuevo elemento <text> con el resultado evaluado
                    text_element = etree.Element("text", {
                        "x": x,
                        "y": y,
                        "style": f"font-size:{font_size}; fill:{fill_color};",
                        "transform": transform
                    })
                    text_element.text = rounded_value  # Usar el valor redondeado

                    # Reemplazar el <path> por el <text>
                    path.getparent().replace(path, text_element)

                else:
                    _logger.info(f"[Blueprint] No hay fórmula configurada para '{formula_name}', se mantiene sin cambios en el SVG.")

            # Convertir el nuevo SVG de vuelta a base64
            new_svg_data = etree.tostring(root, pretty_print=True, encoding="utf-8").decode("utf-8")
            new_svg_base64 = base64.b64encode(new_svg_data.encode("utf-8"))

            # Guardar el nuevo archivo como adjunto en Odoo
            attachment = self.env["ir.attachment"].create({
                "name": f"{blueprint.name}_evaluated.svg",
                "datas": new_svg_base64,
                "res_model": "sale.order.line",
                "res_id": self.id,
                "mimetype": "image/svg+xml",
            })

            _logger.info(f"[Blueprint] SVG evaluado guardado como adjunto ID={attachment.id}")

            return attachment.id

        except Exception as e:
            _logger.exception(f"[Blueprint] Error en la evaluación del plano") # Usar logger.exception
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
            allowed_names.update(variables)  # Agregar variables de la línea de venta

            # Analizar la expresión de forma segura
            tree = ast.parse(expression, mode='eval')
            compiled = compile(tree, "<string>", "eval")

            result = eval(compiled, {"__builtins__": {}}, allowed_names)

            _logger.info(f"[Blueprint] Resultado de la evaluación: {result}")
            return str(result)  # Convertimos a string para evitar errores con tipos de datos

        except Exception as e:
            _logger.exception(f"[Blueprint] Error al evaluar la fórmula '{expression}'") # Usar logger.exception
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

    def _get_evaluated_blueprint(self):
        self.ensure_one()
        if not self.product_id or not self.product_id.product_tmpl_id.blueprint_ids:
            _logger.info(f"[Blueprint] No hay blueprint asociado a {self.product_id.name}")
            return ""

        blueprint = self.product_id.product_tmpl_id.blueprint_ids[0]

        # Obtener variables correctamente usando `_get_evaluated_variables()`
        variables = self._get_evaluated_variables(self)

        _logger.info(f"[Blueprint] Variables evaluadas para {self.product_id.name}: {variables}")

        # Evaluar fórmulas con las variables correctas, UNA SOLA VEZ
        evaluated_variables = {}
        for formula in blueprint.formula_ids:
             if formula.name and formula.formula_expression:
                evaluated_value = self.safe_evaluate_formula(formula.formula_expression, variables)
                evaluated_variables[formula.name.name] = evaluated_value # Usar formula.name.name

        _logger.info(f"[Blueprint] Variables con valores evaluados: {evaluated_variables}")


        # Generar el SVG evaluado con las fórmulas ya resueltas
        evaluated_attachment_id = self._generate_evaluated_blueprint_svg(blueprint, evaluated_variables) # Pasamos evaluated_variables
        new_attachment = self.env["ir.attachment"].browse(evaluated_attachment_id)

        if new_attachment and new_attachment.datas:
            svg_data = base64.b64decode(new_attachment.datas).decode("utf-8")
            _logger.info(f"[Blueprint] SVG evaluado obtenido correctamente para {self.product_id.name}")
            return base64.b64encode(svg_data.encode()).decode()

        _logger.info(f"[Blueprint] No se pudo obtener el blueprint evaluado para {self.product_id.name}")
        return ""