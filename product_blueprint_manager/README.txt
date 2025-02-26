+--------------------------------------------------------------------------------------------------------------------+
| Módulo: Product Blueprint Manager                                                                                     |
+====================================================================================================================+
| Descripción Detallada                                                                                               |
+--------------------------------------------------------------------------------------------------------------------+
| Este módulo permite la gestión avanzada de planos (blueprints) en Odoo, con la capacidad de asociar etiquetas      |
| dentro de archivos SVG y definir fórmulas matemáticas que se evalúan dinámicamente. Los resultados se reflejan     |
| directamente en los planos generados en los informes de venta sin modificar el archivo original.                   |
|                                                                                                                    |
| Su objetivo es proporcionar una solución flexible para visualizar especificaciones variables en productos,         |
| especialmente útil en la industria manufacturera y cualquier entorno donde las dimensiones y características       |
| del producto se definan mediante cálculos y atributos personalizados.                                              |
|                                                                                                                    |
| Funcionalidad Principal:                                                                                            |
|                                                                                                                    |
| 1. Asociación de Planos a Productos:                                                                                |
|   - Permite asociar uno o varios planos (archivos SVG) a cada plantilla de producto.                                |
|   - Los planos se configuran en la ficha de la plantilla del producto, en la pestaña "Planos y Fórmulas".         |
|   - Se pueden subir archivos SVG que servirán como base para la visualización de etiquetas con cálculos dinámicos. |
|                                                                                                                    |
| 2. Detección Automática de Etiquetas en los Planos:                                                                |
|   - Al subir un archivo SVG, se detectan automáticamente las etiquetas `<text class="odoo-formula">`.              |
|   - Cada etiqueta identificada se almacena en el sistema como un "Nombre de Etiqueta de Fórmula".                   |
|   - Las etiquetas detectadas están disponibles para ser asociadas con fórmulas personalizadas.                      |
|                                                                                                                    |
| 3. Definición de Fórmulas Asociadas a las Etiquetas:                                                               |
|   - Las fórmulas se configuran en la misma pestaña "Planos y Fórmulas" de la plantilla del producto.               |
|   - Cada fórmula tiene:                                                                                             |
|     - **Nombre**: Referencia a una de las etiquetas detectadas en el plano.                                        |
|     - **Expresión de la Fórmula**: Una ecuación matemática escrita en Python seguro (ej. `mmA * 2`).               |
|     - **Plano**: Relación con el plano al que pertenece la fórmula.                                                |
|     - **Atributos Disponibles**: Lista de atributos personalizados que pueden ser utilizados en la fórmula.        |
|                                                                                                                    |
| 4. Evaluación Segura de Fórmulas:                                                                                  |
|   - Las fórmulas se evalúan de manera segura usando solo variables permitidas y funciones matemáticas restringidas.|
|   - Los valores utilizados en las fórmulas provienen de:                                                            |
|     - Atributos personalizados del producto (capturados en la línea de pedido de venta).                           |
|     - Valores estáticos configurados en la plantilla del producto.                                                 |
|                                                                                                                    |
| 5. Generación de Planos con Resultados de Fórmulas Evaluadas:                                                      |
|   - Al generar un informe de venta, el sistema procesa las etiquetas `<text class="odoo-formula">`.               |
|   - Si una etiqueta está configurada con una fórmula, su contenido es reemplazado por el resultado de la evaluación.|
|   - Si no hay fórmula asociada a una etiqueta, el texto original del SVG permanece intacto.                        |
|   - **Importante:** El archivo SVG original no se modifica, solo se genera una versión temporal para el PDF.       |
|                                                                                                                    |
| 6. Generación de Informes PDF de Planos en Documentos de Venta:                                                    |
|   - Desde el menú "Imprimir" de presupuestos, pedidos de venta y facturas, se puede generar el informe del plano.  |
|   - El PDF incluye:                                                                                                 |
|     - Datos del documento (cliente, número de pedido, fecha, etc.).                                                |
|     - Imágenes de los planos con los resultados de las fórmulas superpuestos sobre las etiquetas configuradas.     |
|     - Cada producto con planos configurados tendrá una página en el informe.                                       |
|                                                                                                                    |
| Objetivos:                                                                                                         |
|                                                                                                                    |
| * Automatizar la visualización de información variable sobre planos.                                               |
| * Mantener los planos originales intactos mientras se generan versiones con datos calculados en los informes.      |
| * Facilitar la interpretación de dimensiones y características variables en documentos de venta.                   |
| * Evitar errores humanos al calcular manualmente valores en planos técnicos.                                       |
|                                                                                                                    |
| Manejo del Módulo:                                                                                                 |
|                                                                                                                    |
| 1. **Configuración de Planos:**                                                                                    |
|   - Ir a la ficha de la plantilla del producto.                                                                    |
|   - En la pestaña "Planos y Fórmulas", subir un archivo SVG en la sección "Planos".                                |
|   - El sistema detectará automáticamente las etiquetas `<text class="odoo-formula">`.                             |
|                                                                                                                    |
| 2. **Configuración de Fórmulas:**                                                                                  |
|   - En la pestaña "Planos y Fórmulas", en la sección "Fórmulas", crear una nueva fórmula.                          |
|   - Seleccionar una de las etiquetas detectadas en el plano.                                                       |
|   - Escribir la expresión matemática a evaluar, usando los atributos personalizados disponibles.                   |
|                                                                                                                    |
| 3. **Generación del Informe de Planos en Documentos de Venta:**                                                    |
|   - Crear un documento de venta (presupuesto, pedido, etc.).                                                        |
|   - Añadir productos que tengan planos configurados.                                                               |
|   - En el menú "Imprimir", seleccionar la opción "Plano Orden de Venta".                                           |
|   - Se generará un informe PDF con los planos y los resultados de las fórmulas evaluadas.                         |
|                                                                                                                    |
| Consideraciones:                                                                                                   |
|                                                                                                                    |
| * El módulo solo procesa archivos SVG que contengan etiquetas `<text class="odoo-formula">`.                      |
| * Si una etiqueta no tiene una fórmula configurada, su contenido original se mantiene en el informe.               |
| * El módulo es compatible con los módulos `product`, `sale`, `sale_management` y `product_configurator_attribute_price`.|
| * La evaluación de fórmulas se hace en un entorno seguro, sin acceso a funciones peligrosas de Python.             |
+--------------------------------------------------------------------------------------------------------------------+
