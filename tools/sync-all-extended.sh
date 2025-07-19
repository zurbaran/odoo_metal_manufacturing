#!/bin/bash

set -e

ORIGINAL_BRANCH=$(git symbolic-ref --short HEAD)
SYNC_STATE=".sync_state"

touch "$SYNC_STATE"

# 🚫 Validaciones iniciales
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

# 🚀 Validar último commit en develop y pushearlo si falta
LAST_COMMIT=$(git log -1 --pretty=format:"%H")
IS_PUSHED=$(git branch -r --contains "$LAST_COMMIT" | grep "origin/develop")

if [ -z "$IS_PUSHED" ]; then
  echo "🔄 El último commit no ha sido pusheado. Ejecutando push..."
  git push origin develop || exit 1
fi

echo "🔍 Último commit: $LAST_COMMIT"

# ✅ Obtener patch-id del último commit
PATCH_ID=$(git show "$LAST_COMMIT" | git patch-id --stable | awk '{print $1}')

# === Función para comprobar si el patch ya existe en una rama ===
branch_has_patch() {
  local BRANCH="$1"
  if git log "$BRANCH" --pretty=format:"%H" | while read -r commit; do
    git show "$commit" | git patch-id --stable
  done | grep -q "$PATCH_ID"; then
    return 0
  else
    return 1
  fi
}

# === Función principal de sincronización ===
sync_commit() {
  local BRANCH="$1"
  local COMMIT="$2"
  local TYPE="$3"

  echo "🧭 Cambiando a $BRANCH..."
  git checkout "$BRANCH" || exit 1

  # 🧠 Verificar si ya se aplicó por patch-id
  if branch_has_patch "$BRANCH"; then
    echo "✅ $BRANCH ya contiene el commit (por contenido). Saltando..."
    echo "$BRANCH|$PATCH_ID" >> "$SYNC_STATE"
    return
  fi

  if [[ "$TYPE" == "normal" ]]; then
    echo "🎯 Cherry-pick en $BRANCH..."
    PARENTS=$(git rev-list --parents -n 1 "$COMMIT" | wc -w)
    if [ "$PARENTS" -gt 2 ]; then
      echo "⚠ El commit es una fusión. Usando cherry-pick -m 1"
      if git cherry-pick -m 1 "$COMMIT"; then
        echo "✅ Cherry-pick fusión exitoso"
      elif git status | grep -q "El cherry-pick anterior ahora está vacío"; then
        git cherry-pick --skip
        echo "⚠ Cherry-pick vacío (fusión). Saltado."
      else
        echo "❌ Error en cherry-pick fusión"
        exit 1
      fi
    else
      if git cherry-pick "$COMMIT"; then
        echo "✅ Cherry-pick normal exitoso"
      elif git status | grep -q "El cherry-pick anterior ahora está vacío"; then
        git cherry-pick --skip
        echo "⚠ Cherry-pick vacío. Saltado."
      else
        echo "❌ Error en cherry-pick"
        exit 1
      fi
    fi
    git push origin "$BRANCH"
    echo "$BRANCH|$PATCH_ID" >> "$SYNC_STATE"

  elif [[ "$TYPE" == "no_manifest" || "$TYPE" == "no_manifest_no_dir" ]]; then
    echo "🎯 Cherry-pick en $BRANCH (sin commit)..."
    git cherry-pick -n "$COMMIT" || exit 1

    # Excluir archivo del propio script
    git restore --staged tools/sync-all-extended.sh 2>/dev/null
    git restore tools/sync-all-extended.sh 2>/dev/null

    if [[ "$TYPE" == "no_manifest" ]]; then
      echo "🔄 Restaurando __manifest__.py..."
      git restore --staged product_blueprint_manager/__manifest__.py 2>/dev/null
      git restore --staged product_configurator_attribute_price/__manifest__.py 2>/dev/null
      git restore product_blueprint_manager/__manifest__.py 2>/dev/null
      git restore product_configurator_attribute_price/__manifest__.py 2>/dev/null

    elif [[ "$TYPE" == "no_manifest_no_dir" ]]; then
      echo "🔄 Restaurando __manifest__.py y sale_product_configurator/..."
      git restore --staged product_blueprint_manager/__manifest__.py 2>/dev/null
      git restore --staged product_configurator_attribute_price/__manifest__.py 2>/dev/null
      git restore --staged sale_product_configurator/ 2>/dev/null
      git restore product_blueprint_manager/__manifest__.py 2>/dev/null
      git restore product_configurator_attribute_price/__manifest__.py 2>/dev/null
      git restore sale_product_configurator/ 2>/dev/null
    fi

    if git diff --staged --quiet; then
      echo "⚠ No hay cambios para commitear. Commit vacío."
      git commit --allow-empty -m "Cherry-pick $COMMIT ya aplicado en $BRANCH"
    else
      read -p "✍ Revisá los archivos restaurados. ENTER para hacer commit... "
      git commit -m "Cherry-pick $COMMIT desde develop sin modificar __manifest__.py ni el script"
    fi

    git push origin "$BRANCH"
    echo "$BRANCH|$PATCH_ID" >> "$SYNC_STATE"
  fi
}

run_if_not_synced() {
  local BRANCH="$1"
  local COMMIT="$2"
  local TYPE="$3"
  sync_commit "$BRANCH" "$COMMIT" "$TYPE"
}

run_if_not_synced "17.0" "$LAST_COMMIT" "normal"
run_if_not_synced "16.0" "$LAST_COMMIT" "no_manifest"
run_if_not_synced "18.0" "$LAST_COMMIT" "no_manifest_no_dir"

git checkout "$ORIGINAL_BRANCH"
rm -f "$SYNC_STATE"
echo "✅ Sincronización completa. De vuelta en $ORIGINAL_BRANCH"
