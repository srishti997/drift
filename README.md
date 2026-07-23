# 🧠 Drift — Human Observability Platform

> **Most productivity tools measure time. Drift measures attention, intent, and behavior.**

Drift is an AI-inspired behavioral intelligence platform that observes desktop activity, understands what you're trying to accomplish, identifies how your attention changes throughout the day, and converts raw activity into actionable productivity insights.

Instead of simply telling you **how long** you spent in an application, Drift explains **why your focus shifted**, **where productivity was lost**, and **how you can improve tomorrow**.

---

#  Why Drift?

Traditional productivity tools answer questions like:

- How much time did I spend on Chrome?
- How long was VS Code open?
- How many hours did I work?

Drift answers questions that are far more meaningful:

- Was I actually focused?
- What interrupted my work?
- Did I recover after distractions?
- How many deep work sessions did I complete?
- Which mission dominated my day?
- What behavioral patterns reduced my productivity?

Drift transforms passive activity logs into behavioral intelligence.

---

#  Key Highlights

- 🧠 Intent-aware productivity tracking
- 📊 Real-time desktop activity monitoring
- 🎯 Goal and mission inference
- 🔥 Deep work detection
- 🔄 Context switch analysis
- 🧩 Behavioral pattern recognition
- 🤖 AI-powered coaching engine
- 📋 Executive daily productivity reports
- 📈 Interactive analytics dashboard

---

#  System Architecture

```
Keyboard + Mouse
        │
Active Window Detection
        │
        ▼
Activity Collection Layer
(pynput • psutil • pywin32)
        │
        ▼
Activity Classification
(Coding • Learning • Browsing • Communication • Idle)
        │
        ▼
Intent Engine
        │
        ▼
Mission Engine
        │
        ├──────────────┐
        │              │
        ▼              ▼
Deep Work        Context Switching
Engine           Engine

        │              │
        ├──────────────┤
        ▼
Behavior Pattern Engine
        │
        ▼
Productivity Analytics
        │
        ▼
AI Coach + Daily Report
        │
        ▼
FastAPI Backend
        │
        ▼
Streamlit Dashboard
```

---

#  Core Features

## Activity Intelligence

Drift continuously monitors desktop activity and records:

- Active application
- Window title
- Keyboard activity
- Mouse activity
- Session duration
- Idle periods

Activity is automatically classified into categories such as:

- Coding
- Learning
- Browsing
- Communication
- Entertainment
- Idle

---

## Intent Inference

Drift doesn't stop at application tracking.

It infers **why** you're using an application.

Example:

```
VS Code
Window:
tracker.py — Visual Studio Code

↓

Intent:
Building Drift

↓

Goal:
Develop Human Observability Platform

↓

Mission:
Build Drift
```

---

## Mission Intelligence

Goals are grouped into higher-level missions including:

- Build Drift
- Career Growth
- Skill Development
- Communication
- Break / Distraction

This allows Drift to measure productivity at a behavioral level instead of an application level.

---

## Deep Work Detection

Drift identifies uninterrupted productive sessions by analyzing:

- Mission continuity
- Intent stability
- Activity duration
- Distraction interruptions

It highlights meaningful focus sessions instead of simply measuring screen time.

---

## Context Switch Analysis

Drift detects meaningful attention changes throughout the day.

It distinguishes between:

- Productive transitions
- Distraction switches
- Recoveries
- Fragmented work

instead of counting every application change equally.

---

## Behavioral Pattern Detection

Drift identifies recurring productivity behaviors such as:

- Mission Abandonment
- Mission Recovery
- App Ping-Pong
- Repeated distractions
- Focus fragmentation

These patterns are used to generate personalized coaching.

---

## AI Coach

Drift includes a deterministic coaching engine that converts analytics into actionable advice.

Each recommendation explains:

- Observation
- Impact
- Suggested improvement

The coaching engine works locally without requiring an LLM.

---

## Daily Report

At the end of each day Drift automatically generates:

- Executive Summary
- Productivity Score
- Mission Breakdown
- Deep Work Summary
- Attention Changes
- Timeline
- Personalized Recommendations

---

#  Dashboard

The Streamlit dashboard provides:

- Executive Overview
- Deep Dive Analytics
- Intelligence Dashboard
- History
- Replay
- AI Coach
- Daily Report
- Productivity Goals

---

#  Technology Stack

| Category | Technologies |
|-----------|--------------|
| Language | Python |
| Backend | FastAPI, Pydantic |
| Frontend | Streamlit |
| Visualization | Plotly, Pandas |
| Desktop Monitoring | pynput, psutil, pywin32 |
| Storage | JSON |
| APIs | REST |

---

#  Project Structure

```
drift/
│
├── agent/
│   ├── tracker.py
│   ├── app_classifier.py
│   └── local_store.py
│
├── backend/
│   ├── main.py
│   ├── context_switch_engine.py
│   ├── deep_work_engine.py
│   ├── drift_engine.py
│   ├── mission_engine.py
│   ├── productivity_score_engine.py
│   ├── daily_report_engine.py
│   ├── coach_engine.py
│   ├── replay_engine.py
│   ├── history_engine.py
│   └── ...
│
├── ui/
│
├── data/
│
├── dashboard.py
├── requirements.txt
└── README.md
```

---

#  Getting Started

## Clone the repository

```bash
git clone https://github.com/srishti997/drift.git
cd drift
```

## Install dependencies

```bash
pip install -r requirements.txt
```

## Start the backend

```bash
uvicorn backend.main:app --reload
```

## Start the activity tracker

```bash
cd agent
python tracker.py
```

## Launch the dashboard

```bash
streamlit run dashboard.py
```

Open:

```
http://localhost:8501
```

Allow Drift to collect activity for several minutes before viewing analytics.

---

#  API Endpoints

| Endpoint | Description |
|------------|------------|
| `/activity` | Store activity logs |
| `/summary` | Overall activity summary |
| `/drift` | Drift metrics |
| `/missions` | Mission analytics |
| `/intent` | Intent inference |
| `/deep-work` | Deep work analysis |
| `/context-switches` | Attention changes |
| `/patterns` | Behavioral patterns |
| `/coach` | AI coaching |
| `/daily-report` | Executive report |
| `/history` | Historical analytics |
| `/replay` | Day replay |
| `/goals` | Productivity goals |

---

#  Engineering Decisions

Some notable design decisions behind Drift:

- Modular engine architecture where each behavioral analysis runs independently.
- Rule-based intent inference to provide deterministic and explainable outputs.
- FastAPI backend exposing reusable analytics APIs.
- Streamlit frontend separated from business logic.
- Human-readable coaching instead of opaque productivity scores.
- Local-first design with no mandatory cloud dependency.

---

#  Future Roadmap

- Desktop widget
- Browser extension
- Weekly & monthly reports
- Calendar integration
- Cross-device synchronization
- LLM-powered behavioral coach
- Team productivity analytics

---

#  What I Learned

Building Drift strengthened my understanding of:

- Behavioral analytics
- Human-computer interaction
- FastAPI architecture
- Desktop activity monitoring
- Productivity systems
- Software modularization
- Data visualization
- Designing explainable AI-inspired systems

---
