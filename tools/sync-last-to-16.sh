#!/bin/bash

# Obtener el último commit de develop
LAST_COMMIT=$(git log develop -1 --pretty=format:"%H")

echo ">> Último commit en develop: $LAST_COMMIT"

git checkout 16.0 || exit 1
git cherry-pick "$LAST_COMMIT" || exit 1

echo ">> Haciendo push a origin/16.0"
git push origin 16.0
