def detect_behavior_loops(activity_logs, sequence_length=3):
    if len(activity_logs) < sequence_length:
        return {
            "loops": [],
            "top_loop": None,
            "insight": "Not enough activity to detect behavior loops."
        }

    sequence_counts = {}

    apps = [log.app_name for log in activity_logs]

    for i in range(len(apps) - sequence_length + 1):
        sequence = tuple(apps[i:i + sequence_length])

        # Ignore boring loops like Code -> Code -> Code
        if len(set(sequence)) == 1:
            continue

        sequence_counts[sequence] = sequence_counts.get(sequence, 0) + 1

    loops = [
        {
            "sequence": list(sequence),
            "count": count
        }
        for sequence, count in sequence_counts.items()
        if count >= 2
    ]

    loops.sort(key=lambda item: item["count"], reverse=True)

    top_loop = loops[0] if loops else None

    if top_loop:
        insight = (
            "Your strongest behavior loop is "
            + " → ".join(top_loop["sequence"])
            + f" with {top_loop['count']} occurrence(s)."
        )
    else:
        insight = "No repeated behavior loops detected yet."

    return {
        "loops": loops,
        "top_loop": top_loop,
        "insight": insight
    }


def get_next_app_prediction(activity_logs):
    if len(activity_logs) < 3:
        return {
            "predicted_next_app": None,
            "confidence": 0,
            "insight": "Not enough activity to predict next app."
        }

    apps = [log.app_name for log in activity_logs]
    current_pair = tuple(apps[-2:])

    next_app_counts = {}

    for i in range(len(apps) - 2):
        pair = tuple(apps[i:i + 2])
        next_app = apps[i + 2]

        if pair == current_pair:
            next_app_counts[next_app] = next_app_counts.get(next_app, 0) + 1

    if not next_app_counts:
        return {
            "predicted_next_app": None,
            "confidence": 0,
            "insight": "No historical next-app pattern found for current behavior."
        }

    predicted_next_app = max(next_app_counts, key=next_app_counts.get)
    total = sum(next_app_counts.values())
    confidence = round(next_app_counts[predicted_next_app] / total, 2)

    return {
        "current_sequence": list(current_pair),
        "predicted_next_app": predicted_next_app,
        "confidence": confidence,
        "insight": (
            f"After {' → '.join(current_pair)}, "
            f"you usually open {predicted_next_app}."
        )
    }