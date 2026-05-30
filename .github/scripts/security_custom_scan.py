#!/usr/bin/env python3
"""Lightweight educational security scanner for PR CI.

The scanner intentionally reports patterns, not secrets or exploit payloads.
It is designed to complement dependency scanners and SAST tools in the study
repository with a few project-specific OWASP Top 10 checks.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SKIP_DIRS = {
    ".git",
    ".gradle",
    ".mvn",
    "build",
    "dist",
    "node_modules",
    "target",
    "vendor",
}

INCLUDE_SUFFIXES = {
    ".java",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".html",
    ".yml",
    ".yaml",
    ".properties",
    ".xml",
}


@dataclass(frozen=True)
class Rule:
    rule_id: str
    severity: str
    category: str
    message: str
    pattern: re.Pattern[str]


RULES = [
    Rule(
        "java-native-query-concat",
        "high",
        "A03 Injection",
        "Native SQL query construction was detected. Prefer parameter binding or repository methods.",
        re.compile(r"createNativeQuery\s*\(|Statement\s+\w+\s*=|execute(Query|Update)?\s*\(", re.I),
    ),
    Rule(
        "command-exec",
        "critical",
        "A03 Injection",
        "OS command execution was detected. Never concatenate user input into shell commands.",
        re.compile(r"Runtime\.getRuntime\(\)\.exec|ProcessBuilder\s*\(", re.I),
    ),
    Rule(
        "react-dangerous-html",
        "high",
        "A03 Injection",
        "React dangerous HTML rendering was detected. Sanitize input or avoid raw HTML rendering.",
        re.compile(r"dangerouslySetInnerHTML", re.I),
    ),
    Rule(
        "spring-admin-permit-all",
        "critical",
        "A01 Broken Access Control",
        "Admin route appears to be permitAll. Require authentication and role checks.",
        re.compile(r"(admin|management|actuator).{0,80}permitAll\s*\(", re.I | re.S),
    ),
    Rule(
        "mass-assignment-role-state",
        "high",
        "A01 Broken Access Control",
        "Role or account state appears to be updated from request data. Verify server-side authorization.",
        re.compile(r"\b(role|active|enabled)\s*=\s*\w+\.(role|active|enabled)\b|set(Role|Active|Enabled)\s*\(", re.I),
    ),
    Rule(
        "csrf-disabled",
        "medium",
        "A05 Security Misconfiguration",
        "CSRF disablement was detected. Confirm this is intentional and documented.",
        re.compile(r"csrf\s*\([^)]*\)\s*\.disable\s*\(|csrf\s*\(\s*csrf\s*->\s*csrf\.disable\s*\(", re.I),
    ),
    Rule(
        "wildcard-cors",
        "high",
        "A05 Security Misconfiguration",
        "Wildcard CORS was detected. Restrict origins and never combine wildcard origins with credentials.",
        re.compile(r"allowedOrigins\s*\([^)]*[\"']\*[\"']|allowedOriginPatterns\s*\([^)]*[\"']\*[\"']", re.I),
    ),
    Rule(
        "noop-password-encoder",
        "critical",
        "A02 Cryptographic Failures",
        "NoOpPasswordEncoder was detected. Use a strong adaptive password encoder.",
        re.compile(r"NoOpPasswordEncoder|withDefaultPasswordEncoder", re.I),
    ),
    Rule(
        "weak-crypto",
        "high",
        "A02 Cryptographic Failures",
        "Weak cryptography or randomness was detected. Use modern algorithms and SecureRandom.",
        re.compile(r"MessageDigest\.getInstance\s*\(\s*[\"']MD5|new\s+Random\s*\(", re.I),
    ),
    Rule(
        "secret-like-literal",
        "high",
        "A02 Cryptographic Failures",
        "Secret-like variable assignment was detected. Store credentials in secrets or environment variables.",
        re.compile(
            r"(?i)(password|passwd|secret|token|api[_-]?key|signing[_-]?key)\s*[:=]\s*[\"'][^\"']{8,}[\"']"
        ),
    ),
    Rule(
        "sensitive-log",
        "medium",
        "A09 Security Logging and Monitoring Failures",
        "Sensitive value logging keyword was detected. Avoid logging tokens, passwords, and signing keys.",
        re.compile(r"(log|logger|console)\.\w+\s*\([^)]*(token|password|secret|key)", re.I | re.S),
    ),
    Rule(
        "ssrf-sink",
        "high",
        "A10 Server-Side Request Forgery",
        "Server-side URL fetch sink was detected. Allowlist destinations and block private ranges.",
        re.compile(r"RestTemplate|WebClient|openConnection\s*\(|HttpClient|new\s+URL\s*\(", re.I),
    ),
    Rule(
        "external-script-without-sri",
        "medium",
        "A08 Software and Data Integrity Failures",
        "External script tag was detected. Verify Subresource Integrity and pinned versions.",
        re.compile(r"<script[^>]+src=[\"']https?://(?![^>]+integrity=)", re.I),
    ),
]


def iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in INCLUDE_SUFFIXES:
            yield path


def sanitize_excerpt(line: str) -> str:
    line = re.sub(
        r"(?i)(password|passwd|secret|token|api[_-]?key|signing[_-]?key)(\s*[:=]\s*)[\"'][^\"']+[\"']",
        r"\1\2\"[REDACTED]\"",
        line,
    )
    return line.strip()[:220]


def scan(root: Path) -> dict:
    findings = []
    cwd = Path.cwd().resolve()
    for path in iter_files(root):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        lines = text.splitlines()
        for rule in RULES:
            for match in rule.pattern.finditer(text):
                line_no = text.count("\n", 0, match.start()) + 1
                excerpt = sanitize_excerpt(lines[line_no - 1] if line_no <= len(lines) else "")
                findings.append(
                    {
                        "rule_id": rule.rule_id,
                        "severity": rule.severity,
                        "category": rule.category,
                        "message": rule.message,
                        "file": str(path.relative_to(cwd) if path.is_relative_to(cwd) else path),
                        "line": line_no,
                        "excerpt": excerpt,
                    }
                )

    by_severity: dict[str, int] = {}
    by_category: dict[str, int] = {}
    for finding in findings:
        by_severity[finding["severity"]] = by_severity.get(finding["severity"], 0) + 1
        by_category[finding["category"]] = by_category.get(finding["category"], 0) + 1

    return {
        "summary": {
            "total": len(findings),
            "by_severity": by_severity,
            "by_category": by_category,
        },
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Directory to scan")
    parser.add_argument("--out", default="security-custom-scan.json", help="JSON report path")
    parser.add_argument("--fail-on", default="high", choices=["critical", "high", "medium", "never"])
    args = parser.parse_args()

    root = Path(args.root).resolve()
    report = scan(root)
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    severity_rank = {"critical": 3, "high": 2, "medium": 1}
    threshold = severity_rank.get(args.fail_on, 0)
    if threshold:
        for severity, count in report["summary"]["by_severity"].items():
            if severity_rank.get(severity, 0) >= threshold and count > 0:
                print(f"Security custom scan found {count} {severity} finding(s).")
                return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
