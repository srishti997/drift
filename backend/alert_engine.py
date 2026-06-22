from plyer import notification

DISTRACTION_APPS = {
    "youtube",
    "instagram",
    "whatsapp",
    "discord",
    "telegram",
    "facebook"
}


def show_alert(title, message):
    print("ALERT TRIGGERED:", title, message)

    notification.notify(
        title=title,
        message=message,
        app_name="Drift",
        timeout=5
    )


def analyze_for_alerts(activity_logs):
    if len(activity_logs) < 2:
        return

    latest = activity_logs[-1]
    previous = activity_logs[-2]

    app_name = latest.app_name.lower()

    # Alert 1: Opened distraction app
    if any(app in app_name for app in DISTRACTION_APPS):
        show_alert(
            "⚠ Drift Alert",
            f"You opened {latest.app_name}. Stay focused on your mission."
        )

    # Alert 2: Excessive context switching
    if latest.app_name != previous.app_name:
        recent_logs = activity_logs[-5:]

        switches = 0

        for i in range(1, len(recent_logs)):
            if recent_logs[i].app_name != recent_logs[i - 1].app_name:
                switches += 1

        if switches >= 4:
            show_alert(
                "⚠ High Context Switching",
                "You have switched apps multiple times in a short period."
            )