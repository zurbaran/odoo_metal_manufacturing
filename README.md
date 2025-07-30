# odoo_metal_manufacturing

Este repositorio contiene desarrollos para la vertical de manufactura en Odoo, incluyendo los módulos:

- `product_configurator_attribute_price`
- `product_blueprint_manager`
- `auto_journal_by_company`

Cada módulo incluye su propio `README.md` con detalles específicos.

---

## 🔄 Sincronización entre ramas (`develop` → `17.0` y `16.0`)

Este proyecto mantiene tres ramas principales:

- `develop`: rama activa de desarrollo (basada en Odoo 17)
- `17.0`: versión estable para Odoo 17 (**se mantiene completamente sincronizada con `develop`**)
- `16.0`: versión para Odoo 16 (**recibe sincronización parcial** – se excluyen los archivos `__manifest__.py`)

---

## ⚙️ Scripts disponibles en `tools/`

| Script                       | Descripción                                                                                 |
|-----------------------------|---------------------------------------------------------------------------------------------|
| `sync-last-to-17.sh`        | Cherry-pick del último commit de `develop` a `17.0`, con `push` automático.                |
| `sync-last-to-16.sh`        | Cherry-pick del último commit de `develop` a `16.0`, **sin modificar `__manifest__.py`**. |
| `git-cp17.sh <commit>`      | Cherry-pick manual de un commit específico a `17.0`.                                        |
| `git-cp16.sh <commit>`      | Cherry-pick manual de un commit a `16.0`, permitiendo edición manual de los manifests.     |
| `sync-all.sh`               | Versión combinada e inteligente: sincroniza el último commit de `develop` a `17.0` y `16.0`, permitiendo edición manual del manifest antes del commit. |

---

## 🔐 Protección de `__manifest__.py` en `16.0`

Los scripts de sincronización restauran automáticamente los siguientes archivos tras hacer cherry-pick:

- `product_blueprint_manager/__manifest__.py`
- `product_configurator_attribute_price/__manifest__.py`

Esto permite que `develop` y `17.0` evolucionen con los cambios de Odoo 17, sin interferir con los requerimientos específicos de Odoo 16.

> Durante el proceso de sincronización con `16.0`, se te dará la oportunidad de editar manualmente los manifests antes de hacer commit.

---

### 🛠️ Ejemplo de sincronización completa

```bash
./tools/sync-all.sh
```

Este comando:

1. Verifica que estés en la rama `develop`
2. Aplica el último commit a `17.0` automáticamente
3. Luego lo aplica a `16.0`, permitiendo que edites los manifests antes del commit
4. Vuelve a tu rama original

---

## 🚨 Seguridad

**TODO**:
