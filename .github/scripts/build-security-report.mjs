#!/usr/bin/env node
// Aggregates outputs from all security scanners into a single Markdown report.
// Inputs: ./reports/<artifact-name>/... (downloaded via actions/download-artifact)
// Output: ./security-report.md

import { readFileSync, existsSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const REPORTS_DIR = 'reports';
const OUT = 'security-report.md';

const env = process.env;
const STATUSES = {
  'OWASP Dependency-Check (Backend)': env.BACKEND_STATUS || 'unknown',
  'npm audit (Frontend)': env.FRONTEND_STATUS || 'unknown',
  'Semgrep SAST': env.SEMGREP_STATUS || 'unknown',
  'Trivy Filesystem Scan': env.TRIVY_STATUS || 'unknown',
};

const SEVERITY_ORDER = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3, INFO: 4, UNKNOWN: 5 };
const SEVERITY_EMOJI = {
  CRITICAL: '🟥',
  HIGH: '🟧',
  MEDIUM: '🟨',
  LOW: '🟦',
  INFO: '⬜',
  UNKNOWN: '⬜',
};

function statusBadge(s) {
  if (s === 'success') return '✅ PASS';
  if (s === 'failure') return '❌ FAIL';
  if (s === 'skipped') return '⏭️ SKIPPED';
  if (s === 'cancelled') return '🚫 CANCELLED';
  return `❓ ${s}`;
}

function readJSON(path) {
  if (!existsSync(path)) return null;
  try { return JSON.parse(readFileSync(path, 'utf8')); } catch { return null; }
}

function readText(path) {
  if (!existsSync(path)) return null;
  try { return readFileSync(path, 'utf8'); } catch { return null; }
}

function normSeverity(s) {
  if (!s) return 'UNKNOWN';
  const up = String(s).toUpperCase();
  return SEVERITY_ORDER[up] !== undefined ? up : 'UNKNOWN';
}

// --- Parsers ---------------------------------------------------------------

function parseOwaspDependencyCheck() {
  const path = join(REPORTS_DIR, 'backend-owasp-report', 'dependency-check-report.json');
  const data = readJSON(path);
  if (!data) return { scanner: 'OWASP Dependency-Check', findings: [], error: 'report not found' };

  const findings = [];
  for (const dep of data.dependencies || []) {
    const vulns = dep.vulnerabilities || [];
    for (const v of vulns) {
      const cvss = v.cvssv3 || v.cvssv2 || {};
      const score = cvss.baseScore ?? cvss.score ?? null;
      findings.push({
        id: v.name || v.source || 'CVE',
        severity: normSeverity(v.severity),
        score,
        title: `${dep.fileName || dep.filePath || 'dependency'}: ${v.name || 'vulnerability'}`,
        description: (v.description || '').trim(),
        remediation:
          'Upgrade the affected dependency to a patched version. If no patch exists, ' +
          'apply vendor workaround, pin a safer transitive version, or remove the dependency. ' +
          (v.references?.length ? `References: ${v.references.slice(0, 3).map(r => r.url).filter(Boolean).join(', ')}` : ''),
        location: dep.filePath || dep.fileName || '',
      });
    }
  }
  return { scanner: 'OWASP Dependency-Check', findings };
}

function parseNpmAudit() {
  const path = join(REPORTS_DIR, 'frontend-npm-audit-report', 'npm-audit-report.json');
  const data = readJSON(path);
  if (!data) return { scanner: 'npm audit', findings: [], error: 'report not found' };

  const findings = [];
  // npm v7+ uses { vulnerabilities: { <pkg>: { name, severity, via: [...] } } }
  const vulns = data.vulnerabilities || {};
  for (const [pkg, info] of Object.entries(vulns)) {
    const via = Array.isArray(info.via) ? info.via : [];
    const advisories = via.filter(v => typeof v === 'object');
    if (advisories.length === 0) {
      findings.push({
        id: pkg,
        severity: normSeverity(info.severity),
        score: null,
        title: `${pkg} (${info.severity})`,
        description: `Vulnerable npm package. Fix available: ${info.fixAvailable ? 'yes' : 'no'}.`,
        remediation: info.fixAvailable
          ? `Run \`npm audit fix\` (or \`npm audit fix --force\` for breaking upgrades) to update ${pkg}.`
          : `No automatic fix available. Pin to a non-vulnerable version, replace the package, or upgrade the parent dependency.`,
        location: `frontend/node_modules/${pkg}`,
      });
    }
    for (const a of advisories) {
      findings.push({
        id: a.source ? `GHSA-${a.source}` : (a.url || pkg),
        severity: normSeverity(a.severity || info.severity),
        score: null,
        title: `${pkg}: ${a.title || 'vulnerability'}`,
        description: (a.title || '') + (a.url ? ` (${a.url})` : ''),
        remediation: info.fixAvailable
          ? `Run \`npm audit fix\` to apply the patched version. If a major bump is required, run \`npm audit fix --force\` and verify the build.`
          : `No safe upgrade path detected by npm audit. Consider replacing ${pkg} or pinning the transitive dependency manually.`,
        location: `frontend/package.json (${pkg})`,
      });
    }
  }
  return { scanner: 'npm audit', findings };
}

