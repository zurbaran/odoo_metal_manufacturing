### Módulo: Product Blueprint Manager

#### Descripción General:
El módulo **Product Blueprint Manager** está diseñado para gestionar planos de productos y generar documentos de forma dinámica en Odoo. Este módulo permite a los usuarios vincular documentos característicos (como planos en formato SVG) a productos, y generar documentos dinámicos con fórmulas integradas basadas en los atributos personalizados del producto, como plantilla configurada para cuando se realice un presupuesto dar valor a los atributos en la "Entrada de cuadrícula de variante", y esos atributos dan valor a las variables de las formulas contenidas en las plantilla preconfigurada como anteriormente se ha dicho.

#### Funcionalidades Principales:

1. **Gestión de Planos de Productos**:
    - **Vinculación de Documentos**: Permite a los usuarios vincular documentos en formato SVG a productos específicos.
    - **Almacenamiento de Planos**: Los planos se almacenan como archivos binarios en Odoo y están asociados a productos mediante la relación `One2many`.

2. **Fórmulas Dinámicas**:
    - **Definición de Fórmulas**: Los usuarios pueden definir fórmulas que se evaluarán dinámicamente. Estas fórmulas pueden usar variables basadas en los atributos personalizados del producto.
    - **Posicionamiento de Fórmulas**: Las fórmulas se pueden posicionar en coordenadas X e Y específicas dentro del plano SVG.

3. **Evaluación de Fórmulas en Presupuestos**:
    - **Captura de Valores Personalizados**: Durante la creación de presupuestos, se capturan los valores personalizados de los atributos del producto.
    - **Evaluación de Fórmulas**: Las fórmulas definidas se evalúan utilizando los valores personalizados capturados.
    - **Generación de Documentos Adicionales**: Una vez evaluadas las fórmulas, se genera un documento adicional del plano con las fórmulas evaluadas y se adjunta al presupuesto.

4. **Interfaz de Usuario**:
    - **Configuración del Producto**: En la vista de configuración del producto, se añaden pestañas para gestionar los planos y las fórmulas asociadas.
    - **Entrada de Cuadrícula de Variante**: Permite a los usuarios introducir valores para los atributos personalizados del producto durante la creación de presupuestos.

#### Casos de Uso:

1. **Industria de Manufactura**: Empresas que fabrican productos personalizados y necesitan generar planos específicos para cada producto basado en atributos personalizados.
2. **Ingeniería**: Firmas de ingeniería que requieren planos detallados y personalizados para sus productos o componentes.
3. **Diseño de Productos**: Diseñadores de productos que necesitan generar documentos detallados y personalizados para la producción o presentación de productos.

#### Beneficios:

- **Automatización**: Automatiza la generación de documentos personalizados, reduciendo la carga de trabajo manual y disminuyendo los errores.
- **Flexibilidad**: Permite una alta personalización de los documentos generados, adaptándose a las necesidades específicas de cada cliente o proyecto.
- **Integración**: Se integra perfectamente con el módulo de ventas de Odoo, permitiendo una gestión fluida desde la creación del producto hasta la generación del presupuesto y la entrega final del documento.

#### Componentes Técnicos:

1. **Modelos**:
    - `product.template`: Extendido para incluir `blueprint_ids` y `formula_ids`.
    - `product.blueprint`: Definido para almacenar los planos vinculados a productos.
    - `product.formula`: Definido para almacenar las fórmulas asociadas a los productos.
    - `sale.order.line`: Extendido para capturar y evaluar los valores personalizados durante la creación de presupuestos.

2. **Vistas**:
    - Vistas heredadas de `product.template` para incluir pestañas de gestión de planos y fórmulas.
    - Vistas heredadas de `sale.order.line` para capturar los valores personalizados y evaluar las fórmulas.

3. **Permisos de Seguridad**:
    - Reglas de acceso definidas para permitir la lectura y escritura en los modelos `product.blueprint` y `product.formula`.

4. **Acciones de Servidor**:
    - Acción de servidor para generar planos dinámicos basada en la evaluación de fórmulas.

    
