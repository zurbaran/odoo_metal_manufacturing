# ---------------------------------------------------------------------------
# Extensión de sale.order.line para:
#   - Gestionar valores personalizados de atributos (custom_value) en líneas.
#   - Calcular el precio final combinando:
#       * Precio base de Odoo.
#       * Fórmulas en atributos (price_formula).
#       * Incrementos fijos de atributo (price_extra).
#   - Construir una descripción detallada de la línea con todos los atributos
#     (variant, no_variant y personalizados) evitando duplicados.
# ---------------------------------------------------------------------------
import logging

from odoo import api, fields, models

# Logger para trazar el proceso de cálculo de precios y descripción de líneas
_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    # -----------------------------------------------------------------------
    # Campos adicionales
    # -----------------------------------------------------------------------

    # Relación 1:N con los valores personalizados de atributos asociados
    # a la línea de pedido de venta. Cada registro almacena:
    #   - El atributo de plantilla (product.template.attribute.value).
    #   - El valor numérico introducido (custom_value).
    product_custom_attribute_value_ids = fields.One2many(
        "product.custom.attribute.value",
        "sale_order_line_id",
        string="Valores personalizados de atributos",
    )

    # Campo calculado que refleja el precio final que se ha modificado
    # mediante las fórmulas y los incrementos de atributo.
    # No se almacena, solo se muestra para referencia.
    price_modified = fields.Monetary(
        string="Precio Modificado",
        currency_field="currency_id",
        compute="_compute_price_modified",
        store=False,
    )

    @api.depends("price_unit")
    def _compute_price_modified(self):
        """
        Mantiene price_modified sincronizado con price_unit.

        Este método existe principalmente como campo de "apoyo visual" para
        mostrar el precio resultante del cálculo de fórmulas, sin cambiar la
        lógica nativa de almacenamiento de Odoo (price_unit es el real).
        """
        for line in self:
            line.price_modified = line.price_unit

    # -----------------------------------------------------------------------
    # Onchange de producto: punto central de cálculo de precio y descripción
    # -----------------------------------------------------------------------
    @api.onchange(
        "product_id",
        "product_uom_qty",
        "product_uom",
        "order_id",
        "product_custom_attribute_value_ids",
        "product_no_variant_attribute_value_ids",
        "product_template_attribute_value_ids",
    )
    def _onchange_product_id(self):
        """
        Sobrescribe el onchange de producto para:

        1) Tomar el precio calculado por Odoo como base (price_unit).
        2) Aplicar las fórmulas definidas en los atributos:
           - Fórmulas basadas en 'custom_value'.
           - Fórmulas basadas en 'price_so_far'.
        3) Sumar los incrementos fijos 'price_extra' de todos los atributos.
        4) Redondear con la moneda de la línea y fijar el price_unit final.
        5) Construir una descripción detallada de la línea, listando:
           - Atributos de variante.
           - Atributos no_variant (con cuidado de no duplicar los custom).
           - Atributos personalizados con su valor numérico.
        """
        # Llamada al comportamiento estándar de Odoo (cálculo base de precio,
        # impuestos, etc.), que será el punto de partida de nuestro cálculo.
        res = super()._onchange_product_id()

        for line in self:
            # Si no hay producto, no hay nada que recalcular.
            if not line.product_id:
                continue

            # Tomamos como base el precio calculado por Odoo.
            price_so_far = line.price_unit
            _logger.debug(f"[Line {line.id}] Base Odoo: {price_so_far}")

            # ----------------------------------------------------------------
            # A) Fórmulas que utilizan 'custom_value'
            #    (atributos personalizados en la cuadrícula)
            # ----------------------------------------------------------------
            for cav in line.product_custom_attribute_value_ids:
                # PTAV al que está ligado el valor personalizado
                ptav = cav.custom_product_template_attribute_value_id
                if not ptav:
                    continue

                # Obtenemos la posible fórmula definida en el PTAV
                formula = getattr(ptav, "price_formula", False)
                # Solo aplicamos si hay fórmula y hace referencia a 'custom_value'
                if not formula or "custom_value" not in formula:
                    continue
                try:
                    # El valor introducido por el usuario para este atributo
                    cv = float(cav.custom_value or 0.0)
                    # Se delega en el PTAV el cálculo concreto del incremento
                    incr = ptav.calculate_price_increment(cv, price_so_far)
                except Exception as e:
                    # Ante cualquier error en la evaluación de la fórmula,
                    # registramos el problema pero evitamos que reviente el flujo.
                    _logger.exception(
                        "[Line %s] Error evaluando fórmula %r en %s: %s",
                        line.id,
                        formula,
                        ptav.display_name,
                        e,
                    )
                    incr = 0.0

                # Acumulamos el incremento calculado
                price_so_far += incr

            # ----------------------------------------------------------------
            # B) Fórmulas que utilizan 'price_so_far'
            #    (atributos no_variant y variante que ajustan el precio
            #     en función del precio acumulado hasta el momento)
            # ----------------------------------------------------------------

            # 1) Atributos no_variant (product_no_variant_attribute_value_ids)
            for nav in line.product_no_variant_attribute_value_ids:
                formula = getattr(nav, "price_formula", False)
                # Solo aplicamos si la fórmula hace referencia a 'price_so_far'
                if formula and "price_so_far" in formula:
                    try:
                        incr = nav.calculate_price_increment(0.0, price_so_far)
                    except Exception as e:
                        _logger.exception(
                            "[Line %s] Error fórmula %r en %s: %s",
                            line.id,
                            formula,
                            nav.display_name,
                            e,
                        )
                        incr = 0.0
                    price_so_far += incr

            # 2) Atributos de variante (product_template_attribute_value_ids)
            for ptav in line.product_template_attribute_value_ids:
                formula = getattr(ptav, "price_formula", False)
                if formula and "price_so_far" in formula:
                    try:
                        incr = ptav.calculate_price_increment(0.0, price_so_far)
                    except Exception as e:
                        _logger.exception(
                            "[Line %s] Error fórmula %r en %s: %s",
                            line.id,
                            formula,
                            ptav.display_name,
                            e,
                        )
                        incr = 0.0
                    price_so_far += incr

            # ----------------------------------------------------------------
            # C) Sumar los incrementos fijos 'price_extra'
            #    (se suman al final sobre el precio ya ajustado)
            # ----------------------------------------------------------------
            # Atributos personalizados
            for cav in line.product_custom_attribute_value_ids:
                ptav = cav.custom_product_template_attribute_value_id
                price_so_far += ptav.price_extra or 0.0

            # Atributos no_variant
            for nav in line.product_no_variant_attribute_value_ids:
                price_so_far += nav.price_extra or 0.0

            # Atributos de variante
            for ptav in line.product_template_attribute_value_ids:
                price_so_far += ptav.price_extra or 0.0

            # Redondeo final con la moneda de la línea y asignación del precio
            final_price = line.currency_id.round(price_so_far)
            line.price_unit = final_price
            _logger.info("[Line %s] Precio final calculado: %s", line.id, final_price)

            # ----------------------------------------------------------------
            # Construcción de la descripción de la línea (line.name)
            # ----------------------------------------------------------------
            _logger.debug("[Line %s] === INICIO descripción personalizada ===", line.id)

            # ...............................................................
            # Dump de los atributos personalizados (para debugging detallado)
            # ...............................................................
            for cav in line.product_custom_attribute_value_ids:
                ptav = cav.custom_product_template_attribute_value_id
                _logger.debug(
                    "[Line %s] CUSTOM -> Atributo: %s, PTAV: %s (%s), Valor: %s",
                    line.id,
                    ptav.attribute_id.name if ptav and ptav.attribute_id else "N/A",
                    ptav.name if ptav else "N/A",
                    ptav.id if ptav else "N/A",
                    cav.custom_value,
                )

            # Dump de los atributos no_variant (también solo informativo)
            for nav in line.product_no_variant_attribute_value_ids:
                _logger.debug(
                    "[Line %s] NO_VARIANT -> Atributo: %s, PTAV: %s (%s)",
                    line.id,
                    nav.attribute_id.name if nav.attribute_id else "N/A",
                    nav.name,
                    nav.id,
                )

            # Lista de líneas de descripción a mostrar bajo el nombre del producto
            descriptions = []

            # ----------------------------------------------------------------
            # Recolectar los PTAV que se usan como "custom" para evitar
            # duplicar información cuando también aparecen como no_variant.
            # Se trabaja con _origin.id para evitar problemas con registros
            # "new" (no guardados aún).
            # ----------------------------------------------------------------
            custom_ptav_ids = {
                cav.custom_product_template_attribute_value_id._origin.id
                for cav in line.product_custom_attribute_value_ids
                if cav.custom_product_template_attribute_value_id
            }

            # ----------------------------------------------------------------
            # Atributos tipo variante
            #   Se muestran siempre como: "<Nombre Atributo>: <Nombre Valor>"
            # ----------------------------------------------------------------
            for ptav in line.product_template_attribute_value_ids:
                if ptav.attribute_id and ptav.name:
                    descriptions.append(f"{ptav.attribute_id.name}: {ptav.name}")

            # ----------------------------------------------------------------
            # Atributos tipo no_variant
            #   Se muestran solo si NO tienen un valor personalizado asociado
            #   para el mismo PTAV (evitar duplicados).
            # ----------------------------------------------------------------
            for nav in line.product_no_variant_attribute_value_ids:
                # Si este PTAV ya está recogido como custom, se omite aquí
                if nav._origin.id in custom_ptav_ids:
                    _logger.debug(
                        "[Line %s] SKIP NO_VARIANT por estar en CUSTOM \
                              (por _origin.id) -> PTAV %s (%s)",
                        line.id,
                        nav.name,
                        nav._origin.id,
                    )
                    continue  # ya se muestra con valor

                if nav.attribute_id and nav.name:
                    descriptions.append(f"{nav.attribute_id.name}: {nav.name}")

            # ----------------------------------------------------------------
            # Atributos personalizados con valor numérico
            #   Formato: "<Nombre Atributo>: <Nombre PTAV>: <Valor>"
            #   Ejemplo: "Alto: mmA: 1456.0"
            # ----------------------------------------------------------------
            for cav in line.product_custom_attribute_value_ids:
                ptav = cav.custom_product_template_attribute_value_id
                if ptav and ptav.attribute_id:
                    attribute_name = ptav.attribute_id.name
                    value_label = cav.custom_value
                    descriptions.append(f"{attribute_name}: {ptav.name}: {value_label}")

            # ----------------------------------------------------------------
            # Construcción del texto final en line.name:
            #   - Primera línea: nombre del producto.
            #   - Siguientes líneas: descripción de atributos (si existen).
            # ----------------------------------------------------------------
            if descriptions:
                line.name = f"{line.product_id.display_name}\n" + "\n".join(
                    descriptions
                )
            else:
                line.name = line.product_id.display_name

        # Se devuelve el diccionario original del onchange (por compatibilidad)
        return res
