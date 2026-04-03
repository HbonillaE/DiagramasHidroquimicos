# -*- coding: utf-8 -*-
"""
diagrams/piper.py
Genera el Diagrama de Piper como figura Plotly interactiva y la exporta a HTML.
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

    Parámetros
    ----------
    data_percent : DataFrame con columnas Ca, Mg, Na, K, Cl, SO4, HCO3, CO3, IDs
                   (valores en %)

    Retorna
    -------
    DataFrame con columnas: observation, x, y
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

    # Intersección en el diamante
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
# Líneas de los contornos (triángulos + diamante + grillas)
# ---------------------------------------------------------------------------

def _triangle_lines() -> list:
    """Devuelve trazas Plotly para los bordes y grillas del diagrama de Piper."""
    traces = []

    def line(xs, ys, dash='solid', color='black', width=1):
        return go.Scatter(x=xs, y=ys, mode='lines',
                          line=dict(color=color, width=width, dash=dash),
                          showlegend=False, hoverinfo='skip')

    # --- Triángulo izquierdo ---
    traces.append(line([0, 100, 50, 0], [0, 0, 86.603, 0]))
    # --- Triángulo derecho ---
    traces.append(line([120, 220, 170, 120], [0, 0, 86.603, 0]))
    # --- Diamante central ---
    traces.append(line([110, 60, 110, 160, 110], [190.5266, 103.9236, 17.3206, 103.9236, 190.5266]))

    # Grillas (líneas internas a 20%, 40%, 60%, 80%)
    grid_style = dict(dash='dot', color='grey', width=0.5)

    # Triángulo izq. – horizontales Mg
    for pct, y in zip([20, 40, 60, 80],
                      [17.3206, 34.6412, 51.9618, 69.2824]):
        traces.append(go.Scatter(x=[100 - pct / 2, 100 - pct],
                                 y=[y, 0],
                                 mode='lines', line=grid_style,
                                 showlegend=False, hoverinfo='skip'))
        traces.append(go.Scatter(x=[pct / 2, pct],
                                 y=[y, 0],
                                 mode='lines', line=grid_style,
                                 showlegend=False, hoverinfo='skip'))

    # Triángulo izq. – diagonales Ca
    for pct in [20, 40, 60, 80]:
        traces.append(go.Scatter(x=[pct, pct + (100 - pct) / 2],
                                 y=[0, (100 - pct) * 0.86603],
                                 mode='lines', line=grid_style,
                                 showlegend=False, hoverinfo='skip'))

    # Triángulo der. – mismas grillas desplazadas +120
    for pct, y in zip([20, 40, 60, 80],
                      [17.3206, 34.6412, 51.9618, 69.2824]):
        traces.append(go.Scatter(x=[120 + 100 - pct / 2, 120 + 100 - pct],
                                 y=[y, 0],
                                 mode='lines', line=grid_style,
                                 showlegend=False, hoverinfo='skip'))
        traces.append(go.Scatter(x=[120 + pct / 2, 120 + pct],
                                 y=[y, 0],
                                 mode='lines', line=grid_style,
                                 showlegend=False, hoverinfo='skip'))

    return traces


def _piper_annotations() -> list:
    """Devuelve anotaciones de texto para las etiquetas de los ejes."""
    return [
        dict(x=17, y=50,  text='Mg²⁺',               showarrow=False, font=dict(size=11)),
        dict(x=82, y=50,  text='Na⁺ + K⁺',            showarrow=False, font=dict(size=11)),
        dict(x=50, y=-8,  text='Ca²⁺',                showarrow=False, font=dict(size=11)),
        dict(x=170, y=-8, text='Cl⁻',                 showarrow=False, font=dict(size=11)),
        dict(x=208, y=48, text='SO₄²⁻',               showarrow=False, font=dict(size=11)),
        dict(x=133, y=50, text='HCO₃⁻ + CO₃²⁻',      showarrow=False, font=dict(size=11)),
        dict(x=72, y=150, text='SO₄²⁻ + Cl⁻',        showarrow=False, font=dict(size=10)),
        dict(x=148, y=150, text='Ca²⁺ + Mg²⁺',       showarrow=False, font=dict(size=10)),
    ]


# ---------------------------------------------------------------------------
# Figura Plotly
# ---------------------------------------------------------------------------

def create_piper_plotly(piper_data: pd.DataFrame) -> go.Figure:
    """
    Construye la figura Plotly del diagrama de Piper.

    Parámetros
    ----------
    piper_data : salida de transform_piper_data()

    Retorna
    -------
    plotly.graph_objects.Figure
    """
    fig = go.Figure()

    # Bordes y grillas
    for trace in _triangle_lines():
        fig.add_trace(trace)

    # Puntos de datos (una traza por pozo para la leyenda)
    observations = piper_data['observation'].unique()
    colors = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ]

    for i, obs in enumerate(observations):
        subset = piper_data[piper_data['observation'] == obs]
        fig.add_trace(go.Scatter(
            x=subset['x'],
            y=subset['y'],
            mode='markers',
            marker=dict(size=9, color=colors[i % len(colors)]),
            name=str(obs),
            hovertemplate=f'<b>{obs}</b><br>x: %{{x:.1f}}<br>y: %{{y:.1f}}<extra></extra>',
        ))

    fig.update_layout(
        title=dict(text='Diagrama de Piper', font=dict(size=16), x=0.5),
        xaxis=dict(visible=False, range=[-10, 235]),
        yaxis=dict(visible=False, scaleanchor='x', range=[-20, 210]),
        annotations=_piper_annotations(),
        legend=dict(title='Puntos', bgcolor='rgba(255,255,255,0.8)',
                    bordercolor='black', borderwidth=1),
        plot_bgcolor='white',
        paper_bgcolor='white',
        width=850,
        height=700,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return fig


def export_piper_html(fig: go.Figure, output_path: str) -> str:
    """Exporta la figura Plotly a un archivo HTML. Retorna la ruta."""
    fig.write_html(output_path,         
    include_plotlyjs='cdn',
    full_html=True,
    config={'responsive': True})
    return output_path
