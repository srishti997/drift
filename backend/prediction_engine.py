from backend.context_switch_engine import analyze_context_switches
from backend.deep_work_engine import build_deep_work_summary
from backend.mission_engine import infer_mission_for_log
from backend.pattern_engine import detect_behavior_patterns


RISKY_MISSIONS = {
    "Break / Distraction",
    "Unclassified Mission",
}

PRODUCTIVE_MISSIONS = {
    "Build Drift",
    "Career Growth",
    "Skill Development",
}


def predict_drift_risk(activity_logs):
    if len(activity_logs) < 3:
        return {
            "risk_score": 0,
            "risk_level": "LOW",
            "success_probability": 1.0,
            "primary_risk": "Not enough activity data",
            "prediction": "Keep collecting activity data.",
            "confidence": 0.2,
        }

    latest = activity_logs[-1]
    latest_mission = infer_mission_for_log(latest)["mission"]

    recent_logs = activity_logs[-10:]
    recent_missions = [
        infer_mission_for_log(log)["mission"]
        for log in recent_logs
    ]

    switches = analyze_context_switches(recent_logs)
    patterns = detect_behavior_patterns(recent_logs)
    deep_work = build_deep_work_summary(activity_logs)

    risk_score = 0
    risk_reasons = []

    if latest_mission in RISKY_MISSIONS:
        risk_score += 35
        risk_reasons.append("Current activity is not aligned with a productive mission.")

    if switches["total_switches"] >= 5:
        risk_score += 25
        risk_reasons.append("High context switching detected in recent activity.")

    if switches["distraction_switches"] >= 2:
        risk_score += 25
        risk_reasons.append("Multiple distraction switches detected.")

    if _has_mission_abandonment(patterns):
        risk_score += 20
        risk_reasons.append("Recent behavior resembles mission abandonment.")

    if _has_app_ping_pong(patterns):
        risk_score += 15
        risk_reasons.append("Repeated app ping-pong detected.")

    if deep_work["total_deep_work_minutes"] < 30:
        risk_score += 10
        risk_reasons.append("No meaningful deep work block detected yet.")

    if _recent_productive_recovery(recent_missions):
        risk_score -= 15
        risk_reasons.append("Recent recovery back to productive mission detected.")

    risk_score = max(0, min(100, risk_score))
    success_probability = round((100 - risk_score) / 100, 2)

    if risk_score >= 75:
        risk_level = "CRITICAL"
    elif risk_score >= 55:
        risk_level = "HIGH"
    elif risk_score >= 30:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    primary_risk = risk_reasons[0] if risk_reasons else "No major risk detected."

    prediction = _build_prediction(
        risk_level,
        latest_mission,
        success_probability
    )

    confidence = _calculate_confidence(len(activity_logs), len(risk_reasons))

    return {
        "current_mission": latest_mission,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "success_probability": success_probability,
        "primary_risk": primary_risk,
        "risk_reasons": risk_reasons,
        "prediction": prediction,
        "confidence": confidence,
    }


def _has_mission_abandonment(patterns):
    for pattern in patterns.get("patterns", []):
        if pattern.get("type") == "Mission Abandonment":
            return True
    return False


def _has_app_ping_pong(patterns):
    for pattern in patterns.get("patterns", []):
        if pattern.get("type") == "App Ping-Pong":
            return True
    return False


def _recent_productive_recovery(recent_missions):
    if len(recent_missions) < 3:
        return False

    for i in range(len(recent_missions) - 2):
        if (
            recent_missions[i] in PRODUCTIVE_MISSIONS
            and recent_missions[i] == recent_missions[i + 2]
            and recent_missions[i + 1] in RISKY_MISSIONS
        ):
            return True

    return False


def _calculate_confidence(total_logs, risk_reason_count):
    base = min(total_logs / 50, 1.0)
    reason_strength = min(risk_reason_count / 5, 1.0)

    confidence = (0.6 * base) + (0.4 * reason_strength)

    return round(confidence, 2)


def _build_prediction(risk_level, latest_mission, success_probability):
    if risk_level == "CRITICAL":
        return (
            f"Your current work pattern is highly unstable. "
            f"There is a high chance you will drift away from '{latest_mission}'."
        )

    if risk_level == "HIGH":
        return (
            f"You are at risk of losing focus on '{latest_mission}'. "
            f"Success probability is around {int(success_probability * 100)}%."
        )

    if risk_level == "MEDIUM":
        return (
            f"Some drift signals are present, but your mission is still recoverable."
        )

    return (
        f"Your current pattern looks stable. Continue protecting your focus."
    )