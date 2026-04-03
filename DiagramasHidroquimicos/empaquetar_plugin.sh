#!/usr/bin/env bash
# =============================================================================
# empaquetar_plugin.sh
# Script para empaquetar el plugin DiagramasHidroquimicos listo para QGIS.
#
# uso:
#   bash empaquetar_plugin.sh
#
# Requiere: pyrcc5 (del paquete pyqt5-dev-tools) para compilar resources.qrc
# =============================================================================

set -e

PLUGIN_NAME="DiagramasHidroquimicos"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="${SCRIPT_DIR}"
PARENT_DIR="$(dirname "${PLUGIN_DIR}")"
ZIP_PATH="${PARENT_DIR}/${PLUGIN_NAME}.zip"

echo "=============================================="
echo " Empacando plugin: ${PLUGIN_NAME}"
echo " Directorio fuente: ${PLUGIN_DIR}"
echo "=============================================="

# 1. Compilar recursos Qt (icon.png embebido)
if command -v pyrcc5 &>/dev/null; then
    echo "[1/4] Compilando resources.qrc → resources.py ..."
    cd "${PLUGIN_DIR}"
    pyrcc5 resources.qrc -o resources.py
    echo "      ✅ resources.py generado."
else
    echo "[1/4] ⚠️  pyrcc5 no encontrado. Omitiendo compilación de recursos."
    echo "      El ícono se cargará directamente desde icon.png."
fi

# 2. Limpiar archivos temporales
echo "[2/4] Limpiando archivos temporales ..."
find "${PLUGIN_DIR}" -name "*.pyc" -delete
find "${PLUGIN_DIR}" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "${PLUGIN_DIR}" -name "*.py~" -delete 2>/dev/null || true
echo "      ✅ Limpieza completada."

# 3. Crear el ZIP
echo "[3/4] Creando ZIP: ${ZIP_PATH} ..."
cd "${PARENT_DIR}"
zip -r "${ZIP_PATH}" "${PLUGIN_NAME}/" \
    --exclude "*/.git/*" \
    --exclude "*/__pycache__/*" \
    --exclude "*.pyc" \
    --exclude "*.py~" \
    --exclude "*/empaquetar_plugin.sh" \
    --exclude "*.ipynb"

echo "      ✅ ZIP creado en: ${ZIP_PATH}"

# 4. Verificar contenido mínimo
echo "[4/4] Verificando contenido esencial del ZIP ..."
REQUIRED_FILES=("metadata.txt" "__init__.py" "plugin.py" "dialog.py" "icon.png")
ALL_OK=true
for f in "${REQUIRED_FILES[@]}"; do
    if unzip -l "${ZIP_PATH}" | grep -q "${PLUGIN_NAME}/${f}"; then
        echo "      ✅ ${f}"
    else
        echo "      ❌ FALTA: ${f}"
        ALL_OK=false
    fi
done

echo "=============================================="
if $ALL_OK; then
    echo " 🎉 Plugin empacado correctamente."
    echo " Archivo: ${ZIP_PATH}"
    echo ""
    echo " Para instalar en QGIS:"
    echo "   Plugins → Administrar e Instalar → Instalar desde ZIP"
    echo ""
    echo " Para subir al repositorio de QGIS:"
    echo "   1. Regístrate en: https://plugins.qgis.org/accounts/register/"
    echo "   2. Sube el ZIP en: https://plugins.qgis.org/plugins/add/"
else
    echo " ⚠️  Verificación fallida. Revisa los archivos faltantes."
fi
echo "=============================================="
