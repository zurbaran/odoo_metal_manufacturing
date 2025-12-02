# Product Blueprint Manager

**Módulo para Odoo que permite generar planos técnicos SVG evaluados dinámicamente según los atributos configurables del producto.**

---

## 🎯 ¿Qué es?

Este módulo permite asociar **planos SVG dinámicos** a productos en Odoo. Cada plano puede contener **fórmulas matemáticas** que se evalúan automáticamente según los atributos configurados por el cliente (ej. ancho, alto, tipo de vidrio), y los resultados se muestran directamente en el plano que se incluye en los informes PDF.

Está pensado para fabricantes de productos a medida: mamparas, ventanas, carpintería metálica, mobiliario técnico, etc.

---

## ⚙ Características principales

- Cargar uno o varios **planos SVG** por plantilla de producto.
- Definir **fórmulas dinámicas** vinculadas a elementos del SVG.
- Evaluación de las fórmulas usando atributos estándar, no_variant y personalizados de la línea de venta.
- Generación automática de planos personalizados como adjuntos SVG/PNG asociados a la **línea de pedido de venta**.
- Soporte para **tipos de plano**:
  - Orden de fabricación (`type_blueprint = manufacturing`)
  - Orden de compra (`type_blueprint = purchase`)
- Condiciones opcionales basadas en los **atributos del producto** para determinar qué plano se genera.
- Renderizado directo del SVG evaluado en QWeb (`t-raw`) y/o conversión a **PNG** mediante CairoSVG para máxima compatibilidad en PDF.
- Conserva el estilo visual original (`font-size`, `fill`, `transform`, etc.), con posibilidad de sobreescribir color y tamaño de fuente en la configuración de la fórmula.
- Resumen de atributos seleccionados en la línea: el módulo expone un helper para mostrar en el plano los valores de atributos relevantes (Color, Vidrio, Altura, etc.).

### Filtrado de planos con condiciones

El filtrado se realiza mediante el modelo `product.blueprint.condition`. Cada registro de condición
vincula un atributo con los valores que activan el plano. Un mismo plano puede tener varias
condiciones y **todas** deben cumplirse para que el plano se incluya en el informe.

#### Ejemplo con múltiples condiciones

Plano **"Mampara Premium"**:

1. `Vidrio` debe ser `Transparente` o `Impreso Carglas`.
2. `Acabado` igual a `Negro`.

El plano solo se generará si la línea del pedido cumple los dos criterios anteriores.

---

## 📂 Requisitos

### Módulos de Odoo necesarios

- `product`
- `sale`
- `sale_management`

### Módulo adicional requerido

- `product_configurator_attribute_price`: permite definir atributos personalizados (como "mmAncho", "mmAltura") y capturarlos en la línea del pedido para usarlos como variables en las fórmulas de plano.

---

## 🖼 Requisitos del archivo SVG

### ¿Cómo marcar los elementos reemplazables?

Para que una fórmula se aplique a un nodo en el SVG, este debe:

1. **Tener la clase CSS `odoo-formula`**
2. Tener algún texto o etiqueta que identifique el nombre de la fórmula. El motor intenta extraer el nombre de:
   - `aria-label`
   - `aria-text`
   - El texto del propio nodo o de sus descendientes

La práctica recomendada es utilizar:

- `class="odoo-formula"`
- `aria-label="NombreFormula"`

#### Ejemplo:

```xml
<text x="100" y="50" font-size="12" fill="#000000"
      class="odoo-formula"
      aria-label="AnchoCalculado">
  0
</text>
```
El valor "0" será reemplazado por el resultado evaluado.

El estilo visual será conservado o puede configurarse manualmente en Odoo.

⚠ Importante: no es necesario convertir los textos a path si puedes usar nodos `<text>` bien posicionados con `class="odoo-formula"`.
El módulo también es capaz de sustituir nodos de otro tipo (por ejemplo `<path>`) por `<text>` si llevan la clase `odoo-formula`.

