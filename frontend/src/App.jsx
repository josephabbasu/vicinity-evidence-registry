import { useEffect, useMemo, useState } from "react";
import {
  Link,
  NavLink,
  Route,
  Routes,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";

import {
  API_DOCS_URL,
  askEvidence,
  createRelease,
  exportUrl,
  fulltextCandidate,
  getChangelog,
  getDashboard,
  getGaps,
  getReleases,
  getStats,
  getStudies,
  getStudy,
  getUpdates,
  releaseDownloadUrl,
  rescoreCandidates,
  reviewerLogin,
  screenCandidate,
  submitStudy,
  triggerSearch,
} from "./api";


// ── Constants ─────────────────────────────────────────────────────────────────

const EMPTY_FILTERS = {
  search: "",
  design_type: "",
  age_group: "",
  country: "",
  outcome_type: "",
  exposure_window: "",
  quality_tier: "",
  causal_tier: "",
  year_min: "",
  year_max: "",
  intervention_only: false,
  stream: "",
};

const DIRECTION_STYLES = {
  Harmful: "bg-scarlet/10 text-scarlet border-scarlet/20",
  Protective: "bg-emerald-50 text-emerald-800 border-emerald-200",
  Mixed: "bg-gold/15 text-amber-900 border-gold/30",
  Null: "bg-slate-100 text-slate-700 border-slate-200",
  "Needs verification": "bg-purple-50 text-purple-800 border-purple-200",
};

const CERTAINTY_STYLES = {
  High: "bg-emerald-50 text-emerald-800 border-emerald-200",
  Moderate: "bg-gold/15 text-amber-900 border-gold/30",
  Low: "bg-scarlet/10 text-scarlet border-scarlet/20",
};

const PRIORITY_STYLES = {
  High: "border-scarlet/30 bg-scarlet/5",
  Medium: "border-gold/30 bg-gold/5",
  Low: "border-navy/10 bg-navy/3",
};

const DOMAIN_ICONS = {
  Geographic: "🌍",
  Outcome: "📊",
  Method: "🔬",
  Population: "👥",
};

const STREAM_META = {
  exposure: { label: "Exposure & Harm", color: "text-scarlet", bg: "bg-scarlet/10 border-scarlet/20" },
  intervention: { label: "Intervention & Recovery", color: "text-emerald-700", bg: "bg-emerald-50 border-emerald-200" },
  implementation: { label: "Implementation", color: "text-navy", bg: "bg-navy/5 border-navy/15" },
};

const CHANGE_TYPE_STYLES = {
  addition: "bg-emerald-50 text-emerald-800 border-emerald-200",
  correction: "bg-gold/15 text-amber-900 border-gold/30",
  retraction: "bg-scarlet/10 text-scarlet border-scarlet/20",
  methodology: "bg-purple-50 text-purple-800 border-purple-200",
  surveillance: "bg-sky-50 text-sky-800 border-sky-200",
};


// ── Shared components ─────────────────────────────────────────────────────────

function Header({ reviewerToken }) {
  const navClass = ({ isActive }) =>
    `rounded-full px-3 py-2 text-sm font-semibold transition ${
      isActive ? "bg-navy text-white" : "text-navy hover:bg-navy/5"
    }`;

  return (
    <header className="sticky top-0 z-40 border-b border-navy/10 bg-warm/95 backdrop-blur">
      <div className="page-shell flex min-h-16 items-center justify-between gap-4">
        <Link to="/" className="flex items-baseline gap-2 text-navy">
          <span className="font-serif text-2xl font-bold tracking-tight">VICINITY</span>
          <span className="hidden text-xs font-semibold uppercase tracking-wider text-scarlet sm:inline">
            Evidence Observatory
          </span>
        </Link>
        <nav aria-label="Primary" className="flex flex-wrap items-center gap-1">
          <NavLink to="/registry" className={navClass}>Registry</NavLink>
          <NavLink to="/ask" className={navClass}>Ask</NavLink>
          <NavLink to="/gaps" className={navClass}>Gap Radar</NavLink>
          <NavLink to="/changelog" className={navClass}>Changelog</NavLink>
          <NavLink to="/about" className={navClass}>About</NavLink>
          <NavLink to="/submit" className={navClass}>Submit</NavLink>
          {reviewerToken && (
            <NavLink
              to="/reviewer"
              className={({ isActive }) =>
                `rounded-full px-3 py-2 text-sm font-semibold transition ${
                  isActive ? "bg-scarlet text-white" : "bg-scarlet/10 text-scarlet hover:bg-scarlet/20"
                }`
              }
            >
              Reviewer
            </NavLink>
          )}
        </nav>
      </div>
    </header>
  );
}


function Footer() {
  return (
    <footer className="mt-20 border-t border-navy/10 bg-navy text-white">
      <div className="page-shell grid gap-8 py-10 md:grid-cols-[1.5fr_1fr_1fr]">
        <div>
          <p className="font-serif text-2xl font-bold">VICINITY</p>
          <p className="mt-2 max-w-xl text-sm leading-6 text-white/75">
            Living Causal Evidence Observatory for neighborhood violence and youth mental health.
          </p>
          <p className="mt-4 text-xs text-white/50">
            Developed by J. Abbas · Rutgers University · Version 2.0
          </p>
        </div>
        <div className="text-sm leading-7 text-white/75">
          <p className="font-bold text-white">Evidence streams</p>
          <Link to="/registry?stream=exposure" className="block hover:text-white">Exposure & Harm (32)</Link>
          <Link to="/registry?stream=intervention" className="block hover:text-white">Intervention & Recovery (26)</Link>
          <Link to="/gaps" className="block hover:text-white">Evidence Gap Radar</Link>
          <Link to="/implementation" className="block hover:text-white">Will It Work Here?</Link>
        </div>
        <div className="text-sm leading-7 text-white/75">
          <p className="font-bold text-white">Resources</p>
          <Link to="/ask" className="block hover:text-white">Practitioner Query</Link>
          <Link to="/changelog" className="block hover:text-white">Public Changelog</Link>
          <Link to="/about" className="block hover:text-white">Protocol & Citation</Link>
          <Link to="/submit" className="block hover:text-white">Nominate a Study</Link>
          <a href={API_DOCS_URL} target="_blank" rel="noreferrer" className="block hover:text-white">Public API</a>
        </div>
      </div>
    </footer>
  );
}


function Loading({ label = "Loading evidence..." }) {
  return (
    <div className="page-shell py-24 text-center">
      <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-navy/15 border-t-scarlet" />
      <p className="mt-4 text-sm font-semibold text-navy">{label}</p>
    </div>
  );
}


function ErrorMessage({ message }) {
  return (
    <div className="page-shell py-16">
      <div className="card border-scarlet/30 p-6">
        <p className="font-bold text-scarlet">The registry could not load this view.</p>
        <p className="mt-2 text-sm text-slate-700">{message}</p>
      </div>
    </div>
  );
}


function Badge({ children, tone = "navy" }) {
  const tones = {
    navy: "border-navy/15 bg-navy/5 text-navy",
    red: "border-scarlet/20 bg-scarlet/10 text-scarlet",
    gold: "border-gold/30 bg-gold/15 text-amber-900",
    green: "border-emerald-200 bg-emerald-50 text-emerald-800",
    sky: "border-sky-200 bg-sky-50 text-sky-800",
  };
  return (
    <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-bold ${tones[tone]}`}>
      {children}
    </span>
  );
}


function StreamBadge({ stream }) {
  const meta = STREAM_META[stream] || STREAM_META.exposure;
  return (
    <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-bold ${meta.bg} ${meta.color}`}>
      {meta.label}
    </span>
  );
}


// ── Home page ─────────────────────────────────────────────────────────────────

