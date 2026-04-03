# -*- coding: utf-8 -*-
"""
DiagramasHidroquimicos – Plugin principal de QGIS 3.44
Clase que registra el plugin en la interfaz de QGIS.
"""
import os
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QCoreApplication


class DiagramasHidroquimicosPlugin:
    """Plugin principal."""

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.action = None
        self.dialog = None

    # ------------------------------------------------------------------
    # Instalar dependencias si no están disponibles
    # ------------------------------------------------------------------
    def _check_dependencies(self):
        missing = []
        for pkg in ['pandas', 'numpy', 'geopandas', 'shapely', 'plotly', 'openpyxl']:
            try:
                __import__(pkg)
            except ImportError:
                missing.append(pkg)
        if missing:
            reply = QMessageBox.question(
                self.iface.mainWindow(),
                'Dependencias faltantes',
                f'El plugin necesita instalar: {", ".join(missing)}.\n'
                '¿Desea instalarlas ahora? (requiere conexión a internet)',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                from .utils.install_deps import install_dependencies
                ok, msg = install_dependencies(missing)
                if not ok:
                    QMessageBox.critical(
                        self.iface.mainWindow(),
                        'Error de instalación',
                        f'No se pudieron instalar las dependencias:\n{msg}'
                    )
                    return False
        return True

    # ------------------------------------------------------------------
    # Métodos del ciclo de vida del plugin
    # ------------------------------------------------------------------
    def initGui(self):
        """Crea la acción/botón en la barra de herramientas de QGIS."""
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        self.action = QAction(
            QIcon(icon_path),
            'Diagramas Hidroquímicos',
            self.iface.mainWindow()
        )
        self.action.setStatusTip('Genera diagramas de Piper, Gibbs y Stiff')
        self.action.setToolTip('Diagramas Hidroquímicos')
        self.action.triggered.connect(self.run)

        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu('&Diagramas Hidroquímicos', self.action)

    def unload(self):
        """Elimina el plugin de la interfaz de QGIS."""
        self.iface.removePluginMenu('&Diagramas Hidroquímicos', self.action)
        self.iface.removeToolBarIcon(self.action)
        if self.action:
            self.action.deleteLater()

    def run(self):
        """Abre el diálogo principal del plugin."""
        if not self._check_dependencies():
            return
        from .dialog import DiagramasDialog
        if self.dialog is None or not self.dialog.isVisible():
            self.dialog = DiagramasDialog(self.iface, self.iface.mainWindow())
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()
