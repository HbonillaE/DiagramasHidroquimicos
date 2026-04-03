# -*- coding: utf-8 -*-
"""Instala dependencias Python faltantes en el entorno de QGIS."""
import subprocess
import sys


def install_dependencies(packages: list) -> tuple:
    """
    Instala una lista de paquetes pip en el intérprete Python de QGIS.
    Retorna (True, '') si todo salió bien, o (False, mensaje_error) si falla.
    """
    errors = []
    for pkg in packages:
        try:
            subprocess.check_call(
                [sys.executable, '-m', 'pip', 'install', '--user', pkg],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )
        except subprocess.CalledProcessError as e:
            errors.append(f"{pkg}: {e.stderr.decode('utf-8', errors='replace')}")
    if errors:
        return False, '\n'.join(errors)
    return True, ''
