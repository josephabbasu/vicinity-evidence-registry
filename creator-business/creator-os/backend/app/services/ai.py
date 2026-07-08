"""Claude integration with graceful offline fallback.

Every generator works without an ANTHROPIC_API_KEY: it returns a structured
template the editor fills in manually, and reports which mode produced it.
With a key configured, the same functions call the Claude Messages API.
"""

from ..config import settings

BRAND_VOICE = (
    "You are the writing engine for Plain Money, a global money-education "
    "YouTube channel. Voice: plain, calm, honest, respectful, globally "
    "accessible English (B1-B2 reading level). Principles first, then a "
    "'localize it' layer for different countries. Never hype, never shame, "
    "no get-rich-quick framing, no individualized financial advice. Every "
    "factual claim must be marked [CLAIM] so it can be verified before "
    "production."
)


def _client():
    if not settings.anthropic_api_key:
        return None
    try:
        import anthropic
    except ImportError:
        return None
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def _complete(system: str, user: str, max_tokens: int = 4096) -> tuple[str | None, str]:
    """Returns (text or None, mode). mode is 'claude' or 'fallback'."""
    client = _client()
    if client is None:
        return None, "fallback"
    try:
        response = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        if response.stop_reason == "refusal":
            return None, "fallback"
        text = "".join(b.text for b in response.content if b.type == "text")
        return text, "claude"
    except Exception:
        return None, "fallback"


def generate_ideas(pillar: str, topic_hint: str, count: int) -> tuple[list[dict], str]:
    prompt = (
        f"Generate {count} evergreen video ideas for the pillar '{pillar or 'any'}'"
        + (f" related to: {topic_hint}." if topic_hint else ".")
        + " Return one idea per line in the exact format: TITLE | one-line angle."
        " Titles must target recurring global search demand, not news events."
    )
    text, mode = _complete(BRAND_VOICE, prompt, max_tokens=2048)
    if text:
        ideas = []
        for line in text.strip().splitlines():
            if "|" in line:
                title, _, notes = line.partition("|")
                title = title.strip(" -*0123456789.")
                if title:
                    ideas.append({"title": title.strip(), "notes": notes.strip()})
        if ideas:
            return ideas[:count], mode
    # Fallback: seed angles from the content strategy's proven templates
    templates = [
        ("How does {t} actually work?", "Foundations explainer"),
        ("The real cost of {t}", "Receipt-style cost breakdown"),
        ("{t}: myth vs fact, with sources", "Myth-busting verdict video"),
        ("Anatomy of a {t} scam", "Scam Anatomy series"),
        ("{t} explained for every country", "Localize-it global explainer"),
        ("The one chart that explains {t}", "Single-chart story"),
        ("What nobody taught you about {t}", "First-principles curriculum"),
    ]
    topic = topic_hint or pillar or "money"
    out = [{"title": t.format(t=topic), "notes": n} for t, n in templates[:count]]
    return out, "fallback"


def generate_research_brief(title: str, pillar: str) -> tuple[str, str]:
    prompt = (
        f"Write a research brief for the video '{title}' (pillar: {pillar}). Sections: "
        "1) The question viewers are really asking; 2) What existing videos get wrong or miss; "
        "3) 8-12 candidate sources (official statistics, academic work, regulators, reputable "
        "journalism) with what each supports; 4) Key numbers with [CLAIM] markers; "
        "5) Localization notes (how the concept differs by country); 6) Suggested structure."
    )
    text, mode = _complete(BRAND_VOICE, prompt, max_tokens=4096)
    if text:
        return text, mode
    fallback = f"""# Research brief: {title}

## 1. The real question
(What is the viewer trying to decide or understand?)

## 2. Gap analysis
(What do the top existing videos get wrong, skip, or make US-specific?)

## 3. Candidate sources (aim for 8-12; official stats > academic > regulator > journalism)
- [ ] Source 1 — supports:
- [ ] Source 2 — supports:

## 4. Key numbers
- [CLAIM] ...

## 5. Localization notes
- US: / UK: / India: / Brazil: / Nigeria: ...

## 6. Suggested structure
Hook -> stakes -> 3-act explanation -> "what we don't know" -> takeaway -> sequel hook.
"""
    return fallback, "fallback"