function HomePage() {
  const [stats, setStats] = useState(null);
  const [updates, setUpdates] = useState([]);
  const [featured, setFeatured] = useState(null);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([getStats(), getStudies({ limit: 100 }), getUpdates()])
      .then(([statsData, studiesData, updatesData]) => {
        setStats(statsData);
        setUpdates(updatesData);
        setFeatured(studiesData.studies.find((s) => s.featured) || studiesData.studies[0]);
      })
      .catch((err) => setError(err.message));
  }, []);

  if (error) return <ErrorMessage message={error} />;
  if (!stats) return <Loading />;

  const streamCards = [
    {
      stream: "exposure",
      count: stats.exposure_count,
      heading: "Exposure & Harm",
      body: "What happens to young people after neighborhood violence? Causal-design studies on depression, anxiety, PTSD, education, and behavior.",
      cta: "Browse exposure evidence",
      to: "/registry?stream=exposure",
      accent: "border-t-4 border-t-scarlet",
    },
    {
      stream: "intervention",
      count: stats.intervention_count,
      heading: "Intervention & Recovery",
      body: "What reduces harm? Evidence on violence interruption, housing mobility, trauma therapy, hospital-based programs, and school prevention.",
      cta: "Browse interventions",
      to: "/registry?stream=intervention",
      accent: "border-t-4 border-t-emerald-500",
    },
    {
      stream: "gaps",
      count: null,
      heading: "Evidence Gap Radar",
      body: "Where is evidence missing? Auto-computed gaps by geography, outcome, method, and population — guiding the next generation of research.",
      cta: "View gap radar",
      to: "/gaps",
      accent: "border-t-4 border-t-gold",
    },
  ];

  return (
    <>
      {/* Hero */}
      <section className="overflow-hidden bg-navy text-white">
        <div className="page-shell relative grid gap-10 py-20 lg:grid-cols-[1.35fr_0.65fr] lg:py-28">
          <div className="relative z-10">
            <p className="text-xs font-bold uppercase tracking-[0.24em] text-gold">
              Living Causal Evidence Observatory
            </p>
            <h1 className="mt-5 max-w-4xl text-5xl font-bold leading-[1.05] sm:text-6xl">
              What does the evidence actually say about neighborhood violence and youth?
            </h1>
            <p className="mt-7 max-w-3xl text-lg leading-8 text-white/80">
              VICINITY brings three connected evidence streams — exposure effects, intervention outcomes,
              and evidence gaps — into one continuously updated observatory. Study design, causal quality,
              and source limits remain visible on every record.
            </p>
            <div className="mt-9 flex flex-wrap gap-3">
              <Link to="/ask" className="button-primary">
                Ask a question →
              </Link>
              <Link to="/registry" className="button-secondary border-white/30 bg-white/10 text-white hover:bg-white/20">
                Browse all evidence
              </Link>
            </div>
          </div>
          <div className="relative z-10 self-end rounded-3xl border border-white/15 bg-white/10 p-7 backdrop-blur">
            <p className="text-sm font-bold uppercase tracking-wider text-gold">Live registry</p>
            <p className="mt-4 text-6xl font-bold">{stats.study_count}</p>
            <p className="mt-1 text-white/75">studies across {stats.country_count} countries</p>
            <div className="mt-7 grid grid-cols-2 gap-4 border-t border-white/15 pt-6">
              <div>
                <p className="text-2xl font-bold">{stats.credible_count}</p>
                <p className="text-xs text-white/65">credible-tier studies</p>
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.intervention_count}</p>
                <p className="text-xs text-white/65">intervention studies</p>
              </div>
            </div>
            {stats.pending_candidates > 0 && (
              <p className="mt-4 rounded-xl border border-gold/30 bg-gold/15 px-3 py-2 text-xs font-semibold text-amber-900">
                {stats.pending_candidates} publications awaiting review
              </p>
            )}
            <p className="mt-4 text-xs text-white/55">
              {stats.last_search_date
                ? `Last searched ${stats.last_search_date}`
                : `Updated ${stats.updated_date}`}
            </p>
          </div>
          <div className="absolute -right-32 -top-24 h-96 w-96 rounded-full bg-scarlet/25 blur-3xl" />
          <div className="absolute -bottom-48 left-1/3 h-80 w-80 rounded-full bg-gold/15 blur-3xl" />
        </div>
      </section>

      {/* Three streams */}
      <section className="page-shell py-16">
        <div>
          <p className="eyebrow">Three evidence streams</p>
          <h2 className="mt-2 text-3xl font-bold text-navy">
            What happened? What helps? What do we still not know?
          </h2>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600">
            VICINITY separates these as distinct causal questions. Each stream has its own evidence base,
            certainty level, and practitioner relevance.
          </p>
        </div>
        <div className="mt-8 grid gap-5 md:grid-cols-3">
          {streamCards.map((card) => (
            <button
              key={card.stream}
              type="button"
              onClick={() => navigate(card.to)}
              className={`card p-7 text-left transition hover:-translate-y-1 hover:shadow-lg ${card.accent}`}
            >
              {card.count !== null && (
                <p className="text-4xl font-bold text-navy">{card.count}</p>
              )}
              <p className="mt-3 text-xl font-bold text-navy">{card.heading}</p>
              <p className="mt-3 text-sm leading-6 text-slate-600">{card.body}</p>
              <p className="mt-6 text-sm font-bold text-scarlet">{card.cta} →</p>
            </button>
          ))}
        </div>
      </section>

      {/* Practitioner query prompt */}
      <section className="bg-navy text-white">
        <div className="page-shell py-16">
          <div className="grid gap-10 lg:grid-cols-2 lg:items-center">
            <div>
              <p className="eyebrow text-gold">Practitioner query interface</p>
              <h2 className="mt-3 text-4xl font-bold">
                What does the evidence say for your population?
              </h2>
              <p className="mt-5 text-lg leading-8 text-white/80">
                VICINITY translates research into structured evidence briefs. Specify the population,
                exposure type, and outcome you care about — and receive a synthesized answer with causal
                certainty, effect direction, available interventions, and known evidence gaps.
              </p>
              <Link to="/ask" className="button-primary mt-7 border-transparent bg-gold text-navy hover:bg-amber-400">
                Open the query interface →
              </Link>
            </div>
            <div className="rounded-3xl border border-white/15 bg-white/10 p-7 backdrop-blur font-mono text-sm">
              <p className="text-white/50 text-xs mb-4">Example query →</p>
              <p className="text-gold font-bold">For adolescents exposed to shootings near home</p>
              <p className="text-gold font-bold">during the previous 30 days:</p>
              <div className="mt-5 space-y-2 text-white/80">
                <p>Studies matched: <span className="text-white font-bold">14</span></p>
                <p>Credible-tier: <span className="text-white font-bold">9</span></p>
                <p>Effect direction: <span className="text-emerald-400 font-bold">Harmful (13/14)</span></p>
                <p>Certainty: <span className="text-emerald-400 font-bold">High</span></p>
                <p className="mt-3 text-white/50 text-xs">Interventions available: 8 · Evidence gaps: 4</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Featured study */}
      {featured && (
        <section className="page-shell py-16">
          <div className="card overflow-hidden">
            <div className="grid lg:grid-cols-[0.35fr_0.65fr]">
              <div className="bg-scarlet p-8 text-white">
                <p className="text-xs font-bold uppercase tracking-[0.22em] text-white/75">
                  Featured study
                </p>
                <h2 className="mt-4 text-2xl font-bold leading-tight">{featured.title}</h2>
                <p className="mt-3 text-sm text-white/70">{featured.citation}</p>
                <div className="mt-6 flex flex-wrap gap-2">
                  <Badge tone="gold">{featured.design_type}</Badge>
                  <Badge tone="navy">{featured.causal_tier}</Badge>
                </div>
              </div>
              <div className="p-8">
                <p className="text-sm leading-7 text-slate-700">{featured.finding_summary}</p>
                <div className="mt-6 flex flex-wrap items-center gap-4">
                  <Link to={`/studies/${featured.slug}`} className="button-primary">
                    Read study record
                  </Link>
                  <StreamBadge stream={featured.registry_stream} />
                </div>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* What changed */}
      {updates.length > 0 && (
        <section className="page-shell pb-20">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="eyebrow">Living registry</p>
              <h2 className="mt-2 text-3xl font-bold text-navy">What changed recently</h2>
            </div>
            <Link to="/changelog" className="text-sm font-bold text-scarlet hover:underline">
              Full changelog →
            </Link>
          </div>
          <div className="mt-6 space-y-4">
            {updates.slice(0, 3).map((update) => (
              <div key={update.id} className="card p-6">
                <p className="font-bold text-navy">{update.title}</p>
                <p className="mt-2 text-sm leading-6 text-slate-600">{update.description}</p>
                <p className="mt-3 text-xs text-slate-400">
                  {new Date(update.created_at).toLocaleDateString("en-US", {
                    year: "numeric", month: "long", day: "numeric",
                  })}
                </p>
              </div>
            ))}
          </div>
        </section>
      )}
    </>
  );
}


// ── Registry page ─────────────────────────────────────────────────────────────

function FilterSelect({ label, name, value, options, onChange }) {
  return (
    <label>
      <span className="label">{label}</span>
      <select className="field" name={name} value={value} onChange={onChange}>
        <option value="">All</option>
        {options.map((opt) => (
          <option key={opt} value={opt}>{opt}</option>
        ))}
      </select>
    </label>
  );
}


function StudyCard({ study }) {
  const directionStyle = DIRECTION_STYLES[study.effect_direction] || DIRECTION_STYLES["Needs verification"];
  return (
    <article className="card p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-bold text-scarlet">{study.citation}</p>
          <h2 className="mt-2 text-xl font-bold leading-tight text-navy">{study.title}</h2>
        </div>
        <span className={`shrink-0 rounded-full border px-3 py-1 text-xs font-bold ${directionStyle}`}>
          {study.effect_direction}
        </span>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <Badge>{study.design_type}</Badge>
        <Badge tone={study.causal_tier === "Credible" ? "green" : "gold"}>{study.causal_tier}</Badge>
        <Badge tone="red">{study.quality_tier}</Badge>
        <StreamBadge stream={study.registry_stream} />
      </div>
      <dl className="mt-5 grid gap-3 text-sm sm:grid-cols-3">
        <div><dt className="font-bold text-navy">Population</dt><dd className="mt-1 text-slate-600">{study.age_range}</dd></div>
        <div><dt className="font-bold text-navy">Outcome</dt><dd className="mt-1 text-slate-600">{study.outcome_type}</dd></div>
        <div><dt className="font-bold text-navy">Exposure window</dt><dd className="mt-1 text-slate-600">{study.exposure_window}</dd></div>
      </dl>
      <p className="mt-5 line-clamp-3 text-sm leading-6 text-slate-700">{study.finding_summary}</p>
      <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-navy/10 pt-4">
        <span className="text-xs font-semibold text-slate-500">
          {study.country} · {study.publication_year || "Year needs verification"} · {study.verification_count} flags
        </span>
        <Link to={`/studies/${study.slug}`} className="text-sm font-bold text-scarlet hover:underline">
          View full record →
        </Link>
      </div>
    </article>
  );
}


function RegistryPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialFilters = useMemo(() => {
    const values = { ...EMPTY_FILTERS };
    Object.keys(values).forEach((key) => {
      if (key === "intervention_only") {
        values[key] = searchParams.get(key) === "true";
      } else {
        values[key] = searchParams.get(key) || "";
      }
    });
    return values;
  }, [searchParams]);
  const [filters, setFilters] = useState(initialFilters);
  const [stats, setStats] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getStats().then(setStats).catch((err) => setError(err.message));
  }, []);

  useEffect(() => { setFilters(initialFilters); }, [initialFilters]);

  useEffect(() => {
    setError("");
    getStudies(filters).then(setResult).catch((err) => setError(err.message));
  }, [filters]);

  const updateFilter = (e) => {
    const { name, value, type, checked } = e.target;
    const next = { ...filters, [name]: type === "checkbox" ? checked : value };
    setFilters(next);
    const params = new URLSearchParams();
    Object.entries(next).forEach(([key, val]) => { if (val) params.set(key, val); });
    setSearchParams(params, { replace: true });
  };

  const clearFilters = () => { setFilters(EMPTY_FILTERS); setSearchParams({}, { replace: true }); };

  if (error) return <ErrorMessage message={error} />;

  return (
    <main className="page-shell py-12">
      <div className="max-w-3xl">
        <p className="eyebrow">Registry browser</p>
        <h1 className="mt-2 text-4xl font-bold text-navy">Search the current evidence</h1>
        <p className="mt-4 text-base leading-7 text-slate-600">
          Filter across all three streams: exposure effects, intervention outcomes, and implementation
          evidence. Each record preserves its source text and verification notes.
        </p>
      </div>

      <section className="card mt-8 p-5" aria-label="Study filters">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <label className="md:col-span-2">
            <span className="label">Search</span>
            <input
              className="field"
              name="search"
              value={filters.search}
              onChange={updateFilter}
              placeholder="Author, title, outcome, or country"
            />
          </label>
          <FilterSelect label="Evidence stream" name="stream" value={filters.stream}
            options={["exposure", "intervention", "implementation"]} onChange={updateFilter} />
          <FilterSelect label="Design type" name="design_type" value={filters.design_type}
            options={stats?.design_types || []} onChange={updateFilter} />
          <FilterSelect label="Age group" name="age_group" value={filters.age_group}
            options={stats?.age_groups || []} onChange={updateFilter} />
          <FilterSelect label="Country" name="country" value={filters.country}
            options={stats?.countries || []} onChange={updateFilter} />
          <FilterSelect label="Outcome" name="outcome_type" value={filters.outcome_type}
            options={stats?.outcome_types || []} onChange={updateFilter} />
          <FilterSelect label="Exposure window" name="exposure_window" value={filters.exposure_window}
            options={stats?.exposure_windows || []} onChange={updateFilter} />
          <FilterSelect label="Quality tier" name="quality_tier" value={filters.quality_tier}
            options={stats?.quality_tiers || []} onChange={updateFilter} />
          <FilterSelect label="Causal tier" name="causal_tier" value={filters.causal_tier}
            options={stats?.causal_tiers || []} onChange={updateFilter} />
          <label>
            <span className="label">Year from</span>
            <input className="field" type="number" min="1900" max="2100" name="year_min"
              value={filters.year_min} onChange={updateFilter} />
          </label>
          <label>
            <span className="label">Year to</span>
            <input className="field" type="number" min="1900" max="2100" name="year_max"
              value={filters.year_max} onChange={updateFilter} />
          </label>
          <label className="flex items-end gap-3 pb-2 text-sm font-bold text-navy">
            <input type="checkbox" name="intervention_only" checked={filters.intervention_only}
              onChange={updateFilter} className="h-5 w-5 rounded border-navy/30 text-scarlet" />
            Intervention studies only
          </label>
          <div className="flex items-end">
            <button type="button" onClick={clearFilters} className="button-secondary w-full">
              Clear filters
            </button>
          </div>
        </div>
      </section>

      <div className="mt-8 flex flex-wrap items-center justify-between gap-4">
        <p className="text-sm font-bold text-navy">
          {result ? `${result.total} ${result.total === 1 ? "study" : "studies"}` : "Loading…"}
        </p>
        <div className="flex gap-3">
          <a href={exportUrl("csv")} className="text-xs font-bold text-scarlet hover:underline">
            Download CSV ↓
          </a>
          <a href={exportUrl("json")} className="text-xs font-bold text-navy hover:underline">
            Download JSON ↓
          </a>
        </div>
      </div>

      <div className="mt-5 grid gap-5">
        {result?.studies.map((study) => <StudyCard key={study.slug} study={study} />)}
      </div>
      {result && result.total === 0 && (
        <div className="card mt-5 p-10 text-center">
          <p className="text-xl font-bold text-navy">No studies match these filters.</p>
          <p className="mt-2 text-sm text-slate-600">
            This result reflects the current source data. Try a broader view.
          </p>
        </div>
      )}
    </main>
  );
}


// ── Study detail page ─────────────────────────────────────────────────────────

function DetailItem({ label, children }) {
  return (
    <div>
      <dt className="text-xs font-bold uppercase tracking-wider text-scarlet">{label}</dt>
      <dd className="mt-2 whitespace-pre-line text-sm leading-6 text-slate-700">{children || "Not reported"}</dd>
    </div>
  );
}


