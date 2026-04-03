# -*- coding: utf-8 -*-
"""
diagrams/gibbs.py
Diagrama de Gibbs (Plotly)
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go


# ---------------------------------------------------------------------------
# FUNCIONES AUXILIARES
# ---------------------------------------------------------------------------

def log_line(x0, x1, y0, y1, n=100):
    """
    Genera una línea en espacio logarítmico (correcto para Gibbs)
    """
    x = np.linspace(x0, x1, n)
    y = 10 ** np.linspace(np.log10(y0), np.log10(y1), n)
    return x, y


# ---------------------------------------------------------------------------
# FIGURA PRINCIPAL
# ---------------------------------------------------------------------------

def create_gibbs_plotly(milimol_df: pd.DataFrame) -> go.Figure:

    # ---------------- VALIDACIONES ----------------
    if 'Cl_Ratio' not in milimol_df.columns:
        raise ValueError("Falta 'Cl_Ratio'")
    if 'Tds' not in milimol_df.columns:
        raise ValueError("Falta 'Tds'")

    colors = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
    ]

    fig = go.Figure()

    # ---------------- PUNTOS ----------------
    ids = milimol_df['IDs'].unique()

    for i, well_id in enumerate(ids):
        sub = milimol_df[milimol_df['IDs'] == well_id]

        fig.add_trace(go.Scatter(
            x=sub['Cl_Ratio'],
            y=sub['Tds'],
            mode='markers+text',
            marker=dict(size=10, color=colors[i % len(colors)]),
            text=sub['IDs'],
            textposition='top right',
            textfont=dict(size=10),
            name=str(well_id),
            hovertemplate=(
                f'<b>{well_id}</b><br>'
                'Cl/(Cl+HCO₃): %{x:.3f}<br>'
                'TDS: %{y:.1f} mg/L<extra></extra>'
            ),
        ))

    # ---------------- LÍNEAS GIBBS CORRECTAS ----------------
    ref_lines = [
        log_line(0.0, 0.5, 20, 1),
        log_line(0.0, 0.5, 500, 10000),
        log_line(0.22, 0.93, 180, 10000),
        log_line(0.22, 1.0, 180, 2),
    ]

    for x, y in ref_lines:
        fig.add_trace(go.Scatter(
            x=x, y=y,
            mode='lines',
            line=dict(color='red', width=2, dash='dash'),
            showlegend=False,
            hoverinfo='skip'
        ))

    # ---------------- ANOTACIONES CIENTÍFICAS ----------------
    annotations = [
        dict(x=0.85, y=3, text='Lluvia'),
        dict(x=0.35, y=8, text='Mineralización'),
        dict(x=0.12, y=150, text='Dominio de la<br>Geología'),
        dict(x=0.45, y=2000, text='Mezcla'),
        dict(x=0.75, y=9000, text='Agua de mar'),
        dict(x=0.82, y=120, text='Contaminación<br>por cloruros'),
    ]

    for ann in annotations:
        ann.update(dict(
            showarrow=False,
            font=dict(size=16, color='blue', family='Arial Black'),
            xref='paper',
            yref='paper',
            xanchor='center',
            yanchor='middle'
        ))

    # ---------------- LAYOUT PROFESIONAL ----------------
    fig.update_layout(
        title=dict(
            text='Diagrama de Gibbs',
            font=dict(size=24),
            x=0.5,
            xanchor='center'
        ),

        xaxis=dict(
            title='Cl / (Cl + HCO₃) (mmol/L)',
            range=[0, 1],
            showgrid=True,
            gridcolor='lightgrey'
        ),

        yaxis=dict(
            title='Sólidos totales disueltos (mg/L)',
            type='log',
            range=[0, 4],
            showgrid=True,
            gridcolor='lightgrey'
        ),

        annotations=annotations,

        legend=dict(
            title='Puntos',
            x=1.02,
            y=1,
            xanchor='left',
            yanchor='top',
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='black',
            borderwidth=1
        ),

        plot_bgcolor='white',
        paper_bgcolor='white',

        # 🔥 CLAVE: tamaño adecuado para análisis
        autosize=True,
        width=1200,
        height=800,

        margin=dict(l=80, r=220, t=80, b=80)
    )

    return fig


# ---------------------------------------------------------------------------
# EXPORTACIÓN HTML (RESPONSIVO)
# ---------------------------------------------------------------------------

def export_gibbs_html(fig: go.Figure, output_path: str) -> str:
    fig.write_html(
        output_path,
        include_plotlyjs='cdn',
        full_html=True,
        config={'responsive': True}
    )
    return output_path
