from datetime import datetime
from typing import List

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from backend.alert_engine import analyze_for_alerts
from backend.autopsy_engine import build_mission_autopsy
from backend.behavior_graph_engine import build_behavior_graph
from backend.chat_engine import answer_user_question
from backend.coach_engine import build_coach_advice
from backend.context_switch_engine import analyze_context_switches
from backend.daily_report_engine import build_daily_report
from backend.deep_work_engine import build_deep_work_summary
from backend.drift_engine import calculate_drift_metrics
from backend.goal_engine import build_goal_summary
from backend.history_engine import build_history
from backend.intent_engine import infer_intent
from backend.loop_detector_engine import (
    detect_behavior_loops,
    get_next_app_prediction,
)
from backend.mission_engine import build_mission_summary
from backend.pattern_engine import detect_behavior_patterns
from backend.prediction_engine import predict_drift_risk
from backend.productivity_score_engine import build_productivity_score
from backend.recovery_cost_engine import calculate_recovery_cost
from backend.recovery_engine import build_recovery_summary
from backend.replay_engine import build_day_replay
from backend.session_builder import build_sessions
from backend.storage import load_activity_logs, save_activity_logs
from backend.target_engine import (
    evaluate_targets,
    load_targets,
    save_targets,
)
from backend.timeline_engine import build_timeline
from backend.weekly_engine import (
    build_weekly_habits,
    build_weekly_summary,
    build_weekly_trends,
)

app = FastAPI(
    title="Drift API",
    version="1.0.0",
    description="Human observability and productivity analytics API.",
)


class ActivityLog(BaseModel):
    app_name: str
    window_title: str
    activity_type: str
    start_time: datetime
    end_time: datetime
    duration_seconds: int = Field(ge=0)
    key_count: int = Field(default=0, ge=0)
    mouse_count: int = Field(default=0, ge=0)


class ChatRequest(BaseModel):
    question: str


class TargetRequest(BaseModel):
    deep_work_minutes: int = Field(ge=0, le=1440)
    max_context_switches: int = Field(ge=0)
    max_idle_minutes: int = Field(ge=0, le=1440)
    max_youtube_minutes: int = Field(ge=0, le=1440)


def load_saved_activity_logs() -> list[ActivityLog]:
    raw_logs = load_activity_logs()
    valid_logs: list[ActivityLog] = []

    for item in raw_logs:
        try:
            valid_logs.append(ActivityLog(**item))
        except Exception as error:
            print(f"Skipping invalid activity log: {error}")

    return valid_logs


activity_logs = load_saved_activity_logs()


@app.get("/")
def root():
    return {
        "message": "Drift API is running",
        "version": "1.0.0",
    }


@app.get("/history")
def get_history(
    days: int = Query(
        default=30,
        ge=1,
        le=365,
        description="Number of calendar days to include.",
    ),
):
    try:
        return build_history(days=days)

    except Exception as error:
        print(f"History endpoint error: {error}")

        raise HTTPException(
            status_code=500,
            detail="Unable to build historical analytics.",
        ) from error

@app.get("/weekly-summary")
def get_weekly_summary():
    try:
        return build_weekly_summary(activity_logs)

    except Exception as error:
        print(f"Weekly summary endpoint error: {error}")

        raise HTTPException(
            status_code=500,
            detail="Unable to build weekly summary.",
        ) from error


@app.get("/weekly-trends")
def get_weekly_trends():
    try:
        return build_weekly_trends(activity_logs)

    except Exception as error:
        print(f"Weekly trends endpoint error: {error}")

        raise HTTPException(
            status_code=500,
            detail="Unable to build weekly trends.",
        ) from error


@app.get("/weekly-habits")
def get_weekly_habits():
    try:
        return build_weekly_habits(activity_logs)

    except Exception as error:
        print(f"Weekly habits endpoint error: {error}")

        raise HTTPException(
            status_code=500,
            detail="Unable to build weekly habits.",
        ) from error
@app.post("/activity")
def create_activity(log: ActivityLog):
    activity_logs.append(log)

    try:
        save_activity_logs(activity_logs)
        analyze_for_alerts(activity_logs)
    except Exception as error:
        activity_logs.pop()

        raise HTTPException(
            status_code=500,
            detail="Unable to save activity.",
        ) from error

    return {
        "message": "Activity saved.",
        "total_logs": len(activity_logs),
    }


@app.get("/activity", response_model=List[ActivityLog])
def get_activity():
    return activity_logs


@app.get("/summary")
def get_summary():
    total_time = sum(
        log.duration_seconds
        for log in activity_logs
    )

    context_switches = 0
    previous_app = None

    for log in activity_logs:
        current_app = log.app_name.strip().lower()

        if (
            previous_app is not None
            and current_app != previous_app
        ):
            context_switches += 1

        previous_app = current_app

    return {
        "total_tracked_seconds": total_time,
        "context_switches": context_switches,
        "total_keyboard_events": sum(
            log.key_count
            for log in activity_logs
        ),
        "total_mouse_events": sum(
            log.mouse_count
            for log in activity_logs
        ),
        "total_logs": len(activity_logs),
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
            log.activity_type,
        )

        results.append(
            {
                "app_name": log.app_name,
                "window_title": log.window_title,
                "activity_type": log.activity_type,
                "duration_seconds": log.duration_seconds,
                "intent": intent_data["intent"],
                "goal": intent_data["goal"],
                "confidence": intent_data["confidence"],
            }
        )

    return results


@app.get("/goals")
def get_goals():
    """
    Return goals inferred automatically from activity.

    This is different from /user-goals, which contains
    productivity targets configured by the user.
    """
    return build_goal_summary(activity_logs)


@app.get("/user-goals")
def get_user_goals():
    return load_targets()


@app.post("/user-goals")
def update_user_goals(request: TargetRequest):
    try:
        targets = save_targets(request.model_dump())

        return {
            "message": "Targets updated successfully.",
            "targets": targets,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Unable to save productivity targets.",
        ) from error


@app.get("/goal-progress")
def get_goal_progress():
    try:
        return evaluate_targets(activity_logs)

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Unable to evaluate productivity targets.",
        ) from error


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


@app.get("/recovery")
def get_recovery():
    return build_recovery_summary(activity_logs)


@app.get("/autopsy")
def get_autopsy():
    return build_mission_autopsy(activity_logs)


@app.post("/chat")
def chat(request: ChatRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Please enter a productivity question.",
        )

    try:
        return answer_user_question(
            question,
            activity_logs,
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Unable to generate a coaching response.",
        ) from error


@app.get("/replay")
def get_replay():
    return build_day_replay(activity_logs)