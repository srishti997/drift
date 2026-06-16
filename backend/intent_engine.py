INTENT_RULES = [
    {
        "keywords": ["resume", "cv", "linkedin", "portfolio", "ats"],
        "intent": "Career Development",
        "goal": "Improve professional profile",
        "confidence": 0.95,
    },
    {
        "keywords": ["drift", "tracker.py", "main.py", "session_builder", "intent_engine", "fastapi", "uvicorn"],
        "intent": "Building Drift",
        "goal": "Develop Drift platform",
        "confidence": 0.95,
    },
    {
        "keywords": ["github", "git", "repository", "commit", "pull request"],
        "intent": "Source Code Management",
        "goal": "Manage project code",
        "confidence": 0.9,
    },
    {
        "keywords": ["stackoverflow", "stack overflow", "error", "traceback", "exception", "debug"],
        "intent": "Debugging",
        "goal": "Fix implementation issue",
        "confidence": 0.9,
    },
    {
        "keywords": ["chatgpt", "gungun", "gemini", "claude"],
        "intent": "AI-Assisted Work",
        "goal": "Research or build with AI support",
        "confidence": 0.85,
    },
    {
        "keywords": ["leetcode", "dsa", "coding problem", "interview preparation"],
        "intent": "Interview Preparation",
        "goal": "Prepare for technical interviews",
        "confidence": 0.9,
    },
    {
        "keywords": ["python", "machine learning", "ml", "ai", "scikit", "pandas", "numpy"],
        "intent": "Technical Learning",
        "goal": "Improve AI/ML skills",
        "confidence": 0.85,
    },
    {
        "keywords": ["documentation", "docs", "tutorial", "course", "learn"],
        "intent": "Learning",
        "goal": "Skill development",
        "confidence": 0.8,
    },
    {
        "keywords": ["youtube", "netflix", "prime video", "hotstar", "instagram", "reels"],
        "intent": "Entertainment",
        "goal": "No productive goal",
        "confidence": 0.85,
    },
    {
        "keywords": ["whatsapp", "gmail", "mail", "slack", "discord", "teams"],
        "intent": "Communication",
        "goal": "Message or collaboration",
        "confidence": 0.8,
    },
]


def infer_intent(app_name: str, window_title: str, activity_type: str):
    app = app_name.lower()
    title = window_title.lower()

    combined_text = f"{app} {title}"

    if activity_type == "IDLE":
        return {
            "intent": "Inactive",
            "goal": "No active goal",
            "confidence": 1.0,
        }

    matched_rules = []

    for rule in INTENT_RULES:
        match_count = 0

        for keyword in rule["keywords"]:
            if keyword in combined_text:
                match_count += 1

        if match_count > 0:
            matched_rules.append({
                "intent": rule["intent"],
                "goal": rule["goal"],
                "confidence": rule["confidence"],
                "match_count": match_count,
            })

    if matched_rules:
        best_match = max(
            matched_rules,
            key=lambda rule: (rule["match_count"], rule["confidence"])
        )

        return {
            "intent": best_match["intent"],
            "goal": best_match["goal"],
            "confidence": best_match["confidence"],
        }

    if activity_type == "CODING":
        return {
            "intent": "Software Development",
            "goal": "Build or modify software",
            "confidence": 0.75,
        }

    if activity_type == "LEARNING":
        return {
            "intent": "Learning",
            "goal": "Skill development",
            "confidence": 0.7,
        }

    if activity_type == "BROWSING":
        return {
            "intent": "Research",
            "goal": "Information Gathering",
            "confidence": 0.5,
        }

    return {
    "intent": "Unclassified Activity",
    "goal": "Needs Better Classification",
    "confidence": 0.2,
}