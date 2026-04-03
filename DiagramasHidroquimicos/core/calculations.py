# -*- coding: utf-8 -*-
"""
core/calculations.py
Funciones de conversión hidroquímica:
  - mg/L → meq/L
  - mg/L → mmol/L
  - Normalización a porcentaje (para diagrama de Piper)
  - Ratio Cl/(Cl+HCO3) (para diagrama de Gibbs)
"""
import pandas as pd
import numpy as np

# -----------------------------------------------------------------------
# Pesos moleculares y valencia → factor de conversión  mg/L → meq/L
# factor = peso_molecular / valencia
# -----------------------------------------------------------------------
MEQ_FACTORS = {
    'HCO3': 61.01684 / 1,
    'CO3':  60.0089  / 2,
    'SO4':  96.0626  / 2,
    'Cl':   35.453   / 1,
    'Ca':   40.078   / 2,
    'Mg':   24.305   / 2,
    'Na':   22.9898  / 1,
    'K':    39.1     / 1,
}

# Factor mg/L → mmol/L  (solo peso molecular)
MMOL_FACTORS = {
    'HCO3': 61.01684,
    'CO3':  60.0089,
    'SO4':  96.0626,
    'Cl':   35.453,
    'Ca':   40.078,
    'Mg':   24.305,
    'Na':   22.9898,
    'K':    39.1,
}

IONS = list(MEQ_FACTORS.keys())
CATIONS = ['Ca', 'Mg', 'Na', 'K']
ANIONS  = ['Cl', 'SO4', 'HCO3', 'CO3']


def convert_to_meq(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega columnas '<ion>_meq' al DataFrame.
    Espera columnas con nombres exactos: Ca, Mg, Na, K, HCO3, CO3, SO4, Cl (en mg/L).
    """
    df = df.copy()
    for ion, factor in MEQ_FACTORS.items():
        col = ion  # columna de origen en mg/L
        if col in df.columns:
            df[f'{ion}_meq'] = df[col] / factor
        else:
            df[f'{ion}_meq'] = np.nan
    return df


def convert_to_mmol(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega columnas '<ion>_mmol' al DataFrame.
    """
    df = df.copy()
    for ion, factor in MMOL_FACTORS.items():
        col = ion
        if col in df.columns:
            df[f'{ion}_mmol'] = df[col] / factor
        else:
            df[f'{ion}_mmol'] = np.nan
    return df


def build_meq_dataframe(df_enriched: pd.DataFrame, id_col: str,
                        x_col: str = None, y_col: str = None) -> pd.DataFrame:
    """
    Construye un DataFrame limpio solo con meq/L más las columnas auxiliares.
    """
    data = {ion: df_enriched[f'{ion}_meq'] for ion in IONS}
    data['IDs'] = df_enriched[id_col]
    if x_col and x_col in df_enriched.columns:
        data['X'] = df_enriched[x_col]
    if y_col and y_col in df_enriched.columns:
        data['Y'] = df_enriched[y_col]
    return pd.DataFrame(data)


def build_mmol_dataframe(df_enriched: pd.DataFrame, id_col: str,
                         tds_col: str = None) -> pd.DataFrame:
    """
    Construye un DataFrame limpio solo con mmol/L más las columnas auxiliares.
    """
    data = {ion: df_enriched[f'{ion}_mmol'] for ion in IONS}
    data['IDs'] = df_enriched[id_col]
    if tds_col and tds_col in df_enriched.columns:
        data['Tds'] = df_enriched[tds_col]
    return pd.DataFrame(data)


def to_percent(meq_df: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte cationes y aniones a porcentaje del total de su grupo.
    Agrega columnas 'Alcalinos' (Na+K) y 'BicarbonatoMasCarbonato' (HCO3+CO3).
    """
    df = meq_df.copy()
    df[CATIONS] = df[CATIONS].div(df[CATIONS].sum(axis=1), axis=0) * 100
    df[ANIONS]  = df[ANIONS].div(df[ANIONS].sum(axis=1), axis=0)  * 100
    df['Alcalinos']               = df['Na'] + df['K']
    df['BicarbonatoMasCarbonato'] = df['HCO3'] + df['CO3']
    return df


def calculate_cl_ratio(mmol_df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega la columna Cl_Ratio = Cl / (Cl + HCO3) para el diagrama de Gibbs.
    """
    df = mmol_df.copy()
    df['Cl_Ratio'] = df['Cl'] / (df['Cl'] + df['HCO3'])
    return df
