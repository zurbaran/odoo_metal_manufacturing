#!/bin/bash

ORIGINAL_BRANCH=$(git symbolic-ref --short HEAD)

# Validación previa
if [ -d ".git/rebase-apply" ] || [ -d ".git/rebase-merge" ]; then
  echo "🛑 Rebase en curso. Usa 'git rebase --abort' antes de continuar."
  exit 1
fi

if [ "$ORIGINAL_BRANCH" != "develop" ]; then
  echo "⚠ Debes estar en la rama develop para ejecutar este script. Estás en: $ORIGINAL_BRANCH"
  exit 1
fi

if git ls-files -u | grep .; then
  echo "❌ Hay conflictos sin resolver. Resuélvelos antes de continuar."
  exit 1
fi

LAST_COMMIT=$(git log -1 --pretty=format:"%H")
IS_PUSHED=$(git branch -r --contains "$LAST_COMMIT" | grep "origin/develop")

if [ -z "$IS_PUSHED" ]; then
  echo "🔄 El último commit no ha sido pusheado. Ejecutando push..."
  git push origin develop || exit 1
fi

echo "🔍 Último commit: $LAST_COMMIT"

### === 1. Sync a 17.0 === ###
echo "🧭 Cambiando a 17.0..."
git checkout 17.0 || exit 1
echo "🎯 Cherry-pick en 17.0..."
git cherry-pick "$LAST_COMMIT" || exit 1
echo "🚀 Push a origin/17.0..."
git push origin 17.0 || exit 1

### === 2. Sync a 16.0 === ###
echo "🧭 Cambiando a 16.0..."
git checkout 16.0 || exit 1
echo "🎯 Cherry-pick en 16.0 (sin commit)..."
git cherry-pick -n "$LAST_COMMIT"

echo "🔄 Restaurando __manifest__.py..."
git restore --staged product_blueprint_manager/__manifest__.py 2>/dev/null
git restore --staged product_configurator_attribute_price/__manifest__.py 2>/dev/null
git restore product_blueprint_manager/__manifest__.py 2>/dev/null
git restore product_configurator_attribute_price/__manifest__.py 2>/dev/null

read -p "✍ Revisá los __manifest__.py si es necesario. ENTER para hacer commit... " 
git commit -m "Cherry-pick $LAST_COMMIT desde develop sin modificar __manifest__.py"
git push origin 16.0 || exit 1

### === 3. Sync a 18.0 === ###
echo "🧭 Cambiando a 18.0..."
git checkout 18.0 || exit 1
echo "🎯 Cherry-pick en 18.0 (sin commit)..."
git cherry-pick -n "$LAST_COMMIT"

echo "🔄 Restaurando __manifest__.py y sale_product_configurator/..."
git restore --staged product_blueprint_manager/__manifest__.py 2>/dev/null
git restore --staged product_configurator_attribute_price/__manifest__.py 2>/dev/null
git restore --staged sale_product_configurator/ 2>/dev/null

git restore product_blueprint_manager/__manifest__.py 2>/dev/null
git restore product_configurator_attribute_price/__manifest__.py 2>/dev/null
git restore sale_product_configurator/ 2>/dev/null

read -p "✍ Podés editar archivos ahora. ENTER para hacer commit... " 
git commit -m "Cherry-pick $LAST_COMMIT desde develop sin modificar __manifest__.py ni sale_product_configurator/"
git push origin 18.0 || exit 1

### Finalización ###
git checkout "$ORIGINAL_BRANCH"
echo "✅ Sincronización completa. De vuelta en $ORIGINAL_BRANCH"
