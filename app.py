"""
Plabon — Corrective RAG Flood Relief Assistant
Professional Streamlit UI (Phase 9 + Phase 11 tabs)
"""

from pathlib import Path
import streamlit as st
import random
from datetime import datetime

st.set_page_config(
    page_title="Plabon — Flood Relief Assistant",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS 
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp { background-color: #0F172A; }

[data-testid="stSidebar"] {
    background-color: #1E293B;
    border-right: 1px solid #334155;
}

header[data-testid="stHeader"] {
    background-color: #0F172A;
    border-bottom: 1px solid #1E293B;
}

[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1px solid #334155;
    gap: 4px;
}
[data-testid="stTabs"] [role="tab"] {
    background-color: transparent;
    border: 1px solid #334155;
    border-radius: 8px 8px 0 0;
    color: #64748B;
    font-size: 14px;
    font-weight: 500;
    padding: 8px 20px;
    transition: all 0.2s;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    background-color: #1E293B;
    border-bottom-color: #1E293B;
    color: #F1F5F9;
}
[data-testid="stTabs"] [role="tab"]:hover {
    color: #F1F5F9;
    background-color: #1E293B;
}

[data-testid="stChatMessage"] {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 4px;
    margin-bottom: 8px;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background-color: #1e3a5f;
    border-color: #2563EB;
}

[data-testid="stChatInput"] textarea {
    background-color: #1E293B !important;
    border: 1px solid #334155 !important;
    border-radius: 12px !important;
    color: #F1F5F9 !important;
    font-family: 'Inter', sans-serif !important;
}

.stButton > button {
    background-color: #1E40AF;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-family: 'Inter', sans-serif;
    font-weight: 500;
    transition: background-color 0.2s;
}
.stButton > button:hover {
    background-color: #2563EB;
    border: none;
}

.web-badge {
    display: inline-block;
    background-color: #064E3B;
    color: #34D399;
    border: 1px solid #065F46;
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.05em;
    margin-bottom: 10px;
}

.disclaimer {
    background-color: #1c1408;
    border: 1px solid #78350F;
    border-left: 4px solid #F59E0B;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 12px;
    color: #FCD34D;
    margin-top: 8px;
}

.divider {
    border: none;
    border-top: 1px solid #334155;
    margin: 16px 0;
}

.sidebar-heading {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #64748B;
    margin: 20px 0 8px 0;
}

.map-placeholder {
    background-color: #1E293B;
    border: 2px dashed #334155;
    border-radius: 16px;
    padding: 80px 40px;
    text-align: center;
    margin-top: 24px;
}
            
.live-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #0f2a0f;
    color: #22c55e;
    border: 1px solid #166534;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.05em;
    animation: pulse-live 2s infinite;
}

.live-badge.degraded {
    background: #1c1407;
    color: #f59e0b;
    border-color: #92400e;
}
            
@keyframes pulse-live {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.55; }
}

.source-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 3px 10px;
    font-size: 11px;
    color: #94A3B8;
    margin-right: 6px;
}

</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []


