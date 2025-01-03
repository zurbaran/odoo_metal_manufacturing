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


