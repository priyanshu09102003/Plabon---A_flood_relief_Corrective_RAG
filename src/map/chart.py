"""
Plotly charts for the Assam flood situational dashboard.
"""

from __future__ import annotations

import plotly.graph_objects as go

ALERT_HEX: dict[str, str] = {
    "NORMAL":  "#22c55e",
    "WARNING": "#f59e0b",
    "DANGER":  "#ef4444",
    "EXTREME": "#7f1d1d",
}


def _hex_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def build_status_chart(current_data: dict) -> go.Figure:
    stations = list(current_data.values())
    names = [f"{s['name']} ({s['river']})" for s in stations]
    pcts = [s["pct_of_danger"] for s in stations]
    warning_pcts = [round(s["warning_level"] / s["danger_level"] * 100, 1) for s in stations]
    bar_colors = [ALERT_HEX[s["alert"]] for s in stations]
    min_warn = min(warning_pcts)

    fig = go.Figure()

    fig.add_vrect(x0=0, x1=min_warn,
                  fillcolor=_hex_rgba("#1a5276", 0.22), layer="below", line_width=0)
    fig.add_vrect(x0=min_warn, x1=100,
                  fillcolor=_hex_rgba("#7c4a00", 0.22), layer="below", line_width=0)
    fig.add_vrect(x0=100, x1=135,
                  fillcolor=_hex_rgba("#7c1a1a", 0.22), layer="below", line_width=0)

    fig.add_trace(go.Bar(
        x=pcts, y=names,
        orientation="h",
        marker_color=bar_colors,
        marker_line_width=0,
        text=[f"{p:.1f}%" for p in pcts],
        textposition="outside",
        textfont=dict(color="#94A3B8", size=11, family="Inter"),
        customdata=[
            [s["current_level"], s["warning_level"], s["danger_level"],
             s["trend"], s["alert"], s["change_24h"]]
            for s in stations
        ],
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Current level: %{customdata[0]}m (%{x:.1f}% of danger)<br>"
            "Warning at: %{customdata[1]}m<br>"
            "Danger at: %{customdata[2]}m<br>"
            "24h change: %{customdata[5]:+.2f}m<br>"
            "Trend: %{customdata[3]}<br>"
            "Status: <b>%{customdata[4]}</b>"
            "<extra></extra>"
        ),
        showlegend=False,
    ))

    fig.add_trace(go.Scatter(
        x=warning_pcts, y=names,
        mode="markers",
        marker=dict(symbol="line-ns", size=24, color="#f59e0b",
                    line=dict(width=2.5, color="#f59e0b")),
        name="⚠ Warning threshold",
        hoverinfo="skip",
    ))

    fig.add_vline(x=100, line_dash="dash", line_color="#ef4444", line_width=2,
                  annotation_text="Danger Level",
                  annotation_position="top right",
                  annotation_font=dict(color="#ef4444", size=10, family="Inter"))

    fig.update_layout(
        title=dict(text="Water Level Status — All Gauge Stations",
                   font=dict(color="#F1F5F9", size=14, family="Inter"), x=0),
        paper_bgcolor="#0F172A", plot_bgcolor="#1E293B",
        font=dict(color="#94A3B8", family="Inter, sans-serif"),
        xaxis=dict(title="% of Danger Level", range=[0, 135], gridcolor="#334155",
                   ticksuffix="%", zerolinecolor="#334155", zeroline=False),
        yaxis=dict(gridcolor="rgba(0,0,0,0)", categoryorder="total ascending"),
        height=400,
        margin=dict(l=0, r=80, t=52, b=44),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1, font=dict(color="#94A3B8", size=11)),
        bargap=0.35,
    )
    return fig


def build_trend_chart(history: dict, station_name: str, alert: str) -> go.Figure:
    color = ALERT_HEX.get(alert, "#3B82F6")
    max_y = max(max(history["levels"]), history["danger_level"]) * 1.08

    fig = go.Figure()

    fig.add_hrect(y0=0, y1=history["warning_level"],
                  fillcolor=_hex_rgba("#1a5276", 0.2), layer="below", line_width=0)
    fig.add_hrect(y0=history["warning_level"], y1=history["danger_level"],
                  fillcolor=_hex_rgba("#7c4a00", 0.2), layer="below", line_width=0)
    fig.add_hrect(y0=history["danger_level"], y1=max_y,
                  fillcolor=_hex_rgba("#7c1a1a", 0.2), layer="below", line_width=0)

    fig.add_hline(y=history["warning_level"], line_dash="dot",
                  line_color="#f59e0b", line_width=1.5,
                  annotation_text=f"⚠ Warning {history['warning_level']}m",
                  annotation_position="bottom right",
                  annotation_font=dict(color="#f59e0b", size=10, family="Inter"))

    fig.add_hline(y=history["danger_level"], line_dash="dash",
                  line_color="#ef4444", line_width=2,
                  annotation_text=f"🔴 Danger {history['danger_level']}m",
                  annotation_position="top right",
                  annotation_font=dict(color="#ef4444", size=10, family="Inter"))

    fig.add_trace(go.Scatter(
        x=history["timestamps"], y=history["levels"],
        fill="tozeroy",
        fillcolor=_hex_rgba(color, 0.15),
        line=dict(color=color, width=2.5),
        mode="lines",
        name=station_name,
        hovertemplate="%{x}<br><b>%{y:.2f} m</b><extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=[history["timestamps"][-1]], y=[history["levels"][-1]],
        mode="markers+text",
        marker=dict(size=10, color=color, line=dict(width=2, color="white")),
        text=[f"  {history['levels'][-1]:.2f}m"],
        textposition="middle right",
        textfont=dict(color=color, size=12, family="Inter"),
        hoverinfo="skip", showlegend=False,
    ))

    fig.update_layout(
        title=dict(text=f"{station_name} — 24hr Water Level Trend",
                   font=dict(color="#F1F5F9", size=14, family="Inter"), x=0),
        paper_bgcolor="#0F172A", plot_bgcolor="#1E293B",
        font=dict(color="#94A3B8", family="Inter, sans-serif"),
        xaxis=dict(title="Time (last 24 hours)", gridcolor="#334155",
                   tickangle=-35, nticks=8),
        yaxis=dict(title="Water Level (metres)", gridcolor="#334155", range=[0, max_y]),
        height=400,
        margin=dict(l=10, r=90, t=52, b=60),
        showlegend=False, hovermode="x unified",
    )
    return fig