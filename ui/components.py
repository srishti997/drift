from html import escape
from typing import Literal, Optional

import streamlit as st


TrendType = Literal["positive", "negative", "neutral"]


def section_header(
    title: str,
    description: str = "",
    eyebrow: str = "",
) -> None:
    safe_title = escape(str(title))
    safe_description = escape(str(description))
    safe_eyebrow = escape(str(eyebrow))

    eyebrow_html = (
        f'<div class="drift-section-eyebrow">{safe_eyebrow}</div>'
        if safe_eyebrow
        else ""
    )

    description_html = (
        f'<div class="drift-section-description">{safe_description}</div>'
        if safe_description
        else ""
    )

    html = (
        '<div class="drift-section-header">'
        f"{eyebrow_html}"
        f'<h2 class="drift-section-title">{safe_title}</h2>'
        f"{description_html}"
        "</div>"
    )

    st.markdown(
        html,
        unsafe_allow_html=True,
    )


def metric_card(
    icon: str,
    title: str,
    value: str,
    subtitle: str = "",
    trend: str = "",
    trend_type: TrendType = "neutral",
    badge: str = "",
) -> None:
    safe_icon = escape(str(icon))
    safe_title = escape(str(title))
    safe_value = escape(str(value))
    safe_subtitle = escape(str(subtitle))
    safe_trend = escape(str(trend))
    safe_badge = escape(str(badge))

    if trend_type not in {
        "positive",
        "negative",
        "neutral",
    }:
        trend_type = "neutral"

    badge_html = (
        f'<div class="drift-metric-badge">{safe_badge}</div>'
        if safe_badge
        else ""
    )

    subtitle_html = (
        f'<div class="drift-metric-subtitle">{safe_subtitle}</div>'
        if safe_subtitle
        else ""
    )

    trend_html = (
        f'<div class="drift-metric-trend '
        f'drift-trend-{trend_type}">{safe_trend}</div>'
        if safe_trend
        else ""
    )

    html = (
        '<div class="drift-metric-card">'
        '<div class="drift-metric-top">'
        f'<div class="drift-metric-icon">{safe_icon}</div>'
        f"{badge_html}"
        "</div>"
        f'<div class="drift-metric-title">{safe_title}</div>'
        f'<div class="drift-metric-value">{safe_value}</div>'
        f"{subtitle_html}"
        f"{trend_html}"
        "</div>"
    )

    st.markdown(
        html,
        unsafe_allow_html=True,
    )


def recommendation_card(
    text: str,
    label: str = "Your next step",
    icon: str = "🎯",
) -> None:
    safe_text = escape(str(text))
    safe_label = escape(str(label))
    safe_icon = escape(str(icon))

    html = (
        '<div class="drift-recommendation">'
        f'<div class="drift-recommendation-icon">{safe_icon}</div>'
        "<div>"
        f'<div class="drift-recommendation-label">{safe_label}</div>'
        f'<div class="drift-recommendation-text">{safe_text}</div>'
        "</div>"
        "</div>"
    )

    st.markdown(
        html,
        unsafe_allow_html=True,
    )


def progress_card(
    title: str,
    current: float,
    target: float,
    display_value: str,
    caption: str = "",
    icon: str = "🎯",
) -> None:
    try:
        safe_target = max(float(target or 0), 0)
    except (TypeError, ValueError):
        safe_target = 0

    try:
        safe_current = max(float(current or 0), 0)
    except (TypeError, ValueError):
        safe_current = 0

    progress = (
        min(safe_current / safe_target, 1.0)
        if safe_target > 0
        else 0.0
    )

    with st.container(border=True):
        st.markdown(f"### {icon} {title}")
        st.markdown(f"## {display_value}")
        st.progress(progress)

        if caption:
            st.caption(caption)


def empty_state(
    title: str,
    message: str,
    icon: str = "🌱",
    action_label: Optional[str] = None,
    key: Optional[str] = None,
) -> bool:
    clicked = False

    with st.container(border=True):
        st.markdown(f"## {icon}")
        st.markdown(f"### {title}")
        st.write(message)

        if action_label:
            clicked = st.button(
                action_label,
                key=key,
                use_container_width=True,
            )

    return clicked