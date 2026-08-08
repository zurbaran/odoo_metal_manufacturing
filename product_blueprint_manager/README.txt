Product Blueprint Manager
=========================

Módulo para Odoo que permite generar planos técnicos SVG evaluados
dinámicamente según los atributos configurables del producto.

Descripción
===========

Este módulo permite asociar planos SVG dinámicos a productos en Odoo. Cada
plano puede contener fórmulas matemáticas que se evalúan automáticamente según
los atributos configurados por el cliente, por ejemplo ancho, alto o tipo de
vidrio. Los resultados se muestran directamente en el plano que se incluye en
los informes PDF.

Está pensado para fabricantes de productos a medida: mamparas, ventanas,
carpintería metálica, mobiliario técnico y casos similares.

Características principales
===========================

* Cargar uno o varios planos SVG por plantilla de producto.
* Definir fórmulas dinámicas vinculadas a elementos del SVG.
* Evaluar las fórmulas usando atributos estándar, ``no_variant`` y
  personalizados de la línea de venta.
* Generar automáticamente planos personalizados como adjuntos SVG y PNG
  asociados a la línea de pedido de venta.
* Soportar tipos de plano para orden de fabricación y orden de compra.
* Aplicar condiciones opcionales basadas en atributos del producto para
  determinar qué plano se genera.
* Renderizar directamente el SVG evaluado en QWeb mediante ``t-raw`` o
  convertirlo a PNG mediante CairoSVG para mejorar la compatibilidad en PDF.
* Conservar el estilo visual original, incluyendo ``font-size``, ``fill`` y
  ``transform``, con posibilidad de sobrescribir color y tamaño de fuente en la
  configuración de la fórmula.
* Exponer un helper para mostrar en el plano un resumen de atributos
  seleccionados en la línea, como color, vidrio o altura.

Filtrado de planos con condiciones
----------------------------------

El filtrado se realiza mediante el modelo ``product.blueprint.condition``. Cada
registro de condición vincula un atributo con los valores que activan el plano.
Un mismo plano puede tener varias condiciones y todas deben cumplirse para que
el plano se incluya en el informe.

Ejemplo con múltiples condiciones
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Plano ``Mampara Premium``:

1. ``Vidrio`` debe ser ``Transparente`` o ``Impreso Carglas``.
2. ``Acabado`` debe ser ``Negro``.

El plano solo se generará si la línea del pedido cumple los dos criterios
anteriores.

Requisitos
==========

Módulos de Odoo necesarios
--------------------------

* ``product``
* ``sale``
* ``sale_management``

Módulo adicional requerido
--------------------------

* ``product_configurator_attribute_price``: permite definir atributos
  personalizados, como ``mmAncho`` o ``mmAltura``, y capturarlos en la línea
  del pedido para usarlos como variables en las fórmulas del plano.

Requisitos del archivo SVG
==========================

Cómo marcar los elementos reemplazables
---------------------------------------

Para que una fórmula se aplique a un nodo en el SVG, este debe:

1. Tener la clase CSS ``odoo-formula``.
2. Tener algún texto o etiqueta que identifique el nombre de la fórmula.

El motor intenta extraer el nombre de:

* ``aria-label``
* ``aria-text``
* El texto del propio nodo o de sus descendientes

La práctica recomendada es utilizar:

* ``class="odoo-formula"``
* ``aria-label="NombreFormula"``

Ejemplo::

    <text x="100" y="50" font-size="12" fill="#000000"
          class="odoo-formula"
          aria-label="AnchoCalculado">
      0
    </text>

El valor ``0`` será reemplazado por el resultado evaluado.

El estilo visual será conservado o puede configurarse manualmente en Odoo.

Importante: no es necesario convertir los textos a ``path`` si puedes usar
nodos ``<text>`` bien posicionados con ``class="odoo-formula"``. El módulo
también es capaz de sustituir nodos de otro tipo, por ejemplo ``<path>``, por
``<text>`` si llevan la clase ``odoo-formula``.

Cómo se definen las fórmulas
============================

En la ficha del producto, en la pestaña ``Planos y Fórmulas``:

* Selecciona el plano SVG.
* Añade una fórmula indicando:

  * Etiqueta de fórmula. Debe coincidir con el nombre que se extrae del SVG,
    idealmente ``aria-label``.
  * Expresión matemática. Usa los nombres de variables definidos por los
    atributos, por ejemplo ``mmA``, ``mmB`` o ``mmAltura``.
  * Condiciones opcionales. Permiten mostrar el plano solo cuando se cumple un
    criterio concreto, por ejemplo un valor de ``TipoVidrio``.
  * Color y tamaño de fuente. Son opcionales; cuando es posible se detectan del
    SVG original, pero pueden editarse manualmente para corregir o unificar el
    estilo.

Las variables se construyen a partir de:

* Atributos personalizados con ``is_custom=True``. El nombre del valor define
  la variable y ``custom_value`` define su valor numérico.
