#!/bin/bash

# Guardar la rama original
ORIGINAL_BRANCH=$(git symbolic-ref --short HEAD)

# Obtener el último commit de develop
LAST_COMMIT=$(git log develop -1 --pretty=format:"%H")

echo ">> Último commit en develop: $LAST_COMMIT"

git checkout 17.0 || exit 1
git cherry-pick "$LAST_COMMIT" || exit 1

echo ">> Haciendo push a origin/17.0"
git push origin 17.0

# Volver a la rama original
git checkout "$ORIGINAL_BRANCH"
echo "✅ Sincronización a 17.0 completada. De vuelta en $ORIGINAL_BRANCH"