function parseSemgrep() {
  const path = join(REPORTS_DIR, 'semgrep-sast-report', 'semgrep.json');
  const data = readJSON(path);
  if (!data) return { scanner: 'Semgrep', findings: [], error: 'report not found' };
  const findings = [];
  for (const r of data.results || []) {
    const sev = normSeverity(r.extra?.severity || r.severity);
    findings.push({
      id: r.check_id || 'semgrep-rule',
      severity: sev === 'WARNING' ? 'MEDIUM' : (sev === 'ERROR' ? 'HIGH' : sev),
      score: null,
      title: r.extra?.message?.split('\n')[0] || r.check_id,
      description: (r.extra?.message || '').trim(),
      remediation:
        (r.extra?.metadata?.['fix-suggestion'] ||
         r.extra?.fix ||
         'Refer to the Semgrep rule documentation: ' + (r.extra?.metadata?.source || r.check_id) +
         '. Apply the secure coding pattern suggested by the rule (input validation, parameterized queries, safe APIs, etc.).'),
      location: `${r.path}:${r.start?.line || '?'}`,
    });
  }
  return { scanner: 'Semgrep', findings };
}

function parseTrivy() {
  const path = join(REPORTS_DIR, 'trivy-fs-report', 'trivy-results.json');
  const data = readJSON(path);
  if (!data) return { scanner: 'Trivy', findings: [], error: 'report not found' };
  const findings = [];
  for (const res of data.Results || []) {
    for (const v of res.Vulnerabilities || []) {
      findings.push({
        id: v.VulnerabilityID,
        severity: normSeverity(v.Severity),
        score: v.CVSS?.nvd?.V3Score ?? v.CVSS?.redhat?.V3Score ?? null,
        title: `${v.PkgName}@${v.InstalledVersion} → ${v.VulnerabilityID}: ${v.Title || ''}`,
        description: (v.Description || '').trim().slice(0, 600),
        remediation: v.FixedVersion
          ? `Upgrade ${v.PkgName} to \`${v.FixedVersion}\` or later.`
          : `No fixed version available yet. Apply vendor workaround, isolate the component, or remove the dependency. References: ${(v.References || []).slice(0, 3).join(', ')}`,
        location: `${res.Target} (${v.PkgName})`,
      });
    }
    for (const m of res.Misconfigurations || []) {
      findings.push({
        id: m.ID,
        severity: normSeverity(m.Severity),
        score: null,
        title: `Misconfiguration: ${m.Title}`,
        description: (m.Description || '').trim(),
        remediation: m.Resolution || 'Review the affected configuration and apply the recommended hardening.',
        location: `${res.Target}`,
      });
    }
    for (const s of res.Secrets || []) {
      findings.push({
        id: s.RuleID || 'SECRET',
        severity: normSeverity(s.Severity),
        score: null,
        title: `Secret detected: ${s.Title || s.Category}`,
        description: `A potential secret of type "${s.Category}" was detected. Match: ${s.Match || '(redacted)'}.`,
        remediation:
          'Remove the secret from source control, rotate the credential immediately, and store it in a secret manager (GitHub Actions Secrets, Vault, AWS Secrets Manager, etc.).',
        location: `${res.Target}:${s.StartLine || '?'}`,
      });
    }
  }
  return { scanner: 'Trivy', findings };
}

// --- Build report ----------------------------------------------------------

