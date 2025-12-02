"""Módulo: product_custom_attribute_value

Este archivo extiende el modelo estándar de Odoo
`product.attribute.custom.value` mediante herencia, sin añadir nuevos
campos ni lógica adicional.

Su finalidad principal es:

- Proveer un **punto de extensión** limpio y controlado dentro de este
  módulo (`product_configurator_attribute_price`), de forma que en el
  futuro se pueda:
    - Añadir nueva lógica de negocio (métodos compute, constraints, etc.).
    - Incorporar campos adicionales relacionados con precios o fórmulas.
    - Integrar comportamiento específico con otros módulos (por ejemplo,
      planos, configuradores, etc.).
- Mantener una **buena separación de responsabilidades**: la lógica
  propia de este módulo se incorporará aquí, sin modificar directamente
  el código fuente estándar de Odoo.
- Facilitar la **compatibilidad futura** con versiones posteriores de
  Odoo y con módulos de la OCA, centralizando los cambios en una capa de
  herencia.

Última modificación
-------------------

En la última iteración del módulo se ha introducido explícitamente esta
clase de herencia vacía sobre ``product.attribute.custom.value``:

- Antes, el módulo se apoyaba directamente en el modelo estándar sin
  disponer de un punto de enganche propio.
- Ahora, todo comportamiento futuro relacionado con valores
  personalizados (especialmente los que intervienen en fórmulas de
  precio) deberá añadirse aquí.
- Este cambio **no altera el comportamiento funcional actual**: se trata
  de una modificación estructural/preventiva, pensada para:
    - Evitar introducir bugs mientras el resto del flujo de precios se
      estabiliza.
    - Permitir ampliar o ajustar la lógica de valores personalizados en
      un único sitio, sin tocar el core de Odoo ni dispersar parches
      por otros modelos.

Actualmente, este archivo no introduce cambios funcionales: solo declara
la herencia del modelo estándar para dejar preparado el punto de apoyo
para futuras ampliaciones y para documentar explícitamente su propósito.
"""

from odoo import models  # Importamos el componente base para declarar modelos Odoo


class ProductCustomAttributeValue(models.Model):
    """Extiende el modelo estándar de valores personalizados de atributo.

    Este modelo hereda directamente de ``product.attribute.custom.value``,
    el cual es el modelo nativo de Odoo que almacena los valores
    personalizados (por ejemplo, medidas numéricas introducidas en el
    configurador de productos).

    Claves de diseño:

    - **Sin campos nuevos**:
        No se añaden nuevos campos en esta clase. Se reutiliza
        exactamente la estructura del modelo estándar.
    - **Sin sobreescritura de métodos**:
        Al no sobreescribir métodos, el comportamiento nativo se mantiene
        tal cual. Esto es una herencia "pasiva" o de tipo *hook*, cuyo
        fin es permitir futuras extensiones sin tocar el core.
    - **Punto centralizado para futuras ampliaciones**:
        Si más adelante se necesita:
          * Validar los datos personalizados.
          * Añadir lógica de cálculo adicional relacionada con
            ``custom_value``.
          * Conectarlo con planos, fórmulas de precio u otros modelos.
        todo ello se implementará aquí, manteniendo el núcleo de Odoo
        intacto.

    Último cambio y motivación:

    - Se ha creado esta clase como capa intermedia explícita para que
      cualquier lógica adicional ligada a valores personalizados (por
      ejemplo, validaciones extra o ajustes específicos de cálculo de
      precio) se implemente aquí.
    - De esta forma, se evita tocar directamente ``product.attribute.custom.value``
      desde otros ficheros del módulo y se reduce el riesgo de efectos
      colaterales o conflictos con otros módulos.
    - Hasta que no se definan nuevos requerimientos, la herencia se
      mantiene intencionadamente vacía para no introducir cambios
      inesperados en entornos ya en producción.

    Beneficios:

    - Mayor mantenibilidad: cualquier mejora o corrección de este módulo
      relacionada con valores personalizados se concentra en esta clase.
    - Claridad arquitectónica: queda explícito que el módulo trabaja
      sobre el modelo estándar de valores personalizados.
    - Compatibilidad con otros módulos: al mantener la herencia y no
      redefinir la estructura, otros módulos que dependan de
      ``product.attribute.custom.value`` seguirán funcionando con normalidad.
    """

    # Mediante _inherit indicamos que **no** creamos un modelo nuevo,
    # sino que extendemos el modelo estándar existente. Esto asegura
    # compatibilidad con toda la lógica nativa que use este modelo.
    _inherit = "product.attribute.custom.value"
