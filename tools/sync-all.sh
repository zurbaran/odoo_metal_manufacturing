#!/bin/bash

# Nombre del script: sync-all.sh

ORIGINAL_BRANCH=$(git symbolic-ref --short HEAD)

# PRECAUCIÓN: Abortamos si hay un rebase en curso
if [ -d ".git/rebase-apply" ] || [ -d ".git/rebase-merge" ]; then
  echo "🛑 Rebase detectado en progreso. Termina o aborta el rebase antes de continuar."
  echo "👉 Usa: git rebase --abort  (si querés cancelarlo)"
  exit 1
fi

if [ "$ORIGINAL_BRANCH" != "develop" ]; then
  echo "⚠️ Debes estar en la rama develop para ejecutar este script."
  echo "📍 Estás en: $ORIGINAL_BRANCH"
  exit 1
fi

if git ls-files -u | grep .; then
  echo "❌ Hay conflictos sin resolver en develop. Resuélvelos antes de continuar."
  exit 1
fi

LAST_COMMIT=$(git log -1 --pretty=format:"%H")
IS_PUSHED=$(git branch -r --contains "$LAST_COMMIT" | grep "origin/develop")

if [ -z "$IS_PUSHED" ]; then
  echo "🔄 El último commit aún no ha sido pusheado a origin/develop. Haciendo push..."
  git push origin develop || exit 1
fi

echo "🔍 Último commit en develop: $LAST_COMMIT"

# Cherry-pick en 17.0
echo "🧭 Cambiando a la rama 17.0..."
git checkout 17.0 || exit 1

echo "🎯 Cherry-pick en 17.0..."
git cherry-pick "$LAST_COMMIT" || exit 1

echo "🚀 Push a origin/17.0..."
git push origin 17.0 || exit 1

# Cherry-pick en 16.0
echo "🧭 Cambiando a la rama 16.0..."
git checkout 16.0 || exit 1

echo "🎯 Cherry-pick en 16.0 (sin commit aún)..."
git cherry-pick -n "$LAST_COMMIT"
CHERRYPICK_STATUS=$?

if [ $CHERRYPICK_STATUS -ne 0 ]; then
  echo "⚠️ Conflictos detectados durante cherry-pick. Intentando restaurar __manifest__.py..."

  git restore --staged product_blueprint_manager/__manifest__.py 2>/dev/null
  git restore --staged product_configurator_attribute_price/__manifest__.py 2>/dev/null

  git restore product_blueprint_manager/__manifest__.py 2>/dev/null
  git restore product_configurator_attribute_price/__manifest__.py 2>/dev/null

  if git status | grep -q "no hay nada para confirmar"; then
    echo "✅ Conflictos restaurados. No hay cambios para confirmar."
  else
    echo "✍️ Modificá manualmente los __manifest__.py si lo deseas ahora."
    read -p "⏸️ Presiona ENTER para continuar con el commit..."

    git add .
    if [ -f ".git/CHERRY_PICK_HEAD" ]; then
      git cherry-pick --continue
    else
      echo "ℹ️ No se detectó cherry-pick activo. Realizando commit manual..."
      git commit -m "Cherry-pick manual desde develop sin modificar __manifest__.py"
    fi
  fi
else
  # Restaurar manifests en caso de cherry-pick sin conflicto
  git restore --staged product_blueprint_manager/__manifest__.py
  git restore --staged product_configurator_attribute_price/__manifest__.py

  git restore product_blueprint_manager/__manifest__.py
  git restore product_configurator_attribute_price/__manifest__.py

  echo "✍️ Podés editar manualmente los __manifest__.py si lo deseas ahora."
  read -p "⏸️ Presiona ENTER para continuar con el commit..."

  git commit -m "Cherry-pick $LAST_COMMIT desde develop sin modificar __manifest__.py"
fi

echo "🚀 Push a origin/16.0..."
git push origin 16.0 || exit 1

git checkout "$ORIGINAL_BRANCH"
echo "✅ Proceso completo terminado con éxito. De vuelta en $ORIGINAL_BRANCH"


# Mostrar resumen del commit cherry-pickeado
echo ""
echo "📋 Resumen del commit cherry-pickeado:"
git --no-pager log -1 --stat "$LAST_COMMIT"
