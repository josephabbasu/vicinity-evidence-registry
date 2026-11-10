#!/usr/bin/env python3
"""Mechanism Debt Atlas (exploratory, derived analysis).

Question: where does the evidence base ASSERT a causal pathway without ever TESTING it,
and which documented harm pathways have NO intervention aimed at them?

Integrity rules (same as the registry):
  * No effect sizes, p-values, or DOIs are created.
  * Everything computed here is a DERIVED field from the 'Mediators/Mechanisms' and
    'Intervention Type' columns, using a transparent keyword lexicon (below).
  * Keyword matching is a triage aid. Every row is flagged for human verification.

Usage: python3 scripts/mechanism_debt.py   (writes docs/mechanism_debt.json and .md)
"""
import json, re, sys
from collections import Counter, defaultdict
from pathlib import Path
import openpyxl

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "source"
STREAMS = {
    "exposure": SRC / "Synthesis_Systematic_Review_Extraction_Paper_1.xlsx",
    "intervention": SRC / "Intervention_Systematic_Review_Extraction_Paper_2.xlsx",
}
MECH_COL, TYPE_COL = 10, 12  # 0-indexed; verified against headers at load time

# Pathway lexicon: domain -> regex. Edit here; the rule is the audit trail.
LEXICON = {
    "Stress physiology & sleep": r"stress response|biobehavioral|hpa|cortisol|sleep|vigilance|chronic stress|stress\b",
    "Trauma & emotional distress": r"trauma|anxiety|emotional|distress|psychological",
    "School disruption & cognition": r"school disruption|absentee|learning|cognitive|distraction|school",
    "Parenting & caregiver": r"parent|caregiver|stimulation",
    "Social control & cohesion": r"collective efficacy|social control|guardianship|social ties|social organi[sz]ation|eyes on the street|monitoring|social disorder|support systems|peer|role models",
    "Physical environment": r"physical disorder|built environment|land use|vacant|greening|exercise|target hardening|disinvestment",
    "Safety perception & fear": r"perceived safety|perceived crime|neighborhood safety|fear|safety perceptions",
    "Norms & social cognition": r"normali[sz]ation|cultural scripts|social information processing|self-regulation|social norms|social cognition",
    "Institutional trust & policing": r"distrust|injustice|policing|discrimination|structural racism",
    "Health-care access": r"health-care utili[sz]ation|providers",
    "Genetic / shared-family confounding": r"genetic|nonshared|shared environment|liability",
}
UNTESTED = re.compile(
    r"^\s*(nr|none|no\b|not (tested|modeled|modelled|assessed|reported|directly|formally|explicitly)|not tested)|"
    r"not (formally|directly) tested|no formal|no empirical mediator|not modeled|not estimated|"
    r"discussed conceptually|conceptual|posited|hypothesi[sz]ed|not tested/reported|tested/reported",
    re.I,
)


def load(path):
    ws = openpyxl.load_workbook(path, read_only=True).active
    rows = list(ws.iter_rows(values_only=True))
    hdr = rows[0]
    assert "Mediators" in str(hdr[MECH_COL]), f"column drift in {path.name}"
    out = []
    for r in rows[1:]:
        if r[0] and r[MECH_COL] and not str(r[0]).strip().startswith(("Place-based", "Single", "Psychosocial")):
            out.append((str(r[0]).strip(), str(r[MECH_COL]), str(r[TYPE_COL] or "")))
    return out


def classify(text):
    if UNTESTED.search(text):
        return "asserted-not-tested"
    return "listed-verify-if-tested"  # never claims 'tested' without human verification


def itype(t):
    t = t.lower()
    return "psychosocial" if "psychosocial" in t else "structural" if "structural" in t else "unspecified"


def main():
    studies, dom_ct = [], {s: Counter() for s in STREAMS}
    for stream, path in STREAMS.items():
        for sid, mech, typ in load(path):
            doms = sorted(d for d, rx in LEXICON.items() if re.search(rx, mech, re.I))
            status = classify(mech)
            studies.append({
                "stream": stream, "study": sid, "intervention_type": itype(typ) if stream == "intervention" else None,
                "mechanism_status": status, "pathway_domains": doms, "verification_required": True,
            })
            for d in doms:
                dom_ct[stream][d] += 1

    n = Counter(s["stream"] for s in studies)
    stat = {k: Counter(s["mechanism_status"] for s in studies if s["stream"] == k) for k in STREAMS}
    orphan, one_sided = [], []
    for d in LEXICON:
        e, i = dom_ct["exposure"][d], dom_ct["intervention"][d]
        if e >= 2 and i == 0:
            orphan.append((d, e, i))
        elif i >= 2 and e == 0:
            one_sided.append((d, e, i))
    # Mechanism debt = share of studies whose pathway language is asserted but untested
    debt = {k: round(stat[k]["asserted-not-tested"] / n[k], 2) for k in STREAMS}
    psy = [s for s in studies if s["intervention_type"] == "psychosocial"]
    psy_blank = sum(1 for s in psy if not s["pathway_domains"])

    result = {
        "derived": True, "n_studies": dict(n), "mechanism_status": {k: dict(v) for k, v in stat.items()},
        "mechanism_debt_share": debt,
        "domain_counts": {k: dict(v) for k, v in dom_ct.items()},
        "harm_pathways_with_no_intervention_language": orphan,
        "intervention_pathways_never_linked_to_harm_stream": one_sided,
        "psychosocial_studies_naming_no_pathway": [psy_blank, len(psy)],
        "studies": studies,
    }
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "mechanism_debt.json").write_text(json.dumps(result, indent=2))

    L = ["# Mechanism Debt Atlas (exploratory, derived)", "",
         "Derived from the `Mediators/Mechanisms` and `Intervention Type` columns by keyword lexicon "
         "(`scripts/mechanism_debt.py`). Triage aid only; every row requires human verification. "
         "No effect estimates are created.", "",
         "## Mechanism debt", "",
         "Share of studies whose mechanism text is asserted or discussed but not formally tested:", ""]
    for k in STREAMS:
        L.append(f"- **{k}** stream: {stat[k]['asserted-not-tested']} of {n[k]} studies ({debt[k]:.0%})")
    L += ["", "## Pathway domains: harm stream vs intervention stream", "",
          "| Pathway domain | Exposure studies | Intervention studies |", "|---|---|---|"]
    for d in LEXICON:
        L.append(f"| {d} | {dom_ct['exposure'][d]} | {dom_ct['intervention'][d]} |")
    L += ["", "## Orphan harm pathways (named in 2+ exposure studies, no intervention study names them)", ""]
    L += [f"- {d} ({e} exposure, {i} intervention)" for d, e, i in orphan] or ["- none under this lexicon"]
    L += ["", "## Intervention pathways never linked to the harm stream", ""]
    L += [f"- {d} ({e} exposure, {i} intervention)" for d, e, i in one_sided] or ["- none under this lexicon"]
    L += ["", f"Psychosocial intervention studies naming no pathway: {psy_blank} of {len(psy)}.", ""]
    (ROOT / "docs" / "MECHANISM_DEBT.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    sys.exit(main())
