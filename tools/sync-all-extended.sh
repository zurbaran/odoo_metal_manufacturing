#!/bin/bash

ORIGINAL_BRANCH=$(git symbolic-ref --short HEAD)

if [ -d ".git/rebase-apply" ] || [ -d ".git/rebase-merge" ]; then
  echo "🛑 Rebase en curso. Usa 'git rebase --abort' antes de continuar."
  exit 1
fi

if [ "$ORIGINAL_BRANCH" != "develop" ]; then
  echo "⚠ Debes estar en la rama develop. Estás en: $ORIGINAL_BRANCH"
  exit 1
fi

if git ls-files -u | grep .; then
  echo "❌ Hay conflictos sin resolver. Abortando..."
  exit 1
fi

LAST_COMMIT=$(git log -1 --pretty=format:"%H")
IS_PUSHED=$(git branch -r --contains "$LAST_COMMIT" | grep "origin/develop")

if [ -z "$IS_PUSHED" ]; then
  echo "🔄 El último commit no ha sido pusheado. Ejecutando push..."
  git push origin develop || exit 1
fi

echo "🔍 Último commit: $LAST_COMMIT"

### === Función reutilizable === ###
sync_commit() {
  local RAMA="$1"
  local COMMIT="$2"
  local TIPO="$3"

  echo "🧭 Cambiando a $RAMA..."
  git checkout "$RAMA" || exit 1

  if git branch --contains "$COMMIT" | grep -q "$RAMA"; then
    echo "🔁 El commit ya está presente en $RAMA. Saltando..."
    return
  fi

  if [[ "$TIPO" == "normal" ]]; then
    echo "🎯 Cherry-pick en $RAMA..."
    git cherry-pick "$COMMIT" || exit 1
    git push origin "$RAMA" || exit 1

  elif [[ "$TIPO" == "no_manifest" ]]; then
    echo "🎯 Cherry-pick en $RAMA (sin commit)..."
    git cherry-pick -n "$COMMIT" || exit 1
    echo "🔄 Restaurando __manifest__.py..."
    git restore --staged product_blueprint_manager/__manifest__.py 2>/dev/null
    git restore --staged product_configurator_attribute_price/__manifest__.py 2>/dev/null
    git restore product_blueprint_manager/__manifest__.py 2>/dev/null
    git restore product_configurator_attribute_price/__manifest__.py 2>/dev/null
    read -p "✍ Revisá los __manifest__.py si es necesario. ENTER para hacer commit... "
    git commit -m "Cherry-pick $COMMIT desde develop sin modificar __manifest__.py"
    git push origin "$RAMA" || exit 1

  elif [[ "$TIPO" == "no_manifest_no_dir" ]]; then
    echo "🎯 Cherry-pick en $RAMA (sin commit)..."
    git cherry-pick -n "$COMMIT" || exit 1
    echo "🔄 Restaurando __manifest__.py y sale_product_configurator/..."
    git restore --staged product_blueprint_manager/__manifest__.py 2>/dev/null
    git restore --staged product_configurator_attribute_price/__manifest__.py 2>/dev/null
    git restore --staged sale_product_configurator/ 2>/dev/null
    git restore product_blueprint_manager/__manifest__.py 2>/dev/null
    git restore product_configurator_attribute_price/__manifest__.py 2>/dev/null
    git restore sale_product_configurator/ 2>/dev/null
    read -p "✍ Podés editar archivos ahora. ENTER para hacer commit... "
    git commit -m "Cherry-pick $COMMIT desde develop sin modificar __manifest__.py ni sale_product_configurator/"
    git push origin "$RAMA" || exit 1
  fi
}

# Aplicar a cada rama
sync_commit "17.0" "$LAST_COMMIT" "normal"
sync_commit "16.0" "$LAST_COMMIT" "no_manifest"
sync_commit "18.0" "$LAST_COMMIT" "no_manifest_no_dir"

git checkout "$ORIGINAL_BRANCH"
echo "✅ Sincronización completa. De vuelta en $ORIGINAL_BRANCH"
