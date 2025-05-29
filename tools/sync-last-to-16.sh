#!/bin/bash

ORIGINAL_BRANCH=$(git symbolic-ref --short HEAD)

LAST_COMMIT=$(git log develop -1 --pretty=format:"%H")
echo ">> Último commit en develop: $LAST_COMMIT"

git checkout 16.0 || exit 1
git cherry-pick -n "$LAST_COMMIT" || exit 1

# Restaurar los manifests
git restore --staged product_blueprint_manager/__manifest__.py
git restore --staged product_configurator_attribute_price/__manifest__.py

git restore product_blueprint_manager/__manifest__.py
git restore product_configurator_attribute_price/__manifest__.py

echo ">> Puedes modificar manualmente los __manifest__.py si lo deseas."
read -p "Presiona ENTER para continuar con el commit..."

git commit -m "Cherry-pick $LAST_COMMIT desde develop sin modificar __manifest__.py"

echo ">> Haciendo push a origin/16.0"
git push origin 16.0

git checkout "$ORIGINAL_BRANCH"
echo "✅ Sincronización a 16.0 completada. De vuelta en $ORIGINAL_BRANCH"
