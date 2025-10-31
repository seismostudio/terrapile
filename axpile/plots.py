import plotly.graph_objects as go
import pandas as pd
from typing import List

from .models import SoilLayer


def plot_depth_vs_qall(df: pd.DataFrame):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=df["Qall_kN"], y=df["Depth_m"], mode="lines", name="Qall")
    )
    fig.update_yaxes(autorange="reversed", title_text="Depth (m)")
    fig.update_xaxes(title_text="Qall (kN)")
    return fig


def plot_depth_vs_components(df: pd.DataFrame):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=df["Qfs_kN"], y=df["Depth_m"], mode="lines", name="Qfs")
    )
    fig.add_trace(
        go.Scatter(x=df["Qb_kN"], y=df["Depth_m"], mode="lines", name="Qb")
    )
    fig.add_trace(
        go.Scatter(x=df["Qult_kN"], y=df["Depth_m"], mode="lines", name="Qult")
    )
    fig.add_trace(
        go.Scatter(x=df["Qall_kN"], y=df["Depth_m"], mode="lines", name="Qall")
    )
    fig.update_yaxes(autorange="reversed", title_text="Depth (m)")
    fig.update_xaxes(title_text="Capacity (kN)")
    return fig

def plot_pilecap_layout(piles_df: pd.DataFrame, width_m: float, length_m: float, pile_diameter_m: float = 0.0):
    fig = go.Figure()

    w = float(width_m)
    l = float(length_m)
    x0 = -w / 2.0
    x1 = w / 2.0
    y0 = -l / 2.0
    y1 = l / 2.0

    # Pilecap rectangle centered at 0,0
    fig.add_shape(
        type="rect",
        x0=x0,
        x1=x1,
        y0=y0,
        y1=y1,
        line=dict(color="#4a5568", width=2),
        fillcolor="#e2e8f0",
        layer="below",
    )

    # Plot piles (as circles) and labels
    if not piles_df.empty:
        x_vals = piles_df["X (m)"].astype(float).tolist()
        y_vals = piles_df["Y (m)"].astype(float).tolist()
        labels = piles_df["Pile Number"].astype(int).astype(str).tolist()

        circle_edge = "#2b6cb0"
        circle_fill = "#90cdf4"
        label_color = circle_edge

        r = max(float(pile_diameter_m), 0.0) / 2.0
        for x, y in zip(x_vals, y_vals):
            if r > 0.0:
                fig.add_shape(
                    type="circle",
                    x0=x - r,
                    x1=x + r,
                    y0=y - r,
                    y1=y + r,
                    line=dict(color=circle_edge, width=2),
                    fillcolor=circle_fill,
                )
            else:
                fig.add_shape(
                    type="circle",
                    x0=x - 0.05,
                    x1=x + 0.05,
                    y0=y - 0.05,
                    y1=y + 0.05,
                    line=dict(color=circle_edge, width=2),
                    fillcolor=circle_fill,
                )

        # labels only (keep axis labels, hide grid)
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=y_vals,
                mode="text",
                text=labels,
                textposition="top center",
                textfont=dict(color=label_color),
                showlegend=False,
            )
        )

    # Equal aspect ratio and margins
    max_extent = max(w, l) / 2.0
    pad = max_extent * 0.1 + 0.1
    fig.update_layout(
        xaxis=dict(title="X (m)", range=[x0 - pad, x1 + pad], zeroline=False, showgrid=False, showline=False),
        yaxis=dict(title="Y (m)", range=[y0 - pad, y1 + pad], zeroline=False, showgrid=False, showline=False, scaleanchor="x", scaleratio=1),
        margin=dict(l=40, r=10, t=10, b=40),
        height=500,
        showlegend=False,
    )
    return fig

def plot_soil_profile(layers: List[SoilLayer], pile_depth_m: float, cutoff_m: float) -> go.Figure:
    # Canvas x-domain [0, 1]; pile centered at 0.5
    fig = go.Figure()

    # Color map per soil behavior
    behavior_color = {
        "clay": "#d4b5ff",
        "silt": "#c7e3ff",
        "sand": "#ffe5a3",
    }

    # Draw soil layers as horizontal rectangles filling width
    z_top = 0.0
    annotations = []
    for idx, layer in enumerate(layers):
        z_bot = z_top - layer.thickness_m
        # stop at pile depth visual extent
        if z_top >= pile_depth_m:
            break
        y0 = z_top
        y1 = min(z_bot, pile_depth_m)
        fig.add_shape(
            type="rect",
            x0=0.0,
            x1=1.0,
            y0=y0,
            y1=y1,
            line=dict(color="#999999", width=1),
            fillcolor=behavior_color.get(layer.soil_behavior, "#eeeeee"),
            layer="below",
        )
        # Layer label
        annotations.append(
            dict(
                x=0.8,
                y=((y0 + y1) / 2.0)+0.2,
                text=f"{layer.soil_type}",
                showarrow=False,
                font=dict(size=12, color="#303030"),
            )
        )
        z_top = z_bot

    # Draw pile as centered vertical rectangle
    pile_half_width = 0.04  # relative to canvas width
    fig.add_shape(
        type="rect",
        x0=0.5 - pile_half_width,
        x1=0.5 + pile_half_width,
        y0=-cutoff_m,
        y1=-pile_depth_m,
        line=dict(color="#444444", width=2),
        fillcolor="#caa37a",
    )

    # Cut-off line
    fig.add_shape(
        type="line",
        x0=0.0,
        x1=1.0,
        y0=-cutoff_m,
        y1=-cutoff_m,
        line=dict(color="#ff4d4f", width=2, dash="dash"),
    )
    annotations.append(
        dict(x=0.02, y=-cutoff_m + 0.2, text="Cut-off", showarrow=False, xanchor="left", font=dict(color="#ff4d4f"))
    )

    fig.update_layout(
        annotations=annotations,
        xaxis=dict(visible=False, range=[0, 1]),
        yaxis=dict(title="Depth (m)", autorange="reversed", range=[min(cutoff_m,z_bot),0]),
        margin=dict(l=40, r=10, t=10, b=40),
        height=600,
        showlegend=False,
    )
    return fig


