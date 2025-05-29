# Product Blueprint Manager

**Módulo para Odoo que permite generar planos técnicos SVG evaluados dinámicamente según los atributos configurables del producto.**

---

## 🎯 ¿Qué es?

Este módulo permite asociar **planos SVG dinámicos** a productos en Odoo. Cada plano puede contener **fórmulas matemáticas** que se evalúan automáticamente según los atributos configurados por el cliente (ej. ancho, alto, tipo de vidrio), y los resultados se muestran directamente en el plano que se genera como PDF.

Ideal para fabricantes de productos a medida: mamparas, ventanas, carpintería metálica, mobiliario técnico, etc.

---

## ⚙️ Características principales

- Cargar uno o varios planos SVG por producto.
- Definir **fórmulas dinámicas** vinculadas a elementos del SVG.
- Evaluación de las fórmulas usando atributos personalizados definidos por el cliente.
- Generación automática de planos personalizados como **adjuntos PDF** al pedido de venta o compra.
- Soporte para **tipos de plano**: orden de fabricación, orden de compra.
- Condiciones opcionales basadas en los **atributos del producto** para determinar qué plano se genera.
- Renderizado directo del SVG evaluado con `t-raw`, o conversión opcional a **PNG** mediante CairoSVG.
- Conserva estilo visual original (`font-size`, `fill`, etc.), editable por el usuario si se desea.

---

## 📂 Requisitos

### Módulos de Odoo necesarios

- `product`
- `sale`
- `sale_management`

### Módulo adicional requerido

- `product_configurator_attribute_price`: permite definir atributos personalizados (como "mmAncho", "TipoVidrio") y capturarlos en la línea del pedido.

---

## 🖼️ Requisitos del archivo SVG

### ¿Cómo marcar los elementos reemplazables?

Para que una fórmula se aplique a un nodo en el SVG, este debe:

1. **Tener la clase CSS `odoo-formula`**
2. Tener el atributo `aria-label="NombreFormula"` (donde `NombreFormula` es el nombre vinculado a la fórmula configurada en Odoo)

#### Ejemplo:

```xml
<text x="100" y="50" font-size="12" fill="#000000" class="odoo-formula" aria-label="AnchoCalculado">0</text>
```

- El valor `"0"` será reemplazado por el resultado evaluado.
- El estilo visual será conservado o puede configurarse manualmente.

> ⚠️ Importante: ya no es necesario convertir los textos a `path` (trayectos) si puedes usar nodos `<text>` bien posicionados con `class="odoo-formula"`.

---

## 🧮 Cómo se definen las fórmulas

En la ficha del producto, pestaña **"Planos y Fórmulas"**:

1. Selecciona el plano SVG.
2. Añade una fórmula indicando:
   - **Etiqueta de fórmula** → coincide con `aria-label` en el SVG.
   - **Expresión matemática** → usa los nombres de atributos definidos.
   - **Condiciones** opcionales (por ejemplo, sólo mostrar este plano si el atributo `TipoVidrio` es "Transparente").
   - **Color y tamaño de fuente** → opcionales; se detectan automáticamente pero pueden editarse manualmente.

---

## 📄 ¿Qué se genera?

En cada línea del pedido, al generar el informe:

- Se evalúan las fórmulas.
- Se reemplazan los nodos con `class="odoo-formula"` por un `<text>` SVG con el resultado.
- Se respetan el color, tamaño de letra y posición.
- Si `wkhtmltopdf` no renderiza bien el SVG, se convierte automáticamente a **PNG**.
- El resultado se adjunta al pedido como PDF personalizado.

---

## 🧪 Flujo de trabajo completo

1. **Diseña el plano SVG**
   - En Inkscape o similar, usa texto donde quieras un valor dinámico.
   - Asegúrate de que cada texto tenga `class="odoo-formula"` y `aria-label`.
   - Opcional: convierte los textos a trayectos con Inkscape si necesitas máxima compatibilidad:
     ```bash
     inkscape plano.svg --export-text-to-path --export-plain-svg -o plano_convertido.svg
     ```

2. **Configura la plantilla de producto en Odoo**
   - Añade los atributos personalizados (mmAncho, mmAlto...).
   - Sube el SVG.
   - Define las fórmulas correspondientes (ej. `mmAncho * 2.5`).

3. **Crea un pedido de venta o compra**
   - Selecciona el producto.
   - Configura los valores de atributos.
   - Guarda el pedido.

4. **Genera el plano**
   - Desde el menú "Imprimir", elige "Plano Orden de Venta" o "Plano Orden de Compra".
   - Se genera un PDF con los planos dinámicos evaluados.

---

## 🔐 Seguridad

Las fórmulas se evalúan en un entorno restringido:
- Solo se permiten operadores y funciones matemáticas (`+`, `-`, `*`, `/`, `math.sqrt`, etc.).
- No se ejecuta ningún código arbitrario ni peligroso.
- Los valores sólo provienen de atributos configurados por el usuario.

---

## 📁 Estructura del módulo

```
product_blueprint_manager/
├── models/
│   ├── product_blueprint.py
│   ├── product_blueprint_formula_name.py
│   └── ...
├── views/
│   └── product_blueprint_views.xml
├── report/
│   ├── sale_order_report.xml
│   └── purchase_order_report.xml
└── static/
    └── ...
```

---

## 💡 Consejo práctico

¿Tus valores evaluados no se ven en el PDF?

- Asegúrate de que los nodos tengan `class="odoo-formula"`.
- Verifica que el `aria-label` coincida exactamente con el nombre de la fórmula.
- Revisa que se hayan definido valores en la línea de pedido.

---

## 🧷 Módulo mantenido por

Zurbaran Sistemas de Producción  
Repositorio oficial: https://github.com/zurbaran/odoo_metal_manufacturing

---
