# odoo_metal_manufacturing

product_configurator_attribute_price

product_blueprint_manager


TODO:
Eliminar vulnerabilidad por inyeccion de codigo atraves de eval e intentar utilizar la libreria numexpr


## 🔄 Sincronización entre ramas (`develop` → `17.0` y `16.0`)

Este proyecto mantiene tres ramas principales:

- `develop`: rama activa de desarrollo (base en Odoo 17)
- `17.0`: rama de versión estable para Odoo 17 (**se mantiene totalmente sincronizada con `develop`**)
- `16.0`: rama para Odoo 16 (**sincroniza parcialmente**, preservando `__manifest__.py`)

---

### ⚙️ Scripts de sincronización

| Script                       | Acción                                                                 |
|-----------------------------|------------------------------------------------------------------------|
| `tools/sync-last-to-17.sh`  | Cherry-pick del último commit de `develop` a `17.0`, con `push` automático |
| `tools/sync-last-to-16.sh`  | Cherry-pick del último commit de `develop` a `16.0`, **preservando `__manifest__.py`** |
| `tools/sync-all.sh`         | Ejecuta ambos scripts anteriores en orden y vuelve a la rama de origen |

---

### 🔐 Protección de `__manifest__.py` en `16.0`

El script `tools/sync-last-to-16.sh` protege los archivos:

- `product_blueprint_manager/__manifest__.py`
- `product_configurator_attribute_price/__manifest__.py`

Esto asegura que `develop` y `17.0` puedan evolucionar libremente para Odoo 17, mientras que `16.0` mantiene sus manifests específicos.

Puedes modificar manualmente los manifests en `16.0` con:

```bash
git checkout 16.0
# Editar los manifests según sea necesario
git add product_*/*__manifest__.py
git commit -m "Actualización manual del manifest para Odoo 16"
git push origin 16.0
```

Los scripts de sincronización **respetarán esos cambios**.

---

### 🛠️ Ejemplo de uso

```bash
./tools/sync-all.sh
```

> Esto cherry-pickea el último commit de `develop` a `16.0` (sin modificar manifests) y luego a `17.0` (completo), con `push` incluido y retorno automático a tu rama actual.