### Flujo de Trabajo del Módulo `product_blueprint_manager`

1. **Configuración Inicial del Producto:**
   - **Paso 1:** El usuario crea o selecciona un producto en el formulario de `product.template`.
   - **Paso 2:** En la pestaña "Blueprints", el usuario puede añadir uno o más blueprints (planos) asociados al producto.
   - **Paso 3:** En la pestaña "Formulas", el usuario puede definir fórmulas que se aplicarán al blueprint. Estas fórmulas usan atributos personalizados del producto.

2. **Generación de Plantilla de Blueprint:**
   - **Paso 4:** El usuario pulsa el botón "Generate Blueprint" en el formulario del producto.
   - **Paso 5:** El método `generate_dynamic_blueprint` en el modelo `product.template` genera un archivo SVG dinámico. Este archivo incluye las fórmulas no evaluadas, indicadas con un formato especial (`{{ formula_expression }}`), y se añade al blueprint del producto.

3. **Proceso de Presupuesto:**
   - **Paso 6:** Durante la creación de un presupuesto, se capturan los valores personalizados de los atributos configurables del producto en el modelo `sale.order.line`.
   - **Paso 7:** El método `_capture_blueprint_custom_values` se asegura de que los valores de los atributos configurables se capturen y se almacenen en el campo `blueprint_custom_values`.

4. **Evaluación de Fórmulas en el Blueprint:**
   - **Paso 8:** En el momento de generar el presupuesto, se invoca el método `evaluate_formulas` en el modelo `product.template`.
   - **Paso 9:** Este método evalúa las fórmulas utilizando los valores personalizados capturados de los atributos configurables.
   - **Paso 10:** Las fórmulas evaluadas se colocan en el archivo SVG del blueprint, reemplazando los placeholders con los valores calculados.

5. **Generación del Documento Final:**
   - **Paso 11:** El archivo SVG del blueprint, ahora con las fórmulas evaluadas, se guarda y está listo para ser utilizado como documento final en el presupuesto o cualquier otro proceso necesario como documuento adicional adjunto al presupuesto, factura,....

Este flujo de trabajo asegura que los blueprints se creen con fórmulas no evaluadas inicialmente y se actualicen dinámicamente con valores personalizados durante el proceso de presupuesto.


Este modulo en desarrollo debe interaccionar con este otro (product_configurator_attribute_price), pero ambos tienen que guardar independencia. Ambos modulos comparten la parte en la que obtienen como valor para las variables de las formulas independientes de cada modulo el valor de los atributos cuando se hace un presupuesto, uno utiliza el valor de las variables para la modificación del precio (product_configurator_attribute_price) y el otro para generar los planos adjuntos (product_blueprint_manager). El modulo 


El modulo product_configurator_attribute_price contiene el siguiente arbol de archivos, funciona perfectamente asi que no quiero modificarlo, excepto que se necesitara modificar para poder utilizar el valor de los atributos configurables cuando se hace el presupuesto a disposicion de otro modulo.


