# -*- coding: utf-8 -*-
"""
diagrams/stiff.py
Genera polígonos de Stiff y líneas centrales como GeoDataFrames,
y los exporta a Shapefile o GeoPackage.
"""
import numpy as np
import pandas as pd


def calcular_coordenadas(meq_df: pd.DataFrame, feh: float, fev: float) -> pd.DataFrame:
    """
    Calcula las coordenadas cartesianas de cada vértice del polígono Stiff.

    Parámetros
    ----------
    meq_df : DataFrame con columnas Ca_meq, Mg_meq, Na_meq, K_meq,
             HCO3_meq, SO4_meq, Cl_meq, X, Y
    feh    : Factor de escala horizontal (metros por meq/L)
    fev    : Factor de escala vertical (metros entre filas)

    Retorna
    -------
    DataFrame con columnas de coordenadas para cada vértice.
    """
    x = meq_df['X'].values
    y = meq_df['Y'].values

    return pd.DataFrame({
        # Aniones (lado derecho)
        'XHCO3': x + feh * meq_df['HCO3_meq'].values,
        'XSO4':  x + feh * meq_df['SO4_meq'].values,
        'XCl':   x + feh * meq_df['Cl_meq'].values,
        'YHCO3': y - fev,
        'YSO4':  y,
        'YCl':   y + fev,
        # Cationes (lado izquierdo)
        'XCa':   x - feh * meq_df['Ca_meq'].values,
        'XMg':   x - feh * meq_df['Mg_meq'].values,
        'XNaK':  x - feh * (meq_df['Na_meq'].values + meq_df['K_meq'].values),
        'YCa':   y - fev,
        'YMg':   y,
        'YNaK':  y + fev,
        # Línea central
        'XLC':   x,
        'YSLC':  y + fev + feh / 2,
        'YILC':  y - fev - feh / 2,
    })


def crear_poligonos_stiff(meq_df: pd.DataFrame, feh: float, fev: float,
                           crs: str = 'EPSG:4326') -> 'gpd.GeoDataFrame':
    """
    Crea un GeoDataFrame con los polígonos Stiff.
    """
    try:
        import geopandas as gpd
        from shapely.geometry import Polygon
    except ImportError as e:
        raise ImportError('geopandas y shapely son requeridos para crear polígonos Stiff.') from e

    coords = calcular_coordenadas(meq_df, feh, fev)

    def _poligono(i):
        r = coords.iloc[i]
        return Polygon([
            (r['XCa'],   r['YCa']),
            (r['XMg'],   r['YMg']),
            (r['XNaK'],  r['YNaK']),
            (r['XCl'],   r['YCl']),
            (r['XSO4'],  r['YSO4']),
            (r['XHCO3'], r['YHCO3']),
            (r['XCa'],   r['YCa']),   # cerrar polígono
        ])

    poligonos = [_poligono(i) for i in range(len(meq_df))]

    # Atributos: todas las columnas meq + IDs
    attr_cols = [c for c in meq_df.columns if c not in ('X', 'Y')]
    gdf = gpd.GeoDataFrame(
        meq_df[attr_cols].reset_index(drop=True),
        geometry=poligonos,
        crs=crs
    )
    return gdf


def crear_lineas_centrales(meq_df: pd.DataFrame, feh: float, fev: float,
                            crs: str = 'EPSG:4326') -> 'gpd.GeoDataFrame':
    """
    Crea un GeoDataFrame con las líneas centrales verticales de cada diagrama Stiff.
    """
    try:
        import geopandas as gpd
        from shapely.geometry import LineString
    except ImportError as e:
        raise ImportError('geopandas y shapely son requeridos.') from e

    coords = calcular_coordenadas(meq_df, feh, fev)

    lineas = [
        LineString([(coords.iloc[i]['XLC'], coords.iloc[i]['YILC']),
                    (coords.iloc[i]['XLC'], coords.iloc[i]['YSLC'])])
        for i in range(len(meq_df))
    ]

    gdf = gpd.GeoDataFrame(
        meq_df[['IDs']].reset_index(drop=True),
        geometry=lineas,
        crs=crs
    )
    return gdf


def export_to_shapefile(gdf_poly: 'gpd.GeoDataFrame',
                        gdf_lines: 'gpd.GeoDataFrame',
                        output_dir: str) -> tuple:
    """
    Exporta polígonos y líneas como shapefiles separados.
    Retorna (ruta_poligonos, ruta_lineas).
    """
    import os
    poly_path  = os.path.join(output_dir, 'stiff_poligonos.shp')
    lines_path = os.path.join(output_dir, 'stiff_lineas.shp')
    gdf_poly.to_file(poly_path, driver='ESRI Shapefile', encoding='utf-8')
    gdf_lines.to_file(lines_path, driver='ESRI Shapefile', encoding='utf-8')
    return poly_path, lines_path


def export_to_gpkg(gdf_poly: 'gpd.GeoDataFrame',
                   gdf_lines: 'gpd.GeoDataFrame',
                   output_path: str) -> str:
    """
    Exporta polígonos y líneas en un único GeoPackage con dos capas.
    Retorna la ruta del archivo.
    """
    gdf_poly.to_file(output_path,  layer='stiff_poligonos', driver='GPKG')
    gdf_lines.to_file(output_path, layer='stiff_lineas',    driver='GPKG', mode='a')
    return output_path
