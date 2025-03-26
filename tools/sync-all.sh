#!/bin/bash

# Guardar la rama actual para volver después
ORIGINAL_BRANCH=$(git symbolic-ref --short HEAD)

echo "🔄 Iniciando sincronización del último commit de develop a 16.0 y 17.0..."

# Ejecutar la sincronización a 16.0
./tools/sync-last-to-16.sh
if [ $? -ne 0 ]; then
  echo "❌ Error durante la sincronización a 16.0. Abortando..."
  exit 1
fi

# Ejecutar la sincronización a 17.0
./tools/sync-last-to-17.sh
if [ $? -ne 0 ]; then
  echo "❌ Error durante la sincronización a 17.0. Abortando..."
  exit 1
fi

# Volver a la rama original
git checkout "$ORIGINAL_BRANCH"

echo "✅ Sincronización completada. De vuelta en la rama: $ORIGINAL_BRANCH"
