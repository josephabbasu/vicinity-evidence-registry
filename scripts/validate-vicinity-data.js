#!/usr/bin/env node
/**
 * VICINITY data validation script.
 * Run: node scripts/validate-vicinity-data.js
 * Validates backend/app/data/studies.json and intervention_studies.json.
 */

import { readFileSync, writeFileSync, mkdirSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");

const ALLOWED = {
  design_type: [
    "Randomized controlled trial", "Cluster randomized controlled trial",
    "Difference-in-differences", "Event study", "Natural experiment",
    "Instrumental variables", "Within-person fixed effects",
    "Within-family fixed effects", "Twin fixed effects",
    "Matching only", "Cross-sectional", "Longitudinal observational",
    "Other quasi-experimental", "Sibling/twin fixed effects", "Needs verification",
  ],
  effect_direction: ["Harmful", "Protective", "Null", "Mixed", "Needs verification"],
  causal_tier: ["Credible", "Associational", "Needs verification"],
  quality_tier: ["Low risk", "Moderate risk", "High risk", "Needs verification"],
  registry_stream: ["exposure", "intervention", "implementation"],
};

const REQUIRED_FIELDS = [
  "study_id", "slug", "title", "citation", "publication_year",
  "country", "design_type", "causal_tier", "outcome_type",
  "effect_direction", "registry_stream", "finding_summary",
];

function loadJSON(relPath) {
  const full = join(ROOT, relPath);
  return JSON.parse(readFileSync(full, "utf8"));
}

function validate() {
  const exposure = loadJSON("backend/app/data/studies.json");
  const intervention = loadJSON("backend/app/data/intervention_studies.json");
  const all = [...exposure, ...intervention];

  const errors = [];
  const warnings = [];
  const seenIds = new Set();
  const seenDois = new Set();

  for (const study of all) {
    const ref = study.study_id || study.slug || "(unknown)";

    // Required fields
    for (const field of REQUIRED_FIELDS) {
      if (!study[field] && study[field] !== 0) {
        errors.push(`${ref}: missing required field "${field}"`);
      }
    }

    // Duplicate study_id
    if (study.study_id) {
      if (seenIds.has(study.study_id)) errors.push(`Duplicate study_id: ${study.study_id}`);
      seenIds.add(study.study_id);
    }

    // Duplicate DOI
    if (study.doi) {
      if (seenDois.has(study.doi)) warnings.push(`Duplicate DOI: ${study.doi} (${ref})`);
      seenDois.add(study.doi);
    }

    // Allowed value checks
    for (const [field, allowed] of Object.entries(ALLOWED)) {
      if (study[field] && !allowed.includes(study[field])) {
        warnings.push(`${ref}: "${field}" value "${study[field]}" not in allowed list`);
      }
    }

    // Intervention claim safety check
    if (study.registry_stream === "intervention") {
      const directness = (study.outcome_directness || "").toLowerCase();
      if (!directness.includes("direct") && directness && directness !== "scope requires verification") {
        warnings.push(`${ref}: intervention study without direct mental-health outcome — review claim safety`);
      }
    }
  }

  // Counts
  const exposureCount = all.filter((s) => s.registry_stream === "exposure").length;
  const interventionCount = all.filter((s) => s.registry_stream === "intervention").length;
  const credibleCount = all.filter((s) => s.causal_tier === "Credible").length;
  const needsVerificationCount = all.filter(
    (s) => (s.verification_flags || []).length > 0
  ).length;

  const report = {
    generated_at: new Date().toISOString(),
    validation_status: errors.length === 0 ? "passed" : "failed",
    total_records: all.length,
    exposure_records: exposureCount,
    intervention_records: interventionCount,
    credible_tier_records: credibleCount,
    records_with_verification_flags: needsVerificationCount,
    error_count: errors.length,
    warning_count: warnings.length,
    errors,
    warnings,
  };

  // Write report
  const outDir = join(ROOT, "frontend", "public", "data");
  try { mkdirSync(outDir, { recursive: true }); } catch {}
  writeFileSync(join(outDir, "validation-report.json"), JSON.stringify(report, null, 2));

  console.log(`\nVICINITY data validation`);
  console.log(`========================`);
  console.log(`Total records : ${all.length} (${exposureCount} exposure, ${interventionCount} intervention)`);
  console.log(`Design-identified : ${credibleCount}`);
  console.log(`Needs verification flags : ${needsVerificationCount}`);
  console.log(`Errors   : ${errors.length}`);
  console.log(`Warnings : ${warnings.length}`);
  if (errors.length) {
    console.log("\nErrors:");
    errors.forEach((e) => console.log(`  ✗ ${e}`));
  }
  if (warnings.length) {
    console.log("\nWarnings:");
    warnings.slice(0, 20).forEach((w) => console.log(`  ⚠ ${w}`));
    if (warnings.length > 20) console.log(`  ... and ${warnings.length - 20} more`);
  }
  console.log(`\nReport written to frontend/public/data/validation-report.json`);
  if (errors.length > 0) {
    console.error("\nValidation FAILED. Fix errors before release.");
    process.exit(1);
  }
  console.log("\nValidation passed.\n");
}

validate();
