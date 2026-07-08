"""Deterministic, explainable SEO heuristics (no API required)."""

POWER_WORDS = {
    "how", "why", "what", "explained", "truth", "real", "cost", "mistake",
    "guide", "avoid", "actually", "honest", "myth", "anatomy", "rules",
}


def score_metadata(title: str, description: str, tags: str) -> dict:
    checks: list[dict] = []
    suggestions: list[str] = []
    score = 0

    def check(name: str, passed: bool, weight: int, fix: str):
        nonlocal score
        checks.append({"name": name, "passed": passed, "weight": weight})
        if passed:
            score_add(weight)
        else:
            suggestions.append(fix)

    def score_add(w: int):
        nonlocal score
        score += w

    t = title.strip()
    words = [w.strip(".,!?").lower() for w in t.split()]

    check("Title length 20-60 chars", 20 <= len(t) <= 60, 15,
          "Keep titles between 20 and 60 characters so they don't truncate in search.")
    check("Keyword in first 3 words", any(w in POWER_WORDS for w in words[:3]), 15,
          "Front-load a search word (how / why / what / cost / explained) in the first 3 words.")
    check("Has a hook word", any(w in POWER_WORDS for w in words), 10,
          "Add one curiosity or utility word (truth, real, mistake, honest, explained).")
    check("Not ALL CAPS", t != t.upper() or not t, 5,
          "Avoid all-caps titles; the brand voice is calm, not shouty.")
    check("No clickbait punctuation", "!!" not in t and "??" not in t, 5,
          "Drop doubled punctuation; trust is the moat.")

    d = description.strip()
    check("Description >= 150 chars", len(d) >= 150, 15,
          "Write at least 150 characters; the first 150 are the search snippet.")
    check("Description answers the question early",
          len(d) >= 50 and any(w in d[:150].lower() for w in ("how", "why", "what", "learn", "explain")),
          10, "Restate the question being answered inside the first 150 characters.")
    check("Sources section present", "source" in d.lower(), 10,
          "End the description with a 'Sources:' list — it is part of the brand promise.")

    tag_list = [x.strip() for x in tags.split(",") if x.strip()]
    check("8-20 tags", 8 <= len(tag_list) <= 20, 10,
          f"Use 8-20 tags (currently {len(tag_list)}).")
    check("Tags include a broad and a specific term",
          len(tag_list) >= 2 and any(len(x.split()) == 1 for x in tag_list)
          and any(len(x.split()) >= 2 for x in tag_list),
          5, "Mix single-word broad tags with multi-word specific phrases.")

    return {"score": score, "checks": checks, "suggestions": suggestions}
