## Product Blueprint Manager para Odoo: Descripción Detallada y Guía de Uso

**Introducción:**

El módulo "Product Blueprint Manager" para Odoo extiende las capacidades de gestión de productos, permitiendo integrar planos técnicos (en formato SVG) directamente en tus procesos de venta. Lo más potente de este módulo es su capacidad para **evaluar fórmulas matemáticas dentro del propio plano**, mostrando información dinámica y personalizada en los documentos de venta (presupuestos, pedidos, facturas). Esto es ideal para empresas que fabrican productos a medida o con características variables.

**¿Para qué sirve?**

Imagina que vendes ventanas personalizadas. Cada cliente puede elegir el ancho, el alto, el tipo de cristal, etc. Con Product Blueprint Manager, puedes:

1.  **Subir un plano SVG** de una ventana genérica.
2.  **Definir fórmulas** que calculen, por ejemplo, el área del cristal o la longitud del marco, basándose en las dimensiones elegidas por el cliente.
3.  **Visualizar estos cálculos *directamente* sobre el plano** en el presupuesto o pedido de venta, sin tener que editar manualmente el archivo SVG.

El módulo elimina errores manuales, automatiza la presentación de información técnica y mejora la claridad de tus documentos comerciales.

**Dependencias:**

*   `product` (Módulo estándar de Odoo)
*   `sale` (Módulo estándar de Odoo)
*   `sale_management` (Módulo estándar de Odoo)
*   `product_configurator_attribute_price`: **Crucial**. Este módulo es el que permite definir los atributos personalizados (ej. "Ancho", "Alto") y sus valores en las líneas de pedido. Product Blueprint Manager *extrae* estos valores para usarlos en las fórmulas.

**Funcionalidades Clave:**

1.  **Asociación de Planos a Productos:**

    *   En la ficha de cada *plantilla* de producto (no en las variantes, sino en el producto "padre"), encontrarás una nueva pestaña llamada "Planos y Fórmulas".
    *   Aquí puedes subir uno o más archivos SVG. Estos serán los planos base.

2.  **Definición de Fórmulas (Vinculadas a Etiquetas en el SVG):**

    *   **Preparación del SVG (¡IMPORTANTE!):** Antes de subir el archivo SVG a Odoo, debes prepararlo. El módulo *no* funciona con etiquetas `<text>` estándar de SVG. **Debes convertir los textos que quieres que sean dinámicos en *trayectos* (paths).**
        *   **¿Por qué trayectos?** Odoo, al generar los PDFs, tiene problemas para renderizar correctamente los elementos `<text>` de SVG, especialmente si tienen transformaciones o estilos complejos. Convertirlos a trayectos asegura una visualización correcta.
        *   **¿Cómo convertir textos a trayectos?** Puedes hacerlo con software de edición vectorial como Inkscape. El proceso consiste, en resumen, en seleccionar los objetos de texto y aplicar una función del tipo "Objeto a Trayecto" o "Convertir a Contornos". Esto *convierte* la representación del texto en un conjunto de curvas, que Odoo sí puede renderizar.
        *   **Conversión con Inkscape (Línea de Comandos):** Si tienes muchos archivos, puedes automatizar la conversión usando Inkscape desde la línea de comandos (terminal):

            ```bash
            inkscape archivo_original.svg --export-text-to-path --export-plain-svg -o archivo_convertido.svg
            ```

            *   `archivo_original.svg`: El archivo SVG original.
            *   `--export-text-to-path`: La opción mágica que convierte los textos a trayectos.
            *   `--export-plain-svg`: Genera un SVG "plano" (sin características especiales de Inkscape).
            *   `-o archivo_convertido.svg`: Especifica el nombre del archivo de salida.

        *   **Identificación de los Trayectos (aria-label):** Despues de transformar el texto a trayectos, en el campo "aria-label" de cada `<path>` convertido desde texto, escribe el **nombre de la etiqueta**. Este nombre será la *referencia* que usarás para vincular el trayecto con una fórmula en Odoo.

    *   **Creación de Fórmulas en Odoo:**
        *   En la pestaña "Planos y Fórmulas" de la plantilla de producto, verás una sección llamada "Fórmulas".
        *   Al crear una nueva fórmula, debes especificar:
            *   **Plano:** Selecciona el archivo SVG al que pertenece esta fórmula.
            *   **Nombre de Etiqueta de Fórmula:** Aquí debes introducir el **nombre exacto** que pusiste en el atributo `aria-label` del `<path>` en el SVG. *Es la conexión entre el plano y la fórmula.*
            *   **Expresión de la Fórmula:** La fórmula matemática en sí, escrita en sintaxis Python. Puedes usar:
                *   Operadores matemáticos básicos (`+`, `-`, `*`, `/`, `**` para potencias).
                *   Funciones matemáticas de Python (`math.sin`, `math.cos`, `math.sqrt`, etc.). Consulta la documentación de Python para ver todas las funciones disponibles.
                *   **Variables:** Aquí es donde entran los atributos personalizados del módulo `product_configurator_attribute_price`. Por ejemplo, si has definido un atributo llamado "mmAncho", puedes usarlo en tu fórmula: `mmAncho * 2`.
            *   **Atributos Disponibles:** Este campo *calculado* muestra los atributos que puedes usar en la fórmula, a partir de los atributos personalizados definidos.

