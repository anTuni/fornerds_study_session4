#!/usr/bin/env python3
"""Create a consolidated security report and optionally upsert a PR comment."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path


MARKER = "<!-- team-security-audit-report -->"


def load_json(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {"summary": {"total": 0, "by_severity": {}, "by_category": {}}, "findings": []}
    return json.loads(p.read_text(encoding="utf-8"))


def job_status(name: str) -> str:
    return os.environ.get(name, "unknown")


def has_blockers(scan_report: dict) -> bool:
    by_severity = scan_report.get("summary", {}).get("by_severity", {})
    if by_severity.get("critical", 0) or by_severity.get("high", 0):
        return True
    blocking_status_vars = [
        "BACKEND_TEST_RESULT",
        "FRONTEND_BUILD_RESULT",
        "DEPENDENCY_SCAN_RESULT",
        "NPM_AUDIT_RESULT",
        "SEMGREP_RESULT",
        "TRIVY_RESULT",
        "GITLEAKS_RESULT",
    ]
    return any(job_status(var) == "failure" for var in blocking_status_vars)


def render_report(scan_report: dict) -> str:
    statuses = [
        ("Backend test", "BACKEND_TEST_RESULT"),
        ("Frontend build", "FRONTEND_BUILD_RESULT"),
        ("Dependency scan", "DEPENDENCY_SCAN_RESULT"),
        ("npm audit", "NPM_AUDIT_RESULT"),
        ("Semgrep SAST", "SEMGREP_RESULT"),
        ("Trivy fs/config", "TRIVY_RESULT"),
        ("Gitleaks", "GITLEAKS_RESULT"),
        ("Custom OWASP scan", "CUSTOM_SCAN_RESULT"),
    ]
    summary = scan_report.get("summary", {})
    findings = scan_report.get("findings", [])
    blockers = has_blockers(scan_report)

    lines = [
        MARKER,
        "# Team Security Audit Report",
        "",
        f"- Result: {'BLOCKED' if blockers else 'PASSED'}",
        f"- Repository: {os.environ.get('GITHUB_REPOSITORY', 'unknown')}",
        f"- Ref: {os.environ.get('GITHUB_REF_NAME', 'unknown')}",
        f"- Commit: {os.environ.get('GITHUB_SHA', 'unknown')}",
        "",
        "## Job Summary",
        "",
        "| Check | Result |",
        "| --- | --- |",
    ]
    for label, env_name in statuses:
        lines.append(f"| {label} | {job_status(env_name)} |")

    lines.extend(
        [
            "",
            "## Custom OWASP Scan",
            "",
            f"- Total findings: {summary.get('total', 0)}",
            f"- By severity: {json.dumps(summary.get('by_severity', {}), ensure_ascii=False)}",
            f"- By category: {json.dumps(summary.get('by_category', {}), ensure_ascii=False)}",
            "",
            "| Severity | Category | Rule | Location | Message |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for finding in findings[:30]:
        location = f"{finding.get('file')}:{finding.get('line')}"
        lines.append(
            "| {severity} | {category} | `{rule}` | `{location}` | {message} |".format(
                severity=finding.get("severity", "unknown"),
                category=finding.get("category", "unknown").replace("|", "/"),
                rule=finding.get("rule_id", "unknown"),
                location=location.replace("|", "/"),
                message=finding.get("message", "").replace("|", "/"),
            )
        )
    if len(findings) > 30:
        lines.append(f"| info | report | truncated | artifact | {len(findings) - 30} more findings in artifact |")

    lines.extend(
        [
            "",
            "## Required Action",
            "",
            "- Fix critical/high findings before merge.",
            "- Treat medium findings as review-required unless the team accepts the risk.",
            "- Check uploaded artifacts for full JSON/SARIF reports.",
        ]
    )
    return "\n".join(lines) + "\n"


def github_request(method: str, url: str, token: str, payload: dict | None = None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        body = response.read().decode("utf-8")
        return json.loads(body) if body else None


def upsert_comment(report: str) -> None:
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    pr_number = os.environ.get("PR_NUMBER")
    if not token or not repo or not pr_number:
        return

    api = os.environ.get("GITHUB_API_URL", "https://api.github.com")
    comments_url = f"{api}/repos/{repo}/issues/{pr_number}/comments"
    try:
        comments = github_request("GET", comments_url, token) or []
        for comment in comments:
            if MARKER in comment.get("body", ""):
                github_request("PATCH", comment["url"], token, {"body": report[:60000]})
                return
        github_request("POST", comments_url, token, {"body": report[:60000]})
    except (urllib.error.URLError, urllib.error.HTTPError) as exc:
        print(f"::warning::Could not upsert PR comment: {exc}")


def main() -> int:
    scan_report = load_json(os.environ.get("CUSTOM_SCAN_JSON", "security-custom-scan.json"))
    report = render_report(scan_report)
    Path("security-report.md").write_text(report, encoding="utf-8")
    upsert_comment(report)
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with Path(output).open("a", encoding="utf-8") as f:
            f.write(f"has_blockers={'true' if has_blockers(scan_report) else 'false'}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
