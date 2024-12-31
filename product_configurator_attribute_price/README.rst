### Descripción Detallada del Módulo `Product Configurator Attribute Price`

#### Introducción

El módulo `Product Configurator Attribute Price` extiende la funcionalidad de configuración de productos en Odoo, permitiendo la definición de fórmulas dinámicas para calcular incrementos de precio basados en atributos personalizados. Este módulo es especialmente útil para empresas que necesitan ajustar los precios de sus productos en función de características específicas, como medidas personalizadas o colores.

#### Funcionalidades Principales

1. **Definición de Fórmulas de Precio:**
   - **Campo `price_formula`:** Permite definir fórmulas de precio dinámicas utilizando variables como `custom_value` y `price_so_far`. 
     - `custom_value`: Utilizado para atributos que requieren valores personalizados, como medidas. Este valor se ingresa a través de la "Entrada de cuadrícula de variante" en el presupuesto.
     - `price_so_far`: Utilizado para aplicar incrementos acumulativos basados en el precio calculado hasta el momento. Este acumulador considera los incrementos de otros atributos y el `price_extra`.

2. **Compatibilidad con Incrementos Fijos (`price_extra`):**
   - **Campo `price_extra`:** Mantiene la funcionalidad nativa de Odoo para incrementos fijos. Este campo se aplica después de calcular las fórmulas definidas en `price_formula`.

3. **Cálculo Dinámico del Precio Unitario:**
   - **Modelo `sale.order.line`:** Calcula el precio unitario de los productos en las líneas de pedido de venta considerando las fórmulas definidas y los incrementos fijos. El cálculo sigue el orden: primero atributos de tipo "medida" (`custom_value`), luego atributos con `price_so_far`, y finalmente `price_extra`.

#### Estructura del Módulo

- **`__init__.py`:** Inicializa el módulo y carga los modelos.
- **`__manifest__.py`:** Contiene la configuración y metadatos del módulo.
- **`models/__init__.py`:** Inicializa los modelos definidos en el módulo.
- **`models/product_template_attribute_value.py`:** Define el modelo `product.template.attribute.value` con la funcionalidad de cálculo de precios basada en fórmulas.
- **`models/sale_order_line.py`:** Define el modelo `sale.order.line` para calcular el precio unitario basado en los atributos configurables.
- **`security/ir.model.access.csv`:** Define los permisos de acceso para los modelos.
- **`views/__init__.py`:** Inicializa las vistas definidas en el módulo.
- **`views/product_template_attribute_value_view.xml`:** Define la vista para el modelo `product.template.attribute.value`, añadiendo el campo `price_formula`.
- **`views/sale_order_line_view.xml`:** Define la vista para el modelo `sale.order.line`, añadiendo un campo adicional para mostrar el precio modificado.

#### Descripción de los Archivos del Módulo

1. **`__init__.py`:** 
   - Importa y carga los modelos del módulo.

2. **`__manifest__.py`:**
   - Define la configuración del módulo, incluyendo su nombre, versión, resumen, descripción detallada, autor, mantenedor, dependencias y datos a cargar.

3. **`models/__init__.py`:**
   - Inicializa y carga los modelos `product_template_attribute_value` y `sale_order_line`.

4. **`models/product_template_attribute_value.py`:**
   - Extiende el modelo `product.template.attribute.value` de Odoo.
   - Añade el campo `price_formula` para definir fórmulas de precio dinámicas.
   - Implementa el método `calculate_price_increment` que evalúa la fórmula y calcula el incremento de precio basado en `custom_value` y `price_so_far`.

5. **`models/sale_order_line.py`:**
   - Extiende el modelo `sale.order.line` de Odoo.
   - Implementa el método `_compute_price_unit` que calcula el precio unitario de los productos considerando las fórmulas en `price_formula` y los incrementos fijos en `price_extra`.
   - Procesa los atributos en el siguiente orden: primero atributos de tipo "medida" (`custom_value`), luego atributos con `price_so_far`, y finalmente `price_extra`.

6. **`security/ir.model.access.csv`:**
   - Define los permisos de acceso para los modelos `product.template.attribute.value` y `sale.order.line`.

7. **`views/__init__.py`:**
   - Importa y carga las vistas del módulo.

8. **`views/product_template_attribute_value_view.xml`:**
   - Extiende la vista del modelo `product.template.attribute.value`.
   - Añade el campo `price_formula` para permitir la definición de fórmulas de precio directamente desde la interfaz de usuario.
   - Proporciona ejemplos de cómo usar las fórmulas en el `placeholder` del campo.

9. **`views/sale_order_line_view.xml`:**
   - Extiende la vista del modelo `sale.order.line`.
   - Añade un campo adicional `price_modified` para mostrar el precio modificado después de aplicar las fórmulas y los incrementos fijos.

#### Uso del Módulo

1. **Configuración de Atributos:**
   - Navega a la configuración de atributos del producto.
   - Define las fórmulas de precio en el campo `price_formula` utilizando `custom_value` y `price_so_far`.

2. **Creación de Presupuestos:**
   - Al crear un presupuesto, ingresa los valores personalizados (como medidas) a través de la "Entrada de cuadrícula de variante".
   - El sistema calculará automáticamente el precio unitario considerando las fórmulas definidas y los incrementos fijos.

3. **Verificación de Cálculos:**
   - Revisa los logs para verificar los cálculos y los incrementos aplicados.
   - Asegúrate de que los valores se calculen correctamente según las fórmulas y los incrementos fijos configurados.

Este módulo proporciona una forma flexible y dinámica de ajustar los precios de los productos en función de atributos específicos, mejorando la precisión y eficiencia en la configuración de productos y la creación de presupuestos en Odoo.
