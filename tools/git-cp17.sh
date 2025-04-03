#!/bin/bash

COMMIT="$1"

if [ -z "$COMMIT" ]; then
  echo "Uso: ./tools/git-cp17.sh <commit_hash>"
  exit 1
fi

echo ">> Cherry-pickeando $COMMIT desde develop a 17.0"
git checkout 17.0 &&
git cherry-pick "$COMMIT"
