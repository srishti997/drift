def build_behavior_graph(activity_logs):
    if len(activity_logs) < 2:
        return {
            "nodes": [],
            "edges": [],
            "top_transition": None,
            "insight": "Not enough activity to build behavior graph."
        }

    app_time = {}
    transition_counts = {}

    for log in activity_logs:
        app_time[log.app_name] = app_time.get(log.app_name, 0) + log.duration_seconds

    for i in range(len(activity_logs) - 1):
        from_app = activity_logs[i].app_name
        to_app = activity_logs[i + 1].app_name

        if from_app == to_app:
            continue

        key = (from_app, to_app)
        transition_counts[key] = transition_counts.get(key, 0) + 1

    nodes = [
        {
            "app": app,
            "total_time_seconds": total_time
        }
        for app, total_time in app_time.items()
    ]

    edges = [
        {
            "from_app": from_app,
            "to_app": to_app,
            "count": count
        }
        for (from_app, to_app), count in transition_counts.items()
    ]

    edges.sort(key=lambda item: item["count"], reverse=True)

    top_transition = edges[0] if edges else None

    if top_transition:
        insight = (
            f"Your most common behavior transition is "
            f"{top_transition['from_app']} → {top_transition['to_app']} "
            f"with {top_transition['count']} occurrence(s)."
        )
    else:
        insight = "No meaningful app transitions detected yet."

    return {
        "nodes": nodes,
        "edges": edges,
        "top_transition": top_transition,
        "insight": insight
    }


def get_transition_probability(activity_logs, from_app, to_app):
    outgoing = {}

    for i in range(len(activity_logs) - 1):
        current_app = activity_logs[i].app_name
        next_app = activity_logs[i + 1].app_name

        if current_app not in outgoing:
            outgoing[current_app] = {}

        outgoing[current_app][next_app] = outgoing[current_app].get(next_app, 0) + 1

    if from_app not in outgoing:
        return 0

    total_outgoing = sum(outgoing[from_app].values())
    transition_count = outgoing[from_app].get(to_app, 0)

    if total_outgoing == 0:
        return 0

    return round(transition_count / total_outgoing, 2)