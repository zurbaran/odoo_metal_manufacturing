# odoo_metal_manufacturing

Este repositorio contiene desarrollos para la vertical de manufactura en Odoo, incluyendo los módulos:

- `product_configurator_attribute_price`
- `product_blueprint_manager`
- `auto_journal_by_company`

Cada módulo mantiene su propio `README.md` con detalles específicos.

---

## 🌳 Estructura de ramas

Este proyecto sigue el flujo de trabajo recomendado por la **OCA**:

- `16.0`: versión estable para Odoo 16.
- `17.0`: versión estable para Odoo 17. 
- `18.0`: versión para Odoo 18 y **rama principal de desarrollo** (Odoo 18).
- `19.0`: versión para Odoo 18 y **rama principal de desarrollo** (Odoo 18).

---

## 🔄 Propagación de cambios entre versiones

Cuando un cambio realizado en `18.0` debe aplicarse también en `17.0` o `16.0`, se utilizan **herramientas OCA** para portarlo:

- [oca-port](https://github.com/OCA/oca-port): detecta y aplica commits que faltan entre ramas.
- Cherry-pick manual: para casos puntuales.

## 🚨 Seguridad

**TODO**:
