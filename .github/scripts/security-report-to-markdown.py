#!/usr/bin/env python3
"""Aggregate scan outputs into a human-readable Markdown security report.

Consumes the JSON outputs produced by the security-audit workflow's
scan jobs (OWASP Dependency-Check, npm audit, Semgrep, Trivy) and emits
a single Markdown report with severity counts and recommended fixes.

Missing inputs are tolerated so this script can also run locally with a
subset of files.
"""
from __future__ import annotations

import argparse
import json
import os
from typing import Any


SEVERITY_BADGE = {
    "critical": "[CRITICAL]",
    "high": "[HIGH]",
    "medium": "[MEDIUM]",
    "moderate": "[MEDIUM]",
    "low": "[LOW]",
    "error": "[ERROR]",
    "warning": "[WARNING]",
}
SEVERITY_ORDER = {
    "critical": 0,
    "high": 1,
    "error": 1,
    "medium": 2,
    "moderate": 2,
    "warning": 2,
    "low": 3,
}


def load_json(path: str | None) -> Any:
    if not path or not os.path.exists(path) or os.path.getsize(path) == 0:
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return None


def fmt_badge(severity: str) -> str:
    key = (severity or "").lower()
    return SEVERITY_BADGE.get(key, f"[{(severity or '?').upper()}]")


def escape(text: str | None) -> str:
    if text is None:
        return ""
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


# ---------- OWASP Dependency-Check ----------

def render_owasp_dc(data: Any) -> tuple[list[str], int]:
    lines = ["### OWASP Dependency-Check (Maven)", ""]
    if not data:
        lines.append("_No dependency-check report produced. Check the owasp-dependency-check job logs._")
        lines.append("")
        return lines, 0

    rows: list[dict[str, Any]] = []
    for dep in data.get("dependencies", []) or []:
        vulns = dep.get("vulnerabilities") or []
        for v in vulns:
            severity = (v.get("severity") or "").lower()
            cvss = v.get("cvssv3", {}).get("baseScore") or v.get("cvssv2", {}).get("score")
            pkg = dep.get("fileName") or dep.get("filePath") or "?"
            rows.append({
                "severity": severity,
                "id": v.get("name") or "",
                "title": v.get("description") or "",
                "package": pkg,
                "cvss": cvss,
            })

    high_or_crit = sum(1 for r in rows if r["severity"] in ("critical", "high"))
    if not rows:
        lines.append("No vulnerabilities reported.")
        lines.append("")
        return lines, 0

    counts: dict[str, int] = {}
    for r in rows:
        counts[r["severity"]] = counts.get(r["severity"], 0) + 1
    summary = ", ".join(
        f"{sev.upper()}={counts[sev]}"
        for sev in ("critical", "high", "medium", "low")
        if counts.get(sev)
    )
    lines.append(f"**Findings:** {summary}")
    lines.append("")
    lines.append("| Severity | CVE / ID | Package | CVSS | Recommended fix |")
    lines.append("| --- | --- | --- | --- | --- |")

    rows.sort(key=lambda r: (SEVERITY_ORDER.get(r["severity"], 9), r["package"]))
    shown = [r for r in rows if r["severity"] in ("critical", "high")][:30]
    if not shown:
        shown = rows[:20]
    for r in shown:
        title = escape(r["title"])[:140]
        fix = f"Upgrade or replace `{escape(r['package'])}`; see advisory `{escape(r['id'])}`."
        lines.append(
            f"| {fmt_badge(r['severity'])} | {escape(r['id'])} | `{escape(r['package'])}` | {r['cvss'] or '—'} | {fix} |"
        )
    lines.append("")
    return lines, high_or_crit


# ---------- npm audit ----------

def render_npm_audit(data: Any) -> tuple[list[str], int]:
    lines = ["### npm audit (frontend)", ""]
    if not data:
        lines.append("_No npm audit report produced. Check the npm-audit job logs._")
        lines.append("")
        return lines, 0

    vulnerabilities = data.get("vulnerabilities") or {}
    rows: list[dict[str, Any]] = []
    for name, info in vulnerabilities.items():
        severity = (info.get("severity") or "").lower()
        via = info.get("via") or []
        titles: list[str] = []
        cves: list[str] = []
        for entry in via:
            if isinstance(entry, dict):
                if entry.get("title"):
                    titles.append(entry["title"])
                if entry.get("url"):
                    cves.append(entry.get("source") and str(entry["source"]) or entry["url"])
            elif isinstance(entry, str):
                titles.append(entry)
        fix_available = info.get("fixAvailable")
        if isinstance(fix_available, dict):
            fix_version = fix_available.get("version")
            fix_text = f"Upgrade `{name}` to {fix_version}" if fix_version else "Upgrade available"
        elif fix_available is True:
            fix_text = "Upgrade available (`npm audit fix`)"
        else:
            fix_text = "No automatic fix; review dependency tree"
        rows.append({
            "severity": severity,
            "name": name,
            "title": "; ".join(titles)[:160],
            "fix": fix_text,
            "range": info.get("range") or "",
        })

    high_or_crit = sum(1 for r in rows if r["severity"] in ("critical", "high"))
    if not rows:
        lines.append("No vulnerabilities reported.")
        lines.append("")
        return lines, 0

    counts: dict[str, int] = {}
    for r in rows:
        counts[r["severity"]] = counts.get(r["severity"], 0) + 1
    summary = ", ".join(
        f"{sev.upper()}={counts[sev]}"
        for sev in ("critical", "high", "moderate", "low")
        if counts.get(sev)
    )
    lines.append(f"**Findings:** {summary}")
    lines.append("")
    lines.append("| Severity | Package | Affected range | Title | Recommended fix |")
    lines.append("| --- | --- | --- | --- | --- |")
    rows.sort(key=lambda r: (SEVERITY_ORDER.get(r["severity"], 9), r["name"]))
    shown = [r for r in rows if r["severity"] in ("critical", "high")][:30] or rows[:20]
    for r in shown:
        lines.append(
            f"| {fmt_badge(r['severity'])} | `{escape(r['name'])}` | `{escape(r['range'])}` | {escape(r['title'])} | {escape(r['fix'])} |"
        )
    lines.append("")
    return lines, high_or_crit


# ---------- Semgrep ----------

def render_semgrep(data: Any) -> tuple[list[str], int]:
    lines = ["### Semgrep SAST", ""]
    if not data:
        lines.append("_No Semgrep report produced. Check the semgrep job logs._")
        lines.append("")
        return lines, 0

    results = data.get("results") or []
    if not results:
        lines.append("No code-level issues at ERROR/WARNING severity.")
        lines.append("")
        return lines, 0

    counts: dict[str, int] = {}
    rows: list[dict[str, Any]] = []
    for r in results:
        sev = (r.get("extra", {}).get("severity") or "").lower()
        counts[sev] = counts.get(sev, 0) + 1
        rows.append({
            "severity": sev,
            "rule": r.get("check_id") or "",
            "message": (r.get("extra", {}).get("message") or "").split("\n", 1)[0],
            "file": r.get("path") or "",
            "line": (r.get("start") or {}).get("line"),
        })

    error_or_warn = counts.get("error", 0) + counts.get("warning", 0)
    summary = ", ".join(f"{k.upper()}={v}" for k, v in counts.items() if v)
    lines.append(f"**Findings:** {summary}")
    lines.append("")
    lines.append("| Severity | Rule | File:line | Message |")
    lines.append("| --- | --- | --- | --- |")
    rows.sort(key=lambda r: (SEVERITY_ORDER.get(r["severity"], 9), r["file"]))
    shown = rows[:30]
    for r in shown:
        loc = f"`{escape(r['file'])}:{r['line']}`" if r["line"] else f"`{escape(r['file'])}`"
        lines.append(
            f"| {fmt_badge(r['severity'])} | `{escape(r['rule'])}` | {loc} | {escape(r['message'])[:160]} |"
        )
    lines.append("")
    return lines, error_or_warn


# ---------- Trivy ----------