3.  **Evaluación Segura de Fórmulas:**

    *   El módulo evalúa las fórmulas en un entorno seguro. Esto significa que no se pueden ejecutar comandos arbitrarios de Python, solo las operaciones matemáticas permitidas.
    *   Los valores de las variables se obtienen de los atributos personalizados que el usuario haya introducido en la línea de pedido de venta.

4.  **Generación de Informes PDF:**

    *   Cuando creas un presupuesto, pedido de venta o factura que incluye un producto con planos y fórmulas configurados, puedes imprimir un informe especial.
    *   Ve al menú "Imprimir" del documento de venta y selecciona "Plano Orden de Venta".
    *   El PDF generado incluirá:
        *   La información estándar del documento (cliente, productos, precios, etc.).
        *   **El plano SVG**, pero con una modificación importante: Los `<path>` que tenían un `aria-label` coincidente con una fórmula configurada serán *reemplazados* por el *resultado* de esa fórmula.
        *   Si un `<path>` con `aria-label` *no* tiene una fórmula asociada, se mostrará tal cual, sin cambios.
        *   Cada producto con planos configurados aparecerá en una página separada del informe.

**Flujo de Trabajo Completo (Ejemplo):**

1.  **Diseño del Plano (SVG):**
    *   Crea tu plano en un editor vectorial (Inkscape, Adobe Illustrator, etc.).
    *   Donde quieras que aparezcan valores dinámicos, inserta texto.
    *   **Convierte ese texto a trayectos (paths).** Importante: en Inkscape, selecciona el texto y ve a "Trayecto" -> "Objeto a Trayecto" o usa el comando de terminal que te di antes.
    *   A cada `<path>` resultante, asígnale un atributo `aria-label`. Por ejemplo, si tienes un texto que mostrará el ancho, podrías poner `aria-label="AnchoCalculado"`.

2.  **Configuración en Odoo:**
    *   Crea una plantilla de producto.
    *   Define los atributos personalizados necesarios (ej. "mmAncho", "mmAlto") usando el módulo `product_configurator_attribute_price`.
    *   En la pestaña "Planos y Fórmulas" de la plantilla de producto:
        *   Sube el archivo SVG.
        *   Crea una nueva fórmula.
        *   En "Nombre de Etiqueta de Fórmula", escribe "AnchoCalculado" (o el nombre que hayas usado en el `aria-label`).
        *   En "Expresión de la Fórmula", escribe algo como `mmAncho * 2`.
        *   Guarda la fórmula y la plantilla de producto.

3.  **Creación de un Pedido de Venta:**
    *   Crea un nuevo pedido de venta.
    *   Añade el producto.
    *   Al añadir el producto, Odoo te pedirá que introduzcas los valores de los atributos personalizados (ej. "mmAncho" = 1000, "mmAlto" = 500).
    *   Guarda el pedido de venta.

4.  **Impresión del Informe:**
    *   En el pedido de venta, ve a "Imprimir" -> "Plano Orden de Venta".
    *   El PDF generado mostrará el plano. Donde antes tenías el `<path>` con `aria-label="AnchoCalculado"`, ahora verás el resultado de la fórmula (en este ejemplo, 2000).

**En resumen:** Product Blueprint Manager te da un control total sobre la presentación de información técnica variable en tus documentos de venta, de forma automatizada, segura y visualmente clara. La clave está en la correcta preparación del SVG y la definición precisa de las fórmulas.