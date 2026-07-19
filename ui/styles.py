import streamlit as st


PRIMARY = "#6366F1"
SUCCESS = "#22C55E"
WARNING = "#F59E0B"
ERROR = "#EF4444"

BACKGROUND = "#070C16"
CARD = "#0E1626"
CARD_HOVER = "#111C30"

TEXT = "#F8FAFC"
MUTED = "#94A3B8"
SUBTLE = "#64748B"
BORDER = "rgba(148, 163, 184, 0.14)"


def apply_global_styles() -> None:
    st.markdown(
        f"""
<style>
/* Main application */
.stApp {{
    background:
        radial-gradient(
            circle at 70% -10%,
            rgba(99, 102, 241, 0.10),
            transparent 30%
        ),
        {BACKGROUND};
}}

/* Main content width and spacing */
.block-container {{
    max-width: 1420px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}}

/* Hide Streamlit header decoration */
[data-testid="stHeader"] {{
    background: transparent;
}}

/* General text */
html,
body,
[class*="css"] {{
    color: {TEXT};
}}

/* Native bordered containers */
[data-testid="stVerticalBlockBorderWrapper"] {{
    background: rgba(14, 22, 38, 0.82);
    border: 1px solid {BORDER} !important;
    border-radius: 20px;
    box-shadow: 0 14px 40px rgba(0, 0, 0, 0.14);
    transition:
        transform 180ms ease,
        border-color 180ms ease,
        box-shadow 180ms ease;
}}

[data-testid="stVerticalBlockBorderWrapper"]:hover {{
    transform: translateY(-2px);
    border-color: rgba(99, 102, 241, 0.30) !important;
    box-shadow: 0 18px 48px rgba(0, 0, 0, 0.20);
}}

/* Streamlit metrics */
[data-testid="stMetric"] {{
    background: transparent;
}}

[data-testid="stMetricLabel"] {{
    color: {MUTED};
    font-size: 0.78rem;
}}

[data-testid="stMetricValue"] {{
    color: {TEXT};
    font-weight: 800;
    letter-spacing: -0.04em;
}}

/* Progress bars */
[data-testid="stProgress"] > div > div {{
    background: rgba(51, 65, 85, 0.60);
    border-radius: 999px;
}}

[data-testid="stProgress"] > div > div > div {{
    background: linear-gradient(
        90deg,
        {PRIMARY},
        #818CF8
    );
    border-radius: 999px;
}}

/* Buttons */
.stButton > button {{
    width: 100%;
    min-height: 44px;

    color: {TEXT};
    font-weight: 700;

    background: rgba(99, 102, 241, 0.12);
    border: 1px solid rgba(99, 102, 241, 0.28);
    border-radius: 14px;

    transition:
        transform 160ms ease,
        background 160ms ease,
        border-color 160ms ease;
}}

.stButton > button:hover {{
    transform: translateY(-1px);
    color: white;
    background: rgba(99, 102, 241, 0.22);
    border-color: rgba(129, 140, 248, 0.55);
}}

/* Expanders */
[data-testid="stExpander"] {{
    background: rgba(15, 23, 42, 0.40);
    border: 1px solid {BORDER};
    border-radius: 14px;
    overflow: hidden;
}}

/* Alerts */
[data-testid="stAlert"] {{
    border-radius: 16px;
}}

/* Section headings */
.drift-section-header {{
    margin-top: 18px;
    margin-bottom: 16px;
}}

.drift-section-eyebrow {{
    margin-bottom: 6px;

    color: #818CF8;
    font-size: 0.69rem;
    font-weight: 800;
    letter-spacing: 0.13em;
    text-transform: uppercase;
}}

.drift-section-title {{
    margin: 0;

    color: {TEXT};
    font-size: 1.55rem;
    font-weight: 800;
    letter-spacing: -0.025em;
}}

.drift-section-description {{
    max-width: 760px;
    margin-top: 7px;

    color: {MUTED};
    font-size: 0.88rem;
    line-height: 1.6;
}}

/* Metric cards */
.drift-metric-card {{
    position: relative;
    min-height: 190px;
    padding: 22px;

    background:
        radial-gradient(
            circle at 95% 0%,
            rgba(99, 102, 241, 0.10),
            transparent 38%
        ),
        linear-gradient(
            145deg,
            rgba(17, 28, 48, 0.92),
            rgba(12, 20, 35, 0.96)
        );

    border: 1px solid {BORDER};
    border-radius: 20px;

    box-shadow: 0 14px 38px rgba(0, 0, 0, 0.15);

    transition:
        transform 180ms ease,
        border-color 180ms ease,
        box-shadow 180ms ease;
}}

.drift-metric-card:hover {{
    transform: translateY(-3px);
    border-color: rgba(99, 102, 241, 0.34);
    box-shadow: 0 20px 48px rgba(0, 0, 0, 0.22);
}}

.drift-metric-top {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
}}

.drift-metric-icon {{
    display: flex;
    align-items: center;
    justify-content: center;

    width: 42px;
    height: 42px;

    font-size: 1.18rem;

    background: rgba(99, 102, 241, 0.12);
    border: 1px solid rgba(99, 102, 241, 0.20);
    border-radius: 13px;
}}

.drift-metric-badge {{
    padding: 5px 9px;

    color: #A5B4FC;
    font-size: 0.68rem;
    font-weight: 800;

    background: rgba(99, 102, 241, 0.10);
    border: 1px solid rgba(99, 102, 241, 0.20);
    border-radius: 999px;
}}

.drift-metric-title {{
    margin-top: 18px;

    color: {MUTED};
    font-size: 0.78rem;
    font-weight: 750;
}}

.drift-metric-value {{
    margin-top: 5px;

    color: {TEXT};
    font-size: 2rem;
    font-weight: 850;
    letter-spacing: -0.045em;
}}

.drift-metric-subtitle {{
    margin-top: 10px;

    color: {SUBTLE};
    font-size: 0.76rem;
    line-height: 1.55;
}}

.drift-metric-trend {{
    margin-top: 14px;

    font-size: 0.75rem;
    font-weight: 750;
}}

.drift-trend-positive {{
    color: {SUCCESS};
}}

.drift-trend-negative {{
    color: {ERROR};
}}

.drift-trend-neutral {{
    color: {MUTED};
}}

/* Recommendation card */
.drift-recommendation {{
    display: flex;
    align-items: flex-start;
    gap: 14px;

    padding: 18px 20px;
    margin: 10px 0 24px;

    background:
        linear-gradient(
            135deg,
            rgba(59, 130, 246, 0.15),
            rgba(99, 102, 241, 0.08)
        );

    border: 1px solid rgba(96, 165, 250, 0.24);
    border-radius: 17px;
}}

.drift-recommendation-icon {{
    font-size: 1.05rem;
}}

.drift-recommendation-label {{
    margin-bottom: 4px;

    color: #93C5FD;
    font-size: 0.69rem;
    font-weight: 800;
    letter-spacing: 0.09em;
    text-transform: uppercase;
}}

.drift-recommendation-text {{
    color: #DBEAFE;
    font-size: 0.88rem;
    line-height: 1.55;
}}

/* Responsive */
@media (max-width: 800px) {{
    .block-container {{
        padding-left: 1rem;
        padding-right: 1rem;
    }}

    .drift-metric-card {{
        min-height: auto;
    }}
}}
</style>
        """,
        unsafe_allow_html=True,
    )