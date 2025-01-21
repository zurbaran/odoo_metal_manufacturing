+--------------------------------------------------------------------------------------------------------------------+
| Módulo: Product Blueprint Manager                                                                                     |
+====================================================================================================================+
| Descripción Detallada                                                                                               |
+--------------------------------------------------------------------------------------------------------------------+
| Este módulo permite la gestión de planos (blueprints) para productos en Odoo, con la capacidad de definir           |
| fórmulas que se evalúan dinámicamente para generar valores que se muestran sobre el plano. Su objetivo principal es |
| proporcionar una forma flexible y automatizada de crear y visualizar representaciones gráficas de productos        |
| con especificaciones variables, especialmente útil en la industria manufacturera, en particular la industria del    |
| metal, y en cualquier entorno donde las características del producto se definan mediante cálculos o selecciones    |
| de atributos.                                                                                                     |
|                                                                                                                    |
| Funcionalidad Principal:                                                                                            |
|                                                                                                                    |
| 1. Asociación de Planos a Productos:                                                                                |
|   - Permite asociar uno o varios planos (archivos SVG) a cada plantilla de producto.                                |
|   - Los planos se configuran en la ficha de la plantilla del producto, en una pestaña específica llamada          |
|     "Planos y Fórmulas".                                                                                             |
|   - Se puede subir un archivo SVG que servirá como base para la visualización de las fórmulas.                      |
|                                                                                                                    |
| 2. Definición de Fórmulas:                                                                                           |
|   - Permite definir fórmulas asociadas a cada plano.                                                                 |
|   - Las fórmulas se configuran en la misma pestaña "Planos y Fórmulas" de la plantilla del producto.                 |
|   - Cada fórmula tiene:                                                                                             |
|     - Nombre: Un identificador único.                                                                                |
|     - Expresión de la Fórmula: Una expresión en Python que se evalúa dinámicamente.                                  |
|     - Plano: El plano al que pertenece la fórmula.                                                                  |
|     - Posición X (mm): La coordenada X (en milímetros) donde se mostrará el resultado de la fórmula en el plano.    |
|     - Posición Y (mm): La coordenada Y (en milímetros) donde se mostrará el resultado de la fórmula en el plano.    |
|     - Atributos Disponibles: Muestra los atributos personalizados del producto que se pueden usar en la fórmula.    |
|     - Tamaño de la fuente (mm): El tamaño de la fuente (en milímetros) con el que se mostrará el resultado.         |
|     - Color de la Fuente: El color con el que se mostrará el resultado.                                            |
|                                                                                                                    |
| 3. Evaluación Dinámica de Fórmulas:                                                                                |
|   - Las fórmulas se evalúan utilizando un método seguro que restringe el acceso a funciones built-in de Python.    |
|   - Las variables disponibles para la evaluación de las fórmulas provienen de:                                      |
|     - Atributos personalizados del producto: Se obtienen a través de un "hook" que captura los valores             |
|       seleccionados en la línea de pedido de venta.                                                                 |
|     - Valores configurados en la propia fórmula (nombre, posición, etc.).                                            |
|                                                                                                                    |
| 4. Generación de Informes:                                                                                          |
|   - Modo 'preview':                                                                                                 |
|     - Accesible desde un botón en la ficha de la plantilla del producto.                                            |
|     - Muestra el plano SVG con los *nombres* de las fórmulas en las posiciones configuradas.                        |
|     - Permite verificar la correcta configuración de las fórmulas (posición, tamaño de fuente, color) antes de      |
|       generar el informe final.                                                                                    |
|   - Modo 'final':                                                                                                   |
|     - Accesible desde el menú "Imprimir" de los documentos de compra/venta (presupuestos, pedidos, proformas,      |
|       facturas).                                                                                                   |
|     - Genera un informe PDF que contiene:                                                                           |
|       - Encabezado y pie de página estándar del documento de compra/venta.                                          |
|       - Por cada producto del documento que tenga planos configurados:                                               |
|         - Una página por cada plano.                                                                               |
|         - En cada página:                                                                                          |
|           - Información del documento (nombre, cliente, fecha, etc.).                                               |
|           - Nombre del producto.                                                                                   |
|           - Nombre del plano.                                                                                      |
|           - El plano SVG original, ajustado al ancho del A4 vertical.                                               |
|           - Los *resultados* de las fórmulas evaluadas, superpuestos sobre el plano en las posiciones              |
|             configuradas, con el tamaño de fuente y color especificados.                                             |
|                                                                                                                    |
| 5. Escalado de Fórmulas:                                                                                            |
|   - Las fórmulas (tanto en modo 'preview' como 'final') se escalan utilizando dos factores de escala:              |
|     - `FORMULA_POSITION_SCALE_FACTOR`: Se multiplica por las coordenadas X e Y de la fórmula.                        |
|     - `FORMULA_FONT_SIZE_SCALE_FACTOR`: Se multiplica por el tamaño de fuente de la fórmula.                          |
|   - Estos factores permiten ajustar la posición y el tamaño de las fórmulas en relación con el tamaño del plano    |
|     original y la resolución de la pantalla o impresión. Actualmente el factor de escalado es de 100 para las       |
|     coordenadas, y de 36.45 para el tamaño de la fuente.                                                            |
|                                                                                                                    |
| Objetivos:                                                                                                         |
|                                                                                                                    |
| * Facilitar la visualización de información variable sobre un plano.                                              |
| * Automatizar la generación de informes de planos con valores calculados dinámicamente.                            |
| * Proporcionar una herramienta flexible para adaptar la visualización de planos a diferentes productos y            |
|   configuraciones.                                                                                                 |
| * Mejorar la comunicación y la claridad de la información en los documentos de compra/venta.                       |
|                                                                                                                    |
| Manejo del Módulo:                                                                                                 |
|                                                                                                                    |
| 1. Configuración de Planos:                                                                                         |
|   - Ir a la ficha de la plantilla del producto.                                                                     |
|   - En la pestaña "Planos y Fórmulas", subir un archivo SVG en la sección "Planos".                               |
|                                                                                                                    |
| 2. Configuración de Fórmulas:                                                                                       |
|   - En la pestaña "Planos y Fórmulas", en la sección "Fórmulas", crear una nueva fórmula.                         |
|   - Completar los campos: Nombre, Expresión de la Fórmula, Plano, Posición X, Posición Y, Tamaño de la fuente y    |
|     Color de la Fuente.                                                                                            |
|   - Utilizar los "Atributos Disponibles" como variables en la "Expresión de la Fórmula".                           |
|                                                                                                                    |
| 3. Previsualización de Planos:                                                                                     |
|   - En la ficha de la plantilla del producto, hacer clic en el botón "Generar / Previsualizar Plano".                |
|   - Se generará un informe PDF que muestra el plano con los nombres de las fórmulas en las posiciones               |
|     configuradas.                                                                                                   |
|                                                                                                                    |
| 4. Generación del Informe Final:                                                                                   |
|   - Crear un documento de compra/venta (presupuesto, pedido, etc.).                                                 |
|   - Añadir productos que tengan planos configurados.                                                                |
|   - En el menú "Imprimir", seleccionar la opción "Sale Order Blueprint".                                           |
|   - Se generará un informe PDF que incluye los planos con los resultados de las fórmulas evaluadas.                |
|                                                                                                                    |
| Consideraciones:                                                                                                   |
|                                                                                                                    |
| * Los planos originales se asumen en formato A4 horizontal y en milímetros.                                         |
| * El SVG original NO se modifica, solo se le superponen las fórmulas.                                              |
| * Los factores de escala de las fórmulas (`FORMULA_POSITION_SCALE_FACTOR` y `FORMULA_FONT_SIZE_SCALE_FACTOR`) se      |
|   pueden ajustar en el código según sea necesario.                                                                 |
| * Se asume que las coordenadas y el tamaño de fuente configurados en las fórmulas están en milímetros.             |
| * El módulo depende de los módulos `product`, `sale`, `sale_management` y `product_configurator_attribute_price`.   |
+--------------------------------------------------------------------------------------------------------------------+
