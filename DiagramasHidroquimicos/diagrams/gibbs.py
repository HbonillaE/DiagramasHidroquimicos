# -*- coding: utf-8 -*-
"""
diagrams/gibbs.py
Diagrama de Gibbs – Plotly interactivo (HTML) y exportación PNG con matplotlib.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go


# ---------------------------------------------------------------------------
# FUNCIONES AUXILIARES
# ---------------------------------------------------------------------------

def log_line(x0, x1, y0, y1, n=100):
    """Genera una línea en espacio logarítmico (correcto para Gibbs)."""
    x = np.linspace(x0, x1, n)
    y = 10 ** np.linspace(np.log10(y0), np.log10(y1), n)
    return x, y


# ---------------------------------------------------------------------------
# FIGURA PLOTLY
# ---------------------------------------------------------------------------

GIBBS_COLORS = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
]


def create_gibbs_plotly(milimol_df: pd.DataFrame) -> go.Figure:

    if 'Cl_Ratio' not in milimol_df.columns:
        raise ValueError("Falta 'Cl_Ratio'")
    if 'Tds' not in milimol_df.columns:
        raise ValueError("Falta 'Tds'")

    fig = go.Figure()

    # Puntos de datos
    ids = milimol_df['IDs'].unique()
    for i, well_id in enumerate(ids):
        sub = milimol_df[milimol_df['IDs'] == well_id]
        fig.add_trace(go.Scatter(
            x=sub['Cl_Ratio'],
            y=sub['Tds'],
            mode='markers+text',
            marker=dict(size=10, color=GIBBS_COLORS[i % len(GIBBS_COLORS)],
                        line=dict(width=0.8, color='white')),
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

    # Líneas de referencia de Gibbs
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
            showlegend=False, hoverinfo='skip',
        ))

    # Anotaciones de dominios hidrogeoquímicos
    annotations = [
        dict(x=0.85, y=3,    text='Lluvia'),
        dict(x=0.35, y=8,    text='Mineralización'),
        dict(x=0.12, y=150,  text='Dominio de la<br>Geología'),
        dict(x=0.45, y=2000, text='Mezcla'),
        dict(x=0.75, y=9000, text='Agua de mar'),
        dict(x=0.82, y=120,  text='Contaminación<br>por cloruros'),
    ]
    for ann in annotations:
        ann.update(dict(
            showarrow=False,
            font=dict(size=16, color='blue', family='Arial Black'),
            xref='paper', yref='paper',
            xanchor='center', yanchor='middle',
        ))

    fig.update_layout(
        title=dict(text='Diagrama de Gibbs', font=dict(size=24), x=0.5, xanchor='center'),
        xaxis=dict(
            title='Cl / (Cl + HCO₃) (mmol/L)',
            range=[0, 1],
            showgrid=True, gridcolor='lightgrey',
        ),
        yaxis=dict(
            title='Sólidos totales disueltos (mg/L)',
            type='log', range=[0, 4],
            showgrid=True, gridcolor='lightgrey',
        ),
        annotations=annotations,
        legend=dict(
            title='Puntos', x=1.02, y=1,
            xanchor='left', yanchor='top',
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='black', borderwidth=1,
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        autosize=True,
        margin=dict(l=80, r=220, t=80, b=80),
    )
    return fig


# ---------------------------------------------------------------------------
# EXPORTACIÓN HTML – ocupa toda la página
# ---------------------------------------------------------------------------

def export_gibbs_html(fig: go.Figure, output_path: str) -> str:
    """Exporta la figura Plotly a HTML que ocupa 100 % del viewport."""
    html_str = fig.to_html(
        include_plotlyjs='cdn',
        full_html=True,
        config={'responsive': True, 'displayModeBar': True},
        div_id='gibbs-plot',
    )

    full_page_css = """<style>
  html, body {
    margin: 0; padding: 0;
    width: 100%; height: 100%;
    overflow: hidden;
    background: #ffffff;
  }
  #gibbs-plot {
    width: 100vw !important;
    height: 100vh !important;
  }
</style>"""
    html_str = html_str.replace('</head>', full_page_css + '\n</head>')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_str)
    return output_path


# ---------------------------------------------------------------------------
# FIGURA MATPLOTLIB (para exportar PNG)
# ---------------------------------------------------------------------------

def create_gibbs_matplotlib(milimol_df: pd.DataFrame):
    """
    Construye el diagrama de Gibbs con matplotlib.
    Retorna un objeto matplotlib.figure.Figure.
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    if 'Cl_Ratio' not in milimol_df.columns:
        raise ValueError("Falta 'Cl_Ratio'")
    if 'Tds' not in milimol_df.columns:
        raise ValueError("Falta 'Tds'")

    fig, ax = plt.subplots(figsize=(12, 9))
    ax.set_yscale('log')

    # Líneas de referencia
    ref_lines = [
        log_line(0.0, 0.5, 20, 1),
        log_line(0.0, 0.5, 500, 10000),
        log_line(0.22, 0.93, 180, 10000),
        log_line(0.22, 1.0, 180, 2),
    ]
    for x, y in ref_lines:
        ax.plot(x, y, color='red', linewidth=2, linestyle='--', zorder=2)

    # Puntos de datos
    ids = milimol_df['IDs'].unique()
    for i, well_id in enumerate(ids):
        sub = milimol_df[milimol_df['IDs'] == well_id]
        ax.scatter(sub['Cl_Ratio'], sub['Tds'],
                   color=GIBBS_COLORS[i % len(GIBBS_COLORS)],
                   s=70, zorder=5, label=str(well_id),
                   edgecolors='white', linewidths=0.6)
        for _, row in sub.iterrows():
            ax.annotate(str(well_id),
                        xy=(row['Cl_Ratio'], row['Tds']),
                        xytext=(4, 4), textcoords='offset points',
                        fontsize=8, color='#333333')

    # Anotaciones de dominios
    domain_labels = [
        (0.85, 3,    'Lluvia'),
        (0.35, 8,    'Mineralización'),
        (0.12, 150,  'Dominio\nGeología'),
        (0.45, 2000, 'Mezcla'),
        (0.75, 9000, 'Agua de mar'),
        (0.82, 120,  'Contaminación\npor cloruros'),
    ]
    for xd, yd, txt in domain_labels:
        ax.text(xd, yd, txt, fontsize=11, color='blue',
                fontweight='bold', ha='center', va='center',
                alpha=0.75, zorder=3)

    ax.set_xlim(0, 1)
    ax.set_ylim(1, 10000)
    ax.set_xlabel('Cl / (Cl + HCO₃) (mmol/L)', fontsize=13)
    ax.set_ylabel('Sólidos totales disueltos (mg/L)', fontsize=13)
    ax.set_title('Diagrama de Gibbs', fontsize=16, fontweight='bold', pad=12)
    ax.grid(True, which='both', color='lightgrey', linewidth=0.5)
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')

    ax.legend(title='Muestras', bbox_to_anchor=(1.02, 1),
              loc='upper left', framealpha=0.9,
              fontsize=9, title_fontsize=10)

    plt.tight_layout()
    return fig


def export_gibbs_png(milimol_df: pd.DataFrame, output_path: str, dpi: int = 150) -> str:
    """Exporta el diagrama de Gibbs como imagen PNG usando matplotlib."""
    import matplotlib.pyplot as plt
    fig = create_gibbs_matplotlib(milimol_df)
    fig.savefig(output_path, dpi=dpi, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig)
    return output_path
