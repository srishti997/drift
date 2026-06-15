from datetime import datetime
from typing import List

from fastapi import FastAPI
from pydantic import BaseModel
from backend.drift_engine import calculate_drift_metrics

from backend.session_builder import build_sessions


app = FastAPI(title="Drift API")

activity_logs = []


class ActivityLog(BaseModel):
    app_name: str
    window_title: str
    activity_type: str
    start_time: datetime
    end_time: datetime
    duration_seconds: int
    key_count: int
    mouse_count: int


@app.get("/")
def root():
    return {"message": "Drift API is running"}


@app.post("/activity")
def create_activity(log: ActivityLog):
    activity_logs.append(log)
    return {"message": "activity saved"}


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