def render_trivy(data: Any) -> tuple[list[str], int]:
    lines = ["### Trivy filesystem", ""]
    if not data:
        lines.append("_No Trivy JSON produced. Check the trivy-fs job logs._")
        lines.append("")
        return lines, 0

    rows: list[dict[str, Any]] = []
    for result in data.get("Results", []) or []:
        target = result.get("Target") or ""
        for v in result.get("Vulnerabilities") or []:
            severity = (v.get("Severity") or "").lower()
            rows.append({
                "severity": severity,
                "id": v.get("VulnerabilityID") or "",
                "package": v.get("PkgName") or "",
                "installed": v.get("InstalledVersion") or "",
                "fixed": v.get("FixedVersion") or "",
                "title": v.get("Title") or v.get("Description") or "",
                "target": target,
            })
        for s in result.get("Secrets") or []:
            rows.append({
                "severity": (s.get("Severity") or "").lower(),
                "id": s.get("RuleID") or "secret",
                "package": "(secret)",
                "installed": "",
                "fixed": "rotate and remove from history",
                "title": s.get("Title") or "Secret detected",
                "target": target,
            })

    high_or_crit = sum(1 for r in rows if r["severity"] in ("critical", "high"))
    if not rows:
        lines.append("No filesystem findings at CRITICAL/HIGH/MEDIUM.")
        lines.append("")
        return lines, 0

    counts: dict[str, int] = {}
    for r in rows:
        counts[r["severity"]] = counts.get(r["severity"], 0) + 1
    summary = ", ".join(
        f"{sev.upper()}={counts[sev]}"
        for sev in ("critical", "high", "medium", "low")
        if counts.get(sev)
    )
    lines.append(f"**Findings:** {summary}")
    lines.append("")
    lines.append("| Severity | ID | Package | Installed | Fixed | Target |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    rows.sort(key=lambda r: (SEVERITY_ORDER.get(r["severity"], 9), r["package"]))
    shown = [r for r in rows if r["severity"] in ("critical", "high")][:30] or rows[:20]
    for r in shown:
        fix = r["fixed"] or "no fix yet"
        lines.append(
            f"| {fmt_badge(r['severity'])} | {escape(r['id'])} | `{escape(r['package'])}` | `{escape(r['installed'])}` | `{escape(fix)}` | `{escape(r['target'])}` |"
        )
    lines.append("")
    return lines, high_or_crit


# ---------- main ----------

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--owasp-dc", help="Path to OWASP Dependency-Check JSON")
    parser.add_argument("--npm-audit", help="Path to npm audit JSON")
    parser.add_argument("--semgrep", help="Path to Semgrep JSON")
    parser.add_argument("--trivy", help="Path to Trivy JSON")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    sections: list[str] = ["## Security Audit Report", ""]

    owasp_lines, owasp_hi = render_owasp_dc(load_json(args.owasp_dc))
    npm_lines, npm_hi = render_npm_audit(load_json(args.npm_audit))
    semgrep_lines, semgrep_hi = render_semgrep(load_json(args.semgrep))
    trivy_lines, trivy_hi = render_trivy(load_json(args.trivy))

    total = owasp_hi + npm_hi + semgrep_hi + trivy_hi
    if total:
        sections.append(
            f"**Status:** :rotating_light: {total} high/critical findings across scans. "
            "Build is gated on these jobs and will not run if any of them fail."
        )
    else:
        sections.append(
            "**Status:** :white_check_mark: No high/critical findings detected by any scan."
        )
    sections.append("")
    sections.append(
        "Scans: OWASP Dependency-Check (Maven), npm audit, Semgrep (OWASP Top 10 + secrets), Trivy filesystem. "
        "Detailed JSON/SARIF artifacts are attached to this workflow run."
    )
    sections.append("")
    sections.append("| Scan | High/Critical |")
    sections.append("| --- | --- |")
    sections.append(f"| OWASP Dependency-Check | {owasp_hi} |")
    sections.append(f"| npm audit | {npm_hi} |")
    sections.append(f"| Semgrep (ERROR+WARNING) | {semgrep_hi} |")
    sections.append(f"| Trivy filesystem | {trivy_hi} |")
    sections.append("")

    sections.extend(owasp_lines)
    sections.extend(npm_lines)
    sections.extend(semgrep_lines)
    sections.extend(trivy_lines)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write("\n".join(sections))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
