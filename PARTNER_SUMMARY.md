# VICINITY: Plain-Language Launch Summary

VICINITY is a public evidence registry for research on neighborhood violence and youth mental health. It helps prevention practitioners find studies without reading an entire systematic review first.

The registry starts with 32 studies from a structured extraction workbook. Users can filter the evidence by research design, age group, country, outcome, exposure window, quality tier, causal tier, and publication year. Each study page explains the population, exposure, outcome, methods, main finding, and practical implications.

VICINITY separates stronger causal designs from associational evidence. A study enters the credible tier only when the source clearly documents a randomized trial, difference-in-differences design, natural experiment, instrumental variable, within-person fixed-effects design, or within-family fixed-effects design. The current release includes 26 credible-tier studies and 6 associational studies.

The registry also shows what remains uncertain. The supplied workbook did not include dedicated fields for DOI links, standardized effect sizes, confidence-interval bounds, or intervention type. VICINITY marks those fields as `[NEEDS VERIFICATION]`. It does not invent missing estimates.

Practitioners can use the registry to answer focused questions. For example, a user can narrow the evidence to adolescents, acute violence exposure, depression outcomes, and credible designs. Researchers can inspect the original extraction language and the reason for each causal-tier decision.

The site includes a study nomination form. New nominations enter a review queue. They do not appear publicly until a reviewer confirms eligibility, extraction accuracy, causal identification, and risk of bias.

The MVP uses React and Tailwind CSS for the public site. It uses FastAPI and PostgreSQL for the evidence and submission system. Render hosts the frontend, API, and database.

The next development phase will add data-driven synthesis panels and a forest plot. A later phase may add dynamic narrative updates and Bayesian evidence updating. Those features will not replace human review.
