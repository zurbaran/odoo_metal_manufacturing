#!/bin/bash

echo "Iniciando sincronización del último commit de develop a 16.0 y 17.0..."

# Ejecutar la sincronización a 16.0
./tools/sync-last-to-16.sh
if [ $? -ne 0 ]; then
  echo "Error durante la sincronización a 16.0. Abortando..."
  exit 1
fi

# Ejecutar la sincronización a 17.0
./tools/sync-last-to-17.sh
if [ $? -ne 0 ]; then
  echo "Error durante la sincronización a 17.0. Abortando..."
  exit 1
fi

echo "Sincronización completada exitosamente en ambas ramas."