antonio@oficina:~/Programas/odoo/odoo_metal_manufacturing$ cat product_configurator_attribute_price/__init__.py 
from . import models
antonio@oficina:~/Programas/odoo/odoo_metal_manufacturing$ cat product_configurator_attribute_price/__manifest__.py 
{
    'name': 'Product Configurator Attribute Price',
    'version': '16.0.2.0.0',
    'summary': 'Extiende la configuración de atributos en productos con cálculos dinámicos de precios',
    'description': '''
        Permite configurar productos con incrementos de precio basados en fórmulas:
        - Atributos personalizados (custom_value)
        - Incrementos fijos nativos (price_extra)
        - Incrementos acumulativos (price_so_far)
    ''',
    'author': 'Antonio Caballero',
    'maintainer': 'Antonio Caballero',
    'website': 'https://github.com/zurbaran/odoo_metal_manufacturing',
    'depends': ['sale', 'sale_product_configurator', 'product'],
    'data': [
        'views/product_template_attribute_value_view.xml',
        'views/sale_order_line_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'license': 'AGPL-3',
}
antonio@oficina:~/Programas/odoo/odoo_metal_manufacturing$ cat product_configurator_attribute_price/models/__init__.py 
from . import product_template_attribute_value
from . import sale_order_line
antonio@oficina:~/Programas/odoo/odoo_metal_manufacturing$ cat product_configurator_attribute_price/models/product_template_attribute_value.py 
from odoo import models, fields
from odoo.exceptions import ValidationError
import math
import logging

_logger = logging.getLogger(__name__)

class ProductTemplateAttributeValue(models.Model):
    _inherit = 'product.template.attribute.value'

    # Campo para definir una fórmula de precio
    price_formula = fields.Char(
        string="Price Formula",
        help="Define a formula to calculate the price variation dynamically. Use 'custom_value' and 'price_so_far' as variables."
    )

    def calculate_price_increment(self, custom_value, price_so_far):
        """
        Calcula el incremento de precio basado en la fórmula configurada.
        :param custom_value: Valor personalizado ingresado en la cuadrícula.
        :param price_so_far: Precio calculado del producto hasta el momento.
        :return: Incremento calculado como un número flotante.
        """
        _logger.info(f"Starting calculate_price_increment for attribute {self.name}")
        _logger.info(f"Formula: {self.price_formula}, custom_value: {custom_value}, price_so_far: {price_so_far}")

        if not self.price_formula:
            _logger.info(f"No price formula defined for attribute {self.name}. Using price_extra: {self.price_extra}")
            return self.price_extra  # Si no hay fórmula, usa el incremento fijo

        try:
            # Asegurarse de que custom_value y price_so_far sean números
            custom_value = float(custom_value)
            price_so_far = float(price_so_far)

            _logger.info(f"Evaluating formula: {self.price_formula}")
            _logger.info(f"custom_value: {custom_value}, price_so_far: {price_so_far}")

            # Variables adicionales que pueden ser útiles en las fórmulas
            variables = {
                'custom_value': custom_value,
                'price_so_far': price_so_far,
                'math': math  # Para permitir el uso de funciones de math
            }
            allowed_names = {"__builtins__": None}
            allowed_names.update(variables)

            # Evaluar la fórmula
            increment = eval(self.price_formula, {"__builtins__": None}, allowed_names)
            _logger.info(f"Result of formula evaluation: {increment}")

            # Asegurarse de que el incremento no sea negativo
            if increment < 0:
                _logger.warning(f"Negative increment calculated: {increment}. Resetting to 0.")
                increment = 0

            _logger.info(f"Increment calculated: {increment}")
            return float(increment)
        except Exception as e:
            _logger.error(f"Error evaluating formula for attribute '{self.name}': {e}")
            raise ValidationError(f"Error evaluating formula for attribute '{self.name}': {e}")
antonio@oficina:~/Programas/odoo/odoo_metal_manufacturing$ cat product_configurator_attribute_price/models/sale_order_line.py 
from odoo import models, api
import math
import logging

_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('product_id', 'product_custom_attribute_value_ids', 'product_no_variant_attribute_value_ids')
    def _compute_price_unit(self):
        """
        Calcula el precio unitario, aplicando fórmulas y ajustes específicos para atributos configurables.
        """
        for line in self:
            if not line.product_id:
                _logger.warning(f"[Line {line.id}] Producto no definido. Saltando cálculo.")
                continue

            # Precio inicial basado en el precio del producto
            price_so_far = line.product_id.lst_price
            _logger.info(f"[Line {line.id}] Precio inicial: {price_so_far}")

            # Procesar atributos de tipo "medida" (custom_value)
            for custom_attribute in line.product_custom_attribute_value_ids:
                attribute_value = custom_attribute.custom_product_template_attribute_value_id

                if attribute_value and attribute_value.price_formula and 'custom_value' in attribute_value.price_formula:
                    try:
                        custom_value = float(custom_attribute.custom_value or 0)
                        increment = eval(
                            attribute_value.price_formula,
                            {"custom_value": custom_value, "price_so_far": price_so_far, "math": math}
                        )
                        price_so_far += increment
                        _logger.info(f"[Line {line.id}] Incremento por custom_value ({attribute_value.name}): {increment}")
                    except Exception as e:
                        _logger.error(f"[Line {line.id}] Error al evaluar la fórmula para {attribute_value.name}: {e}")
                        continue

            # Procesar atributos de tipo "price_so_far"
            for no_variant_attribute in line.product_no_variant_attribute_value_ids:
                if no_variant_attribute and no_variant_attribute.price_formula and 'price_so_far' in no_variant_attribute.price_formula:
                    try:
                        increment = eval(
                            no_variant_attribute.price_formula,
                            {"price_so_far": price_so_far, "math": math}
                        )
                        price_so_far += increment
                        _logger.info(f"[Line {line.id}] Incremento por price_so_far ({no_variant_attribute.name}): {increment}")
                    except Exception as e:
                        _logger.error(f"[Line {line.id}] Error al evaluar la fórmula para {no_variant_attribute.name}: {e}")
                        continue

            # Aplicar price_extra después de procesar las fórmulas
            for custom_attribute in line.product_custom_attribute_value_ids:
                attribute_value = custom_attribute.custom_product_template_attribute_value_id
                if attribute_value and attribute_value.price_extra:
                    price_so_far += attribute_value.price_extra
                    _logger.info(f"[Line {line.id}] Incremento por price_extra ({attribute_value.name}): {attribute_value.price_extra}")

            for no_variant_attribute in line.product_no_variant_attribute_value_ids:
                if no_variant_attribute and no_variant_attribute.price_extra:
                    price_so_far += no_variant_attribute.price_extra
                    _logger.info(f"[Line {line.id}] Incremento por price_extra ({no_variant_attribute.name}): {no_variant_attribute.price_extra}")

            # Asignar precio final al campo price_unit
            line.price_unit = price_so_far
            _logger.info(f"[Line {line.id}] Precio final calculado: {line.price_unit}")
antonio@oficina:~/Programas/odoo/odoo_metal_manufacturing$ cat product_configurator_attribute_price/security/ir.model.access.csv 
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_product_template_attribute_value,access.product.template.attribute.value,model_product_template_attribute_value,base.group_user,1,1,1,1
access_sale_order_line,access.sale.order.line,model_sale_order_line,base.group_user,1,1,1,1
antonio@oficina:~/Programas/odoo/odoo_metal_manufacturing$ cat product_configurator_attribute_price/views/__init__.py 
from . import product_template_attribute_value_view
from . import sale_order_line_view
antonio@oficina:~/Programas/odoo/odoo_metal_manufacturing$ cat product_configurator_attribute_price/views/product_template_attribute_value_view.xml 
<odoo>
    <record id="view_product_template_attribute_value_form_inherit" model="ir.ui.view">
        <field name="name">product.template.attribute.value.form.inherit</field>
        <field name="model">product.template.attribute.value</field>
        <field name="inherit_id" ref="product.product_template_attribute_value_view_form"/>
        <field name="arch" type="xml">
            <xpath expr="//field[@name='price_extra']" position="after">
                <field name="price_formula" string="Fórmula de Precio" placeholder="Ejemplos: (math.ceil(custom_value / 50) * 50 - 950) // 50 * 4 o (price_so_far * 0.2)"/>
            </xpath>
        </field>
    </record>
</odoo>
antonio@oficina:~/Programas/odoo/odoo_metal_manufacturing$ cat product_configurator_attribute_price/views/sale_order_line_view.xml 
<odoo>
    <record id="view_sale_order_line_form_inherit" model="ir.ui.view">
        <field name="name">sale.order.line.form.inherit.product.configurator</field>
        <field name="model">sale.order.line</field>
        <field name="inherit_id" ref="sale.view_order_form"/>
        <field name="arch" type="xml">
            <xpath expr="//field[@name='order_line']/form/sheet/group/field[@name='price_unit']" position="after">
                <field name="price_modified" readonly="1"/>
            </xpath>
        </field>
    </record>
</odoo>


El modulo en fase de desarrollo product_blueprint_manager actualmente esta en este estado y no funciona como se espera. Lo pego aqui para poder seguir avanzando sobre el. Pudiera ser que existan archivos inecesarios, redundantes,.....


antonio@oficina:~/workspace/odoo_metal_manufacturing$ cat product_blueprint_manager/__init__.py 
from . import models
antonio@oficina:~/workspace/odoo_metal_manufacturing$ cat product_blueprint_manager/__manifest__.py 
{
    'name': 'Product Blueprint Manager',
    'version': '16.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Gestione planos de productos y genere documentos de forma dinámica.',
    'description': '''
        Este módulo permite la gestión de planos de productos, incluyendo
        la vinculación de documentos característicos y la generación de documentos dinámicos
        con fórmulas integradas basadas en atributos de producto.
    ''',
    'author': 'Antonio Caballero',
    'maintainer': 'Antonio Caballero',
    'website': 'https://github.com/zurbaran/odoo_metal_manufacturing',
    'depends': ['product', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
        'views/menu_views.xml',
        #'data/product_blueprint_demo.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'AGPL-3',
}
antonio@oficina:~/workspace/odoo_metal_manufacturing$ cat product_blueprint_manager/models/__init__.py 
from . import product_blueprint
from . import product_formula
from . import product_template_extension
from . import sale_order_line
antonio@oficina:~/workspace/odoo_metal_manufacturing$ cat product_blueprint_manager/models/product_blueprint.py 
from odoo import models, fields

class ProductBlueprint(models.Model):
    _name = 'product.blueprint'
    _description = 'Product Blueprint'

    name = fields.Char('Document Name', required=True)
    file = fields.Binary('SVG File', attachment=True)
    filename = fields.Char('File Name')
    product_id = fields.Many2one('product.template', string='Product', required=True)
antonio@oficina:~/workspace/odoo_metal_manufacturing$ cat product_blueprint_manager/models/product_formula.py 
from odoo import models, fields, api

class ProductFormula(models.Model):
    _name = 'product.formula'
    _description = 'Product Formula'

    name = fields.Char('Formula Name', required=True)
    formula_expression = fields.Char('Formula Expression', required=True)
    product_id = fields.Many2one('product.template', string='Product', required=True)
    blueprint_id = fields.Many2one('product.blueprint', string='Blueprint', required=True, help="El blueprint al que pertenece esta fórmula.")
    position_x = fields.Float('Position X', required=True, help="La coordenada X para posicionar la fórmula en el plano.")
    position_y = fields.Float('Position Y', required=True, help="La coordenada Y para posicionar la fórmula en el plano.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'product_id' in vals:
                product = self.env['product.template'].browse(vals['product_id'])
                variable_names = product.get_attribute_variable_names()
                # Aquí podrías agregar lógica para validar que `formula_expression` use los nombres de variables adecuados
        return super(ProductFormula, self).create(vals_list)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            variable_names = self.product_id.get_attribute_variable_names()
            # Aquí podrías agregar lógica para actualizar `formula_expression` con los nombres de variables disponibles
antonio@oficina:~/workspace/odoo_metal_manufacturing$ cat product_blueprint_manager/models/product_template_extension.py 
from odoo import models, fields, api
import base64
from lxml import etree
import logging

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    blueprint_ids = fields.One2many('product.blueprint', 'product_id', string='Blueprints')
    formula_ids = fields.One2many('product.formula', 'product_id', string='Formulas')

    def get_custom_attribute_values(self, sale_order_line=None):
        """
        Obtiene los valores personalizados (custom_value) de los atributos configurables del producto desde `sale.order.line`.
        """
        return sale_order_line.blueprint_custom_values if sale_order_line else {}

    def get_attribute_variable_names(self):
        """
        Obtiene los nombres de las variables (atributos personalizados) configuradas en el producto.
        """
        variable_names = []
        for attribute_line in self.attribute_line_ids:
            for value in attribute_line.value_ids:
                variable_names.append(value.name)
        return variable_names

    def generate_dynamic_blueprint(self):
        """
        Genera un archivo SVG dinámico con las fórmulas no evaluadas.
        """
        for product in self:
            for blueprint in product.blueprint_ids:
                if not blueprint.file:
                    _logger.warning(f"Blueprint sin archivo SVG para el producto: {product.name}")
                    continue

                # Decodificar el archivo SVG
                svg_data = base64.b64decode(blueprint.file)
                root = etree.fromstring(svg_data)

                # Añadir las fórmulas no evaluadas al SVG
                for formula in product.formula_ids.filtered(lambda f: f.blueprint_id == blueprint):
                    try:
                        # Crear un nuevo elemento de texto en el SVG con la fórmula no evaluada
                        text_element = etree.Element("text", x=str(formula.position_x), y=str(formula.position_y))
                        text_element.text = f'{{{{ {formula.formula_expression} }}}}'  # Usar {{ }} para indicar una fórmula no evaluada
                        root.append(text_element)
                    except Exception as e:
                        _logger.error(f"Error al añadir la fórmula para {product.name}: {e}")
                        continue

                # Guardar el archivo actualizado en el blueprint
                blueprint.file = base64.b64encode(etree.tostring(root)).decode('utf-8')
                _logger.info(f"Blueprint generado dinámicamente con fórmulas no evaluadas para el producto: {product.name}")

    def evaluate_formulas(self, custom_values):
        """
        Evalúa las fórmulas con los valores personalizados y genera el documento adicional.
        """
        for blueprint in self.blueprint_ids:
            if not blueprint.file:
                _logger.warning(f"Blueprint sin archivo SVG para el producto: {self.name}")
                continue

            # Decodificar el archivo SVG
            svg_data = base64.b64decode(blueprint.file)
            root = etree.fromstring(svg_data)

            # Reemplazar los placeholders con valores reales y posicionar las fórmulas
            for formula in self.formula_ids.filtered(lambda f: f.blueprint_id == blueprint):
                try:
                    # Evaluar la expresión de la fórmula
                    formula_result = eval(formula.formula_expression, {}, custom_values)
                    # Crear un nuevo elemento de texto en el SVG
                    text_element = etree.Element("text", x=str(formula.position_x), y=str(formula.position_y))
                    text_element.text = str(formula_result)
                    # Añadir el elemento de texto al SVG
                    root.append(text_element)
                except Exception as e:
                    _logger.error(f"Error al procesar la fórmula para {self.name}: {e}")
                    continue

            # Guardar el archivo actualizado en el blueprint
            blueprint.file = base64.b64encode(etree.tostring(root)).decode('utf-8')
            _logger.info(f"Blueprint generado dinámicamente para el producto: {self.name}")
antonio@oficina:~/workspace/odoo_metal_manufacturing$ cat product_blueprint_manager/models/sale_order_line.py 
from odoo import models, fields, api
import base64
from lxml import etree
import logging

_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('product_id', 'product_custom_attribute_value_ids')
    def _capture_blueprint_custom_values(self):
        """
        Captura los valores de custom_value durante el proceso de presupuesto.
        """
        for line in self:
            blueprint_custom_values = {}
            for custom_attribute in line.product_custom_attribute_value_ids:
                attribute_value = custom_attribute.custom_product_template_attribute_value_id
                if attribute_value:
                    custom_value = custom_attribute.custom_value
                    blueprint_custom_values[attribute_value.name] = custom_value
            self.blueprint_custom_values = blueprint_custom_values
            # Solo evaluar las fórmulas si están definidas en el producto
            if hasattr(self.product_id.product_tmpl_id, 'evaluate_formulas'):
                self.product_id.product_tmpl_id.evaluate_formulas(blueprint_custom_values)

    blueprint_custom_values = fields.Char(compute='_capture_blueprint_custom_values', string='Blueprint Custom Values')
antonio@oficina:~/workspace/odoo_metal_manufacturing$ cat product_blueprint_manager/models/blueprint_generator.py 
 
import base64
from io import BytesIO
from reportlab.pdfgen import canvas
from odoo import models, fields

class BlueprintGenerator(models.Model):
    _inherit = 'product.template'

    def generate_blueprints(self):
        for product in self:
            variables = {attr.name: attr.value for attr in product.attribute_value_ids}
            for formula in product.formula_ids:
                result = eval(formula.formula_expression, {}, variables)
                
                buffer = BytesIO()
                c = canvas.Canvas(buffer)
                c.drawString(100, 750, f"Product: {product.name}")
                c.drawString(100, 700, f"Formula ({formula.name}): {result}")
                c.save()
                buffer.seek(0)

                self.env['product.blueprint'].create({
                    'name': f'{product.name} Blueprint',
                    'file': base64.b64encode(buffer.read()),
                    'product_id': product.id
                })
antonio@oficina:~/workspace/odoo_metal_manufacturing$ cat product_blueprint_manager/models/product_attribute.py 
 
from odoo import models, fields

class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    is_custom = fields.Boolean(string="Es valor personalizable", default=False)
antonio@oficina:~/workspace/odoo_metal_manufacturing$ cat product_blueprint_manager/models/product_formula_expression.py 
from odoo import models, fields

class ProductFormulaExpression(models.Model):
    _name = 'product.formula.expression'
    _description = 'Product Formula Expression'

    name = fields.Char('Expression', required=True)
antonio@oficina:~/workspace/odoo_metal_manufacturing$ cat product_blueprint_manager/security/ir.model.access.csv 
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_product_blueprint,access.product.blueprint,model_product_blueprint,,1,1,1,1
access_product_formula,access.product.formula,model_product_formula,,1,1,1,1
access_product_formula_expression,access.product.formula.expression,model_product_formula_expression,,1,1,1,1
antonio@oficina:~/workspace/odoo_metal_manufacturing$ cat product_blueprint_manager/views/__init__.py 
from . import menu_views
from . import product_views
antonio@oficina:~/workspace/odoo_metal_manufacturing$ cat product_blueprint_manager/views/menu_views.xml 
<odoo>
    <menuitem id="menu_product_blueprints_root" name="Product Blueprints"/>
    <menuitem id="menu_product_blueprints" name="Blueprints" parent="menu_product_blueprints_root"/>
    <menuitem id="menu_product_formulas" name="Formulas" parent="menu_product_blueprints_root"/>
</odoo>
antonio@oficina:~/workspace/odoo_metal_manufacturing$ cat product_blueprint_manager/views/product_views.xml 
<odoo>
    <record id="view_product_template_form" model="ir.ui.view">
        <field name="name">product.template.form</field>
        <field name="model">product.template</field>
        <field name="inherit_id" ref="product.product_template_only_form_view"/>
        <field name="arch" type="xml">
            <xpath expr="//header" position="inside">
                <button name="generate_dynamic_blueprint" string="Generate Blueprint" type="object" class="oe_highlight"/>
            </xpath>
            <xpath expr="//sheet/notebook/page[@name='general_information']" position="inside">
                <page string="Blueprints">
                    <field name="blueprint_ids">
                        <tree>
                            <field name="name"/>
                            <field name="filename"/>
                        </tree>
                        <form>
                            <sheet>
                                <group>
                                    <field name="name"/>
                                    <field name="filename"/>
                                    <field name="file" filename="filename"/>
                                </group>
                            </sheet>
                        </form>
                    </field>
                </page>
                <page string="Formulas">
                    <field name="formula_ids">
                        <tree>
                            <field name="name"/>
                            <field name="formula_expression"/>
                            <field name="blueprint_id"/>
                        </tree>
                        <form>
                            <sheet>
                                <group>
                                    <field name="name"/>
                                    <field name="formula_expression"/>
                                    <field name="blueprint_id"/>
                                    <field name="position_x"/>
                                    <field name="position_y"/>
                                </group>
                            </sheet>
                        </form>
                    </field>
                </page>
            </xpath>
        </field>
    </record>
</odoo>

