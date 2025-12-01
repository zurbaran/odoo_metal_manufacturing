from odoo.tests.common import TransactionCase


# Esta batería de tests valida el comportamiento del hook
# `product.configurator.attribute.hook`, que sirve como punto de integración
# entre el configurador de productos y otros módulos (por ejemplo, planos /
# blueprints). El objetivo es comprobar que el hook devuelve un diccionario
# con los valores de atributos personalizados en el formato esperado.
class TestHookBehavior(TransactionCase):
    # Usamos TransactionCase porque se crean registros reales en la base de
    # datos (mediante `create()`), y no simples registros transient con `new()`.
    def test_hook_returns_attribute_values(self):
        # Obtenemos el modelo del hook. Según la configuración del módulo,
        # esto puede heredar de `product.blueprint.attribute.hook` o ser un
        # modelo propio (`product.configurator.attribute.hook`), pero desde
        # los tests siempre lo invocamos mediante este nombre genérico.
        hook = self.env["product.configurator.attribute.hook"]

        # Creamos un atributo de producto sencillo llamado "Color".
        attr = self.env["product.attribute"].create({"name": "Color"})

        # Creamos un valor de atributo de plantilla asociado al atributo "Color".
        # Este PTAV será el que referencie el valor personalizado en la línea.
        ptav = self.env["product.template.attribute.value"].create(
            {"name": "Rojo", "attribute_id": attr.id}
        )

        # Creamos una línea de pedido de venta mínima. No necesitamos producto
        # ni otros campos para este test, solo una línea para asociarle el valor
        # personalizado.
        line = self.env["sale.order.line"].create({})

        # Creamos el valor personalizado del atributo. Este registro enlaza:
        # - la línea de pedido (`sale_order_line_id`)
        # - el valor de atributo de plantilla
        #  (`custom_product_template_attribute_value_id`)
        # - y el valor numérico concretado por el usuario (`custom_value`)
        cav = self.env["product.custom.attribute.value"].create(
            {
                "sale_order_line_id": line.id,
                "custom_product_template_attribute_value_id": ptav.id,
                "custom_value": 123,
            }
        )

        # Ejecutamos el hook para recuperar los valores de atributos
        # personalizados asociados a la línea. Se espera un diccionario donde
        # la clave es el nombre del atributo (por ejemplo, "Color") y el valor
        # es el resultado del método `eval()` del registro `custom_value`
        # (si existe) o, en su defecto, el valor numérico almacenado.
        result = hook.get_attribute_values_for_blueprint(line)

        # Comprobamos que el diccionario devuelto contiene la clave "Color" y
        # que su valor coincide con:
        # - `cav.eval()` si el método existe (permite lógica adicional
        #   de evaluación), o
        # - `123` (valor bruto de `custom_value`) como fallback.
        self.assertEqual(result["Color"], cav.eval() if hasattr(cav, "eval") else 123)