---

## 🧮 Cómo se definen las fórmulas

En la ficha del producto, pestaña "Planos y Fórmulas":

- Selecciona el plano SVG.
- Añade una fórmula indicando:
  - **Etiqueta de fórmula** → coincide con el nombre que se extrae del SVG (idealmente `aria-label`).
  - **Expresión matemática** → usa los nombres de variables definidos por los atributos (ej. `mmA`, `mmB`, `mmAltura`).
  - **Condiciones opcionales** (por ejemplo, solo mostrar este plano si el atributo `TipoVidrio` es "Transparente").
  - **Color y tamaño de fuente** → opcionales; se detectan automáticamente del SVG original (cuando es posible), pero pueden editarse manualmente para corregir o unificar estilo.

Las variables se construyen a partir de:

- **Atributos personalizados** (`is_custom=True`) → el nombre del valor define el nombre de la variable, y el `custom_value` define su valor numérico.
- **Atributos estándar** que tengan al menos un valor `is_custom=True` → se usa ese valor `is_custom` como alias de variable, y el valor seleccionado en la línea (ej. "1850") se convierte a entero.

---

## 📄 ¿Qué se genera?

En cada línea del pedido de venta, al generar el informe:

1. Se capturan todos los valores de atributos relevantes y se proyectan a un diccionario de variables.
2. Se evalúan las expresiones matemáticas de cada fórmula, de forma segura.
3. Se localizan los nodos con `class="odoo-formula"` en el SVG.
4. Cada nodo de fórmula se sustituye por un nodo `<text>` limpio con:
   - El resultado evaluado redondeado (cuando es numérico).
   - El `font-size` y el `fill` heredados del SVG o de la configuración de la fórmula.
   - La posición (`x`, `y`) y transformaciones (`transform`) coherentes con el elemento original.
5. Si alguna fórmula no se puede evaluar, el nodo se marca con una clase especial y se añade un símbolo de aviso `(!)` en rojo cerca de la posición.
6. El SVG resultante se guarda como adjunto en `ir.attachment` y se genera, además, una versión PNG vía CairoSVG.
7. El informe QWeb (presupuesto/orden de fabricación o plano de compra) incluye el plano evaluado, ya sea como SVG inline (`t-raw`) o como imagen PNG, según la plantilla.

---

## 🧪 Flujo de trabajo completo

### 1. Diseña el plano SVG

- En Inkscape o similar, usa texto donde quieras un valor dinámico.
- Asegúrate de que cada texto tenga `class="odoo-formula"` y, preferiblemente, `aria-label` con el nombre de la fórmula.
- Evita estilos excesivos: tamaños de fuente extremadamente grandes o transformaciones complejas pueden dificultar el renderizado.

### 2. Configura la plantilla de producto en Odoo

- Añade los atributos personalizados (`mmAncho`, `mmAltura`, etc.).
- Sube el SVG como plano asociado al producto.
- Define las fórmulas correspondientes (ej. `mmAltura - 50`, `(mmA + mmB) / 2`).
- Opcionalmente, define condiciones de plano basadas en atributos (modelo `product.blueprint.condition`).

### 3. Crea un pedido de venta o compra

- Selecciona el producto.
- Configura los valores de atributos (incluidos los personalizados).
- Guarda el pedido.

### 4. Genera el plano

- Desde el menú "Imprimir", elige "Plano Orden de Fabricación" o "Plano Orden de Compra" (según el tipo de plano configurado).
- Se genera un PDF con los planos dinámicos evaluados y, opcionalmente, un resumen de atributos.

---

## 🔐 Seguridad

Las fórmulas se evalúan en un entorno restringido:

- Solo se permiten operadores y funciones matemáticas (`+`, `-`, `*`, `/`, `//`, `math.ceil`, `math.floor`, etc.).
- Se usa `ast.parse` y un entorno sin `__builtins__` para evitar ejecuciones arbitrarias.
- Los valores solo provienen de atributos configurados en la línea de pedido.

