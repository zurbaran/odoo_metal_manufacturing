#!/bin/bash
# Sincronización de commits entre ramas estilo OCA usando oca-port
# Uso: ./tools/oca-sync.sh <from_branch> <to_branch> [ruta]

set -e

if [ $# -lt 2 ]; then
    echo "Uso: $0 <from_branch> <to_branch> [ruta]"
    exit 1
fi

FROM_BRANCH="$1"
TO_BRANCH="$2"
TARGET_PATH="${3:-.}"

echo "🔍 Comprobando ramas locales y remotas..."
git fetch --all --prune

if ! git show-ref --verify --quiet "refs/heads/$FROM_BRANCH"; then
    echo "❌ La rama local $FROM_BRANCH no existe."
    exit 1
fi
if ! git show-ref --verify --quiet "refs/heads/$TO_BRANCH"; then
    echo "❌ La rama local $TO_BRANCH no existe."
    exit 1
fi

if ! command -v oca-port &> /dev/null; then
    echo "❌ No se encontró 'oca-port'. Instálalo con: pip install oca-port"
    exit 1
fi

echo "🔄 Mostrando commits en $FROM_BRANCH que no están en $TO_BRANCH..."
oca-port "origin/$FROM_BRANCH" "origin/$TO_BRANCH" "$TARGET_PATH"

echo
read -p "¿Quieres aplicar estos commits de $FROM_BRANCH a $TO_BRANCH? [s/N]: " CONFIRM
if [[ "$CONFIRM" != "s" && "$CONFIRM" != "S" ]]; then
    echo "⏭  Operación cancelada."
    exit 0
fi

echo "🚀 Aplicando commits con oca-port..."
oca-port "origin/$FROM_BRANCH" "origin/$TO_BRANCH" "$TARGET_PATH" --apply

echo
echo "✅ Commits aplicados. Ejecutando pre-commit..."
pre-commit run --all-files || true

echo
echo "📌 Cambios listos en la rama $TO_BRANCH. Haz un push manual si es necesario."
