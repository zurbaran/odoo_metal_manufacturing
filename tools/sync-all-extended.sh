#!/bin/bash

set -e

ORIGINAL_BRANCH=$(git symbolic-ref --short HEAD)
SYNC_STATE=".sync_state"

# Parámetros
ONLY_BRANCH=""
EXCLUDE_BRANCH=""

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --only)
            ONLY_BRANCH="$2"
            shift 2
            ;;
        --exclude)
            EXCLUDE_BRANCH="$2"
            shift 2
            ;;
        *)
            echo "Uso: $0 [--only <branch>] [--exclude <branch>]"
            exit 1
            ;;
    esac
done

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
PATCH_ID=$(git show "$LAST_COMMIT" | git patch-id --stable | awk '{print $1}')

# Función: chequear si patch ya existe en la rama
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

# Función: sincronización
sync_commit() {
  local BRANCH="$1"
  local COMMIT="$2"
  local TYPE="$3"

  # Filtrar con --only y --exclude
  if [ -n "$ONLY_BRANCH" ] && [ "$ONLY_BRANCH" != "$BRANCH" ]; then
    echo "⏭  Saltando $BRANCH (no está en --only $ONLY_BRANCH)"
    return
  fi
  if [ -n "$EXCLUDE_BRANCH" ] && [ "$EXCLUDE_BRANCH" == "$BRANCH" ]; then
    echo "⏭  Saltando $BRANCH (está en --exclude)"
    return
  fi

  echo "🧭 Cambiando a $BRANCH..."
  git checkout "$BRANCH" || exit 1

  # Verificar si ya existe por patch-id
  if branch_has_patch "$BRANCH"; then
    echo "✅ $BRANCH ya contiene el commit (por contenido). Saltando..."
    echo "$BRANCH|$PATCH_ID" >> "$SYNC_STATE"
    return
  fi

  # Cherry-pick
  echo "🎯 Cherry-pick en $BRANCH..."
  if [[ "$TYPE" == "normal" ]]; then
    git cherry-pick "$COMMIT" || exit 1
  else
    git cherry-pick -n "$COMMIT" || exit 1
    git restore --staged tools/sync-all-extended.sh 2>/dev/null
    git restore tools/sync-all-extended.sh 2>/dev/null
    echo "Archivos listos para commit en $BRANCH. Presiona ENTER para continuar."
    read
    git commit -m "Cherry-pick $COMMIT desde develop"
  fi
  git push origin "$BRANCH"
}

sync_commit "17.0" "$LAST_COMMIT" "normal"
sync_commit "16.0" "$LAST_COMMIT" "no_manifest"
sync_commit "18.0" "$LAST_COMMIT" "no_manifest_no_dir"

git checkout "$ORIGINAL_BRANCH"
rm -f "$SYNC_STATE"
echo "✅ Sincronización completa. De vuelta en $ORIGINAL_BRANCH"