function StudyDetailPage() {
  const { slug } = useParams();
  const [study, setStudy] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getStudy(slug).then(setStudy).catch((err) => setError(err.message));
  }, [slug]);

  if (error) return <ErrorMessage message={error} />;
  if (!study) return <Loading label="Loading study record..." />;

  const barPosition = {
    Protective: "justify-start", Null: "justify-center", Mixed: "justify-center",
    Harmful: "justify-end", "Needs verification": "justify-center",
  }[study.effect_direction];

  return (
    <main className="page-shell py-12">
      <Link to="/registry" className="text-sm font-bold text-scarlet hover:underline">← Back to registry</Link>
      <div className="mt-6 grid gap-8 lg:grid-cols-[1fr_320px]">
        <article>
          <p className="eyebrow">{study.citation}</p>
          <h1 className="mt-3 text-4xl font-bold leading-tight text-navy">{study.title}</h1>
          <div className="mt-5 flex flex-wrap gap-2">
            <Badge>{study.design_type}</Badge>
            <Badge tone={study.causal_tier === "Credible" ? "green" : "gold"}>{study.causal_tier}</Badge>
            <Badge tone="red">{study.quality_tier}</Badge>
            <Badge>{study.country}</Badge>
            <StreamBadge stream={study.registry_stream} />
          </div>

          <section className="card mt-8 p-7">
            <p className="eyebrow">Plain-language finding</p>
            <p className="mt-4 whitespace-pre-line text-base leading-7 text-slate-700">{study.finding_summary}</p>
          </section>

          <section className="card mt-6 p-7">
            <h2 className="text-2xl font-bold text-navy">Effect direction</h2>
            <div className="mt-5">
              <div className="flex justify-between text-xs font-bold uppercase tracking-wider text-slate-500">
                <span>Protective</span><span>Null or mixed</span><span>Harmful</span>
              </div>
              <div className={`mt-2 flex h-5 rounded-full bg-gradient-to-r from-emerald-400 via-slate-200 to-scarlet ${barPosition}`}>
                <span className="h-5 w-5 rounded-full border-4 border-white bg-navy shadow" />
              </div>
              <p className="mt-4 text-sm leading-6 text-slate-700">{study.effect_direction_raw}</p>
              <p className="mt-4 rounded-xl border border-gold/40 bg-gold/10 p-4 text-sm leading-6 text-amber-950">
                {study.effect_size_note}
              </p>
            </div>
          </section>

          {study.effect_estimates?.length > 0 && (
            <section className="mt-8">
              <h2 className="text-3xl font-bold text-navy">Effect estimates</h2>
              <p className="mt-2 text-sm text-slate-500">
                One row per distinct effect reported. Enables meta-analytic synthesis.
              </p>
              <div className="mt-4 overflow-x-auto rounded-2xl border border-navy/10">
                <table className="w-full text-sm">
                  <thead className="bg-navy/5 text-xs font-bold uppercase tracking-wider text-navy">
                    <tr>
                      <th className="px-4 py-3 text-left">Outcome</th>
                      <th className="px-4 py-3 text-left">Population</th>
                      <th className="px-4 py-3 text-left">Estimate</th>
                      <th className="px-4 py-3 text-left">Type</th>
                      <th className="px-4 py-3 text-left">CI</th>
                      <th className="px-4 py-3 text-left">Primary</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-navy/5">
                    {study.effect_estimates.map((ee) => (
                      <tr key={ee.id} className="hover:bg-navy/3">
                        <td className="px-4 py-3 font-semibold text-navy">{ee.outcome_label}</td>
                        <td className="px-4 py-3 text-slate-600">{ee.population_subgroup}</td>
                        <td className="px-4 py-3 font-mono">{ee.point_estimate ?? "—"}</td>
                        <td className="px-4 py-3 text-slate-500">{ee.estimate_type || "—"}</td>
                        <td className="px-4 py-3 font-mono text-slate-500">
                          {ee.ci_lower != null && ee.ci_upper != null
                            ? `[${ee.ci_lower}, ${ee.ci_upper}]` : "—"}
                        </td>
                        <td className="px-4 py-3 text-center">
                          {ee.is_primary ? <span className="text-emerald-600 font-bold">✓</span> : ""}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          <section className="mt-10">
            <h2 className="text-3xl font-bold text-navy">Study record</h2>
            <dl className="mt-6 grid gap-7 md:grid-cols-2">
              <DetailItem label="Population">{study.age_range}</DetailItem>
              <DetailItem label="Sample size">{study.sample_size}</DetailItem>
              <DetailItem label="Population details">{study.population_details}</DetailItem>
              <DetailItem label="Outcome category">{study.outcome_type}</DetailItem>
              <DetailItem label="Outcome measure">{study.outcome_measure}</DetailItem>
              <DetailItem label="Outcome scale">{study.outcome_unit_scale}</DetailItem>
              <DetailItem label="Exposure measure">{study.exposure_measure}</DetailItem>
              <DetailItem label="Exposure window">{study.exposure_window_raw}</DetailItem>
              <DetailItem label="Geographic scale">{study.geographic_scale}</DetailItem>
              <DetailItem label="Outcome timepoint">{study.outcome_timepoint}</DetailItem>
              <DetailItem label="Moderators">{study.moderators}</DetailItem>
              <DetailItem label="Mechanisms">{study.mediators_mechanisms}</DetailItem>
            </dl>
          </section>

          <section className="mt-10">
            <h2 className="text-3xl font-bold text-navy">Methods</h2>
            <dl className="mt-6 grid gap-7">
              <DetailItem label="Design as extracted">{study.design_raw}</DetailItem>
              <DetailItem label="Identification strategy">{study.methodology}</DetailItem>
              <DetailItem label="Causal tier decision">{study.causal_tier_reason}</DetailItem>
              <DetailItem label="Estimator">{study.estimator}</DetailItem>
              <DetailItem label="Estimand">{study.estimand}</DetailItem>
              <DetailItem label="Standard errors or clustering">{study.se_clustering}</DetailItem>
              <DetailItem label="Missing data">{study.missing_data_method}</DetailItem>
              <DetailItem label="Multiple testing">{study.multiple_testing_adjustment}</DetailItem>
            </dl>
          </section>

          <section className="mt-10">
            <h2 className="text-3xl font-bold text-navy">Appraisal and use</h2>
            <dl className="mt-6 grid gap-7">
              <DetailItem label="Risk of bias">{study.risk_of_bias_raw}</DetailItem>
              <DetailItem label="Strengths and limitations">{study.strengths_limitations}</DetailItem>
              <DetailItem label="Policy and practice implications">{study.policy_practice_implications}</DetailItem>
              <DetailItem label="Reviewer notes">{study.reviewer_notes}</DetailItem>
            </dl>
          </section>
        </article>

        <aside className="space-y-5 lg:sticky lg:top-24 lg:self-start">
          <div className="card p-6">
            <h2 className="text-xl font-bold text-navy">Record status</h2>
            <dl className="mt-5 space-y-4">
              <DetailItem label="Publication year">{study.publication_year}</DetailItem>
              <DetailItem label="Significance">{study.statistically_significant_raw}</DetailItem>
              <DetailItem label="Evidence stream">{study.registry_stream}</DetailItem>
              <DetailItem label="Intervention type">{study.intervention_type}</DetailItem>
              <DetailItem label="DOI">{study.doi || "[NEEDS VERIFICATION]"}</DetailItem>
              <DetailItem label="Registry version">{study.added_in_version}</DetailItem>
            </dl>
          </div>
          <div className="card p-6">
            <h2 className="text-xl font-bold text-navy">Export this record</h2>
            <div className="mt-4 flex flex-col gap-2">
              <a
                href={exportUrl("bib")}
                className="button-secondary block text-center text-sm"
                download
              >
                Download BibTeX (.bib)
              </a>
              <a
                href={exportUrl("ris")}
                className="button-secondary block text-center text-sm"
                download
              >
                Download RIS (.ris)
              </a>
              <a
                href={exportUrl("json")}
                className="button-secondary block text-center text-sm"
                download
              >
                Full registry JSON
              </a>
            </div>
          </div>
          {study.verification_flags?.length > 0 && (
            <div className="rounded-2xl border border-gold/40 bg-gold/10 p-6">
              <h2 className="text-xl font-bold text-navy">Verification queue</h2>
              <p className="mt-2 text-sm leading-6 text-slate-700">
                {study.verification_count} source or normalization notes remain open.
              </p>
              <ul className="mt-4 space-y-3 text-sm leading-5 text-slate-700">
                {study.verification_flags.map((flag) => (
                  <li key={flag} className="border-t border-gold/30 pt-3 first:border-0 first:pt-0">{flag}</li>
                ))}
              </ul>
            </div>
          )}
        </aside>
      </div>
    </main>
  );
}


// ── Practitioner Ask page ─────────────────────────────────────────────────────

function AskPage() {
  const [query, setQuery] = useState({
    age_group: "adolescent",
    exposure_type: "",
    exposure_window: "",
    outcome_type: "",
    country: "",
  });
  const [brief, setBrief] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setBrief(null);
    try {
      const result = await askEvidence(query);
      setBrief(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const certParts = brief?.causal_certainty?.split(" — ") || [];
  const certLevel = certParts[0] || "Low";
  const certStyle = Object.entries(CERTAINTY_STYLES).find(([k]) => certLevel.startsWith(k))?.[1] || CERTAINTY_STYLES.Low;

  return (
    <main>
      <section className="bg-navy text-white">
        <div className="page-shell py-16">
          <p className="eyebrow text-gold">Practitioner query interface</p>
          <h1 className="mt-3 max-w-3xl text-5xl font-bold">
            What does the evidence say for your context?
          </h1>
          <p className="mt-5 max-w-2xl text-lg leading-8 text-white/80">
            Specify the population, exposure type, and outcome. VICINITY returns a synthesized
            evidence brief with causal certainty, available interventions, and known evidence gaps.
            This interface answers a different question than the registry browser — it synthesizes,
            not just lists.
          </p>
        </div>
      </section>

      <div className="page-shell py-12">
        <div className="grid gap-10 lg:grid-cols-[380px_1fr] lg:items-start">
          <form onSubmit={handleSubmit} className="card space-y-5 p-7">
            <h2 className="text-xl font-bold text-navy">Define your query</h2>

            <label>
              <span className="label">Population age group</span>
              <select className="field" value={query.age_group}
                onChange={(e) => setQuery({ ...query, age_group: e.target.value })}>
                <option value="all">All ages</option>
                <option value="adolescent">Adolescents (10–17)</option>
                <option value="child">Children (0–9)</option>
                <option value="adult">Young adults (18–25)</option>
              </select>
            </label>

            <label>
              <span className="label">Outcome of concern</span>
              <select className="field" value={query.outcome_type}
                onChange={(e) => setQuery({ ...query, outcome_type: e.target.value })}>
                <option value="">Any mental health outcome</option>
                <option value="mental health">Mental health (general)</option>
                <option value="depression">Depression</option>
                <option value="anxiety">Anxiety</option>
                <option value="PTSD">PTSD / trauma</option>
                <option value="behavioral">Behavioral problems</option>
                <option value="education">Academic / education</option>
                <option value="violence">Violence / aggression</option>
              </select>
            </label>

            <label>
              <span className="label">Exposure window</span>
              <select className="field" value={query.exposure_window}
                onChange={(e) => setQuery({ ...query, exposure_window: e.target.value })}>
                <option value="">Any window</option>
                <option value="Acute">Acute (recent, ≤30 days)</option>
                <option value="Chronic">Chronic (ongoing)</option>
                <option value="Lifetime">Lifetime cumulative</option>
              </select>
            </label>

            <label>
              <span className="label">Country or setting (optional)</span>
              <input className="field" placeholder="e.g. United States"
                value={query.country} onChange={(e) => setQuery({ ...query, country: e.target.value })} />
            </label>

            {error && (
              <p className="rounded-xl border border-scarlet/20 bg-scarlet/5 p-4 text-sm text-scarlet">{error}</p>
            )}

            <button type="submit" disabled={loading} className="button-primary w-full disabled:opacity-60">
              {loading ? "Searching evidence…" : "Get evidence brief →"}
            </button>

            <p className="text-xs text-slate-400 leading-5">
              This interface queries approved studies in real time. It does not replace systematic
              review or clinical judgment.
            </p>
          </form>

          <div>
            {!brief && !loading && (
              <div className="rounded-3xl border-2 border-dashed border-navy/15 p-12 text-center">
                <p className="text-lg font-bold text-navy">Your evidence brief will appear here.</p>
                <p className="mt-3 text-sm text-slate-500">
                  Select a population and outcome, then submit the query.
                </p>
              </div>
            )}
            {loading && <Loading label="Synthesizing evidence…" />}
            {brief && (
              <div className="space-y-5">
                <div className="card p-7">
                  <p className="eyebrow">Evidence brief</p>
                  <h2 className="mt-2 text-3xl font-bold text-navy">{brief.query_description}</h2>

                  <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
                    <div className="rounded-2xl bg-navy/5 p-4 text-center">
                      <p className="text-3xl font-bold text-navy">{brief.study_count}</p>
                      <p className="mt-1 text-xs font-semibold text-slate-500">studies matched</p>
                    </div>
                    <div className="rounded-2xl bg-emerald-50 p-4 text-center">
                      <p className="text-3xl font-bold text-emerald-800">{brief.credible_count}</p>
                      <p className="mt-1 text-xs font-semibold text-emerald-600">credible-tier</p>
                    </div>
                    <div className={`rounded-2xl p-4 text-center ${
                      brief.dominant_direction === "Harmful" ? "bg-scarlet/10" :
                      brief.dominant_direction === "Protective" ? "bg-emerald-50" : "bg-gold/10"}`}>
                      <p className="text-2xl font-bold text-navy">{brief.dominant_direction}</p>
                      <p className="mt-1 text-xs font-semibold text-slate-500">dominant effect</p>
                    </div>
                    <div className={`rounded-2xl border p-4 text-center ${certStyle}`}>
                      <p className="text-lg font-bold">{certLevel}</p>
                      <p className="mt-1 text-xs font-semibold">certainty</p>
                    </div>
                  </div>

                  <div className="mt-7 space-y-4">
                    <div className="rounded-xl bg-navy/5 p-5">
                      <p className="text-sm font-bold text-navy">Causal certainty</p>
                      <p className="mt-2 text-sm leading-6 text-slate-700">{brief.causal_certainty}</p>
                    </div>
                    <div className="rounded-xl bg-navy/5 p-5">
                      <p className="text-sm font-bold text-navy">Effect note</p>
                      <p className="mt-2 text-sm leading-6 text-slate-700">{brief.effect_note}</p>
                    </div>
                    <div className="rounded-xl bg-navy/5 p-5">
                      <p className="text-sm font-bold text-navy">Population relevance</p>
                      <p className="mt-2 text-sm leading-6 text-slate-700">{brief.population_note}</p>
                    </div>
                    <div className="rounded-xl border border-gold/30 bg-gold/10 p-5">
                      <p className="text-sm font-bold text-amber-900">Known limitations</p>
                      <p className="mt-2 text-sm leading-6 text-amber-950">{brief.limitations}</p>
                    </div>
                  </div>
                </div>

                {brief.available_interventions?.length > 0 && (
                  <div className="card p-7">
                    <p className="eyebrow">Available response options</p>
                    <h3 className="mt-2 text-2xl font-bold text-navy">Interventions with evidence</h3>
                    <p className="mt-2 text-sm text-slate-500">
                      Interventions are a distinct causal question from exposure effects.
                    </p>
                    <div className="mt-5 space-y-3">
                      {brief.available_interventions.map((iv) => (
                        <Link
                          key={iv.slug}
                          to={`/studies/${iv.slug}`}
                          className="flex items-center justify-between rounded-xl border border-navy/10 bg-navy/3 p-4 hover:border-navy/30"
                        >
                          <div>
                            <p className="font-semibold text-navy">{iv.citation}</p>
                            <p className="mt-1 text-sm text-slate-600">{iv.intervention_type}</p>
                          </div>
                          <div className="flex flex-col items-end gap-1">
                            <Badge tone={iv.causal_tier === "Credible" ? "green" : "gold"}>{iv.causal_tier}</Badge>
                            <span className={`rounded-full border px-2 py-0.5 text-xs font-bold ${
                              DIRECTION_STYLES[iv.effect_direction] || DIRECTION_STYLES["Needs verification"]}`}>
                              {iv.effect_direction}
                            </span>
                          </div>
                        </Link>
                      ))}
                    </div>
                  </div>
                )}

                {brief.evidence_gaps?.length > 0 && (
                  <div className="card border-gold/30 p-7">
                    <p className="eyebrow">Evidence gaps for this query</p>
                    <h3 className="mt-2 text-2xl font-bold text-navy">What the evidence cannot yet answer</h3>
                    <ul className="mt-5 space-y-3">
                      {brief.evidence_gaps.map((gap, i) => (
                        <li key={i} className="flex gap-3 text-sm leading-6 text-slate-700">
                          <span className="mt-0.5 shrink-0 text-gold font-bold">▲</span>
                          {gap}
                        </li>
                      ))}
                    </ul>
                    <Link to="/gaps" className="mt-5 block text-sm font-bold text-scarlet hover:underline">
                      View full evidence gap radar →
                    </Link>
                  </div>
                )}

                {brief.last_searched && (
                  <p className="text-xs text-slate-400">
                    Registry last searched {brief.last_searched} ·{" "}
                    {brief.pending_candidates > 0
                      ? `${brief.pending_candidates} publications awaiting review`
                      : "All candidates reviewed"}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}


// ── Evidence gap radar page ───────────────────────────────────────────────────

function GapRadarPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [domainFilter, setDomainFilter] = useState("All");

  useEffect(() => {
    getGaps().then(setData).catch((err) => setError(err.message));
  }, []);

  if (error) return <ErrorMessage message={error} />;
  if (!data) return <Loading label="Computing evidence gaps…" />;

  const domains = ["All", "Geographic", "Outcome", "Method", "Population"];
  const filtered = domainFilter === "All" ? data.gaps : data.gaps.filter((g) => g.domain === domainFilter);
  const high = data.gaps.filter((g) => g.priority === "High").length;

  const topCountries = Object.entries(data.geographic_breakdown)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 8);

  const maxCount = Math.max(...topCountries.map(([, n]) => n), 1);

  return (
    <main>
      <section className="bg-navy text-white">
        <div className="page-shell py-16">
          <p className="eyebrow text-gold">Evidence gap radar</p>
          <h1 className="mt-3 max-w-3xl text-5xl font-bold">
            Where is the evidence missing?
          </h1>
          <p className="mt-5 max-w-2xl text-lg leading-8 text-white/80">
            VICINITY automatically computes evidence gaps from live registry data. Gaps guide
            dissertation topics, grant priorities, collaboration invitations, and future search
            strategies. This view updates every time a new study enters the registry.
          </p>
          <div className="mt-8 flex flex-wrap gap-6">
            <div>
              <p className="text-4xl font-bold">{data.gaps.length}</p>
              <p className="mt-1 text-sm text-white/65">identified gaps</p>
            </div>
            <div>
              <p className="text-4xl font-bold text-scarlet">{high}</p>
              <p className="mt-1 text-sm text-white/65">high-priority gaps</p>
            </div>
            <div>
              <p className="text-4xl font-bold">{data.total_studies}</p>
              <p className="mt-1 text-sm text-white/65">studies analyzed</p>
            </div>
          </div>
        </div>
      </section>

      <div className="page-shell py-12">
        <div className="grid gap-10 lg:grid-cols-[280px_1fr]">
          {/* Geographic sidebar */}
          <aside className="space-y-6">
            <div className="card p-6">
              <h2 className="text-lg font-bold text-navy">Geographic coverage</h2>
              <p className="mt-1 text-xs text-slate-500">Studies by country</p>
              <div className="mt-5 space-y-3">
                {topCountries.map(([country, n]) => (
                  <div key={country}>
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium text-navy truncate mr-2">{country}</span>
                      <span className="font-bold text-navy shrink-0">{n}</span>
                    </div>
                    <div className="mt-1 h-2 w-full rounded-full bg-navy/10">
                      <div
                        className="h-2 rounded-full bg-scarlet transition-all"
                        style={{ width: `${(n / maxCount) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="card p-6">
              <h2 className="text-lg font-bold text-navy">Outcome coverage</h2>
              <p className="mt-1 text-xs text-slate-500">Top outcomes</p>
              <div className="mt-4 space-y-2">
                {Object.entries(data.outcome_breakdown)
                  .sort(([, a], [, b]) => b - a)
                  .slice(0, 6)
                  .map(([outcome, n]) => (
                    <div key={outcome} className="flex items-center justify-between text-sm">
                      <span className="text-slate-600 truncate mr-2">{outcome}</span>
                      <Badge tone={n < 3 ? "red" : n < 6 ? "gold" : "green"}>{n}</Badge>
                    </div>
                  ))}
              </div>
            </div>
          </aside>

          {/* Gap cards */}
          <div>
            <div className="flex flex-wrap gap-2 mb-8">
              {domains.map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => setDomainFilter(d)}
                  className={`rounded-full px-4 py-2 text-sm font-bold transition ${
                    domainFilter === d ? "bg-navy text-white" : "bg-navy/5 text-navy hover:bg-navy/10"
                  }`}
                >
                  {d === "All" ? `All gaps (${data.gaps.length})` : `${DOMAIN_ICONS[d]} ${d}`}
                </button>
              ))}
            </div>

            <div className="space-y-4">
              {filtered.map((gap, i) => (
                <div key={i} className={`card p-6 ${PRIORITY_STYLES[gap.priority] || ""}`}>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{DOMAIN_ICONS[gap.domain]}</span>
                        <p className="font-bold text-navy text-lg">{gap.label}</p>
                      </div>
                      <p className="mt-1 text-xs font-semibold uppercase tracking-wider text-slate-500">
                        {gap.domain} gap
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Badge tone={gap.priority === "High" ? "red" : gap.priority === "Medium" ? "gold" : "navy"}>
                        {gap.priority} priority
                      </Badge>
                      <Badge>{gap.n_studies} studies</Badge>
                    </div>
                  </div>
                  <p className="mt-4 text-sm leading-6 text-slate-700">{gap.description}</p>
                  <div className="mt-4 rounded-xl border border-navy/10 bg-white p-4">
                    <p className="text-xs font-bold uppercase tracking-wider text-navy">Suggested action</p>
                    <p className="mt-1 text-sm leading-6 text-slate-700">{gap.suggested_action}</p>
                  </div>
                </div>
              ))}
            </div>

            <p className="mt-8 text-xs text-slate-400">
              Gap radar computed at {new Date(data.computed_at).toLocaleString()}. Updates automatically
              as studies enter the registry.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}


// ── Changelog page ────────────────────────────────────────────────────────────

function ChangelogPage() {
  const [entries, setEntries] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    getChangelog().then(setEntries).catch((err) => setError(err.message));
  }, []);

  if (error) return <ErrorMessage message={error} />;
  if (!entries.length) return <Loading label="Loading changelog…" />;

  return (
    <main>
      <section className="bg-navy text-white">
        <div className="page-shell py-16">
          <p className="eyebrow text-gold">Public audit trail</p>
          <h1 className="mt-3 max-w-3xl text-5xl font-bold">Registry changelog</h1>
          <p className="mt-5 max-w-2xl text-lg leading-8 text-white/80">
            Every addition, correction, and surveillance run is publicly recorded. Researchers can
            cite specific versions. The changelog is the foundation of VICINITY's reproducibility claim.
          </p>
        </div>
      </section>

      <div className="page-shell py-12">
        <div className="mx-auto max-w-3xl">
          <div className="flex flex-wrap gap-3 mb-8">
            <a href={exportUrl("csv")} className="button-secondary text-sm">
              Download registry CSV ↓
            </a>
            <a href={exportUrl("json")} className="button-secondary text-sm">
              Download registry JSON ↓
            </a>
          </div>

          <div className="relative space-y-6 before:absolute before:left-6 before:top-4 before:h-[calc(100%-2rem)] before:w-px before:bg-navy/15">
            {entries.map((entry) => (
              <div key={entry.id} className="relative flex gap-6">
                <div className="relative z-10 mt-1 flex h-12 w-12 shrink-0 items-center justify-center rounded-full border-2 border-navy/15 bg-white shadow">
                  <span className="text-lg">
                    {entry.change_type === "addition" ? "+" :
                     entry.change_type === "correction" ? "✎" :
                     entry.change_type === "surveillance" ? "🔍" :
                     entry.change_type === "retraction" ? "✗" : "≡"}
                  </span>
                </div>
                <div className="card flex-1 p-6">
                  <div className="flex flex-wrap items-center gap-3">
                    <span className={`rounded-full border px-2.5 py-1 text-xs font-bold ${
                      CHANGE_TYPE_STYLES[entry.change_type] || ""}`}>
                      {entry.change_type}
                    </span>
                    <span className="rounded-full bg-navy/5 px-2.5 py-1 text-xs font-bold text-navy">
                      v{entry.version}
                    </span>
                    <span className="text-xs text-slate-400">
                      {new Date(entry.created_at).toLocaleDateString("en-US", {
                        year: "numeric", month: "long", day: "numeric",
                      })}
                    </span>
                  </div>
                  <p className="mt-4 text-sm leading-7 text-slate-700">{entry.summary}</p>
                  {entry.study_count_after > 0 && (
                    <p className="mt-3 text-xs font-semibold text-slate-500">
                      Registry size: {entry.study_count_before} → {entry.study_count_after} studies
                    </p>
                  )}
                  {entry.affected_studies?.length > 0 && (
                    <p className="mt-2 text-xs text-slate-400">
                      Affected: {entry.affected_studies.join(", ")}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="mt-12 rounded-2xl border border-navy/10 bg-navy/3 p-7">
            <h2 className="text-xl font-bold text-navy">How to cite a specific version</h2>
            <p className="mt-3 text-sm leading-7 text-slate-700">
              Use the version number and the access date when citing VICINITY in a publication.
              Permanent versioned releases with DOIs are planned for each calendar-year update.
            </p>
            <div className="mt-4 rounded-xl border border-navy/10 bg-white p-5 font-mono text-sm leading-6 text-slate-700">
              Abbas, J. (2026). VICINITY: Living Causal Evidence Observatory for Neighborhood Violence
              and Youth Mental Health. Version 2.0. Rutgers University.
              Retrieved [date] from https://vicinity.rutgers.edu
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}


// ── About page ────────────────────────────────────────────────────────────────

function ReleasesSection() {
  const [releases, setReleases] = useState(null);
  useEffect(() => { getReleases().then(setReleases).catch(() => setReleases([])); }, []);

  if (!releases) return null;

  return (
    <section>
      <p className="eyebrow">Versioned releases</p>
      <h2 className="mt-2 text-3xl font-bold text-navy">Permanent snapshots</h2>
      <p className="mt-4 leading-7 text-slate-700">
        Each registry release is a frozen, citable snapshot. Where a DOI has been minted
        (via Zenodo), that identifier is permanent and can be cited in peer-reviewed
        publications. Releases without a Zenodo DOI carry a local identifier pending submission.
      </p>
      <div className="mt-6 space-y-4">
        {releases.map((r) => (
          <div key={r.version} className="card p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-lg font-bold text-navy">Version {r.version}</p>
                <p className="mt-1 text-sm text-slate-500">
                  {new Date(r.release_date).toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}
                  {" · "}{r.study_count} studies · {r.credible_count} credible-tier
                </p>
                {r.doi && (
                  <p className="mt-2 font-mono text-xs text-slate-600 break-all">
                    {r.doi.startsWith("vicinity/") ? (
                      <span className="rounded border border-gold/40 bg-gold/10 px-2 py-0.5 text-amber-900">
                        Local ID (DOI pending Zenodo submission): {r.doi}
                      </span>
                    ) : (
                      <span className="rounded border border-emerald-200 bg-emerald-50 px-2 py-0.5 text-emerald-800">
                        DOI: {r.doi}
                      </span>
                    )}
                  </p>
                )}
                {r.notes && <p className="mt-3 text-sm leading-6 text-slate-600">{r.notes}</p>}
              </div>
              <a
                href={releaseDownloadUrl(r.version)}
                className="button-secondary shrink-0 text-sm"
                download
              >
                Download JSON
              </a>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}


function AboutPage() {
  return (
    <main>
      <section className="bg-navy text-white">
        <div className="page-shell py-20">
          <p className="text-xs font-bold uppercase tracking-[0.24em] text-gold">About VICINITY</p>
          <h1 className="mt-4 max-w-4xl text-5xl font-bold">
            A living evidence system with visible limits.
          </h1>
          <p className="mt-6 max-w-3xl text-lg leading-8 text-white/80">
            VICINITY was created to make evidence about neighborhood violence and youth mental
            health easier to inspect, compare, and use. The registry keeps methodological
            distinctions visible because prevention decisions depend on them.
          </p>
        </div>
      </section>

      <div className="page-shell grid gap-12 py-14 lg:grid-cols-[1fr_300px]">
        <article className="space-y-10">

          <section>
            <p className="eyebrow">Inclusion criteria</p>
            <h2 className="mt-2 text-3xl font-bold text-navy">What enters the registry</h2>
            <p className="mt-4 leading-7 text-slate-700">
              The registry includes studies from two systematic reviews: 32 studies examining
              neighborhood violence exposure and youth mental health outcomes, and 26 intervention
              studies evaluating structural, place-based, and psychosocial responses. Studies
              examine violence exposure or neighborhood conditions and outcomes relevant to mental
              health, behavior, physiology, cognition, or education. Users can filter outcome
              categories because the source includes both direct and proximal measures.
            </p>
          </section>

          <section>
            <p className="eyebrow">Causal identification</p>
            <h2 className="mt-2 text-3xl font-bold text-navy">How the tiers work</h2>
            <p className="mt-4 leading-7 text-slate-700">
              A study enters the credible tier only when the workbook clearly documents a
              randomized trial, difference-in-differences design, natural experiment, instrumental
              variable, within-person fixed-effects design, or within-family fixed-effects design.
              Other quasi-experimental studies remain associational until a reviewer verifies the
              design. Associational studies are not discarded — their tier is visible on every
              card and record.
            </p>
          </section>

          <section>
            <p className="eyebrow">Quality appraisal</p>
            <h2 className="mt-2 text-3xl font-bold text-navy">Risk of bias remains traceable</h2>
            <p className="mt-4 leading-7 text-slate-700">
              The source workbooks contain narrative risk-of-bias assessments. VICINITY maps those
              narratives to low, moderate, high, or needs-verification categories. The original
              appraisal text appears on every study page. A reviewer must verify the normalized
              tier against the final JBI protocol before publication use. Search histories are
              documented using PRISMA-S to enable reproducible re-execution of the full
              surveillance protocol.
            </p>
          </section>

          <section>
            <p className="eyebrow">Data integrity</p>
            <h2 className="mt-2 text-3xl font-bold text-navy">What the registry does not infer</h2>
            <p className="mt-4 leading-7 text-slate-700">
              Where source workbooks lack dedicated DOI, standardized effect-size,
              confidence-interval, or intervention-type fields, VICINITY marks those fields for
              verification. It does not manufacture estimates or promote uncertain designs. All
              derived fields retain visible verification flags.
            </p>
          </section>

          <section>
            <p className="eyebrow">Living evidence pipeline</p>
            <h2 className="mt-2 text-3xl font-bold text-navy">How the registry stays current</h2>
            <p className="mt-4 leading-7 text-slate-700">
              VICINITY runs documented searches each month across PubMed, OpenAlex, Crossref,
              Europe PMC, and ERIC. Every publication moves through a defined workflow: Discovered
              → Deduplicated → Screened → Full text reviewed → Extracted → Appraised → Approved →
              Published. Reviewers make every inclusion and causal-quality decision. The system
              follows the Cochrane living-review standard for continual surveillance, explicit
              update rules, and transparent reporting.
            </p>
          </section>

          <ReleasesSection />

          <section>
            <p className="eyebrow">Attribution</p>
            <h2 className="mt-2 text-3xl font-bold text-navy">Citation</h2>
            <div className="mt-4 space-y-4 rounded-2xl border border-navy/10 bg-white p-7">
              <div>
                <p className="text-sm font-bold text-navy">Principal developer</p>
                <p className="mt-1 text-slate-700">
                  J. Abbas · PhD Candidate · School of Social Work · Rutgers University
                </p>
              </div>
              <div>
                <p className="text-sm font-bold text-navy">Systematic review registration</p>
                <p className="mt-1 text-slate-700">PROSPERO (2024). Pre-registered protocol available on request.</p>
              </div>
              <div>
                <p className="text-sm font-bold text-navy">How to cite the registry</p>
                <p className="mt-2 rounded-xl border border-navy/10 bg-navy/3 p-4 font-mono text-sm leading-6 text-slate-700">
                  Abbas, J. (2026). VICINITY: Causal Evidence Registry for Neighborhood Violence
                  and Youth Mental Health. Version 1.0.
                </p>
              </div>
            </div>
          </section>

        </article>

        <aside className="space-y-5">
          <div className="card p-6">
            <h2 className="text-xl font-bold text-navy">Current release</h2>
            <ul className="mt-5 space-y-3 text-sm leading-6 text-slate-700">
              <li>58 validated study records</li>
              <li>32 exposure studies</li>
              <li>26 intervention studies</li>
              <li>Field-level verification queue</li>
              <li>Live evidence gap radar</li>
              <li>Practitioner query interface</li>
              <li>Private reviewer dashboard</li>
              <li>Monthly surveillance pipeline</li>
              <li>Public changelog</li>
              <li>CSV and JSON export</li>
            </ul>
          </div>

          <div className="card p-6">
            <h2 className="text-xl font-bold text-navy">Platforms compared</h2>
            <dl className="mt-4 space-y-4 text-sm">
              {[
                ["Youth Endowment Fund", "Broad approaches"],
                ["CrimeSolutions", "Criminal justice"],
                ["Blueprints", "Certified programs"],
                ["3ie", "Evidence gap maps"],
                ["VICINITY", "All of the above + causal design + living pipeline"],
              ].map(([name, scope]) => (
                <div key={name}>
                  <dt className="font-bold text-navy">{name}</dt>
                  <dd className="text-slate-600">{scope}</dd>
                </div>
              ))}
            </dl>
          </div>

          <Link to="/submit" className="button-primary block w-full text-center">Nominate a study</Link>
        </aside>
      </div>
    </main>
  );
}


// ── Submit page ───────────────────────────────────────────────────────────────

const SUBMISSION_FIELDS = [
  ["citation", "Citation", "text", "Full study citation"],
  ["doi", "DOI", "text", "10.xxxx/xxxxx"],
  ["design_type", "Design type", "text", "Example: difference-in-differences"],
  ["population", "Population", "textarea", "Age range, setting, and sample"],
  ["exposure", "Exposure", "textarea", "Violence exposure and spatial or temporal window"],
  ["outcome", "Outcome", "textarea", "Primary mental health outcome and measure"],
  ["effect_size", "Effect size", "text", "Estimate, unit, and confidence interval"],
  ["submitter_name", "Your name (optional)", "text", ""],
  ["submitter_email", "Your email (optional)", "email", ""],
  ["notes", "Notes (optional)", "textarea", "Why this study may meet the criteria"],
];


function SubmitPage() {
  const [form, setForm] = useState(Object.fromEntries(SUBMISSION_FIELDS.map(([name]) => [name, ""])));
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const update = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const payload = Object.fromEntries(
        Object.entries(form).map(([key, value]) => [key, value.trim() || null]),
      );
      ["citation", "doi", "design_type", "population", "exposure", "outcome", "effect_size"].forEach(
        (key) => { payload[key] = form[key].trim(); },
      );
      setResult(await submitStudy(payload));
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  if (result) {
    return (
      <main className="page-shell py-20">
        <div className="card mx-auto max-w-2xl p-10 text-center">
          <p className="eyebrow">Submission received</p>
          <h1 className="mt-3 text-4xl font-bold text-navy">The study is in the review queue.</h1>
          <p className="mt-5 leading-7 text-slate-700">{result.message}</p>
          <p className="mt-3 text-sm font-semibold text-slate-500">Queue reference: {result.id}</p>
          <Link to="/registry" className="button-primary mt-7">Return to the registry</Link>
        </div>
      </main>
    );
  }

  return (
    <main className="page-shell py-12">
      <div className="mx-auto max-w-3xl">
        <p className="eyebrow">Submit a study</p>
        <h1 className="mt-2 text-4xl font-bold text-navy">Nominate evidence for review</h1>
        <p className="mt-4 leading-7 text-slate-600">
          A nomination does not enter the public registry immediately. The review checks eligibility,
          extraction accuracy, causal identification, and risk of bias.
        </p>
        <form onSubmit={handleSubmit} className="card mt-8 grid gap-5 p-7 sm:grid-cols-2">
          {SUBMISSION_FIELDS.map(([name, label, type, placeholder]) => {
            const required = !["submitter_name", "submitter_email", "notes"].includes(name);
            const wide = ["citation", "population", "exposure", "outcome", "notes"].includes(name);
            return (
              <label key={name} className={wide ? "sm:col-span-2" : ""}>
                <span className="label">{label}{required ? " *" : ""}</span>
                {type === "textarea" ? (
                  <textarea className="field min-h-28" name={name} value={form[name]}
                    onChange={update} placeholder={placeholder} required={required} />
                ) : (
                  <input className="field" type={type} name={name} value={form[name]}
                    onChange={update} placeholder={placeholder} required={required} />
                )}
              </label>
            );
          })}
          {error && (
            <p className="sm:col-span-2 rounded-xl border border-scarlet/20 bg-scarlet/5 p-4 text-sm text-scarlet">
              {error}
            </p>
          )}
          <div className="sm:col-span-2">
            <button disabled={submitting} type="submit" className="button-primary w-full disabled:opacity-60">
              {submitting ? "Submitting…" : "Submit to the review queue"}
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}


// ── Reviewer dashboard ────────────────────────────────────────────────────────

function ReviewerDashboard({ token, onLogout }) {
  const [dashboard, setDashboard] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [error, setError] = useState("");
  const [tab, setTab] = useState("overview");
  const [triggerResult, setTriggerResult] = useState(null);
  const [triggering, setTriggering] = useState(false);
  const [rescoring, setRescoring] = useState(false);
  const [rescoreResult, setRescoreResult] = useState(null);
  const [releaseVersion, setReleaseVersion] = useState("");
  const [releaseNotes, setReleaseNotes] = useState("");
  const [creatingRelease, setCreatingRelease] = useState(false);
  const [releaseResult, setReleaseResult] = useState(null);

  const reload = () => {
    getDashboard(token).then(setDashboard).catch((err) => setError(err.message));
    getCandidates(token).then(setCandidates).catch((err) => setError(err.message));
  };

  useEffect(() => { reload(); }, [token]);

  const handleTrigger = async () => {
    setTriggering(true);
    try {
      const result = await triggerSearch(token);
      setTriggerResult(result);
      reload();
    } catch (err) {
      setError(err.message);
    } finally {
      setTriggering(false);
    }
  };

  const handleRescore = async () => {
    setRescoring(true);
    setRescoreResult(null);
    try {
      const result = await rescoreCandidates(token);
      setRescoreResult(result);
      reload();
    } catch (err) {
      setError(err.message);
    } finally {
      setRescoring(false);
    }
  };

  const handleCreateRelease = async (e) => {
    e.preventDefault();
    if (!releaseVersion.trim()) return;
    setCreatingRelease(true);
    setReleaseResult(null);
    try {
      const result = await createRelease(token, releaseVersion.trim(), releaseNotes.trim());
      setReleaseResult(result);
      setReleaseVersion("");
      setReleaseNotes("");
    } catch (err) {
      setError(err.message);
    } finally {
      setCreatingRelease(false);
    }
  };

  const handleScreen = async (id, decision, reason) => {
    try {
      await screenCandidate(token, id, decision, reason);
      reload();
    } catch (err) {
      setError(err.message);
    }
  };

  if (error) return (
    <div className="page-shell py-16">
      <div className="card border-scarlet/30 p-6">
        <p className="font-bold text-scarlet">Dashboard error</p>
        <p className="mt-2 text-sm text-slate-700">{error}</p>
        <button onClick={onLogout} className="button-secondary mt-4">Log out</button>
      </div>
    </div>
  );

  if (!dashboard) return <Loading label="Loading reviewer dashboard…" />;

  const statCards = [
    { label: "Total approved", value: dashboard.total_studies, color: "text-navy" },
    { label: "Exposure studies", value: dashboard.exposure_count, color: "text-scarlet" },
    { label: "Intervention studies", value: dashboard.intervention_count, color: "text-emerald-700" },
    { label: "Pending candidates", value: dashboard.pending_candidates, color: "text-amber-700" },
    { label: "Awaiting screen", value: dashboard.awaiting_screen, color: "text-purple-700" },
    { label: "Awaiting full text", value: dashboard.awaiting_fulltext, color: "text-sky-700" },
  ];

  return (
    <div className="page-shell py-10">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="eyebrow">Private dashboard</p>
          <h1 className="mt-1 text-4xl font-bold text-navy">Reviewer workspace</h1>
        </div>
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={handleTrigger}
            disabled={triggering}
            className="button-primary disabled:opacity-60"
          >
            {triggering ? "Searching OpenAlex…" : "Trigger surveillance run"}
          </button>
          <button
            type="button"
            onClick={handleRescore}
            disabled={rescoring}
            className="button-secondary disabled:opacity-60"
          >
            {rescoring ? "Scoring…" : "Rescore candidates"}
          </button>
          <button type="button" onClick={onLogout} className="button-secondary">
            Log out
          </button>
        </div>
      </div>

      {triggerResult && (
        <div className="mt-5 rounded-xl border border-emerald-200 bg-emerald-50 p-5">
          <p className="font-bold text-emerald-800">Live OpenAlex search completed</p>
          <p className="mt-1 text-sm text-emerald-700">
            {triggerResult.candidates_found} publications retrieved · {triggerResult.new_candidates} new after deduplication
            · Source: {triggerResult.source || "OpenAlex API"}
          </p>
        </div>
      )}
      {rescoreResult && (
        <div className="mt-4 rounded-xl border border-sky-200 bg-sky-50 p-4">
          <p className="font-bold text-sky-800">Relevance scores updated</p>
          <p className="mt-1 text-sm text-sky-700">
            {rescoreResult.rescored} of {rescoreResult.total} candidates rescored using keyword-weighted algorithm.
          </p>
        </div>
      )}

      {/* Stats overview */}
      <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        {statCards.map((card) => (
          <div key={card.label} className="card p-5 text-center">
            <p className={`text-3xl font-bold ${card.color}`}>{card.value}</p>
            <p className="mt-1 text-xs font-semibold text-slate-500">{card.label}</p>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="mt-8 flex gap-1 border-b border-navy/10">
        {[["overview", "Overview"], ["candidates", "Candidate queue"], ["runs", "Search runs"]].map(([key, label]) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={`px-5 py-3 text-sm font-bold transition border-b-2 ${
              tab === key ? "border-scarlet text-scarlet" : "border-transparent text-navy hover:text-scarlet"
            }`}
          >
            {label}
            {key === "candidates" && dashboard.pending_candidates > 0 && (
              <span className="ml-2 rounded-full bg-scarlet px-1.5 py-0.5 text-xs text-white">
                {dashboard.pending_candidates}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Overview tab */}
      {tab === "overview" && (
        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <div className="card p-6">
            <h2 className="text-xl font-bold text-navy">Recent candidates</h2>
            <p className="mt-1 text-sm text-slate-500">Newly discovered publications requiring screen decision</p>
            <div className="mt-5 space-y-4">
              {dashboard.recent_candidates.slice(0, 5).map((c) => (
                <div key={c.id} className="rounded-xl border border-navy/10 p-4">
                  <p className="font-semibold text-navy text-sm leading-tight">{c.title}</p>
                  <p className="mt-1 text-xs text-slate-500">{c.authors} · {c.year} · {c.journal}</p>
                  <div className="mt-2 flex items-center gap-2">
                    <Badge tone="sky">{c.source_database}</Badge>
                    {c.relevance_score != null && (
                      <span className="text-xs font-bold text-slate-500">Score: {c.relevance_score}</span>
                    )}
                  </div>
                </div>
              ))}
              {dashboard.recent_candidates.length === 0 && (
                <p className="text-sm text-slate-500">No pending candidates.</p>
              )}
            </div>
          </div>
          <div className="card p-6">
            <h2 className="text-xl font-bold text-navy">Recent search runs</h2>
            <p className="mt-1 text-sm text-slate-500">Monthly surveillance history</p>
            <div className="mt-5 space-y-3">
              {dashboard.recent_runs.map((run) => (
                <div key={run.id} className="rounded-xl border border-navy/10 p-4">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-semibold text-navy">
                      {new Date(run.run_date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                    </p>
                    <Badge tone={run.status === "completed" ? "green" : "gold"}>{run.status}</Badge>
                  </div>
                  <p className="mt-1 text-xs text-slate-500">
                    {run.candidates_found} found · {run.new_candidates} new · {run.databases_searched?.join(", ")}
                  </p>
                  <p className="mt-1 text-xs text-slate-400 capitalize">{run.triggered_by}</p>
                </div>
              ))}
              {dashboard.recent_runs.length === 0 && (
                <p className="text-sm text-slate-500">No search runs yet. Trigger the first one above.</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Releases tab added inline in overview */}
      {tab === "overview" && (
        <div className="mt-6">
          <div className="card p-6">
            <h2 className="text-xl font-bold text-navy">Create versioned release</h2>
            <p className="mt-1 text-sm text-slate-500">
              Snapshot the current registry with a DOI-ready version identifier.
              Set <span className="font-mono text-xs">ZENODO_TOKEN</span> env var to mint a real Zenodo DOI automatically.
            </p>
            <form onSubmit={handleCreateRelease} className="mt-5 flex flex-wrap gap-3 items-end">
              <div>
                <label className="block text-xs font-bold text-navy mb-1">Version</label>
                <input
                  type="text"
                  value={releaseVersion}
                  onChange={(e) => setReleaseVersion(e.target.value)}
                  placeholder="e.g. 2.1"
                  className="rounded-xl border border-navy/20 px-4 py-2 text-sm w-28"
                  required
                />
              </div>
              <div className="flex-1 min-w-48">
                <label className="block text-xs font-bold text-navy mb-1">Release notes (optional)</label>
                <input
                  type="text"
                  value={releaseNotes}
                  onChange={(e) => setReleaseNotes(e.target.value)}
                  placeholder="What changed in this release"
                  className="w-full rounded-xl border border-navy/20 px-4 py-2 text-sm"
                />
              </div>
              <button
                type="submit"
                disabled={creatingRelease || !releaseVersion.trim()}
                className="button-primary disabled:opacity-60"
              >
                {creatingRelease ? "Creating…" : "Create release"}
              </button>
            </form>
            {releaseResult && (
              <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 p-4">
                <p className="font-bold text-emerald-800">Release v{releaseResult.version} created</p>
                <p className="mt-1 text-sm text-emerald-700 break-all">
                  {releaseResult.zenodo_minted
                    ? `Zenodo DOI minted: ${releaseResult.doi}`
                    : `Local identifier assigned: ${releaseResult.doi}. Set ZENODO_TOKEN to mint a permanent DOI.`
                  }
                </p>
                <p className="mt-1 text-sm text-emerald-600">{releaseResult.study_count} studies frozen.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Candidate queue tab */}
      {tab === "candidates" && (
        <div className="mt-6 space-y-4">
          {candidates.length === 0 && (
            <div className="card p-10 text-center">
              <p className="font-bold text-navy">No candidates in queue.</p>
              <p className="mt-2 text-sm text-slate-500">Trigger a surveillance run to discover new publications.</p>
            </div>
          )}
          {candidates.map((c) => (
            <div key={c.id} className="card p-6">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <p className="font-bold text-navy leading-tight">{c.title}</p>
                  <p className="mt-1 text-sm text-slate-600">{c.authors}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    {c.year} · {c.journal}
                    {c.doi && <> · <span className="font-mono">{c.doi}</span></>}
                  </p>
                </div>
                <div className="flex gap-2 flex-wrap">
                  <Badge tone="sky">{c.source_database}</Badge>
                  <Badge tone={
                    c.status === "rejected" ? "red" :
                    c.status === "discovered" ? "gold" : "green"
                  }>{c.status}</Badge>
                  {c.relevance_score != null && (
                    <span className="text-xs font-bold text-slate-500 self-center">
                      AI score: {c.relevance_score}
                    </span>
                  )}
                </div>
              </div>

              {c.abstract && (
                <p className="mt-4 text-sm leading-6 text-slate-600 line-clamp-3">{c.abstract}</p>
              )}

              {c.status === "discovered" && (
                <div className="mt-5 space-y-3">
                  <p className="text-sm font-bold text-navy">Screen decision</p>
                  <div className="flex flex-wrap gap-2">
                    {["include", "exclude", "uncertain"].map((dec) => (
                      <button
                        key={dec}
                        type="button"
                        onClick={() => {
                          const reason = prompt(`Reason for "${dec}" decision:`) || "";
                          if (reason) handleScreen(c.id, dec, reason);
                        }}
                        className={`rounded-full px-4 py-2 text-xs font-bold transition ${
                          dec === "include" ? "bg-emerald-100 text-emerald-800 hover:bg-emerald-200" :
                          dec === "exclude" ? "bg-scarlet/10 text-scarlet hover:bg-scarlet/20" :
                          "bg-gold/15 text-amber-900 hover:bg-gold/25"}`}
                      >
                        {dec.charAt(0).toUpperCase() + dec.slice(1)}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {c.screen_decision && (
                <p className="mt-3 text-xs text-slate-500">
                  Screen: <span className="font-semibold">{c.screen_decision}</span>
                  {c.screen_reason && <> — {c.screen_reason}</>}
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Runs tab */}
      {tab === "runs" && (
        <div className="mt-6 space-y-4">
          {dashboard.recent_runs.map((run) => (
            <div key={run.id} className="card p-6">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="font-bold text-navy">
                    {new Date(run.run_date).toLocaleDateString("en-US", {
                      weekday: "long", year: "numeric", month: "long", day: "numeric",
                    })}
                  </p>
                  <p className="mt-1 text-sm text-slate-500">{run.databases_searched?.join(", ")}</p>
                </div>
                <Badge tone={run.status === "completed" ? "green" : "gold"}>{run.status}</Badge>
              </div>
              <div className="mt-4 grid grid-cols-3 gap-4 text-center">
                <div className="rounded-xl bg-navy/5 p-3">
                  <p className="text-2xl font-bold text-navy">{run.candidates_found}</p>
                  <p className="text-xs text-slate-500">found</p>
                </div>
                <div className="rounded-xl bg-navy/5 p-3">
                  <p className="text-2xl font-bold text-navy">{run.new_candidates}</p>
                  <p className="text-xs text-slate-500">new candidates</p>
                </div>
                <div className="rounded-xl bg-navy/5 p-3">
                  <p className="text-2xl font-bold text-slate-400">
                    {run.candidates_found - run.new_candidates}
                  </p>
                  <p className="text-xs text-slate-500">duplicates</p>
                </div>
              </div>
              <p className="mt-3 text-xs text-slate-400 capitalize">Triggered by: {run.triggered_by}</p>
            </div>
          ))}
          {dashboard.recent_runs.length === 0 && (
            <div className="card p-10 text-center">
              <p className="font-bold text-navy">No runs yet.</p>
              <p className="mt-2 text-sm text-slate-500">
                Click "Trigger surveillance run" to start the first monthly search.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}


function ReviewerPage() {
  const [token, setToken] = useState(() => sessionStorage.getItem("vicinity_reviewer_token") || "");
  const [inputToken, setInputToken] = useState("");
  const [authError, setAuthError] = useState("");
  const [authenticating, setAuthenticating] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setAuthenticating(true);
    setAuthError("");
    try {
      const result = await reviewerLogin(inputToken.trim());
      if (result.authenticated) {
        sessionStorage.setItem("vicinity_reviewer_token", inputToken.trim());
        setToken(inputToken.trim());
      }
    } catch (err) {
      setAuthError("Invalid reviewer token. Please check with the registry administrator.");
    } finally {
      setAuthenticating(false);
    }
  };

  const handleLogout = () => {
    sessionStorage.removeItem("vicinity_reviewer_token");
    setToken("");
    setInputToken("");
  };

  if (token) {
    return <ReviewerDashboard token={token} onLogout={handleLogout} />;
  }

  return (
    <main className="page-shell py-24">
      <div className="mx-auto max-w-md">
        <p className="eyebrow">Private access</p>
        <h1 className="mt-2 text-4xl font-bold text-navy">Reviewer dashboard</h1>
        <p className="mt-4 leading-7 text-slate-600">
          This area is restricted to authorized reviewers. Enter your reviewer token to access the
          literature surveillance queue, screening workflow, and registry management tools.
        </p>
        <form onSubmit={handleLogin} className="card mt-8 space-y-5 p-7">
          <label>
            <span className="label">Reviewer token</span>
            <input
              className="field"
              type="password"
              value={inputToken}
              onChange={(e) => setInputToken(e.target.value)}
              placeholder="Enter your reviewer token"
              required
            />
          </label>
          {authError && (
            <p className="rounded-xl border border-scarlet/20 bg-scarlet/5 p-4 text-sm text-scarlet">
              {authError}
            </p>
          )}
          <button disabled={authenticating} type="submit" className="button-primary w-full disabled:opacity-60">
            {authenticating ? "Verifying…" : "Access dashboard"}
          </button>
        </form>
      </div>
    </main>
  );
}


// ── Implementation stream page ────────────────────────────────────────────────

const IMPLEMENTATION_DOMAINS = [
  {
    domain: "Population fit",
    question: "Does the study sample match the population you serve?",
    dimensions: ["Age range", "Gender composition", "Race/ethnicity", "Urbanicity", "Income level"],
    guidance:
      "Interventions tested in one demographic context can transfer, but effect sizes often attenuate. Look for studies with similar age ranges and neighborhood poverty levels before assuming transferability.",
  },
  {
    domain: "Setting transferability",
    question: "Was the intervention tested in a comparable setting?",
    dimensions: ["City size", "Crime rate", "School type", "Housing density", "Policy environment"],
    guidance:
      "Place-based interventions (greening, lighting, housing mobility) are sensitive to local housing markets and zoning. Psychosocial interventions depend on trained providers and school buy-in.",
  },
  {
    domain: "Implementation requirements",
    question: "What does this intervention require to deliver?",
    dimensions: ["Staff training", "Fidelity protocols", "Technology", "Physical space", "Time commitment"],
    guidance:
      "High-fidelity programs like TF-CBT require 8–25 sessions with a licensed clinician. School-based programs depend on administrator approval and class-time access.",
  },
  {
    domain: "Cost and sustainability",
    question: "What does it cost and who has funded it?",
    dimensions: ["Per-participant cost", "Funding source", "Ongoing costs", "Revenue model", "Scale economics"],
    guidance:
      "Most published RCTs were funded by NIH or federal grants. Real-world implementation costs often exceed trial costs by 2–4× after accounting for staff time and overhead.",
  },
  {
    domain: "Equity implications",
    question: "Who benefits most — and who might be left out?",
    dimensions: ["Differential effects by subgroup", "Access barriers", "Stigma", "Language", "Trust"],
    guidance:
      "Several housing mobility studies show larger effects for younger children (ages 0–13). Opt-in designs may systematically exclude families with the highest needs.",
  },
];

function ImplementationPage() {
  return (
    <main>
      <section className="bg-navy text-white">
        <div className="page-shell py-20">
          <p className="text-xs font-bold uppercase tracking-[0.24em] text-gold">Stream 3 — Implementation</p>
          <h1 className="mt-4 max-w-4xl text-5xl font-bold">Will it work here?</h1>
          <p className="mt-6 max-w-3xl text-lg leading-8 text-white/80">
            Knowing that an intervention works on average is necessary but not sufficient. This stream
            covers the five domains that determine whether a study finding will transfer to a specific
            community, school, or clinical setting.
          </p>
        </div>
      </section>

      <div className="page-shell py-14">
        <div className="mb-10 rounded-2xl border border-gold/40 bg-gold/10 p-6">
          <p className="font-bold text-amber-900">This stream is under active development.</p>
          <p className="mt-2 text-sm leading-6 text-slate-700">
            Implementation evidence will be extracted from the 26 intervention studies already in
            the registry and supplemented by implementation science literature. The framework below
            defines what will be coded. Practitioners and researchers can nominate studies with
            implementation data via the{" "}
            <Link to="/submit" className="font-bold text-scarlet hover:underline">nomination form</Link>.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {IMPLEMENTATION_DOMAINS.map((d) => (
            <div key={d.domain} className="card p-7">
              <p className="eyebrow">{d.domain}</p>
              <h2 className="mt-2 text-xl font-bold text-navy">{d.question}</h2>
              <ul className="mt-4 space-y-1 text-sm text-slate-600">
                {d.dimensions.map((dim) => (
                  <li key={dim} className="flex items-start gap-2">
                    <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-scarlet" />
                    {dim}
                  </li>
                ))}
              </ul>
              <p className="mt-5 text-sm leading-6 text-slate-500 border-t border-navy/10 pt-4">{d.guidance}</p>
            </div>
          ))}
        </div>

        <div className="mt-12 rounded-2xl bg-navy p-8 text-white">
          <h2 className="text-2xl font-bold">How to use this framework now</h2>
          <p className="mt-4 leading-7 text-white/80">
            Until structured implementation data is coded, apply this framework manually to any
            intervention study in the registry. Open a study, read the population details and
            policy implications fields, and score each domain against your local context. Studies
            with high population fit and low implementation burden have the best transfer prospects.
          </p>
          <div className="mt-6 flex gap-4">
            <Link to="/registry?stream=intervention" className="button-primary">Browse intervention studies</Link>
            <Link to="/ask" className="button-secondary">Practitioner query</Link>
          </div>
        </div>
      </div>
    </main>
  );
}


// ── 404 ───────────────────────────────────────────────────────────────────────

function NotFoundPage() {
  return (
    <main className="page-shell py-24 text-center">
      <p className="eyebrow">404</p>
      <h1 className="mt-3 text-4xl font-bold text-navy">This page does not exist.</h1>
      <Link to="/" className="button-primary mt-7">Return home</Link>
    </main>
  );
}


// ── App root ──────────────────────────────────────────────────────────────────

export default function App() {
  const [reviewerToken] = useState(() => sessionStorage.getItem("vicinity_reviewer_token") || "");

  return (
    <div className="min-h-screen">
      <Header reviewerToken={reviewerToken} />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/registry" element={<RegistryPage />} />
        <Route path="/studies/:slug" element={<StudyDetailPage />} />
        <Route path="/ask" element={<AskPage />} />
        <Route path="/gaps" element={<GapRadarPage />} />
        <Route path="/changelog" element={<ChangelogPage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/submit" element={<SubmitPage />} />
        <Route path="/reviewer" element={<ReviewerPage />} />
        <Route path="/implementation" element={<ImplementationPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
      <Footer />
    </div>
  );
}
