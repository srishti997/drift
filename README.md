# 🧠 Drift — Human Observability Platform

> Most productivity tools track time. Drift tracks **intent**.

Drift is a behavioral intelligence system that runs silently in the background, watches what you're actually doing on your computer, and figures out *why* you're doing it — not just *what* app is open. It detects deep work, measures focus loss from context switching, infers your active mission, and generates a personalized AI coaching report at the end of the day.

---

## The Problem

Time trackers tell you that you spent 3 hours on Chrome. They don't tell you that you opened YouTube 7 times during a coding session, abandoned your mission twice, and only hit one real deep work block. Drift does.

---

## How It Works

```
Keystroke + Mouse Input (pynput)
        +
Active Window (win32gui + psutil)
        ↓
Activity Classifier → CODING / LEARNING / BROWSING / ENTERTAINMENT / IDLE
        ↓
Intent Engine → infers goal from window title keywords (e.g. "Building Drift", "Career Development")
        ↓
Mission Engine → maps goals to missions (Build Drift / Career Growth / Skill Development / Break)
        ↓
Behavior Analysis Engines:
  ├── Deep Work Engine     → detects 30+ min uninterrupted productive sessions
  ├── Context Switch Engine → tracks goal changes, flags distraction switches
  ├── Pattern Engine       → finds Mission Abandonment, Recovery, App Ping-Pong
  ├── Drift Engine         → calculates Drift Index (fragmentation score 0–100)
  └── Productivity Score Engine → weighted score: Focus (40%) + Mission (25%) + Recovery (20%) + Switch (15%)
        ↓
Coach Engine → generates observation/impact/suggestion advice cards
        ↓
Daily Report Engine → executive summary + timeline + recommendations
        ↓
Streamlit Dashboard → live visualization of all signals
```

---

## Features

### 🎯 Activity Intelligence
- Tracks active window, app name, keystrokes, and mouse clicks every 10 seconds
- Classifies activity into: `CODING`, `LEARNING`, `BROWSING`, `ENTERTAINMENT`, `COMMUNICATION`, `IDLE`
- Detects idle states automatically (zero keyboard + mouse input)

### 🧠 Intent & Mission Inference
- Infers user intent from window title keywords — e.g. `"tracker.py — VS Code"` → Intent: *Building Drift*, Goal: *Develop Drift platform*
- Maps goals to high-level missions: `Build Drift`, `Career Growth`, `Skill Development`, `Communication`, `Break / Distraction`
- Confidence-scored matching with fallback rules by activity type

### 📊 Drift Index
- Proprietary fragmentation score (0–100) combining distraction ratio, idle ratio, and context switch penalty
- `< 25` = Stable · `25–50` = Minor Drift · `50–75` = Significant · `75+` = Critical

### 🔬 Deep Work Detection
- Identifies continuous productive sessions ≥ 30 minutes with no distraction interruptions
- Tracks intent breakdown and app usage within each deep work block

### 🔁 Context Switch Analysis
- Detects every goal change in the activity stream
- Separates goal-aligned switches from distraction switches
- Estimates focus loss: 2 minutes per context switch

### 🕵️ Behavioral Pattern Recognition
- **Mission Abandonment** — left a productive mission mid-way
- **Mission Recovery** — returned to a productive mission after distraction
- **App Ping-Pong** — bounced between two apps more than 3 times

### 🤖 AI Coach
- Rule-based coaching engine that generates structured `observation → impact → suggestion` cards
- Triggers specific advice based on low deep work time, high distraction switches, abandonment patterns, and strong mission alignment
- No LLM dependency — fully local and deterministic

### 📋 Daily Report
- Executive summary of the day's work pattern
- Cognitive timeline: mission blocks with goal and app breakdown
- Actionable recommendations personalized to detected patterns

### 📈 Streamlit Dashboard
- Live productivity score with gauge chart (Plotly)
- Mission breakdown donut chart
- Cognitive timeline view
- AI Coach card panel
- Daily report with recommendations

---

## Tech Stack

| Layer | Technology |
|---|---|
| Activity Collection | `pynput`, `psutil`, `pywin32` |
| Backend API | `FastAPI`, `Pydantic` |
| Data Layer | JSON persistence |
| Visualization | `Streamlit`, `Plotly`, `Pandas` |
| Language | Python 3.10+ |

> ⚠️ **Windows only** — relies on `pywin32` (`win32gui`, `win32process`) for active window detection.

---

## Project Structure

```
drift/
├── agent/
│   ├── tracker.py            # Activity collection loop (every 10s)
│   └── app_classifier.py     # Rule-based app → activity type classifier
├── backend/
│   ├── main.py               # FastAPI app with all endpoints
│   ├── intent_engine.py      # Keyword-based intent + goal inference
│   ├── mission_engine.py     # Goal → Mission mapping
│   ├── drift_engine.py       # Drift Index calculation
│   ├── deep_work_engine.py   # Deep work session detection
│   ├── context_switch_engine.py  # Context switch + distraction analysis
│   ├── pattern_engine.py     # Behavioral pattern recognition
│   ├── productivity_score_engine.py  # Weighted productivity score
│   ├── coach_engine.py       # Rule-based AI coaching
│   ├── daily_report_engine.py # End-of-day report generation
│   ├── timeline_engine.py    # Cognitive timeline builder
│   ├── goal_engine.py        # Goal summary aggregation
│   ├── session_builder.py    # Session segmentation
│   └── storage.py            # JSON read/write
├── data/
│   └── activity_logs.json    # Persisted activity data
├── dashboard.py              # Streamlit dashboard
└── requirements.txt
```

---

## Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/srishti997/drift.git
cd drift
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Start the FastAPI backend
```bash
uvicorn backend.main:app --reload
```

### 4. Start the activity tracker (new terminal)
```bash
cd agent
python tracker.py
```

### 5. Open the dashboard (new terminal)
```bash
streamlit run dashboard.py
```

The dashboard will be live at `http://localhost:8501`. Let the tracker run for 10–15 minutes to collect enough data for meaningful analysis.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/activity` | Log a new activity event |
| `GET` | `/score` | Weighted productivity score |
| `GET` | `/drift` | Drift Index + focus score |
| `GET` | `/missions` | Mission breakdown |
| `GET` | `/intent` | Per-activity intent inference |
| `GET` | `/deep-work` | Deep work session analysis |
| `GET` | `/context-switches` | Context switch + distraction stats |
| `GET` | `/patterns` | Behavioral pattern detection |
| `GET` | `/timeline` | Cognitive timeline |
| `GET` | `/coach` | AI coaching advice |
| `GET` | `/daily-report` | Full daily report |

---

## Productivity Score Formula

```
Score = (Focus × 0.40) + (Mission × 0.25) + (Recovery × 0.20) + (Switch × 0.15)

Focus Score    → based on total deep work minutes (≥120 min = 100)
Mission Score  → based on top mission dominance percentage
Recovery Score → recovery count / (recovery + abandonment count)
Switch Score   → penalized by total context switches (0 = 100, >20 = 25)
```

Grades: `A+ (≥95)` · `A (≥85)` · `B (≥75)` · `C (≥65)` · `D (≥50)` · `F (<50)`

---

## Built By

Srishti Gupta · [GitHub](https://github.com/srishti997) · [LinkedIn](https://linkedin.com/in/srishtigupta997)