En caso de error en la evaluación:

- El módulo registra un log detallado.
- El nodo correspondiente en el SVG se marca visualmente para facilitar la depuración.

---

## 📁 Estructura del módulo

```text
product_blueprint_manager/
├── models/
│   ├── sale_order_line.py                # Lógica de evaluación y generación de planos por línea
│   ├── product_blueprint.py              # Modelo de plano y condiciones
│   ├── product_blueprint_formula_name.py # Nombres de fórmulas y estilos (color, tamaño)
│   └── ...
├── views/
│   ├── product_blueprint_views.xml       # Vistas de configuración de planos y fórmulas
│   └── ...
├── report/
│   ├── sale_order_report.xml             # Reporte de planos para venta/fabricación
│   └── purchase_order_report.xml         # Reporte de planos para orden de compra
└── static/
    └── ...


## 💡 Consejo práctico

¿Tus valores evaluados no se ven o no aparecen donde esperas?

- Asegúrate de que los nodos tengan `class="odoo-formula"`.
- Verifica que el nombre que se extrae del SVG (texto / `aria-label`) coincida exactamente con la etiqueta de la fórmula configurada.
- Comprueba que los atributos personalizados tengan valores numéricos y que estén marcados como `is_custom` cuando deban generar variables.
- Revisa los logs de Odoo en nivel `debug` para localizar mensajes `[Blueprint]`.

---

## 🧭 TODO / Roadmap

Las siguientes tareas están previstas para futuras versiones del módulo:

### Funcionalidad de planos y fórmulas

- Añadir un botón de **"Reescanear SVG"** en la ficha del plano que:
  - Detecte automáticamente todos los nodos con `class="odoo-formula"`.
  - Proponga crear/actualizar los registros de fórmula (`product.blueprint.formula.name`) incluyendo:
    - ID del nodo en el SVG.
    - Nombre de fórmula sugerido.
    - Color y tamaño de fuente detectados.
- Documentar y, en su caso, extender el soporte a más tipos de nodos SVG (líneas, polígonos, etc.) manteniendo la conversión final a `<text>` cuando se trate de fórmulas.
- Permitir condiciones de plano más avanzadas (rangos numéricos, exclusiones, etc.) sin romper la compatibilidad con las condiciones actuales basadas en valores de atributos.

### Informes y experiencia de usuario

- Unificar el diseño visual de los reportes de:
  - **Plano Orden de Fabricación**
  - **Plano Orden de Compra**
    (márgenes, cabeceras, pie de página, tipografías, tamaños de tabla, etc.).
- Añadir una sección opcional en los reportes con:
  - Tabla de atributos visibles (Color, Vidrio, Altura, etc.).
  - Tabla de variables/fórmulas evaluadas con su valor (útil para fábrica y proveedores).
- Permitir configurar, a nivel de *blueprint*:
  - Si se incrusta el SVG inline o el PNG derivado.
  - El orden de aparición de los planos cuando hay varios aplicables a la misma línea.

### Calidad interna y mantenimiento

- Añadir tests automáticos (Odoo tests) que cubran:
  - Evaluación segura de fórmulas (`safe_evaluate_formula`).
  - Generación de SVG evaluados y conversión a PNG.
  - Aplicación de condiciones de plano según atributos.
- Revisar y optimizar los logs (`_logger.debug/info/warning`) para:
  - Tener trazas detalladas en modo `debug`.
  - Reducir ruido en modo `info` en entornos de producción.
- Completar y mantener esta documentación alineada con las guías de la OCA:
  - Sección de uso avanzado.
  - Ejemplos de SVG de referencia.
  - Notas de actualización entre versiones de Odoo.

---

## 🧷 Módulo mantenido por

**Zurbaran Sistemas de Producción**
Repositorio oficial: https://github.com/zurbaran/odoo_metal_manufacturing

La licencia del módulo se indica en el archivo `__manifest__.py` del propio addon.