# ── Lazy pipeline loader ──────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_pipeline():
    from src.pipeline import run_pipeline
    return run_pipeline


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    logo_path = Path("assets/asdma-logo.png")
    if logo_path.exists():
        col_logo, col_title = st.columns([1, 2.5])
        with col_logo:
            st.image(str(logo_path), width=80)
        with col_title:
            st.markdown("""
                <div style="padding-top:6px;">
                    <div style="font-size:20px;font-weight:700;color:#F1F5F9;letter-spacing:-0.5px;">Plabon (প্লাৱন)</div>
                    <div style="font-size:14px;color:#F8FAFC;">· Flood Relief Assistant</div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style="display:flex;align-items:center;gap:12px;padding:8px 0 16px 0;">
                <div style="font-size:36px;">🌊</div>
                <div>
                    <div style="font-size:22px;font-weight:700;color:#F1F5F9;letter-spacing:-0.5px;">Plabon</div>
                    <div style="font-size:12px;color:#64748B;">প্লাৱন · Flood Relief Assistant</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-heading">About</div>', unsafe_allow_html=True)
    st.markdown("""
        <div style="font-size:13px;color:#CBD5E1;line-height:1.6;">
            Plabon is a flood and disaster relief assistant for Assam, trained on
            official government documents. It automatically checks live government
            data when your question involves current conditions.
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-heading">What it covers</div>', unsafe_allow_html=True)
    st.markdown("""
        <div style="font-size:13px;color:#CBD5E1;line-height:1.9;">
            🏛️ Official government sources only<br>
            🌊 Floods, cyclones, earthquakes & landslides<br>
            📍 Specific to Assam & Northeast India<br>
            ⚡ Cross-checks live data when needed
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-heading">Live Data Sources</div>', unsafe_allow_html=True)
    st.markdown("""
        <div style="font-size:13px;color:#CBD5E1;line-height:1.8;">
            🌦️ Open-Meteo — live rainfall (hourly)<br>
            🌊 Open-Meteo Flood API — river discharge (GloFAS)<br>
            🌐 asdma.assam.gov.in<br>
            🌐 ndma.gov.in<br>
            🌐 cwc.gov.in<br>
            🌐 mausam.imd.gov.in
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("""
        <div class="disclaimer">
            ⚠️ For life-threatening emergencies, call <strong>112</strong> immediately.
            This assistant provides guidance based on official SOPs and may not reflect
            real-time conditions on the ground.
        </div>
    """, unsafe_allow_html=True)



tab_map, tab_chat = st.tabs(["🗺️  Live Flood Map", "💬  Chat Assistant"])

with tab_map:
    from src.map.gauge_data import get_current_levels, get_24h_history, get_data_source_status
    from src.map.flood_map import build_map
    from src.map.chart import build_status_chart, build_trend_chart
    from src.map.alert_log import record_snapshot, get_recent_events
    from streamlit_folium import st_folium

    try:
        from streamlit_autorefresh import st_autorefresh
        _AUTOREFRESH_AVAILABLE = True
    except ImportError:
        _AUTOREFRESH_AVAILABLE = False

    if "selected_station" not in st.session_state:
        st.session_state.selected_station = "tezpur"
    if "map_last_updated" not in st.session_state:
        st.session_state.map_last_updated = datetime.now()
    if "refresh_interval_s" not in st.session_state:
        st.session_state.refresh_interval_s = 60

    if _AUTOREFRESH_AVAILABLE:
        st_autorefresh(interval=st.session_state.refresh_interval_s * 1000, key="map_autorefresh")

    col_hdr, col_actions = st.columns([3, 2])
    with col_hdr:
        seconds_until_next = max(
            st.session_state.refresh_interval_s
            - int((datetime.now() - st.session_state.map_last_updated).total_seconds()),
            0,
        )
        countdown_id = "countdown-timer"
        st.markdown(f"""
            <div style="padding:8px 0 12px 0;">
                <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
                    <span style="font-size:26px;font-weight:700;color:#F1F5F9;letter-spacing:-0.5px;">
                        Live Flood Situational Map
                    </span>
                    <span class="live-badge">⬤ LIVE</span>
                </div>
                <p style="font-size:13px;color:#94A3B8;margin:5px 0 0 0;">
                    Brahmaputra basin · Assam gauge network · Next refresh in
                    <span id="{countdown_id}" style="color:#F1F5F9;font-weight:600;">{seconds_until_next}s</span>
                </p>
            </div>
            <script>
                (function() {{
                    let remaining = {seconds_until_next};
                    const el = window.parent.document.getElementById("{countdown_id}");
                    if (!el) return;
                    const tick = () => {{
                        remaining = Math.max(remaining - 1, 0);
                        el.textContent = remaining + "s";
                        if (remaining > 0) setTimeout(tick, 1000);
                    }};
                    setTimeout(tick, 1000);
                }})();
            </script>
        """, unsafe_allow_html=True)

    with col_actions:
        st.markdown("<div style='padding-top:22px'>", unsafe_allow_html=True)
        col_btn, col_sel = st.columns([1, 2])
        with col_btn:
            if st.button("🔄 Refresh", use_container_width=True):
                get_current_levels.clear()
                st.session_state.map_last_updated = datetime.now()
                st.rerun()
        with col_sel:
            _preview = get_current_levels()
            station_opts = {sid: f"{s['name']} ({s['river']})" for sid, s in _preview.items()}
            sel_key = st.selectbox(
                "Focus station",
                options=list(station_opts.keys()),
                format_func=lambda x: station_opts[x],
                index=list(station_opts.keys()).index(st.session_state.selected_station),
                label_visibility="collapsed",
            )
            if sel_key != st.session_state.selected_station:
                st.session_state.selected_station = sel_key
        st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("⚙️ Refresh settings & live data status", expanded=False):
        col_r1, col_r2 = st.columns([2, 3])
        with col_r1:
            interval_label = st.radio(
                "Auto-refresh every",
                options=["1 min", "5 min", "15 min"],
                index=["1 min", "5 min", "15 min"].index(
                    {60: "1 min", 300: "5 min", 900: "15 min"}.get(st.session_state.refresh_interval_s, "1 min")
                ),
                horizontal=True,
            )
            new_interval = {"1 min": 60, "5 min": 300, "15 min": 900}[interval_label]
            if new_interval != st.session_state.refresh_interval_s:
                st.session_state.refresh_interval_s = new_interval
                st.rerun()
        with col_r2:
            status = get_data_source_status()
            if status["open_meteo_ok"]:
                st.markdown('<span class="source-pill">🟢 Open-Meteo reachable</span>'
                            '<span class="source-pill">🌦️ Rainfall: live</span>'
                            '<span class="source-pill">🌊 Discharge: live (GloFAS)</span>',
                            unsafe_allow_html=True)
            else:
                st.markdown('<span class="source-pill">🟡 Open-Meteo unreachable — showing last cached values</span>',
                            unsafe_allow_html=True)
        if not _AUTOREFRESH_AVAILABLE:
            st.caption("Install `streamlit-autorefresh` (pip install streamlit-autorefresh) to enable timer-based auto-refresh. Manual refresh button still works without it.")

    current_data = get_current_levels()
    new_alert_events = record_snapshot(current_data)
    if new_alert_events:
        for ev in new_alert_events:
            icon = "🔺" if ev["direction"] == "ESCALATION" else "🔻"
            (st.warning if ev["direction"] == "ESCALATION" else st.success)(
                f"{icon} **{ev['station_name']}** ({ev['river']}) moved from "
                f"{ev['from_alert']} → **{ev['to_alert']}**"
            )

    counts: dict[str, int] = {"NORMAL": 0, "WARNING": 0, "DANGER": 0, "EXTREME": 0}
    for s in current_data.values():
        counts[s["alert"]] += 1

    c1, c2, c3, c4 = st.columns(4)
    card_meta = {
        "NORMAL":  ("🟢", "#0f2a0f", "#166534", "#22c55e", "#4ade80"),
        "WARNING": ("🟡", "#1c1407", "#92400e", "#f59e0b", "#fbbf24"),
        "DANGER":  ("🔴", "#1c0b0b", "#991b1b", "#ef4444", "#f87171"),
        "EXTREME": ("⚫", "#0a0505", "#4a0000", "#7f1d1d", "#b91c1c"),
    }
    for col, (level, (icon, bg, border, nc, lc)) in zip([c1, c2, c3, c4], card_meta.items()):
        with col:
            st.markdown(f"""<div style="background:{bg};border:1px solid {border};
                border-radius:10px;padding:14px;text-align:center">
                <div style="font-size:26px;font-weight:700;color:{nc}">{counts[level]}</div>
                <div style="font-size:11px;color:{lc};margin-top:3px;font-weight:600;
                    letter-spacing:.05em">{icon} {level}</div></div>""",
                unsafe_allow_html=True)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    col_map, col_panel = st.columns([5, 2])
    with col_map:
        m = build_map(current_data, selected_station_id=st.session_state.selected_station)
        map_data = st_folium(m, height=500, use_container_width=True,
                             returned_objects=["last_object_clicked_tooltip"])
        if map_data and map_data.get("last_object_clicked_tooltip"):
            tip = str(map_data["last_object_clicked_tooltip"])
            for sid, s in current_data.items():
                if s["name"] in tip:
                    if sid != st.session_state.selected_station:
                        st.session_state.selected_station = sid
                        st.rerun()
                    break

    with col_panel:
        st.markdown("""<div style="font-size:11px;font-weight:600;letter-spacing:.1em;
            text-transform:uppercase;color:#64748B;margin-bottom:10px">
            📍 Gauge Station Status</div>""", unsafe_allow_html=True)
        clrs = {
            "NORMAL":  ("#0f2a0f", "#166534", "#22c55e"),
            "WARNING": ("#1c1407", "#92400e", "#f59e0b"),
            "DANGER":  ("#1c0b0b", "#991b1b", "#ef4444"),
            "EXTREME": ("#0a0505", "#4a0000", "#7f1d1d"),
        }
        for sid, s in current_data.items():
            bg, border, txt = clrs[s["alert"]]
            sb = "#3B82F6" if sid == st.session_state.selected_station else border
            st.markdown(f"""<div style="background:{bg};border:1.5px solid {sb};
                border-radius:8px;padding:9px 12px;margin-bottom:6px;">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <div>
                        <div style="font-size:13px;font-weight:600;color:#F1F5F9">{s['name']}</div>
                        <div style="font-size:11px;color:#94A3B8">{s['river']}</div>
                    </div>
                    <div style="text-align:right">
                        <div style="font-size:12px;font-weight:700;color:{txt}">{s['alert']}</div>
                        <div style="font-size:11px;color:#94A3B8">{s['current_level']}m {s['trend']}</div>
                    </div>
                </div></div>""", unsafe_allow_html=True)

        recent_events = get_recent_events(limit=5)
        if recent_events:
            st.markdown("""<div style="font-size:11px;font-weight:600;letter-spacing:.1em;
                text-transform:uppercase;color:#64748B;margin:16px 0 8px 0">
                🔔 Recent Alert Activity</div>""", unsafe_allow_html=True)
            for ev in recent_events:
                arrow = "🔺" if ev["direction"] == "ESCALATION" else "🔻"
                arrow_color = "#ef4444" if ev["direction"] == "ESCALATION" else "#22c55e"
                ts = ev["timestamp"].split("T")[1] if "T" in ev["timestamp"] else ev["timestamp"]
                st.markdown(f"""<div style="font-size:11px;color:#CBD5E1;padding:5px 0;
                    border-bottom:1px solid #1E293B;">
                    <span style="color:{arrow_color}">{arrow}</span>
                    <strong>{ev['station_name']}</strong> {ev['from_alert']} → {ev['to_alert']}
                    <span style="color:#64748B;float:right">{ts}</span>
                    </div>""", unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.plotly_chart(build_status_chart(current_data), use_container_width=True,
                        config={"displayModeBar": False})
    with col_c2:
        sel = current_data[st.session_state.selected_station]
        hist = get_24h_history(
            st.session_state.selected_station,
            sel["current_level"], sel["warning_level"], sel["danger_level"],
        )
        st.plotly_chart(build_trend_chart(hist, sel["name"], sel["alert"]),
                        use_container_width=True, config={"displayModeBar": False})

    sel = current_data[st.session_state.selected_station]
    st.markdown(f"""<div style="font-size:11px;color:#94A3B8;text-align:center;padding:8px 0 4px 0;">
        ℹ️ Risk Index for <strong>{sel['name']}</strong> is calculated live from combined rainfall and river discharge data — not a direct gauge reading.
        </div>""", unsafe_allow_html=True)

with tab_chat:
    st.markdown("""
        <div style="padding: 8px 0 24px 0;">
            <h1 style="font-size:28px;font-weight:700;color:#F1F5F9;margin:0;letter-spacing:-0.5px;">
                Flood & Disaster Relief Assistant
            </h1>
            <p style="font-size:14px;color:#64748B;margin:6px 0 0 0;">
                Ask about flood preparedness, evacuation, relief operations, or current warnings across Assam.
            </p>
        </div>
    """, unsafe_allow_html=True)

    if "is_generating" not in st.session_state:
        st.session_state.is_generating = False
    if "pending_prompt" not in st.session_state:
        st.session_state.pending_prompt = None

    if not st.session_state.messages:
        st.markdown('<div class="sidebar-heading" style="margin-top:0;">Try asking</div>', unsafe_allow_html=True)

        suggestions = [
            "What should I keep in a flood emergency kit?",
            "What are the evacuation procedures during a flood?",
            "How are IMD flood warning colors classified?",
            "What is the danger level for Brahmaputra gauge stations?",
            "What relief is provided to flood-affected families?",
            "What should I do if trapped in a flooded area?",
        ]

        cols = st.columns(2)
        for i, suggestion in enumerate(suggestions):
            with cols[i % 2]:
                if st.button(suggestion, key=f"suggestion_{i}", use_container_width=True,
                             disabled=st.session_state.is_generating):
                    st.session_state.messages.append({"role": "user", "content": suggestion})
                    st.session_state.pending_prompt = suggestion
                    st.session_state.is_generating = True
                    st.rerun()

        st.markdown('<hr class="divider">', unsafe_allow_html=True)

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🌊"):
            if msg["role"] == "assistant" and msg.get("web_used"):
                st.markdown('<span class="web-badge">⚡ Live data included</span>', unsafe_allow_html=True)
            st.markdown(msg["content"])

    typed_prompt = st.chat_input(
        "Ask about floods, evacuation, relief, warnings...",
        disabled=st.session_state.is_generating,
    )
    if typed_prompt and not st.session_state.is_generating:
        st.session_state.messages.append({"role": "user", "content": typed_prompt})
        st.session_state.pending_prompt = typed_prompt
        st.session_state.is_generating = True
        st.rerun()

    if st.session_state.is_generating and st.session_state.pending_prompt:
        prompt = st.session_state.pending_prompt
        with st.chat_message("assistant", avatar="🌊"):
            with st.spinner("Searching knowledge base..."):
                try:
                    run_pipeline = load_pipeline()
                    result = run_pipeline(prompt)

                    if result["web_used"]:
                        st.markdown('<span class="web-badge">⚡ Live data included</span>', unsafe_allow_html=True)

                    st.markdown(result["answer"])

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result["answer"],
                        "web_used": result["web_used"],
                    })

                except Exception as e:
                    st.error(f"Pipeline error: {type(e).__name__}: {str(e)}")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "web_used": False,
                    })

                finally:
                    st.session_state.is_generating = False
                    st.session_state.pending_prompt = None
                    st.rerun()