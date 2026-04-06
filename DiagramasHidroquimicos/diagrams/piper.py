# -*- coding: utf-8 -*-
"""
diagrams/piper.py
Genera el Diagrama de Piper como figura Plotly interactiva (HTML) o imagen PNG.
Basado en: Appelo & Postma (2005), Bonilla (2025).
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go


# ---------------------------------------------------------------------------
# Transformación de datos
# ---------------------------------------------------------------------------

def transform_piper_data(data_percent: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte los porcentajes de cationes/aniones a coordenadas cartesianas
    para el diagrama de Piper (tres zonas: triángulo izq., triángulo der., diamante).
    """
    Ca  = np.array(data_percent['Ca'])
    Mg  = np.array(data_percent['Mg'])
    Cl  = np.array(data_percent['Cl'])
    SO4 = np.array(data_percent['SO4'])
    name = np.array(data_percent['IDs'])

    # Triángulo izquierdo (cationes)
    y1 = Mg * 0.86603
    x1 = 100 * (1 - (Ca / 100) - (Mg / 200))

    # Triángulo derecho (aniones)
    y2 = SO4 * 0.86603
    x2 = 120 + Cl + 0.5 * SO4

    # Proyección en el diamante
    def _new_point(x1v, x2v, y1v, y2v, grad=1.73206):
        b1 = y1v - grad * x1v
        b2 = y2v + grad * x2v
        M  = np.array([[grad, -1], [-grad, -1]])
        b  = np.array([b1, b2])
        t  = -np.linalg.solve(M, b)
        return t[0], t[1]

    npoints = np.array([_new_point(x1[i], x2[i], y1[i], y2[i]) for i in range(len(x1))])

    obs   = np.tile(name, 3)
    x_all = np.concatenate([x1, x2, npoints[:, 0]])
    y_all = np.concatenate([y1, y2, npoints[:, 1]])

    return pd.DataFrame({'observation': obs, 'x': x_all, 'y': y_all})


# ---------------------------------------------------------------------------
# Líneas de contorno y grillas para Plotly
# ---------------------------------------------------------------------------