* Atributos estándar que tengan al menos un valor ``is_custom=True``. Se usa
  ese valor como alias de variable y el valor seleccionado en la línea, por
  ejemplo ``1850``, se convierte a entero.

Qué se genera
=============

En cada línea del pedido de venta, al generar el informe:

1. Se capturan los valores de atributos relevantes y se proyectan a un
   diccionario de variables.
2. Se evalúan las expresiones matemáticas de cada fórmula de forma segura.
3. Se localizan los nodos con ``class="odoo-formula"`` en el SVG.
4. Cada nodo de fórmula se sustituye por un nodo ``<text>`` limpio con el
   resultado evaluado, la posición correcta y el estilo heredado o configurado.
5. Si alguna fórmula no se puede evaluar, el nodo se marca con una clase
   especial y se añade un símbolo de aviso ``(!)`` en rojo cerca de la
   posición.
6. El SVG resultante se guarda como adjunto en ``ir.attachment`` y se genera,
   además, una versión PNG mediante CairoSVG.
7. El informe QWeb, ya sea de presupuesto, orden de fabricación o plano de
   compra, incluye el plano evaluado como SVG inline o como imagen PNG según la
   plantilla.

Flujo de trabajo completo
=========================

1. Diseña el plano SVG
----------------------

* En Inkscape o similar, usa texto donde quieras un valor dinámico.
* Asegúrate de que cada texto tenga ``class="odoo-formula"`` y, de forma
  preferente, ``aria-label`` con el nombre de la fórmula.
* Evita estilos excesivos: tamaños de fuente muy grandes o transformaciones
  complejas pueden dificultar el renderizado.

2. Configura la plantilla de producto en Odoo
---------------------------------------------

* Añade los atributos personalizados, por ejemplo ``mmAncho`` o ``mmAltura``.
* Sube el SVG como plano asociado al producto.
* Define las fórmulas correspondientes, por ejemplo ``mmAltura - 50`` o
  ``(mmA + mmB) / 2``.
* Opcionalmente, define condiciones de plano basadas en atributos mediante el
  modelo ``product.blueprint.condition``.

3. Crea un pedido de venta o compra
-----------------------------------

* Selecciona el producto.
* Configura los valores de atributos, incluidos los personalizados.
* Guarda el pedido.

4. Genera el plano
------------------

* Desde el menú ``Imprimir``, elige ``Plano Orden de Fabricación`` o
  ``Plano Orden de Compra`` según el tipo de plano configurado.
* Se genera un PDF con los planos dinámicos evaluados y, opcionalmente, un
  resumen de atributos.

Seguridad
=========

Las fórmulas se evalúan en un entorno restringido:

* Solo se permiten operadores y funciones matemáticas, por ejemplo ``+``,
  ``-``, ``*``, ``/``, ``//``, ``math.ceil`` o ``math.floor``.
* Se usa ``ast.parse`` y un entorno sin ``__builtins__`` para evitar
  ejecuciones arbitrarias.
* Los valores solo provienen de atributos configurados en la línea de pedido.

En caso de error en la evaluación:

* El módulo registra un log detallado.
* El nodo correspondiente en el SVG se marca visualmente para facilitar la
  depuración.

Estructura del módulo
=====================

::

    product_blueprint_manager/
    ├── models/
    │   ├── sale_order_line.py
    │   ├── product_blueprint.py
    │   ├── product_blueprint_formula_name.py
    │   └── ...
    ├── views/
    │   ├── product_blueprint_views.xml
    │   └── ...
    ├── report/
    │   ├── sale_order_report.xml
    │   └── purchase_order_report.xml
    └── static/
        └── ...

Consejo práctico
================

Si los valores evaluados no se ven o no aparecen donde esperas:

* Asegúrate de que los nodos tengan ``class="odoo-formula"``.
* Verifica que el nombre que se extrae del SVG, ya sea texto o
  ``aria-label``, coincida exactamente con la etiqueta de la fórmula
  configurada.
* Comprueba que los atributos personalizados tengan valores numéricos y que
  estén marcados como ``is_custom`` cuando deban generar variables.
* Revisa los logs de Odoo en nivel ``debug`` para localizar mensajes
  ``[Blueprint]``.

TODO / Roadmap
==============

Las siguientes tareas están previstas para futuras versiones del módulo:

* Añadir un botón ``Reescanear SVG`` en la ficha del plano para:

  * Detectar automáticamente todos los nodos con ``class="odoo-formula"``.
  * Proponer la creación o actualización de registros de fórmula incluyendo el
    ID del nodo, el nombre sugerido y el color y tamaño de fuente detectados.

* Documentar y, en su caso, extender el soporte a más tipos de nodos SVG,
  como líneas o polígonos, manteniendo la conversión final a ``<text>`` cuando
  se trate de fórmulas.
* Permitir condiciones de plano más avanzadas, como rangos numéricos o
  exclusiones, sin romper la compatibilidad con las condiciones actuales
  basadas en valores de atributos.
