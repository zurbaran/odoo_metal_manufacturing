#!/bin/bash

COMMIT="$1"

if [ -z "$COMMIT" ]; then
  echo "Uso: ./tools/git-cp16.sh <commit_hash>"
  exit 1
fi

echo ">> Cherry-pickeando $COMMIT desde develop a 16.0"
git checkout 16.0 &&
git cherry-pick "$COMMIT"