def _triangle_lines() -> list:
    """Trazas Plotly para bordes y grillas del diagrama de Piper."""
    traces = []

    def line(xs, ys, dash='solid', color='black', width=1.5):
        return go.Scatter(x=xs, y=ys, mode='lines',
                          line=dict(color=color, width=width, dash=dash),
                          showlegend=False, hoverinfo='skip')

    # Triángulo izquierdo (cationes)
    traces.append(line([0, 100, 50, 0], [0, 0, 86.603, 0]))
    # Triángulo derecho (aniones)
    traces.append(line([120, 220, 170, 120], [0, 0, 86.603, 0]))

    # Diamante: cuatro lados individualmente
    traces.append(line([110, 60],  [190.5266, 103.9236]))
    traces.append(line([60,  110], [103.9236, 17.3206]))
    traces.append(line([110, 160], [17.3206,  103.9236]))
    traces.append(line([160, 110], [103.9236, 190.5266]))

    # Grillas internas de triángulos (20 %, 40 %, 60 %, 80 %)
    grid_style = dict(dash='dot', color='grey', width=0.5)

    for pct, y in zip([20, 40, 60, 80], [17.3206, 34.6412, 51.9618, 69.2824]):
        traces.append(go.Scatter(x=[100 - pct/2, 100 - pct], y=[y, 0],
                                 mode='lines', line=grid_style,
                                 showlegend=False, hoverinfo='skip'))
        traces.append(go.Scatter(x=[pct/2, pct], y=[y, 0],
                                 mode='lines', line=grid_style,
                                 showlegend=False, hoverinfo='skip'))
        traces.append(go.Scatter(x=[120 + 100 - pct/2, 120 + 100 - pct], y=[y, 0],
                                 mode='lines', line=grid_style,
                                 showlegend=False, hoverinfo='skip'))
        traces.append(go.Scatter(x=[120 + pct/2, 120 + pct], y=[y, 0],
                                 mode='lines', line=grid_style,
                                 showlegend=False, hoverinfo='skip'))

    for pct in [20, 40, 60, 80]:
        traces.append(go.Scatter(x=[pct, pct + (100 - pct) / 2],
                                 y=[0, (100 - pct) * 0.86603],
                                 mode='lines', line=grid_style,
                                 showlegend=False, hoverinfo='skip'))

    # ---------------------------------------------------------------
    # Grillas diagonales DENTRO DEL DIAMANTE
    # Vértices: Bottom(110,17.3206) Left(60,103.9236)
    #           Top(110,190.5266)   Right(160,103.9236)
    # Para cada t ∈ {0.2, 0.4, 0.6, 0.8}:
    #   - slope ≈ −1.732: desde lado Bottom→Right hasta lado Left→Top
    #   - slope ≈ +1.732: desde lado Bottom→Left hasta lado Right→Top
    # ---------------------------------------------------------------
    for t in [0.2, 0.4, 0.6, 0.8]:
        # slope −1.732 (paralela al lado izquierdo del diamante)
        rx  = 110 + t * 50;   ry  = 17.3206 + t * 86.603   # en Bottom→Right
        lxt = 60  + t * 50;   lyt = 103.9236 + t * 86.603  # en Left→Top
        traces.append(go.Scatter(x=[rx, lxt], y=[ry, lyt],
                                 mode='lines', line=grid_style,
                                 showlegend=False, hoverinfo='skip'))

        # slope +1.732 (paralela al lado derecho del diamante)
        lx  = 110 - t * 50;   ly  = 17.3206 + t * 86.603   # en Bottom→Left
        rxt = 160 - t * 50;   ryt = 103.9236 + t * 86.603  # en Right→Top
        traces.append(go.Scatter(x=[lx, rxt], y=[ly, ryt],
                                 mode='lines', line=grid_style,
                                 showlegend=False, hoverinfo='skip'))

    return traces


def _piper_annotations() -> list:
    """Anotaciones de texto para etiquetas de los ejes y valores numéricos."""
    # Etiquetas principales
    anns = [
        dict(x=17,  y=50,  text='Mg²⁺',           showarrow=False, font=dict(size=11)),
        dict(x=82,  y=50,  text='Na⁺ + K⁺',        showarrow=False, font=dict(size=11)),
        dict(x=50,  y=-12, text='Ca²⁺',             showarrow=False, font=dict(size=11)),
        dict(x=170, y=-12, text='Cl⁻',              showarrow=False, font=dict(size=11)),
        dict(x=213, y=48,  text='SO₄²⁻',            showarrow=False, font=dict(size=11)),
        dict(x=130, y=52,  text='HCO₃⁻ + CO₃²⁻',   showarrow=False, font=dict(size=11)),
        dict(x=72,  y=152, text='SO₄²⁻ + Cl⁻',     showarrow=False, font=dict(size=10)),
        dict(x=148, y=152, text='Ca²⁺ + Mg²⁺',     showarrow=False, font=dict(size=10)),
    ]

    # Valores numéricos (0, 20, 40, 60, 80, 100)
    num_font = dict(size=8, color='grey')

    for pct in [20, 40, 60, 80]:
        # --- Cationes ---
        # Base Ca (derecha a izquierda: 0 a 100)
        anns.append(dict(x=100-pct, y=-4, text=str(pct), showarrow=False, font=num_font))
        # Izquierda Mg (abajo a arriba: 0 a 100)
        anns.append(dict(x=pct/2 - 4.5, y=pct*0.866, text=str(pct), showarrow=False, font=num_font))
        # Derecha Na+K (abajo a arriba: 0 a 100)
        anns.append(dict(x=100 - pct/2 + 4.5, y=pct*0.866, text=str(pct), showarrow=False, font=num_font))

        # --- Aniones ---
        # Base Cl (izquierda a derecha: 0 a 100)
        anns.append(dict(x=120+pct, y=-4, text=str(pct), showarrow=False, font=num_font))
        # Izquierda HCO3 (arriba a abajo: 0 a 100)
        anns.append(dict(x=120 + pct/2 - 4.5, y=pct*0.866, text=str(100-pct), showarrow=False, font=num_font))
        # Derecha SO4 (abajo a arriba: 0 a 100)
        anns.append(dict(x=220 - pct/2 + 4.5, y=pct*0.866, text=str(pct), showarrow=False, font=num_font))

    return anns


