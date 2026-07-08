"""Trend scoring: growth and momentum from stored interest points."""


def analyze_points(points: list[tuple]) -> dict:
    """points: list of (date, interest) sorted ascending."""
    if not points:
        return {"latest": 0.0, "growth_pct": 0.0, "momentum": "no data"}
    values = [p[1] for p in points]
    latest = values[-1]
    if len(values) < 2:
        return {"latest": latest, "growth_pct": 0.0, "momentum": "insufficient data"}
    half = max(1, len(values) // 2)
    older_avg = sum(values[:half]) / half
    recent_avg = sum(values[half:]) / (len(values) - half)
    growth = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else (100.0 if recent_avg > 0 else 0.0)
    if growth >= 25:
        momentum = "rising fast"
    elif growth >= 5:
        momentum = "rising"
    elif growth > -5:
        momentum = "stable (evergreen candidate)"
    else:
        momentum = "declining"
    return {"latest": latest, "growth_pct": round(growth, 1), "momentum": momentum}
