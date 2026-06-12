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

import { getStats, getStudies, getStudy, submitStudy } from "./api";


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
};

const DIRECTION_STYLES = {
  Harmful: "bg-scarlet/10 text-scarlet border-scarlet/20",
  Protective: "bg-emerald-50 text-emerald-800 border-emerald-200",
  Mixed: "bg-gold/15 text-amber-900 border-gold/30",
  Null: "bg-slate-100 text-slate-700 border-slate-200",
  "Needs verification": "bg-purple-50 text-purple-800 border-purple-200",
};


function Header() {
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
            Evidence Registry
          </span>
        </Link>
        <nav aria-label="Primary" className="flex items-center gap-1">
          <NavLink to="/registry" className={navClass}>Registry</NavLink>
          <NavLink to="/about" className={navClass}>About</NavLink>
          <NavLink to="/submit" className={navClass}>Submit</NavLink>
        </nav>
      </div>
    </header>
  );
}


function Footer() {
  return (
    <footer className="mt-20 border-t border-navy/10 bg-navy text-white">
      <div className="page-shell grid gap-8 py-10 md:grid-cols-[1.5fr_1fr]">
        <div>
          <p className="font-serif text-2xl font-bold">VICINITY</p>
          <p className="mt-2 max-w-xl text-sm leading-6 text-white/75">
            What the best evidence actually shows. Updated as it happens.
          </p>
        </div>
        <div className="text-sm leading-6 text-white/75">
          <p>Built for researchers and prevention practitioners.</p>
          <p>All derived fields retain visible verification flags.</p>
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
  };
  return (
    <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-bold ${tones[tone]}`}>
      {children}
    </span>
  );
}


function HomePage() {
  const [stats, setStats] = useState(null);
  const [featured, setFeatured] = useState(null);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([getStats(), getStudies({ limit: 100 })])
      .then(([statsData, studiesData]) => {
        setStats(statsData);
        setFeatured(studiesData.studies.find((study) => study.featured) || studiesData.studies[0]);
      })
      .catch((requestError) => setError(requestError.message));
  }, []);

  if (error) return <ErrorMessage message={error} />;
  if (!stats) return <Loading />;

  const quickFilters = [
    {
      label: "Show me RCTs",
      query: { design_type: "Randomized controlled trial" },
      note: "No RCTs are coded in the 32-study source.",
    },
    {
      label: "Show me fixed-effects studies",
      query: { search: "fixed effects" },
      note: "Within-person and within-family designs.",
    },
    {
      label: "Show me intervention studies",
      query: { intervention_only: "true" },
      note: "Intervention coding needs a separate source.",
    },
  ];

  return (
    <>
      <section className="overflow-hidden bg-navy text-white">
        <div className="page-shell relative grid gap-10 py-20 lg:grid-cols-[1.35fr_0.65fr] lg:py-28">
          <div className="relative z-10">
            <p className="text-xs font-bold uppercase tracking-[0.24em] text-gold">
              Causal Evidence Registry
            </p>
            <h1 className="mt-5 max-w-4xl text-5xl font-bold leading-[1.05] sm:text-6xl">
              Neighborhood violence evidence that practitioners can use.
            </h1>
            <p className="mt-7 max-w-3xl text-lg leading-8 text-white/80">
              VICINITY brings study design, population, exposure, outcome, and quality
              information into one searchable registry. It separates stronger causal
              designs from associational evidence and keeps source limitations visible.
            </p>
            <div className="mt-9 flex flex-wrap gap-3">
              <Link to="/registry" className="button-primary">Browse the evidence</Link>
              <Link to="/about" className="button-secondary border-white/30 bg-white/10 text-white hover:bg-white/20">
                Read the protocol
              </Link>
            </div>
          </div>
          <div className="relative z-10 self-end rounded-3xl border border-white/15 bg-white/10 p-7 backdrop-blur">
            <p className="text-sm font-bold uppercase tracking-wider text-gold">Live registry</p>
            <p className="mt-4 text-6xl font-bold">{stats.study_count}</p>
            <p className="mt-1 text-white/75">studies</p>
            <div className="mt-7 grid grid-cols-2 gap-4 border-t border-white/15 pt-6">
              <div>
                <p className="text-2xl font-bold">{stats.country_count}</p>
                <p className="text-xs text-white/65">countries or groups</p>
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.credible_count}</p>
                <p className="text-xs text-white/65">credible tier</p>
              </div>
            </div>
            <p className="mt-6 text-xs text-white/55">Updated {stats.updated_date}</p>
          </div>
          <div className="absolute -right-32 -top-24 h-96 w-96 rounded-full bg-scarlet/25 blur-3xl" />
          <div className="absolute -bottom-48 left-1/3 h-80 w-80 rounded-full bg-gold/15 blur-3xl" />
        </div>
      </section>

      <section className="page-shell py-16">
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div>
            <p className="eyebrow">Start with a design</p>
            <h2 className="mt-2 text-3xl font-bold text-navy">Quick evidence views</h2>
          </div>
          <p className="max-w-xl text-sm leading-6 text-slate-600">
            Empty results remain visible. The registry does not recode studies to fill a category.
          </p>
        </div>
        <div className="mt-8 grid gap-5 md:grid-cols-3">
          {quickFilters.map((item) => (
            <button
              key={item.label}
              type="button"
              onClick={() => navigate(`/registry?${new URLSearchParams(item.query)}`)}
              className="card p-6 text-left transition hover:-translate-y-1 hover:border-scarlet/30"
            >
              <span className="text-lg font-bold text-navy">{item.label}</span>
              <span className="mt-3 block text-sm leading-6 text-slate-600">{item.note}</span>
              <span className="mt-5 block text-sm font-bold text-scarlet">Open view →</span>
            </button>
          ))}
        </div>
      </section>

      {featured && (
        <section className="page-shell pb-16">
          <div className="card overflow-hidden">
            <div className="grid lg:grid-cols-[0.35fr_0.65fr]">
              <div className="bg-scarlet p-8 text-white">
                <p className="text-xs font-bold uppercase tracking-[0.22em] text-white/75">
                  Featured finding
                </p>
                <h2 className="mt-4 text-3xl font-bold">{featured.citation}</h2>
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
                  <span className="text-xs font-semibold text-slate-500">
                    {featured.verification_count} verification notes remain visible
                  </span>
                </div>
              </div>
            </div>
          </div>
        </section>
      )}
    </>
  );
}


function FilterSelect({ label, name, value, options, onChange }) {
  return (
    <label>
      <span className="label">{label}</span>
      <select className="field" name={name} value={value} onChange={onChange}>
        <option value="">All</option>
        {options.map((option) => (
          <option key={option} value={option}>{option}</option>
        ))}
      </select>
    </label>
  );
}


function StudyCard({ study }) {
  const directionStyle =
    DIRECTION_STYLES[study.effect_direction] || DIRECTION_STYLES["Needs verification"];
  return (
    <article className="card p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-bold text-scarlet">{study.citation}</p>
          <h2 className="mt-2 text-2xl font-bold leading-tight text-navy">{study.title}</h2>
        </div>
        <span className={`rounded-full border px-3 py-1 text-xs font-bold ${directionStyle}`}>
          {study.effect_direction}
        </span>
      </div>
      <div className="mt-5 flex flex-wrap gap-2">
        <Badge>{study.design_type}</Badge>
        <Badge tone={study.causal_tier === "Credible" ? "green" : "gold"}>
          {study.causal_tier}
        </Badge>
        <Badge tone="red">{study.quality_tier}</Badge>
      </div>
      <dl className="mt-5 grid gap-3 text-sm sm:grid-cols-3">
        <div>
          <dt className="font-bold text-navy">Population</dt>
          <dd className="mt-1 text-slate-600">{study.age_range}</dd>
        </div>
        <div>
          <dt className="font-bold text-navy">Outcome</dt>
          <dd className="mt-1 text-slate-600">{study.outcome_type}</dd>
        </div>
        <div>
          <dt className="font-bold text-navy">Exposure window</dt>
          <dd className="mt-1 text-slate-600">{study.exposure_window}</dd>
        </div>
      </dl>
      <p className="mt-5 line-clamp-4 text-sm leading-6 text-slate-700">{study.finding_summary}</p>
      <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-navy/10 pt-5">
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
    getStats().then(setStats).catch((requestError) => setError(requestError.message));
  }, []);

  useEffect(() => {
    setFilters(initialFilters);
  }, [initialFilters]);

  useEffect(() => {
    setError("");
    getStudies(filters).then(setResult).catch((requestError) => setError(requestError.message));
  }, [filters]);

  const updateFilter = (event) => {
    const { name, value, type, checked } = event.target;
    const next = { ...filters, [name]: type === "checkbox" ? checked : value };
    setFilters(next);
    const params = new URLSearchParams();
    Object.entries(next).forEach(([key, filterValue]) => {
      if (filterValue) params.set(key, filterValue);
    });
    setSearchParams(params, { replace: true });
  };

  const clearFilters = () => {
    setFilters(EMPTY_FILTERS);
    setSearchParams({}, { replace: true });
  };

  if (error) return <ErrorMessage message={error} />;

  return (
    <main className="page-shell py-12">
      <div className="max-w-3xl">
        <p className="eyebrow">Registry browser</p>
        <h1 className="mt-2 text-4xl font-bold text-navy">Search the current evidence</h1>
        <p className="mt-4 text-base leading-7 text-slate-600">
          Filter by design, population, country, outcome, exposure window, quality, causal tier,
          and publication year. Each record preserves its source text and verification notes.
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
          <FilterSelect
            label="Design type"
            name="design_type"
            value={filters.design_type}
            options={stats?.design_types || []}
            onChange={updateFilter}
          />
          <FilterSelect
            label="Age group"
            name="age_group"
            value={filters.age_group}
            options={stats?.age_groups || []}
            onChange={updateFilter}
          />
          <FilterSelect
            label="Country"
            name="country"
            value={filters.country}
            options={stats?.countries || []}
            onChange={updateFilter}
          />
          <FilterSelect
            label="Outcome"
            name="outcome_type"
            value={filters.outcome_type}
            options={stats?.outcome_types || []}
            onChange={updateFilter}
          />
          <FilterSelect
            label="Exposure window"
            name="exposure_window"
            value={filters.exposure_window}
            options={stats?.exposure_windows || []}
            onChange={updateFilter}
          />
          <FilterSelect
            label="Quality tier"
            name="quality_tier"
            value={filters.quality_tier}
            options={stats?.quality_tiers || []}
            onChange={updateFilter}
          />
          <FilterSelect
            label="Causal tier"
            name="causal_tier"
            value={filters.causal_tier}
            options={stats?.causal_tiers || []}
            onChange={updateFilter}
          />
          <label>
            <span className="label">Year from</span>
            <input
              className="field"
              type="number"
              min="1900"
              max="2100"
              name="year_min"
              value={filters.year_min}
              onChange={updateFilter}
            />
          </label>
          <label>
            <span className="label">Year to</span>
            <input
              className="field"
              type="number"
              min="1900"
              max="2100"
              name="year_max"
              value={filters.year_max}
              onChange={updateFilter}
            />
          </label>
          <label className="flex items-end gap-3 pb-2 text-sm font-bold text-navy">
            <input
              type="checkbox"
              name="intervention_only"
              checked={filters.intervention_only}
              onChange={updateFilter}
              className="h-5 w-5 rounded border-navy/30 text-scarlet"
            />
            Intervention studies only
          </label>
          <div className="flex items-end">
            <button type="button" onClick={clearFilters} className="button-secondary w-full">
              Clear filters
            </button>
          </div>
        </div>
      </section>

      <div className="mt-8 flex items-center justify-between gap-4">
        <p className="text-sm font-bold text-navy">
          {result ? `${result.total} ${result.total === 1 ? "study" : "studies"}` : "Loading studies"}
        </p>
        <p className="text-xs text-slate-500">No category is filled by inference alone.</p>
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
    getStudy(slug).then(setStudy).catch((requestError) => setError(requestError.message));
  }, [slug]);

  if (error) return <ErrorMessage message={error} />;
  if (!study) return <Loading label="Loading study record..." />;

  const barPosition = {
    Protective: "justify-start",
    Null: "justify-center",
    Mixed: "justify-center",
    Harmful: "justify-end",
    "Needs verification": "justify-center",
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
              <DetailItem label="Intervention type">{study.intervention_type}</DetailItem>
              <DetailItem label="DOI">{study.doi || "[NEEDS VERIFICATION]"}</DetailItem>
            </dl>
          </div>
          <div className="rounded-2xl border border-gold/40 bg-gold/10 p-6">
            <h2 className="text-xl font-bold text-navy">Verification queue</h2>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              This record has {study.verification_count} visible source or normalization notes.
            </p>
            <ul className="mt-4 space-y-3 text-sm leading-5 text-slate-700">
              {study.verification_flags.map((flag) => (
                <li key={flag} className="border-t border-gold/30 pt-3 first:border-0 first:pt-0">
                  {flag}
                </li>
              ))}
            </ul>
          </div>
        </aside>
      </div>
    </main>
  );
}


function AboutPage() {
  return (
    <main>
      <section className="bg-navy text-white">
        <div className="page-shell py-20">
          <p className="text-xs font-bold uppercase tracking-[0.24em] text-gold">About VICINITY</p>
          <h1 className="mt-4 max-w-4xl text-5xl font-bold">A living evidence system with visible limits.</h1>
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
              The current seed includes 32 studies from the supplied systematic-review extraction
              workbook. Studies examine violence exposure or neighborhood conditions and outcomes
              relevant to mental health, behavior, physiology, cognition, or education. Users can
              filter outcome categories because the source includes both direct and proximal measures.
            </p>
          </section>
          <section>
            <p className="eyebrow">Causal identification</p>
            <h2 className="mt-2 text-3xl font-bold text-navy">How the tiers work</h2>
            <p className="mt-4 leading-7 text-slate-700">
              A study enters the credible tier only when the workbook clearly documents a randomized
              trial, difference-in-differences design, natural experiment, instrumental variable,
              within-person fixed-effects design, or within-family fixed-effects design. Other
              quasi-experimental studies remain associational until a reviewer verifies the design.
            </p>
          </section>
          <section>
            <p className="eyebrow">Quality appraisal</p>
            <h2 className="mt-2 text-3xl font-bold text-navy">Risk of bias remains traceable</h2>
            <p className="mt-4 leading-7 text-slate-700">
              The source workbook contains narrative risk-of-bias assessments. VICINITY maps those
              narratives to low, moderate, high, or needs-verification categories. The original
              appraisal text appears on every study page. A reviewer must verify the normalized tier
              against the final JBI protocol before publication use.
            </p>
          </section>
          <section>
            <p className="eyebrow">Data integrity</p>
            <h2 className="mt-2 text-3xl font-bold text-navy">What the registry does not infer</h2>
            <p className="mt-4 leading-7 text-slate-700">
              The source lacks dedicated DOI, standardized effect-size, confidence-interval, and
              intervention-type fields. VICINITY marks those fields for verification. It does not
              manufacture estimates or promote uncertain designs.
            </p>
          </section>
          <section>
            <p className="eyebrow">Citation</p>
            <h2 className="mt-2 text-3xl font-bold text-navy">How to cite the registry</h2>
            <p className="mt-4 rounded-2xl border border-navy/10 bg-white p-6 font-mono text-sm leading-6 text-slate-700">
              Abbas, J. (2026). VICINITY: Causal Evidence Registry for Neighborhood Violence and Youth Mental Health. Version 1.0.
            </p>
          </section>
        </article>
        <aside>
          <div className="card p-6">
            <h2 className="text-xl font-bold text-navy">Current release</h2>
            <ul className="mt-5 space-y-3 text-sm leading-6 text-slate-700">
              <li>32 validated study records</li>
              <li>26 credible-tier studies</li>
              <li>6 associational studies</li>
              <li>Field-level verification queue</li>
              <li>Structured study nominations</li>
            </ul>
            <Link to="/submit" className="button-primary mt-6 w-full">Nominate a study</Link>
          </div>
        </aside>
      </div>
    </main>
  );
}


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

  const update = (event) => setForm({ ...form, [event.target.name]: event.target.value });

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const payload = Object.fromEntries(
        Object.entries(form).map(([key, value]) => [key, value.trim() || null]),
      );
      ["citation", "doi", "design_type", "population", "exposure", "outcome", "effect_size"].forEach(
        (key) => {
          payload[key] = form[key].trim();
        },
      );
      setResult(await submitStudy(payload));
    } catch (requestError) {
      setError(requestError.message);
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
          extraction accuracy, causal identification, and risk of bias first.
        </p>
        <form onSubmit={handleSubmit} className="card mt-8 grid gap-5 p-7 sm:grid-cols-2">
          {SUBMISSION_FIELDS.map(([name, label, type, placeholder]) => {
            const required = !["submitter_name", "submitter_email", "notes"].includes(name);
            const wide = ["citation", "population", "exposure", "outcome", "notes"].includes(name);
            return (
              <label key={name} className={wide ? "sm:col-span-2" : ""}>
                <span className="label">
                  {label}{required ? " *" : ""}
                </span>
                {type === "textarea" ? (
                  <textarea
                    className="field min-h-28"
                    name={name}
                    value={form[name]}
                    onChange={update}
                    placeholder={placeholder}
                    required={required}
                  />
                ) : (
                  <input
                    className="field"
                    type={type}
                    name={name}
                    value={form[name]}
                    onChange={update}
                    placeholder={placeholder}
                    required={required}
                  />
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
              {submitting ? "Submitting..." : "Submit to the review queue"}
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}


function NotFoundPage() {
  return (
    <main className="page-shell py-24 text-center">
      <p className="eyebrow">404</p>
      <h1 className="mt-3 text-4xl font-bold text-navy">This page does not exist.</h1>
      <Link to="/" className="button-primary mt-7">Return home</Link>
    </main>
  );
}


export default function App() {
  return (
    <div className="min-h-screen">
      <Header />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/registry" element={<RegistryPage />} />
        <Route path="/studies/:slug" element={<StudyDetailPage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/submit" element={<SubmitPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
      <Footer />
    </div>
  );
}
