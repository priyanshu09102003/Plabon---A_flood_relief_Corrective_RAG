"""
Live data layer for Assam flood monitoring stations.

Data sources:
  - Rainfall (live, hourly):      Open-Meteo Forecast API
        https://open-meteo.com/en/docs
  - River discharge (live, daily): Open-Meteo Flood API (GloFAS model)
        https://open-meteo.com/en/docs/flood-api

This module computes a transparent, explainable
COMPOSITE FLOOD RISK INDEX from two real, live, physically meaningful
signals:

    1. 24h observed rainfall at the station's catchment point (Open-Meteo)
    2. River discharge anomaly vs. the station's own recent baseline
       (Open-Meteo Flood API, GloFAS reanalysis + forecast)

The risk index is a model output, not a sensor reading, and the UI
labels it as such everywhere it is shown.

Station warning/danger reference levels and coordinates are sourced from
public CWC flood-monitoring records and used only as static metadata
(river name, district, hazard thresholds for context) — these never
change at runtime.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Literal

import requests
import streamlit as st

AlertLevel = Literal["NORMAL", "WARNING", "DANGER", "EXTREME"]

ALERT_PRIORITY: dict[str, int] = {"NORMAL": 0, "WARNING": 1, "DANGER": 2, "EXTREME": 3}

OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_FLOOD_URL = "https://flood-api.open-meteo.com/v1/flood"


RAINFALL_CACHE_TTL_SECONDS = 300       
DISCHARGE_CACHE_TTL_SECONDS = 3600     

GAUGE_STATIONS: dict[str, dict] = {
    "guwahati": {
        "name": "Guwahati",
        "river": "Brahmaputra",
        "district": "Kamrup Metropolitan",
        "lat": 26.183, "lng": 91.736,
        "warning_level": 49.68,
        "danger_level": 51.68,
        "hfl": 54.07,
    },
    "tezpur": {
        "name": "Tezpur",
        "river": "Brahmaputra",
        "district": "Sonitpur",
        "lat": 26.630, "lng": 92.800,
        "warning_level": 62.50,
        "danger_level": 63.50,
        "hfl": 65.71,
    },
    "dibrugarh": {
        "name": "Dibrugarh",
        "river": "Brahmaputra",
        "district": "Dibrugarh",
        "lat": 27.480, "lng": 94.890,
        "warning_level": 107.29,
        "danger_level": 108.29,
        "hfl": 111.14,
    },
    "dhubri": {
        "name": "Dhubri",
        "river": "Brahmaputra",
        "district": "Dhubri",
        "lat": 26.020, "lng": 89.970,
        "warning_level": 20.87,
        "danger_level": 22.87,
        "hfl": 24.50,
    },
    "neamatighat": {
        "name": "Neamatighat",
        "river": "Brahmaputra",
        "district": "Jorhat",
        "lat": 26.801, "lng": 94.193,
        "warning_level": 84.00,
        "danger_level": 86.00,
        "hfl": 89.02,
    },
    "nt_road": {
        "name": "NT Road Crossing",
        "river": "Jia Bharali",
        "district": "Sonitpur",
        "lat": 26.836, "lng": 93.018,
        "warning_level": 76.79,
        "danger_level": 78.79,
        "hfl": 82.05,
    },
    "kampur": {
        "name": "Kampur",
        "river": "Kopili",
        "district": "Nagaon",
        "lat": 26.231, "lng": 92.569,
        "warning_level": 45.00,
        "danger_level": 47.00,
        "hfl": 52.34,
    },
    "badarpurghat": {
        "name": "Badarpurghat",
        "river": "Barak",
        "district": "Hailakandi",
        "lat": 24.870, "lng": 93.150,
        "warning_level": 17.90,
        "danger_level": 19.81,
        "hfl": 22.46,
    },
    "goalpara": {
        "name": "Goalpara",
        "river": "Brahmaputra",
        "district": "Goalpara",
        "lat": 26.169, "lng": 90.619,
        "warning_level": 31.60,
        "danger_level": 34.60,
        "hfl": 36.10,
    },
}


def get_alert_level(risk_pct: float) -> AlertLevel:
    """Map a 0-150 composite risk percentage onto the same alert taxonomy
    used everywhere else in the app, so the map/chart/UI code needs no
    changes."""
    if risk_pct >= 108:
        return "EXTREME"
    elif risk_pct >= 100:
        return "DANGER"
    elif risk_pct >= 70:
        return "WARNING"
    else:
        return "NORMAL"




@st.cache_data(ttl=RAINFALL_CACHE_TTL_SECONDS, show_spinner=False)
def _fetch_rainfall(lat: float, lng: float) -> dict | None:
    """Live rainfall via Open-Meteo Forecast API. Free, no key.
    Docs: https://open-meteo.com/en/docs
    Returns past 24h + next 24h hourly precipitation (mm)."""
    try:
        r = requests.get(
            OPEN_METEO_FORECAST_URL,
            params={
                "latitude": lat,
                "longitude": lng,
                "hourly": "precipitation",
                "past_days": 1,
                "forecast_days": 2,
                "timezone": "Asia/Kolkata",
            },
            timeout=8,
        )
        r.raise_for_status()
        data = r.json()
        return {
            "timestamps": data["hourly"]["time"],
            "precipitation_mm": data["hourly"]["precipitation"],
        }
    except Exception:
        return None


@st.cache_data(ttl=DISCHARGE_CACHE_TTL_SECONDS, show_spinner=False)
def _fetch_discharge(lat: float, lng: float) -> dict | None:
    """Live river discharge via Open-Meteo Flood API (GloFAS model).
    Free, no key. Docs: https://open-meteo.com/en/docs/flood-api
    Returns daily discharge (m3/s) for recent past + forecast days."""
    try:
        r = requests.get(
            OPEN_METEO_FLOOD_URL,
            params={
                "latitude": lat,
                "longitude": lng,
                "daily": "river_discharge",
                "past_days": 14,
                "forecast_days": 5,
            },
            timeout=8,
        )
        r.raise_for_status()
        data = r.json()
        return {
            "dates": data["daily"]["time"],
            "discharge_m3s": data["daily"]["river_discharge"],
        }
    except Exception:
        return None


def _rainfall_24h_sum(rainfall: dict | None) -> float | None:
    if not rainfall or not rainfall.get("precipitation_mm"):
        return None
    # last 24 hourly readings = past day
    vals = [v for v in rainfall["precipitation_mm"][-24:] if v is not None]
    return round(sum(vals), 1) if vals else None


def _rainfall_next_hours_sum(rainfall: dict | None, hours: int = 6) -> float | None:
    """Forecast rainfall over the next N hours, read straight from the same
    Open-Meteo response (past_days=1, forecast_days=2 already includes the
    forecast window) — used for the 'where is it expected to rain' map
    overlay rather than only showing what already fell."""
    if not rainfall or not rainfall.get("precipitation_mm"):
        return None
    vals = rainfall["precipitation_mm"]

    upcoming = [v for v in vals[24:24 + hours] if v is not None]
    return round(sum(upcoming), 1) if upcoming else None


def _discharge_anomaly_pct(discharge: dict | None) -> float | None:
    """Today's discharge vs. the trailing 14-day mean, as a % deviation.
    Positive = discharge running above its recent baseline (rising flood
    potential); this is the GloFAS-based signal the EU/JRC flood
    awareness system itself uses conceptually."""
    if not discharge or not discharge.get("discharge_m3s"):
        return None
    vals = [v for v in discharge["discharge_m3s"] if v is not None]
    if len(vals) < 5:
        return None
    baseline = sum(vals[:-5]) / max(len(vals[:-5]), 1)
    latest = vals[-5]  # last value with forecast confidence still high
    if baseline <= 0:
        return None
    return round(((latest - baseline) / baseline) * 100, 1)


def _composite_risk_pct(rain_24h_mm: float | None, discharge_anom_pct: float | None) -> float:
    """Blend two real, live signals into a single 0-150 risk index that
    plugs into the existing alert taxonomy (warning at ~70, danger at 100).

    This is intentionally simple and explainable:
      - rainfall contributes up to 60 points (saturates near 80mm/24h,
        which is IMD's own 'very heavy rainfall' threshold)
      - discharge anomaly contributes the remaining swing, since rising
        river discharge is the more direct flood-extent signal
      - baseline of 40 reflects "normal" so the index sits mid-NORMAL
        band when both signals are quiet
    """
    rain = rain_24h_mm if rain_24h_mm is not None else 0.0
    disc = discharge_anom_pct if discharge_anom_pct is not None else 0.0

    rain_component = min(rain / 80.0, 1.0) * 60.0
    disc_component = max(min(disc, 60.0), -20.0) * 0.8

    risk = 40.0 + rain_component + disc_component
    return round(max(min(risk, 150.0), 0.0), 1)



def get_current_levels() -> dict[str, dict]:
    """Live composite snapshot for every station. Drop-in replacement for
    the old simulated version — same dict shape, so build_map(),
    build_status_chart() etc. need no changes.

    'current_level' here is expressed in the same metre units/scale as
    warning_level/danger_level so existing rendering code keeps working,
    but it is DERIVED from the composite risk %, not a real ruler reading.
    """
    result: dict[str, dict] = {}

    for sid, meta in GAUGE_STATIONS.items():
        rainfall = _fetch_rainfall(meta["lat"], meta["lng"])
        discharge = _fetch_discharge(meta["lat"], meta["lng"])

        rain_24h = _rainfall_24h_sum(rainfall)
        rain_forecast_6h = _rainfall_next_hours_sum(rainfall, hours=6)
        disc_anom = _discharge_anomaly_pct(discharge)
        risk_pct = _composite_risk_pct(rain_24h, disc_anom)

        alert = get_alert_level(risk_pct)
        current_level = round(meta["danger_level"] * (risk_pct / 100.0), 2)

        if disc_anom is not None and disc_anom > 8:
            trend = "↑ Rising"
        elif disc_anom is not None and disc_anom < -8:
            trend = "↓ Falling"
        else:
            trend = "→ Stable"

        result[sid] = {
            **meta,
            "current_level": current_level,
            "pct_of_danger": risk_pct,
            "alert": alert,
            "trend": trend,
            "change_24h": disc_anom if disc_anom is not None else 0.0,
            "rain_24h_mm": rain_24h,
            "rain_forecast_6h_mm": rain_forecast_6h,
            "discharge_anomaly_pct": disc_anom,
            "data_live": rainfall is not None or discharge is not None,
        }

    return result


def get_24h_history(station_id: str, current_level: float,
                     warning_level: float, danger_level: float) -> dict:
    """Live 24h *rainfall-driven* trend for the selected station, reshaped
    into the {timestamps, levels, warning_level, danger_level} contract
    the existing build_trend_chart() expects, so the chart code is
    untouched. 'levels' here tracks the composite risk trajectory
    (expressed on the same metre scale as the thresholds) computed from
    each hour's trailing rainfall — a live signal, not noise."""
    meta = GAUGE_STATIONS[station_id]
    rainfall = _fetch_rainfall(meta["lat"], meta["lng"])
    discharge = _fetch_discharge(meta["lat"], meta["lng"])
    disc_anom = _discharge_anomaly_pct(discharge)

    now = datetime.now()

    if rainfall and rainfall.get("timestamps"):
        
        timestamps_raw = rainfall["timestamps"][-24:]
        precip = rainfall["precipitation_mm"][-24:]
        timestamps = []
        for t in timestamps_raw:
            try:
                timestamps.append(datetime.fromisoformat(t).strftime("%H:%M"))
            except Exception:
                timestamps.append(t[-5:])

        levels = []
        running_rain = 0.0
        window: list[float] = []
        for p in precip:
            p = p or 0.0
            window.append(p)
            if len(window) > 24:
                window.pop(0)
            running_rain = sum(window)
            risk_pct = _composite_risk_pct(running_rain, disc_anom)
            levels.append(round(danger_level * (risk_pct / 100.0), 2))
    else:

        timestamps = [(now - timedelta(hours=23 - i)).strftime("%H:%M") for i in range(24)]
        levels = [current_level] * 24

    return {
        "timestamps": timestamps,
        "levels": levels,
        "warning_level": warning_level,
        "danger_level": danger_level,
    }


def get_data_source_status() -> dict:

    try:
        r = requests.get(
            OPEN_METEO_FORECAST_URL,
            params={"latitude": 26.1, "longitude": 91.7, "current": "precipitation"},
            timeout=5,
        )
        ok = r.status_code == 200
    except Exception:
        ok = False
    return {"open_meteo_ok": ok, "checked_at": datetime.now()}