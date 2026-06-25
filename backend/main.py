from datetime import datetime
from typing import List

from fastapi import FastAPI
from pydantic import BaseModel

from backend.storage import load_activity_logs, save_activity_logs

from backend.drift_engine import calculate_drift_metrics
from backend.session_builder import build_sessions
from backend.intent_engine import infer_intent
from backend.goal_engine import build_goal_summary
from backend.context_switch_engine import analyze_context_switches
from backend.mission_engine import build_mission_summary
from backend.timeline_engine import build_timeline
from backend.pattern_engine import detect_behavior_patterns
from backend.deep_work_engine import build_deep_work_summary
from backend.productivity_score_engine import build_productivity_score
from backend.daily_report_engine import build_daily_report
from backend.coach_engine import build_coach_advice
from backend.alert_engine import analyze_for_alerts
from backend.prediction_engine import predict_drift_risk
from backend.behavior_graph_engine import build_behavior_graph
from backend.loop_detector_engine import detect_behavior_loops, get_next_app_prediction
from backend.recovery_cost_engine import calculate_recovery_cost
from backend.autopsy_engine import build_mission_autopsy
app = FastAPI(title="Drift API")


class ActivityLog(BaseModel):
    app_name: str
    window_title: str
    activity_type: str
    start_time: datetime
    end_time: datetime
    duration_seconds: int
    key_count: int
    mouse_count: int


activity_logs = load_activity_logs(ActivityLog)


@app.get("/")
def root():
    return {"message": "Drift API is running"}





@app.get("/activity", response_model=List[ActivityLog])
def get_activity():
    return activity_logs


@app.get("/summary")
def get_summary():
    total_time = sum(log.duration_seconds for log in activity_logs)

    return {
        "total_tracked_seconds": total_time,
        "context_switches": len(activity_logs),
        "total_keyboard_events": sum(log.key_count for log in activity_logs),
        "total_mouse_events": sum(log.mouse_count for log in activity_logs),
    }


@app.get("/sessions")
def get_sessions():
    return build_sessions(activity_logs)


@app.get("/drift")
def get_drift():
    return calculate_drift_metrics(activity_logs)


@app.get("/intent")
def get_intents():
    results = []

    for log in activity_logs:
        intent_data = infer_intent(
            log.app_name,
            log.window_title,
            log.activity_type
        )

        results.append({
            "app_name": log.app_name,
            "window_title": log.window_title,
            "activity_type": log.activity_type,
            "duration_seconds": log.duration_seconds,
            "intent": intent_data["intent"],
            "goal": intent_data["goal"],
            "confidence": intent_data["confidence"]
        })

    return results


@app.get("/goals")
def get_goals():
    return build_goal_summary(activity_logs)


@app.get("/context-switches")
def get_context_switches():
    return analyze_context_switches(activity_logs)


@app.get("/missions")
def get_missions():
    return build_mission_summary(activity_logs)


@app.get("/timeline")
def get_timeline():
    return build_timeline(activity_logs)


@app.get("/patterns")
def get_patterns():
    return detect_behavior_patterns(activity_logs)


@app.get("/deep-work")
def get_deep_work():
    return build_deep_work_summary(activity_logs)


@app.get("/score")
def get_score():
    return build_productivity_score(activity_logs)


@app.get("/daily-report")
def get_daily_report():
    return build_daily_report(activity_logs)


@app.get("/coach")
def get_coach():
    return build_coach_advice(activity_logs)

@app.post("/activity")
def create_activity(log: ActivityLog):
    activity_logs.append(log)

    save_activity_logs(activity_logs)

    analyze_for_alerts(activity_logs)

    return {
        "message": "activity saved",
        "total_logs": len(activity_logs)
    }

@app.get("/predict")
def get_prediction():
    return predict_drift_risk(activity_logs)

@app.get("/behavior-graph")
def get_behavior_graph():
    return build_behavior_graph(activity_logs)

@app.get("/loops")
def get_loops():
    return detect_behavior_loops(activity_logs)


@app.get("/next-app")
def get_next_app():
    return get_next_app_prediction(activity_logs)

@app.get("/recovery-cost")
def get_recovery_cost():
    return calculate_recovery_cost(activity_logs)

@app.get("/autopsy")
def get_autopsy():
    return build_mission_autopsy(activity_logs)