# ---------------------------------------------------------------------------
# Figura Plotly
# ---------------------------------------------------------------------------

PIPER_COLORS = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
]


def create_piper_plotly(piper_data: pd.DataFrame) -> go.Figure:
    """Construye la figura Plotly del diagrama de Piper."""
    fig = go.Figure()

    for trace in _triangle_lines():
        fig.add_trace(trace)

    observations = piper_data['observation'].unique()
    for i, obs in enumerate(observations):
        subset = piper_data[piper_data['observation'] == obs]
        fig.add_trace(go.Scatter(
            x=subset['x'], y=subset['y'],
            mode='markers',
            marker=dict(size=10, color=PIPER_COLORS[i % len(PIPER_COLORS)],
                        line=dict(width=0.8, color='white')),
            name=str(obs),
            hovertemplate=f'<b>{obs}</b><br>x: %{{x:.1f}}<br>y: %{{y:.1f}}<extra></extra>',
        ))

    fig.update_layout(
        title=dict(text='Diagrama de Piper', font=dict(size=18), x=0.5),
        # Rangos amplios para que el diamante completo sea visible
        xaxis=dict(visible=False, range=[-18, 245], fixedrange=True),
        yaxis=dict(visible=False, scaleanchor='x', scaleratio=1,
                   range=[-22, 215], fixedrange=True),
        annotations=_piper_annotations(),
        legend=dict(title='Muestras', bgcolor='rgba(255,255,255,0.8)',
                    bordercolor='black', borderwidth=1),
        plot_bgcolor='white',
        paper_bgcolor='white',
        autosize=True,
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


def export_piper_html(fig: go.Figure, output_path: str) -> str:
    """Exporta la figura Plotly a HTML ocupando toda la página del navegador."""
    html_str = fig.to_html(
        include_plotlyjs='cdn',
        full_html=True,
        config={'responsive': True, 'displayModeBar': True},
        div_id='piper-plot',
    )

    # CSS para que el gráfico ocupe 100 % del viewport
    full_page_css = """<style>
  html, body {
    margin: 0; padding: 0;
    width: 100%; height: 100%;
    overflow: hidden;
    background: #ffffff;
  }
  #piper-plot {
    width: 100vw !important;
    height: 100vh !important;
  }
</style>"""
    html_str = html_str.replace('</head>', full_page_css + '\n</head>')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_str)
    return output_path


# ---------------------------------------------------------------------------
# Figura matplotlib (para exportar PNG)
# ---------------------------------------------------------------------------

