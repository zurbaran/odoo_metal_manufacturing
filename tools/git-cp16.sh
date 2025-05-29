#!/bin/bash

COMMIT="$1"

if [ -z "$COMMIT" ]; then
  echo "Uso: ./tools/git-cp16.sh <commit_hash>"
  exit 1
fi

echo ">> Cherry-pickeando $COMMIT desde develop a 16.0 (sin modificar los manifests)"

# Cambiar a la rama 16.0
git checkout 16.0 || exit 1

# Aplicar cherry-pick sin commit
git cherry-pick -n "$COMMIT" || exit 1

# Restaurar los manifests
git restore --staged product_blueprint_manager/__manifest__.py
git restore --staged product_configurator_attribute_price/__manifest__.py

git restore product_blueprint_manager/__manifest__.py
git restore product_configurator_attribute_price/__manifest__.py

echo ">> Puedes modificar manualmente los __manifest__.py si lo necesitas ahora."
read -p "Presiona ENTER para continuar con el commit..."

git commit -m "Cherry-pick $COMMIT desde develop sin modificar __manifest__.py"
