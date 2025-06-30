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

# === Función principal de sincronización ===
sync_commit() {
  local BRANCH="$1"
  local COMMIT="$2"
  local TYPE="$3"

  echo "🧭 Cambiando a $BRANCH..."
  git checkout "$BRANCH" || exit 1

  # 🧠 Verificar si ya se aplicó el mismo patch (contenido)
  if grep -q "^$BRANCH|$PATCH_ID$" "$SYNC_STATE"; then
    echo "✅ $BRANCH ya contiene el patch. Saltando..."
    return
  fi

  # ⚠️ Detectar si el commit ya está en la rama
  if git branch --contains "$COMMIT" | grep -q "$BRANCH"; then
    echo "🔁 El commit ya está presente en $BRANCH. Saltando..."
    echo "$BRANCH|$PATCH_ID" >> "$SYNC_STATE"
    return
  fi

  if [[ "$TYPE" == "normal" ]]; then
    echo "🎯 Cherry-pick en $BRANCH..."

    PARENTS=$(git rev-list --parents -n 1 "$COMMIT" | wc -w)
    if [ "$PARENTS" -gt 2 ]; then
      echo "⚠ El commit es una fusión. Usando cherry-pick -m 1"
      git cherry-pick -m 1 "$COMMIT" || {
        if git status | grep -q "El cherry-pick anterior ahora está vacío"; then
          git cherry-pick --skip
          echo "⚠️ Cherry-pick vacío (fusión). Saltado."
        else
          echo "❌ Error en cherry-pick fusión"
          exit 1
        fi
      }
    else
      git cherry-pick "$COMMIT" || {
        if git status | grep -q "El cherry-pick anterior ahora está vacío"; then
          git cherry-pick --skip
          echo "⚠️ Cherry-pick vacío. Saltado."
        else
          echo "❌ Error en cherry-pick"
          exit 1
        fi
      }
    fi

    git push origin "$BRANCH"

  elif [[ "$TYPE" == "no_manifest" ]]; then
    echo "🎯 Cherry-pick en $BRANCH (sin commit)..."
    git cherry-pick -n "$COMMIT" || exit 1

    echo "🔄 Restaurando __manifest__.py..."
    git restore --staged product_blueprint_manager/__manifest__.py 2>/dev/null
    git restore --staged product_configurator_attribute_price/__manifest__.py 2>/dev/null
    git restore product_blueprint_manager/__manifest__.py 2>/dev/null
    git restore product_configurator_attribute_price/__manifest__.py 2>/dev/null

    read -p "✍ Revisá los __manifest__.py si es necesario. ENTER para hacer commit... "
    git commit -m "Cherry-pick $COMMIT desde develop sin modificar __manifest__.py"
    git push origin "$BRANCH"

  elif [[ "$TYPE" == "no_manifest_no_dir" ]]; then
    echo "🎯 Cherry-pick en $BRANCH (sin commit)..."
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
    git push origin "$BRANCH"
  fi

  echo "$BRANCH|$PATCH_ID" >> "$SYNC_STATE"
}

# ✅ Ejecutar cherry-pick si no fue aplicado ya
run_if_not_synced() {
  local BRANCH="$1"
  local COMMIT="$2"
  local TYPE="$3"

  sync_commit "$BRANCH" "$COMMIT" "$TYPE"
}

# 🧠 Ejecutar sincronización con reanudación inteligente
run_if_not_synced "17.0" "$LAST_COMMIT" "normal"
run_if_not_synced "16.0" "$LAST_COMMIT" "no_manifest"
run_if_not_synced "18.0" "$LAST_COMMIT" "no_manifest_no_dir"

# 🔚 Volver a develop y limpiar
git checkout "$ORIGINAL_BRANCH"
rm -f "$SYNC_STATE"
echo "✅ Sincronización completa. De vuelta en $ORIGINAL_BRANCH"
