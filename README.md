# Drift

## Human Observability Platform

Drift is an AI-powered behavioral intelligence system that analyzes digital activity to understand how people work, learn, and focus.

Instead of only tracking time, Drift infers user intent, detects context switching, identifies deep work sessions, measures productivity, and generates personalized coaching insights.

---

## Key Capabilities

### Activity Intelligence
- Activity Tracking
- Session Building
- Persistent Activity Storage

### Behavioral Understanding
- Intent Inference
- Goal Detection
- Mission Detection
- Context Switch Analysis
- Cognitive Timeline Generation

### Productivity Analytics
- Deep Work Detection
- Productivity Scoring
- Behavioral Pattern Detection
- Mission Recovery & Abandonment Analysis

### AI Insights
- Daily Productivity Reports
- Personalized AI Coach Recommendations

### Visualization
- Streamlit Dashboard
- Mission Breakdown
- Focus Analytics
- Cognitive Timeline View

---

## Tech Stack

### Backend
- Python
- FastAPI
- Pydantic

### Activity Collection
- pynput
- psutil
- pywin32

### Data Layer
- JSON Persistence Layer

### Visualization
- Streamlit
- Plotly
- Pandas

---

## Architecture

```text
Activity Tracker
       ↓
FastAPI Backend
       ↓
Behavior Analysis Engines
       ↓
Productivity Intelligence Layer
       ↓
AI Coach
       ↓
Streamlit Dashboard