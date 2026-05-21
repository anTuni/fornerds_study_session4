#!/usr/bin/env python3
"""Convert Snyk JSON output into a human-readable Markdown report.

Used by the security-audit workflow to render snyk test results as a
PR comment and an uploadable artifact.
"""
from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from typing import Any, Iterable


SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
SEVERITY_BADGE = {
    "critical": "[CRITICAL]",
    "high": "[HIGH]",
    "medium": "[MEDIUM]",
    "low": "[LOW]",
}


def load_projects(path: str | None) -> list[dict[str, Any]]:
    if not path or not os.path.exists(path) or os.path.getsize(path) == 0:
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return [data]


def iter_vulns(projects: Iterable[dict[str, Any]]):
    for project in projects:
        target = project.get("displayTargetFile") or project.get("targetFile") or project.get("projectName") or "(unknown)"
        for vuln in project.get("vulnerabilities", []) or []:
            yield target, vuln


def fixed_in(vuln: dict[str, Any]) -> str:
    fixed = vuln.get("fixedIn") or []
    if isinstance(fixed, list) and fixed:
        return ", ".join(str(v) for v in fixed)
    upgrade = vuln.get("upgradePath") or []
    if isinstance(upgrade, list) and upgrade:
        return " -> ".join(str(v) for v in upgrade if v)
    if vuln.get("isUpgradable"):
        return "upgrade available"
    if vuln.get("isPatchable"):
        return "patch available"
    return "no fix available"


def recommended_action(vuln: dict[str, Any]) -> str:
    name = vuln.get("packageName") or vuln.get("package") or "?"
    fix = fixed_in(vuln)
    if fix not in ("no fix available", ""):
        return f"Upgrade `{name}` to: {fix}"
    return f"No upstream fix yet for `{name}`. Consider removing the dependency or pinning a safe transitive version."


def render_section(title: str, projects: list[dict[str, Any]]) -> list[str]:
    lines = [f"### {title}", ""]
    if not projects:
        lines.append("_No Snyk JSON produced for this project. Check the snyk-scan job logs._")
        lines.append("")
        return lines

    rows: list[tuple[str, dict[str, Any]]] = list(iter_vulns(projects))
    if not rows:
        lines.append("No vulnerabilities reported (severity threshold: high).")
        lines.append("")
        return lines

    severity_counts: dict[str, int] = defaultdict(int)
    for _, v in rows:
        severity_counts[v.get("severity", "unknown")] += 1

    summary_bits = ", ".join(
        f"{sev.upper()}={severity_counts[sev]}"
        for sev in ("critical", "high", "medium", "low")
        if severity_counts.get(sev)
    )
    lines.append(f"**Findings:** {summary_bits or 'none'}")
    lines.append("")

    rows.sort(
        key=lambda item: (
            SEVERITY_ORDER.get(item[1].get("severity", "low"), 99),
            item[1].get("packageName", ""),
        )
    )

    lines.append("| Severity | Package@version | CVE / ID | Title | Recommended fix | File |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for target, vuln in rows:
        severity = vuln.get("severity", "?")
        badge = SEVERITY_BADGE.get(severity, f"[{severity.upper()}]")
        pkg = vuln.get("packageName") or vuln.get("package") or "?"
        version = vuln.get("version") or "?"
        ids = vuln.get("identifiers") or {}
        cves = ", ".join(ids.get("CVE") or []) if isinstance(ids.get("CVE"), list) else ""
        snyk_id = vuln.get("id") or ""
        id_cell = cves or snyk_id or "—"
        title = (vuln.get("title") or "").replace("|", "\\|")
        action = recommended_action(vuln).replace("|", "\\|")
        lines.append(
            f"| {badge} | `{pkg}@{version}` | {id_cell} | {title} | {action} | `{target}` |"
        )
    lines.append("")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frontend", help="Path to snyk JSON for frontend (npm)")
    parser.add_argument("--backend", help="Path to snyk JSON for backend (maven)")
    parser.add_argument("--output", required=True, help="Markdown output path")
    args = parser.parse_args()

    frontend = load_projects(args.frontend)
    backend = load_projects(args.backend)

    lines: list[str] = ["## Snyk Dependency Scan Report", ""]
    total_high_or_critical = sum(
        1
        for projects in (frontend, backend)
        for _, v in iter_vulns(projects)
        if v.get("severity") in ("high", "critical")
    )
    if total_high_or_critical:
        lines.append(
            f"**Status:** :rotating_light: {total_high_or_critical} high/critical "
            f"vulnerabilities. Build will fail."
        )
    else:
        lines.append("**Status:** :white_check_mark: No high or critical vulnerabilities at threshold.")
    lines.append("")
    lines.append("Severity threshold: `high`. Full JSON output is available in the `snyk-report` artifact.")
    lines.append("")

    lines.extend(render_section("Frontend (npm)", frontend))
    lines.extend(render_section("Backend (Maven)", backend))

    with open(args.output, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