const sections = [
  parseOwaspDependencyCheck(),
  parseNpmAudit(),
  parseSemgrep(),
  parseTrivy(),
];

let totals = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0, INFO: 0, UNKNOWN: 0 };
for (const s of sections) {
  for (const f of s.findings) totals[f.severity] = (totals[f.severity] || 0) + 1;
}
const totalFindings = Object.values(totals).reduce((a, b) => a + b, 0);
const blocking = (totals.CRITICAL || 0) + (totals.HIGH || 0);

const lines = [];
lines.push(`# 🛡️ Security Audit Report`);
lines.push('');
lines.push(`- PR: #${env.PR_NUMBER || 'N/A'}`);
lines.push(`- Commit: \`${(env.PR_HEAD_SHA || '').slice(0, 12)}\``);
lines.push(`- Generated: ${new Date().toISOString()}`);
lines.push('');

lines.push(`## Scan Status`);
lines.push('');
lines.push('| Scanner | Result |');
lines.push('| --- | --- |');
for (const [name, status] of Object.entries(STATUSES)) {
  lines.push(`| ${name} | ${statusBadge(status)} |`);
}
lines.push('');

lines.push(`## Summary`);
lines.push('');
lines.push(`Total findings: **${totalFindings}** (Blocking — Critical+High: **${blocking}**)`);
lines.push('');
lines.push('| Severity | Count |');
lines.push('| --- | --- |');
for (const sev of Object.keys(SEVERITY_ORDER)) {
  lines.push(`| ${SEVERITY_EMOJI[sev]} ${sev} | ${totals[sev] || 0} |`);
}
lines.push('');

if (blocking > 0) {
  lines.push(`> ❌ **Merge blocked.** ${blocking} high/critical issue(s) must be resolved before this PR can be merged.`);
} else if (totalFindings > 0) {
  lines.push(`> ⚠️ ${totalFindings} non-blocking issue(s) detected. Review the details below.`);
} else {
  lines.push(`> ✅ No vulnerabilities detected by the configured scanners.`);
}
lines.push('');

for (const sec of sections) {
  lines.push(`## ${sec.scanner}`);
  lines.push('');
  if (sec.error) {
    lines.push(`_${sec.error}_`);
    lines.push('');
    continue;
  }
  if (sec.findings.length === 0) {
    lines.push('No findings.');
    lines.push('');
    continue;
  }
  sec.findings.sort((a, b) =>
    (SEVERITY_ORDER[a.severity] ?? 99) - (SEVERITY_ORDER[b.severity] ?? 99));
  const top = sec.findings.slice(0, 25);
  for (const f of top) {
    lines.push(`### ${SEVERITY_EMOJI[f.severity]} [${f.severity}] ${f.id} — ${f.title}`);
    if (f.score != null) lines.push(`- CVSS: \`${f.score}\``);
    if (f.location) lines.push(`- Location: \`${f.location}\``);
    if (f.description) {
      lines.push('');
      lines.push('**Description**');
      lines.push('');
      lines.push(f.description.length > 800 ? f.description.slice(0, 800) + '…' : f.description);
    }
    lines.push('');
    lines.push('**Remediation**');
    lines.push('');
    lines.push(f.remediation || 'Review the scanner documentation for remediation guidance.');
    lines.push('');
    lines.push('---');
    lines.push('');
  }
  if (sec.findings.length > top.length) {
    lines.push(`_…and ${sec.findings.length - top.length} more finding(s). See the raw artifact for the full list._`);
    lines.push('');
  }
}

lines.push(`## Artifacts`);
lines.push('');
lines.push('Full raw reports are attached to this workflow run as artifacts:');
lines.push('');
lines.push('- `backend-owasp-report` — OWASP Dependency-Check (HTML/JSON/SARIF)');
lines.push('- `frontend-npm-audit-report` — npm audit (JSON/TXT)');
lines.push('- `semgrep-sast-report` — Semgrep findings (SARIF/JSON)');
lines.push('- `trivy-fs-report` — Trivy filesystem scan (SARIF/JSON)');
lines.push('- `security-report` — This consolidated report plus all raw scanner outputs');
lines.push('');

writeFileSync(OUT, lines.join('\n'));
console.log(`Wrote ${OUT} with ${totalFindings} findings (${blocking} blocking).`);