def create_piper_matplotlib(piper_data: pd.DataFrame):
    """
    Construye el diagrama de Piper con matplotlib.
    Retorna un objeto matplotlib.figure.Figure.
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon

    fig, ax = plt.subplots(figsize=(14, 11))
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_xlim(-20, 245)
    ax.set_ylim(-25, 220)

    border_kw = dict(edgecolor='black', facecolor='none', linewidth=1.5, zorder=2)
    grid_kw   = dict(color='grey', linewidth=0.5, linestyle=':', zorder=1)

    # Triángulos
    ax.add_patch(Polygon([(0, 0), (100, 0), (50, 86.603)],     closed=True, **border_kw))
    ax.add_patch(Polygon([(120, 0), (220, 0), (170, 86.603)],  closed=True, **border_kw))
    # Diamante
    ax.add_patch(Polygon([
        (110, 17.3206), (60, 103.9236), (110, 190.5266), (160, 103.9236)
    ], closed=True, **border_kw))

    # Grillas internas de triángulos
    for pct, y in zip([20, 40, 60, 80], [17.3206, 34.6412, 51.9618, 69.2824]):
        ax.plot([100 - pct/2, 100 - pct], [y, 0], **grid_kw)
        ax.plot([pct/2, pct],             [y, 0], **grid_kw)
        ax.plot([120 + 100 - pct/2, 120 + 100 - pct], [y, 0], **grid_kw)
        ax.plot([120 + pct/2, 120 + pct],              [y, 0], **grid_kw)
    for pct in [20, 40, 60, 80]:
        ax.plot([pct, pct + (100 - pct) / 2], [0, (100 - pct) * 0.86603], **grid_kw)

    # Grillas diagonales dentro del diamante (igual que en Plotly)
    for t in [0.2, 0.4, 0.6, 0.8]:
        # slope ≈ −1.732: Bottom→Right  ↔  Left→Top
        ax.plot([110 + t*50, 60  + t*50], [17.3206 + t*86.603, 103.9236 + t*86.603], **grid_kw)
        # slope ≈ +1.732: Bottom→Left  ↔  Right→Top
        ax.plot([110 - t*50, 160 - t*50], [17.3206 + t*86.603, 103.9236 + t*86.603], **grid_kw)

    # Etiquetas de ejes
    lkw = dict(ha='center', va='center', fontsize=11, zorder=3)
    ax.text(17,  50,  'Mg²⁺',           **lkw)
    ax.text(82,  50,  'Na⁺ + K⁺',       **lkw)
    ax.text(50,  -14, 'Ca²⁺',            **lkw)
    ax.text(170, -14, 'Cl⁻',             **lkw)
    ax.text(215, 50,  'SO₄²⁻',           **lkw)
    ax.text(130, 52,  'HCO₃⁻ + CO₃²⁻',  fontsize=10, ha='center', va='center', zorder=3)
    ax.text(72,  153, 'SO₄²⁻ + Cl⁻',    fontsize=10, ha='center', va='center', zorder=3)
    ax.text(148, 153, 'Ca²⁺ + Mg²⁺',    fontsize=10, ha='center', va='center', zorder=3)

    # Valores numéricos (0, 20, 40, 60, 80, 100)
    for pct in [20, 40, 60, 80]:
        # Cationes
        ax.text(100 - pct, -5, str(pct), fontsize=8, color='grey', ha='center')
        ax.text(pct/2 - 5, pct*0.866, str(pct), fontsize=8, color='grey', ha='center')
        ax.text(100 - pct/2 + 5, pct*0.866, str(pct), fontsize=8, color='grey', ha='center')
        # Aniones
        ax.text(120 + pct, -5, str(pct), fontsize=8, color='grey', ha='center')
        ax.text(120 + pct/2 - 5, pct*0.866, str(100-pct), fontsize=8, color='grey', ha='center')
        ax.text(220 - pct/2 + 5, pct*0.866, str(pct), fontsize=8, color='grey', ha='center')

    # Puntos de datos
    observations = piper_data['observation'].unique()
    for i, obs in enumerate(observations):
        subset = piper_data[piper_data['observation'] == obs]
        ax.scatter(subset['x'], subset['y'],
                   color=PIPER_COLORS[i % len(PIPER_COLORS)],
                   s=80, zorder=5, label=str(obs),
                   edgecolors='white', linewidths=0.6)

    ax.set_title('Diagrama de Piper', fontsize=16, fontweight='bold', pad=14)
    ax.legend(title='Muestras', loc='upper right', framealpha=0.9,
              fontsize=10, title_fontsize=11)
    plt.tight_layout()
    return fig


def export_piper_png(piper_data: pd.DataFrame, output_path: str, dpi: int = 150) -> str:
    """Exporta el diagrama de Piper como imagen PNG usando matplotlib."""
    import matplotlib.pyplot as plt
    fig = create_piper_matplotlib(piper_data)
    fig.savefig(output_path, dpi=dpi, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig)
    return output_path
