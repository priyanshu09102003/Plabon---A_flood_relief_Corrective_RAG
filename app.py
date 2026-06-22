"""
Plabon — Corrective RAG Flood Relief Assistant
Professional Streamlit UI (Phase 9 + Phase 11 tabs)
"""

from pathlib import Path
import streamlit as st

st.set_page_config(
    page_title="Plabon — Flood Relief Assistant",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
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
        <div style="font-size:13px;color:#94A3B8;line-height:1.6;">
            Plabon is a flood and disaster relief assistant for Assam, trained on
            official government documents. It automatically checks live government
            data when your question involves current conditions.
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-heading">What it covers</div>', unsafe_allow_html=True)
    st.markdown("""
        <div style="font-size:13px;color:#94A3B8;line-height:1.9;">
            🏛️ Official government sources only<br>
            🌊 Floods, cyclones, earthquakes & landslides<br>
            📍 Specific to Assam & Northeast India<br>
            ⚡ Cross-checks live data when needed
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-heading">Live Data Sources</div>', unsafe_allow_html=True)
    st.markdown("""
        <div style="font-size:13px;color:#94A3B8;line-height:1.8;">
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


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_map, tab_chat = st.tabs(["🗺️  Live Flood Map", "💬  Chat Assistant"])

with tab_map:
    st.markdown("""
        <div style="padding: 8px 0 24px 0;">
            <h1 style="font-size:28px;font-weight:700;color:#F1F5F9;margin:0;letter-spacing:-0.5px;">
                Live Flood Situational Map
            </h1>
            <p style="font-size:14px;color:#64748B;margin:6px 0 0 0;">
                Real-time Assam flood map — district drill-down, gauge station water levels, and satellite imagery.
            </p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="map-placeholder">
            <div style="font-size:48px;margin-bottom:16px;">🗺️</div>
            <div style="font-size:20px;font-weight:600;color:#F1F5F9;margin-bottom:8px;">
                Live Map — Under Development
            </div>
            <div style="font-size:14px;color:#64748B;max-width:480px;margin:0 auto;line-height:1.7;">
                This view will show a real-time interactive map of Assam with district-level
                flood alerts, Brahmaputra gauge station water levels, IMD satellite imagery,
                and live rising water graphs. Click any district to drill down.
            </div>
        </div>
    """, unsafe_allow_html=True)

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
                if st.button(suggestion, key=f"suggestion_{i}", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": suggestion})
                    st.rerun()

        st.markdown('<hr class="divider">', unsafe_allow_html=True)

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🌊"):
            if msg["role"] == "assistant" and msg.get("web_used"):
                st.markdown('<span class="web-badge">⚡ Live data included</span>', unsafe_allow_html=True)
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about floods, evacuation, relief, warnings..."):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user", avatar="🧑"):
            st.markdown(prompt)

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
                    error_msg = (
                        "I encountered an issue processing your request. "
                        "Please try again, or contact emergency services directly.\n\n"
                        "**Emergency helpline: 112**"
                    )
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "web_used": False,
                    })