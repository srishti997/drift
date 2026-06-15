def classify_activity(app_name: str, window_title: str) -> str:
    app = app_name.lower()
    title = window_title.lower()

    if "code" in app or "pycharm" in app or "intellij" in app:
        return "CODING"

    if "chrome" in app or "edge" in app or "firefox" in app:
        if any(word in title for word in ["docs", "documentation", "fastapi", "python", "stackoverflow", "github"]):
            return "LEARNING"
        if any(word in title for word in ["youtube", "instagram", "netflix", "prime video"]):
            return "ENTERTAINMENT"
        if any(word in title for word in ["whatsapp", "gmail", "linkedin"]):
            return "COMMUNICATION"
        return "BROWSING"

    if "explorer" in app:
        return "SYSTEM"

    if "whatsapp" in app or "slack" in app or "discord" in app:
        return "COMMUNICATION"

    return "OTHER"