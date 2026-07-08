"""Idempotent seed: prompt library, knowledge base, starter pillars/ideas/trends."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Idea, KnowledgeArticle, Prompt, TrendKeyword

PROMPTS = [
    ("brand-voice", "System prompt: the Plain Money voice, baked into every generator",
     "Plain, calm, honest, respectful, global-English (B1-B2). Principles first, localize second. "
     "No hype, no shame, no advice — education only. Every factual assertion marked [CLAIM]."),
    ("research-brief", "Produce a research memo for a video idea",
     "Sections: the real question / gap analysis of existing videos / 8-12 candidate sources "
     "(official stats > academic > regulator > journalism) / key numbers with [CLAIM] / "
     "localization notes / suggested structure."),
    ("script-longform", "Two-column script generator",
     "VO + VISUAL beats. Hook <=5s to first payoff, stakes, 3 acts, visual beat every 20-30s, "
     "'what we don't know' honesty beat, one takeaway, sequel hook. Mark [CLAIM] on every fact."),
    ("adversarial-factcheck", "Second-pass reviewer",
     "Find every claim that is overstated, outdated, US-specific without labeling, or unsupported "
     "by its source. Quote, explain, suggest fix or source."),
    ("shorts-cutdown", "Derive 3-5 vertical Shorts from a long-form script",
     "Each Short: one idea, 0.7s brand stamp, hook in first line of text overlay, <=45s."),
    ("title-thumbnail", "Metadata generator",
     "3 title options <=60 chars keyword-front-loaded; thumbnail brief using one of the 7 brand "
     "templates (Stamp / One Number / Split / Anatomy / Chart / Receipt / Face+Verdict), <=4 words."),
]

ARTICLES = [
    ("Brand voice cheat sheet", "brand",
     "Plain: short sentences, define every term. Calm: no urgency or hype. Honest: cite, admit "
     "uncertainty. Respectful: no latte-shaming. Global: 'what's it called in your country?'"),
    ("Publishing checklist", "operations",
     "1) Claims all verified with sources. 2) Hook pays off in <=5s. 3) Citations on screen. "
     "4) Description first 150 chars = search snippet + Sources list. 5) Thumbnail legible at "
     "160x90. 6) End screen to next Foundations episode. 7) Pinned comment: sources + localize-it question."),
    ("KPI targets", "analytics",
     "CTR 4-8%. Avg % viewed >=50 (long-form). Shorts swipe-away <30% in first 3s. Sub conversion "
     ">=3 per 1k views. Corrections rate <0.5% of published claims, all public."),
    ("Sponsor ethics screen", "business",
     "Never: payday lenders, CFD/forex brokers, crypto exchanges, MLMs, individual stock picks. "
     "Allowed with review: budgeting tools, security tools, education platforms, books, banks "
     "(brand campaigns only, no product bounties). Disclosure always up front."),
    ("Publishing cadence", "operations",
     "Long-form Tue & Sat 14:00 UTC. Shorts daily. Batch 3 weeks ahead. Never skip a Money "
     "Foundations sequence week. January / tax seasons / graduation get themed pushes."),
]

PILLAR_IDEAS = [
    ("Compound interest, properly explained", "Money Foundations", 9, 10, 6, 9, 8),
    ("The debt payoff method the math supports", "Debt & Credit", 9, 9, 6, 9, 8),
    ("How to budget when income is irregular", "Saving & Budgeting", 8, 9, 8, 7, 8),
    ("Index funds: why boring beats exciting", "Investing From Zero", 9, 9, 5, 10, 8),
    ("Anatomy of a pig-butchering scam", "Scams & Traps", 8, 8, 8, 7, 7),
    ("Salary negotiation: scripts and evidence", "Earning & Career", 8, 9, 6, 8, 8),
    ("Why is everything so expensive?", "The Economy Explained", 9, 7, 6, 7, 7),
    ("Money and happiness: what research found", "Money Psychology", 7, 9, 7, 7, 8),
    ("Rent vs buy: the real calculation", "Big Life Purchases", 9, 9, 5, 9, 7),
    ("Mobile money: banking without banks", "Money Around the World", 6, 8, 9, 5, 7),
]

TREND_KEYWORDS = [
    ("how to save money", "Saving & Budgeting"),
    ("compound interest", "Money Foundations"),
    ("is it a scam", "Scams & Traps"),
    ("how to invest for beginners", "Investing From Zero"),
    ("inflation explained", "The Economy Explained"),
]


def seed(db: Session) -> None:
    if db.scalar(select(Prompt).limit(1)):
        return  # already seeded
    for name, purpose, body in PROMPTS:
        db.add(Prompt(name=name, purpose=purpose, body=body))
    for title, category, body in ARTICLES:
        db.add(KnowledgeArticle(title=title, category=category, body=body))
    for title, pillar, demand, evergreen, gap, monet, ease in PILLAR_IDEAS:
        db.add(Idea(
            title=title, pillar=pillar, demand=demand, evergreen=evergreen,
            competition_gap=gap, monetization=monet, production_ease=ease,
        ))
    for keyword, category in TREND_KEYWORDS:
        db.add(TrendKeyword(keyword=keyword, category=category))
    db.commit()
