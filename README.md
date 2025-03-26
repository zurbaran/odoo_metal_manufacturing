# odoo_metal_manufacturing

product_configurator_attribute_price

product_blueprint_manager


TODO:
Eliminar vulnerabilidad por inyeccion de codigo atraves de eval e intentar utilizar la libreria numexpr


## 🔄 Sincronización entre ramas (`develop` → `16.0` y `17.0`)

Este proyecto utiliza scripts para sincronizar cambios desde la rama `develop` a las ramas `16.0` y `17.0`, manteniendo compatibilidad entre versiones de Odoo.

### 📁 Estructura
- `develop`: rama de desarrollo principal (basada en Odoo 16)
- `16.0`: versión estable para Odoo 16
- `17.0`: versión para Odoo 17 (con `__manifest__.py` específicos)

---

### ⚙️ Scripts disponibles

| Script                       | Acción                                                                 |
|-----------------------------|------------------------------------------------------------------------|
| `tools/sync-last-to-16.sh`  | Cherry-pick del último commit de `develop` a `16.0` y push automático |
| `tools/sync-last-to-17.sh`  | Cherry-pick del último commit de `develop` a `17.0` (sin tocar manifests) |
| `tools/sync-all.sh`         | Ejecuta ambos scripts anteriores en orden                             |

Todos los scripts hacen `push` automático al finalizar.

---

### 🔐 Protección de los `__manifest__.py` en `17.0`

Al ejecutar `tools/sync-last-to-17.sh` o `tools/sync-all.sh`, se protege el contenido de estos archivos:

- `product_blueprint_manager/__manifest__.py`
- `product_configurator_attribute_price/__manifest__.py`

Esto significa que **los cambios hechos manualmente en estos archivos no serán sobrescritos** por los scripts de sincronización.

✅ Puedes modificar los manifests directamente en `17.0`:

```bash
git checkout 17.0
# editás uno o ambos manifests
git add product_*/*__manifest__.py
git commit -m "Actualización manual del manifest para Odoo 17"
git push origin 17.0
```

Estos cambios se mantendrán intactos en sincronizaciones futuras.

---
