"""
Folium interactive map for the Assam flood situational dashboard.
"""

from __future__ import annotations

import folium
import requests
from folium.features import GeoJsonTooltip

ASSAM_GEOJSON_URL = (
    "https://raw.githubusercontent.com/datameet/maps/master/Districts/Assam.geojson"
)

DISTRICT_FILL: dict[str, str] = {
    "NORMAL":  "#1a4a6b",
    "WARNING": "#7c4a00",
    "DANGER":  "#7c1a1a",
    "EXTREME": "#4a0000",
}

MARKER_FILL: dict[str, str] = {
    "NORMAL":  "#22c55e",
    "WARNING": "#f59e0b",
    "DANGER":  "#ef4444",
    "EXTREME": "#7f1d1d",
}

ALERT_PRIORITY: dict[str, int] = {"NORMAL": 0, "WARNING": 1, "DANGER": 2, "EXTREME": 3}


def _district_alert(district_name: str, current_data: dict) -> str:
    highest = "NORMAL"
    dn = district_name.lower()
    for s in current_data.values():
        sd = s["district"].lower()
        if dn in sd or sd in dn or dn.split()[0] in sd:
            if ALERT_PRIORITY[s["alert"]] > ALERT_PRIORITY[highest]:
                highest = s["alert"]
    return highest


def _rain_color(mm: float) -> str:
    """Colour scale for rainfall intensity circles, roughly aligned to
    IMD's rainfall categories (light / moderate / heavy / very heavy)."""
    if mm < 2.5:
        return "#38bdf8"   # light - sky blue
    elif mm < 15:
        return "#3b82f6"   # moderate - blue
    elif mm < 40:
        return "#7c3aed"   # heavy - violet
    else:
        return "#db2777"   # very heavy - magenta


def _rain_icon(mm: float) -> tuple[str, int]:
    """Pick an emoji + size that visually communicates rainfall intensity,
    roughly aligned to IMD's rainfall categories."""
    if mm < 0.5:
        return "☁️", 22          # no/negligible rain - plain cloud
    elif mm < 2.5:
        return "🌦️", 24          # light - sun/cloud with light rain
    elif mm < 15:
        return "🌧️", 28          # moderate - rain cloud
    elif mm < 40:
        return "🌧️", 34          # heavy - bigger rain cloud
    else:
        return "⛈️", 38          # very heavy - thunderstorm


