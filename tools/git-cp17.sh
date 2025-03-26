#!/bin/bash

COMMIT="$1"

if [ -z "$COMMIT" ]; then
  echo "Uso: ./tools/git-cp17.sh <commit_hash>"
  exit 1
fi

echo ">> Cherry-pickeando $COMMIT desde develop a 17.0 (sin modificar los manifests)"

git checkout 17.0 || exit 1
git cherry-pick -n "$COMMIT" || exit 1

# Restaurar ambos manifests
git restore --staged product_blueprint_manager/__manifest__.py
git restore --staged product_configurator_attribute_price/__manifest__.py

git restore product_blueprint_manager/__manifest__.py
git restore product_configurator_attribute_price/__manifest__.py

git commit -m "Cherry-pick $COMMIT desde develop sin modificar __manifest__.py"
