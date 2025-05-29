#!/bin/bash

# Nombre del script: sync-all.sh (ex combo-sync-from-develop.sh)

# Guardar rama original
ORIGINAL_BRANCH=$(git symbolic-ref --short HEAD)

# Asegurar que estás en develop
if [ "$ORIGINAL_BRANCH" != "develop" ]; then
  echo "⚠️ Debes estar en la rama develop para ejecutar este script."
  echo "📍 Estás en: $ORIGINAL_BRANCH"
  exit 1
fi

# Verificar si hay conflictos pendientes en develop
if git ls-files -u | grep .; then
  echo "❌ Hay conflictos sin resolver en develop. Resuélvelos antes de continuar."
  exit 1
fi

# Asegurar que el último commit está pusheado
LAST_COMMIT=$(git log -1 --pretty=format:"%H")
IS_PUSHED=$(git branch -r --contains "$LAST_COMMIT" | grep "origin/develop")

if [ -z "$IS_PUSHED" ]; then
  echo "🔄 El último commit aún no ha sido pusheado a origin/develop. Haciendo push..."
  git push origin develop || exit 1
fi

echo "🔍 Último commit en develop: $LAST_COMMIT"

# CHERRY-PICK EN 17.0
echo "🧭 Cambiando a la rama 17.0..."
git checkout 17.0 || exit 1

echo "🎯 Cherry-pick en 17.0..."
git cherry-pick "$LAST_COMMIT" || exit 1

echo "🚀 Push a origin/17.0..."
git push origin 17.0 || exit 1

# CHERRY-PICK EN 16.0
echo "🧭 Cambiando a la rama 16.0..."
git checkout 16.0 || exit 1

echo "🎯 Cherry-pick en 16.0 (sin commit aún)..."
git cherry-pick -n "$LAST_COMMIT" || exit 1

# Restaurar los manifests
git restore --staged product_blueprint_manager/__manifest__.py
git restore --staged product_configurator_attribute_price/__manifest__.py

git restore product_blueprint_manager/__manifest__.py
git restore product_configurator_attribute_price/__manifest__.py

echo "✍️ Puedes modificar manualmente los __manifest__.py si lo necesitas ahora."
read -p "⏸️ Presiona ENTER para continuar con el commit en 16.0..."

git commit -m "Cherry-pick $LAST_COMMIT desde develop sin modificar __manifest__.py"

echo "🚀 Push a origin/16.0..."
git push origin 16.0 || exit 1

# Volver a la rama original
git checkout "$ORIGINAL_BRANCH"
echo "✅ Proceso completo terminado con éxito. De vuelta en $ORIGINAL_BRANCH"
