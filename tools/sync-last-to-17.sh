#!/bin/bash

# Obtener el último commit de develop
LAST_COMMIT=$(git log develop -1 --pretty=format:"%H")

echo ">> Último commit en develop: $LAST_COMMIT"

git checkout 17.0 || exit 1
git cherry-pick -n "$LAST_COMMIT" || exit 1

# Restaurar los dos __manifest__.py
git restore --staged product_blueprint_manager/__manifest__.py
git restore --staged product_configurator_attribute_price/__manifest__.py

git restore product_blueprint_manager/__manifest__.py
git restore product_configurator_attribute_price/__manifest__.py

git commit -m "Cherry-pick $LAST_COMMIT desde develop sin modificar __manifest__.py"

echo ">> Haciendo push a origin/17.0"
git push origin 17.0