def generate_script(title: str, pillar: str, research_brief: str) -> tuple[str, str]:
    prompt = (
        f"Write a two-column YouTube script for '{title}' (pillar: {pillar}).\n"
        "Format each beat as:\nVO: <voiceover line>\nVISUAL: <visual direction>\n\n"
        "Structure: cold-open hook (<=5s to first payoff), stakes, 3-act explanation with a "
        "visual beat every 20-30 seconds, an honest 'what we don't know' beat, one actionable "
        "takeaway, and a sequel hook to the next episode. Mark every factual assertion with "
        "[CLAIM]. Target 8-12 minutes of VO.\n\nResearch brief:\n" + research_brief[:6000]
    )
    text, mode = _complete(BRAND_VOICE, prompt, max_tokens=8192)
    if text:
        return text, mode
    fallback = f"""# Script: {title}

## Cold open (0:00-0:15)
VO: <hook — one surprising, verifiable statement> [CLAIM]
VISUAL: Single bold object on paper background.

## Stakes (0:15-0:45)
VO: Why this matters to the viewer today.
VISUAL: The One Number template.

## Act 1 — The principle
VO: ... [CLAIM]
VISUAL: ...

## Act 2 — How it works in practice
VO: ... [CLAIM]
VISUAL: ...

## Act 3 — Localize it
VO: "In the US this is called X, in India Y..." [CLAIM]
VISUAL: World map callouts.

## What we don't know
VO: Honest uncertainty beat.

## Takeaway + sequel hook
VO: One action the viewer can take today. Next episode: ...
"""
    return fallback, "fallback"


def adversarial_fact_check(script: str) -> tuple[str, str]:
    prompt = (
        "Act as an adversarial fact-checker. For the script below, list every claim that is "
        "overstated, outdated, US-specific without being labeled, or unsupported. For each: "
        "quote the line, explain the problem, and suggest a fix or a source to verify.\n\n"
        + script[:8000]
    )
    text, mode = _complete(BRAND_VOICE, prompt, max_tokens=4096)
    if text:
        return text, mode
    return (
        "Fact-check checklist (manual mode):\n"
        "- Extract every [CLAIM] line into the claims table.\n"
        "- Each claim needs a primary source URL before verification.\n"
        "- Check: is it current? Is it global or US-specific? Is the number exact?\n"
        "- Cut or correct anything that cannot be sourced.",
        "fallback",
    )


def seo_suggestions(title: str, description: str, tags: str) -> tuple[str, str]:
    prompt = (
        "Suggest improved YouTube metadata for this video. Provide: 3 alternative titles "
        "(<=60 chars, keyword-front-loaded, curiosity without clickbait), a 2-paragraph "
        "description whose first 150 characters work as a search snippet and which ends with "
        "a Sources section placeholder, and 12 tags.\n\n"
        f"Title: {title}\nDescription: {description}\nTags: {tags}"
    )
    text, mode = _complete(BRAND_VOICE, prompt, max_tokens=2048)
    if text:
        return text, mode
    return (
        "Metadata suggestions (manual mode):\n"
        "- Front-load the search keyword in the first 3 words of the title.\n"
        "- Keep the title <= 60 characters; add one curiosity element.\n"
        "- First 150 chars of the description should restate the question being answered.\n"
        "- End the description with a 'Sources:' list — it is part of the brand promise.",
        "fallback",
    )


ASSISTANT_SYSTEM = (
    BRAND_VOICE
    + " You are also the CreatorOS assistant: help with strategy, scripts, titles, "
    "thumbnails, analytics interpretation, and scheduling questions. Be concise and concrete."
)


def chat(message: str, history: list[dict]) -> tuple[str, str]:
    client = _client()
    if client is None:
        return (
            "The AI assistant is running in offline mode (no ANTHROPIC_API_KEY configured). "
            "Set the key to enable Claude. Meanwhile: the knowledge base contains the brand "
            "voice guide, title templates, and the publishing checklist.",
            "fallback",
        )
    messages = [
        {"role": m.get("role", "user"), "content": m.get("content", "")}
        for m in history[-20:]
        if m.get("role") in ("user", "assistant") and m.get("content")
    ]
    messages.append({"role": "user", "content": message})
    try:
        response = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=2048,
            system=ASSISTANT_SYSTEM,
            messages=messages,
        )
        if response.stop_reason == "refusal":
            return "I can't help with that request.", "claude"
        return "".join(b.text for b in response.content if b.type == "text"), "claude"
    except Exception as exc:  # surface API problems to the UI rather than 500
        return f"Claude API error: {exc}", "fallback"