def _add_rainfall_layer(m: folium.Map, current_data: dict) -> None:
    """Adds a toggleable layer showing live observed (last 24h) and
    forecast (next 6h) rainfall at each station's location, sourced from
    Open-Meteo. Each station gets a cloud/rain emoji marker whose icon and
    size change with rainfall intensity, with a soft colour halo underneath
    for an at-a-glance intensity cue."""
    rain_layer = folium.FeatureGroup(name="🌧️ Rainfall (live)", show=False)

    for s in current_data.values():
        rain_24h = s.get("rain_24h_mm")
        rain_fc = s.get("rain_forecast_6h_mm")
        if rain_24h is None and rain_fc is None:
            continue

        display_mm = rain_24h if rain_24h is not None else 0.0
        color = _rain_color(display_mm)
        emoji, icon_size = _rain_icon(display_mm)

        fc_txt = f"{rain_fc} mm" if rain_fc is not None else "n/a"
        popup_html = f"""
        <div style="font-family:Inter,sans-serif;min-width:180px;padding:2px">
            <div style="font-size:13px;font-weight:700;color:#1e293b;margin-bottom:4px">
                {emoji} {s['name']}
            </div>
            <div style="font-size:12px;color:#334155;line-height:1.5">
                Last 24h: <b>{display_mm} mm</b><br>
                Next 6h (forecast): <b>{fc_txt}</b>
            </div>
        </div>
        """

       
        halo_radius = 14 + min(display_mm, 60) * 0.5
        folium.CircleMarker(
            location=[s["lat"], s["lng"]],
            radius=halo_radius,
            color=color,
            weight=0,
            fill=True,
            fill_color=color,
            fill_opacity=0.18,
        ).add_to(rain_layer)

        folium.Marker(
            location=[s["lat"], s["lng"]],
            icon=folium.DivIcon(
                html=f"""
                <div style="font-size:{icon_size}px;line-height:1;
                            text-align:center;
                            filter:drop-shadow(0 1px 3px rgba(0,0,0,.6));
                            transform:translate(-50%,-50%);">
                    {emoji}
                </div>
                """,
                icon_size=(icon_size, icon_size),
                icon_anchor=(icon_size // 2, icon_size // 2),
            ),
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=f"{emoji} {s['name']}: {display_mm}mm (24h)",
        ).add_to(rain_layer)

    rain_layer.add_to(m)


def build_map(current_data: dict, selected_station_id: str | None = None) -> folium.Map:
    m = folium.Map(
        location=[26.1, 92.8],
        zoom_start=7,
        tiles="CartoDB dark_matter",
        attr="CartoDB",
        prefer_canvas=True,
    )

    folium.TileLayer(
        tiles=(
            "https://server.arcgisonline.com/ArcGIS/rest/services"
            "/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ),
        attr="Esri World Imagery © Esri",
        name="🛰️ Satellite",
        overlay=False,
    ).add_to(m)

    try:
        geojson = requests.get(ASSAM_GEOJSON_URL, timeout=6).json()

        def style_fn(feature: dict) -> dict:
            district = feature["properties"].get("dtname", "")
            alert = _district_alert(district, current_data)
            return {
                "fillColor": DISTRICT_FILL[alert],
                "color": "#1e3a5f",
                "weight": 1.2,
                "fillOpacity": 0.5,
            }

        def highlight_fn(feature: dict) -> dict:
            return {
                "fillColor": "#2563EB",
                "color": "#60A5FA",
                "weight": 2,
                "fillOpacity": 0.65,
            }

        folium.GeoJson(
            geojson,
            name="🗺️ Districts",
            style_function=style_fn,
            highlight_function=highlight_fn,
            tooltip=GeoJsonTooltip(
                fields=["dtname"],
                aliases=["District:"],
                style=(
                    "background-color:#1E293B;color:#F1F5F9;"
                    "font-family:Inter,sans-serif;font-size:13px;"
                    "border:1px solid #334155;border-radius:6px;"
                ),
            ),
        ).add_to(m)
    except Exception:
        pass

    _add_rainfall_layer(m, current_data)

    for sid, s in current_data.items():
        is_selected = sid == selected_station_id
        fill_color = MARKER_FILL[s["alert"]]
        radius = 13 if is_selected else 9
        weight = 3 if is_selected else 2

        popup_html = f"""
        <div style="font-family:Inter,sans-serif;min-width:220px;padding:4px">
            <div style="font-size:15px;font-weight:700;color:#1e293b;margin-bottom:2px">
                📍 {s['name']}
            </div>
            <div style="color:#64748b;font-size:12px;margin-bottom:8px">
                {s['river']} · {s['district']}
            </div>
            <table style="width:100%;font-size:13px;color:#1e293b;border-collapse:collapse">
                <tr><td style="padding:3px 0">Current Level</td>
                    <td style="text-align:right"><b>{s['current_level']} m</b></td></tr>
                <tr><td style="padding:3px 0">Warning Level</td>
                    <td style="text-align:right;color:#d97706">{s['warning_level']} m</td></tr>
                <tr><td style="padding:3px 0">Danger Level</td>
                    <td style="text-align:right;color:#dc2626">{s['danger_level']} m</td></tr>
                <tr><td style="padding:3px 0">24h Change</td>
                    <td style="text-align:right">{'+' if s['change_24h'] >= 0 else ''}{s['change_24h']} m</td></tr>
                <tr><td style="padding:3px 0">Trend</td>
                    <td style="text-align:right">{s['trend']}</td></tr>
            </table>
            <div style="margin-top:10px;padding:5px 10px;border-radius:5px;text-align:center;
                        font-weight:700;font-size:12px;letter-spacing:.06em;
                        background:{'#dcfce7' if s['alert']=='NORMAL' else '#fef3c7' if s['alert']=='WARNING' else '#fee2e2'};
                        color:{'#166534' if s['alert']=='NORMAL' else '#92400e' if s['alert']=='WARNING' else '#991b1b'}">
                {s['alert']}
            </div>
        </div>
        """

        folium.CircleMarker(
            location=[s["lat"], s["lng"]],
            radius=radius,
            color="white",
            weight=weight,
            fill=True,
            fill_color=fill_color,
            fill_opacity=0.95,
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=(
                f"{'● ' if is_selected else ''}"
                f"{s['name']} | {s['river']} | {s['alert']} | {s['current_level']}m"
            ),
        ).add_to(m)

    legend_html = """
    <div style="position:fixed;bottom:28px;left:28px;z-index:1000;
                background:#1E293B;border:1px solid #334155;border-radius:10px;
                padding:12px 16px;font-family:Inter,sans-serif;
                font-size:12px;color:#F1F5F9;box-shadow:0 4px 12px rgba(0,0,0,.4)">
        <div style="font-weight:700;margin-bottom:8px;color:#94A3B8;
                    letter-spacing:.08em;font-size:11px">ALERT STATUS</div>
        <div style="margin:5px 0;display:flex;align-items:center;gap:8px">
            <span style="width:11px;height:11px;border-radius:50%;background:#22c55e;display:inline-block"></span>Normal
        </div>
        <div style="margin:5px 0;display:flex;align-items:center;gap:8px">
            <span style="width:11px;height:11px;border-radius:50%;background:#f59e0b;display:inline-block"></span>Warning
        </div>
        <div style="margin:5px 0;display:flex;align-items:center;gap:8px">
            <span style="width:11px;height:11px;border-radius:50%;background:#ef4444;display:inline-block"></span>Danger
        </div>
        <div style="margin:5px 0;display:flex;align-items:center;gap:8px">
            <span style="width:11px;height:11px;border-radius:50%;background:#7f1d1d;display:inline-block"></span>Extreme
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    folium.LayerControl(collapsed=False, position="topright").add_to(m)

    return m