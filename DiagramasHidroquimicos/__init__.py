# -*- coding: utf-8 -*-
"""
DiagramasHidroquimicos - Plugin de QGIS 3.44
Punto de entrada requerido por QGIS Plugin Manager.
"""


def classFactory(iface):
    """
    Función requerida por QGIS para inicializar el plugin.
    :param iface: QgsInterface — interfaz de QGIS
    """
    from .plugin import DiagramasHidroquimicosPlugin
    return DiagramasHidroquimicosPlugin(iface)
