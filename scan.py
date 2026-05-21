#!/usr/bin/env python3
"""security-audit: regex-based first-pass scanner.

Goal: collect candidates, not pass final judgment. A human (Claude) reads
the actual files to filter false positives.

Usage:
    python scan.py --root <PROJECT_ROOT> [--out result.json]

ripgrep(rg) is used when available; otherwise pure-Python walk is used.
ripgrep's Rust regex does not support lookahead/lookbehind, so those are
handled via post_filter. It also does not accept \" / \' escape sequences,
so patterns use triple-quoted raw strings with bare ' / " characters.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable


RULES = [
    {
        "rule_id": "SEC-001",
        "category": "secrets",
        "severity": "high",
        "title": "Hardcoded JWT/secret with weak/short value",
        "pattern": r"""(JWT_SECRET|SECRET_KEY|API_KEY|access_key)\s*[:=]\s*['"][^'"$\{][^'"]{0,30}['"]""",
        "globs": ["*.ts", "*.js", "*.java", "*.kts", "*.yml", "*.yaml", "*.properties", "*.env*"],
    },
    {
        "rule_id": "SEC-002",
        "category": "secrets",
        "severity": "critical",
        "title": ".env contains plaintext secret tracked by git",
        "pattern": r"^\s*[A-Z][A-Z0-9_]*(SECRET|PASSWORD|TOKEN|KEY|CREDENTIAL)[A-Z0-9_]*\s*=\s*\S+",
        "globs": [".env", ".env.*"],
    },
    {
        "rule_id": "SEC-003",
        "category": "secrets",
        "severity": "high",
        "title": "AWS access key / private key pattern",
        "pattern": r"(AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)",
        "globs": ["*"],
    },
    {
        "rule_id": "AUTH-101",
        "category": "auth",
        "severity": "high",
        "title": "NestJS @Body() any (no DTO)",
        "pattern": r"@Body\(\)\s+\w+\s*:\s*any\b",
        "globs": ["*.ts"],
    },
    {
        "rule_id": "AUTH-102",
        "category": "auth",
        "severity": "high",
        "title": "Object.assign with DTO (Mass Assignment risk)",
        "pattern": r"Object\.assign\(\s*[\w\.]+\s*,\s*[\w\.]+",
        "globs": ["*.ts"],
    },
    {
        "rule_id": "AUTH-103",
        "category": "auth",
        "severity": "high",
        "title": "repository.save({ ...dto }) (Mass Assignment risk)",
        "pattern": r"\.save\(\s*\{\s*\.\.\.\w+",
        "globs": ["*.ts"],
    },
    {
        "rule_id": "AUTH-104",
        "category": "auth",
        "severity": "critical",
        "title": "Public path uses startsWith prefix matching",
        "pattern": r"\b(req\.path|req\.url|path)\s*\.startsWith\(",
        "globs": ["*.ts", "*.js"],
    },
    {
        "rule_id": "AUTH-105",
        "category": "auth",
        "severity": "critical",
        "title": "dev_mode / SKIP_AUTH bypass parameter",
        "pattern": r"\b(dev_mode|skipAuth|bypassAuth|ALLOW_INSECURE|SKIP_AUTH)\b",
        "globs": ["*.ts", "*.js", "*.java", "*.kts", "*.dart"],
    },
    {
        "rule_id": "AUTH-106",
        "category": "auth",
        "severity": "medium",
        "title": "Token stored in localStorage/sessionStorage",
        "pattern": r"""(localStorage|sessionStorage)\.setItem\(\s*['"][^'"]*[tT]oken""",
        "globs": ["*.ts", "*.tsx", "*.js", "*.jsx"],
    },
    {
        "rule_id": "JPA-201",
        "category": "jpa",
        "severity": "critical",
        "title": "TypeORM synchronize: true (data-loss risk)",
        "pattern": r"synchronize\s*:\s*true",
        "globs": ["*.ts", "*.js"],
    },
    {
        "rule_id": "JPA-202",
        "category": "jpa",
        "severity": "critical",
        "title": "JPA ddl-auto = update/create/create-drop",
        "pattern": r"ddl-auto\s*:\s*(update|create|create-drop)\b",
        "globs": ["*.yml", "*.yaml", "*.properties"],
    },
    {
        "rule_id": "CORS-301",
        "category": "cors_csrf",
        "severity": "high",
        "title": "CORS wildcard with credentials",
        "pattern": r"""(setAllowedOriginPatterns\(\s*['"]\*|origin\s*:\s*['"]\*['"]|cors\(\{\s*origin\s*:\s*true)""",
        "globs": ["*.ts", "*.js", "*.java", "*.kts"],
    },
    {
        "rule_id": "CORS-302",
        "category": "cors_csrf",
        "severity": "high",
        "title": "Spring Security csrf().disable() — review reason",
        "pattern": r"\.csrf\(\s*\)\s*\.disable\(\s*\)|csrf\s*->\s*csrf\.disable\(\s*\)",
        "globs": ["*.java", "*.kt", "*.kts"],
    },
    {
        "rule_id": "INPUT-401",
        "category": "input",
        "severity": "high",
        "title": "Spring @RequestBody binds Entity directly",
        "pattern": r"@RequestBody\s+\w*Entity\b",
        "globs": ["*.java", "*.kt"],
    },
    {
        "rule_id": "LOG-501",
        "category": "logging",
        "severity": "medium",
        "title": "Logging entire user object",
        "pattern": r"(console\.(log|info|warn)|logger\.(info|debug|warn))\(\s*\bu(ser)?\b",
        "globs": ["*.ts", "*.tsx", "*.js"],
    },
    {
        "rule_id": "LOG-502",
        "category": "logging",
        "severity": "medium",
        "title": "Spring show-sql / DEBUG logging in prod",
        "pattern": r"(show-sql|show_sql)\s*:\s*true|logging\.level\..*:\s*DEBUG",
        "globs": ["*.yml", "*.yaml", "*.properties"],
    },
    {
        "rule_id": "IP-601",
        "category": "ip",
        "severity": "high",
        "title": "X-Forwarded-For trusted directly",
        "pattern": r"""['"]X-Forwarded-For['"]|x-forwarded-for""",
        "globs": ["*.ts", "*.js", "*.java", "*.kt", "*.kts"],
    },
    {
        "rule_id": "DART-701",
        "category": "flutter",
        "severity": "medium",
        "title": "Dart throw 'string' (not Exception)",
        "pattern": r"""throw\s+['"]""",
        "globs": ["*.dart"],
    },
    {
        "rule_id": "DART-702",
        "category": "flutter",
        "severity": "high",
        "title": "Token stored via SharedPreferences",
        "pattern": r"""setString\(\s*['"]\w*[tT]oken""",
        "globs": ["*.dart"],
    },
    {
        "rule_id": "DART-703",
        "category": "flutter",
        "severity": "medium",
        "title": "Plaintext HTTP call",
        "pattern": r"http://[a-zA-Z0-9\.-]+",
        "globs": ["*.dart"],
        "post_filter": "exclude_localhost_http",
    },
    {
        "rule_id": "INF-801",
        "category": "infra",
        "severity": "critical",
        "title": "docker-compose binds DB/cache port to all hosts",
        "pattern": r"""^\s*-\s*['"]?\d+\s*:\s*(5432|3306|27017|6379|9200|11211|9092)\s*['"]?\s*$""",
        "post_filter": "exclude_loopback_prefix",
        "globs": ["docker-compose*.yml", "docker-compose*.yaml", "compose*.yml"],
    },
    {
        "rule_id": "INF-802",
        "category": "infra",
        "severity": "medium",
        "title": "Docker base image latest tag",
        "pattern": r"^\s*FROM\s+\S+:latest\b",
        "globs": ["Dockerfile", "Dockerfile.*", "*.dockerfile"],
    },
    {
        "rule_id": "INF-803",
        "category": "infra",
        "severity": "medium",
        "title": "Dockerfile USER root",
        "pattern": r"^\s*USER\s+root\b",
        "globs": ["Dockerfile", "Dockerfile.*", "*.dockerfile"],
    },
    {
        "rule_id": "INF-804",
        "category": "infra",
        "severity": "medium",
        "title": "nginx server_tokens off missing (version exposed)",
        "pattern": r"server_tokens\s+off",
        "globs": ["nginx.conf", "*.conf"],
        "negate": True,
    },
    {
        "rule_id": "PAY-901",
        "category": "payment",
        "severity": "critical",
        "title": "Payment callback controller (verify signature/amount manually)",
        "pattern": r"""(callback|webhook|paymentResult|notify).*\b(amount|price|total)\b""",
        "globs": ["*.ts", "*.java", "*.kt"],
    },
]


SKIP_DIRS = {
    "node_modules", ".git", "build", "dist", "out", ".next", ".nuxt",
    "target", "__pycache__", ".gradle", ".idea", ".venv", "venv",
    "coverage", ".turbo", ".dart_tool",
}

TEST_PATTERNS = [
    re.compile(r"\.test\.[jt]sx?$"),
    re.compile(r"\.spec\.[jt]sx?$"),
    re.compile(r"/__tests__/"),
    re.compile(r"/test/"),
    re.compile(r"/tests/"),
    re.compile(r"Test\.java$"),
    re.compile(r"_test\.dart$"),
]


@dataclass
class Finding:
    rule_id: str
    category: str
    severity: str
    title: str
    file: str
    line: int
    snippet: str
    is_test_file: bool = False


@dataclass
class ScanResult:
    root: str
    rg_used: bool
    findings: list = field(default_factory=list)
    summary: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)


def is_test_file(path):
    return any(p.search(path) for p in TEST_PATTERNS)


def relative(path, root):
    try:
        return str(Path(path).resolve().relative_to(Path(root).resolve()))
    except ValueError:
        return path


def has_rg():
    return shutil.which("rg") is not None


def _passes_post_filter(name, line):
    if not name:
        return True
    if name == "exclude_loopback_prefix":
        return "127.0.0.1:" not in line
    if name == "exclude_localhost_http":
        for skip in ("http://localhost", "http://127.0.0.1", "http://10.0.2.2"):
            if skip in line:
                return False
        return True
    return True


def _adjust_severity(sev, is_test):
    if not is_test:
        return sev
    if sev == "critical":
        return "high"
    if sev == "high":
        return "medium"
    return sev


def rg_search(rule, root):
    cmd = ["rg", "--no-heading", "--line-number", "--with-filename", "--color", "never",
           "--hidden", "-e", rule["pattern"]]
    for g in rule.get("globs", []):
        cmd += ["-g", g]
    for skip in SKIP_DIRS:
        cmd += ["-g", "!" + skip + "/**"]
    cmd += [root]

    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return []

    findings = []
    post_filter = rule.get("post_filter")
    for line in out.stdout.splitlines():
        parts = line.split(":", 2)
        if len(parts) < 3:
            continue
        path, lineno, content = parts
        try:
            ln = int(lineno)
        except ValueError:
            continue
        if not _passes_post_filter(post_filter, content):
            continue
        rel = relative(path, root)
        is_test = is_test_file(rel)
        findings.append(Finding(
            rule_id=rule["rule_id"],
            category=rule["category"],
            severity=_adjust_severity(rule["severity"], is_test),
            title=rule["title"],
            file=rel,
            line=ln,
            snippet=content.strip()[:200],
            is_test_file=is_test,
        ))
    return findings


def py_match_files(root, globs):
    import fnmatch
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not (d.startswith(".") and d != ".env")]
        for fn in filenames:
            for g in globs:
                if fnmatch.fnmatch(fn, g) or fnmatch.fnmatch(os.path.join(dirpath, fn), g):
                    yield os.path.join(dirpath, fn)
                    break


def py_search(rule, root):
    pat = re.compile(rule["pattern"], re.MULTILINE)
    post_filter = rule.get("post_filter")
    findings = []
    for path in py_match_files(root, rule.get("globs", [])):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f, start=1):
                    if pat.search(line) and _passes_post_filter(post_filter, line):
                        rel = relative(path, root)
                        is_test = is_test_file(rel)
                        findings.append(Finding(
                            rule_id=rule["rule_id"],
                            category=rule["category"],
                            severity=_adjust_severity(rule["severity"], is_test),
                            title=rule["title"],
                            file=rel,
                            line=i,
                            snippet=line.strip()[:200],
                            is_test_file=is_test,
                        ))
        except (OSError, UnicodeDecodeError):
            continue
    return findings


def handle_negate_rule(rule, root, findings_for_rule):
    matched_files = {f.file for f in findings_for_rule}
    out = []
    for path in py_match_files(root, rule.get("globs", [])):
        rel = relative(path, root)
        if rel in matched_files:
            continue
        out.append(Finding(
            rule_id=rule["rule_id"],
            category=rule["category"],
            severity=rule["severity"],
            title=rule["title"] + " (configuration absent)",
            file=rel,
            line=0,
            snippet="(setting missing - manual verification required)",
            is_test_file=False,
        ))
    return out


def run_scan(root):
    root = str(Path(root).resolve())
    rg = has_rg()
    result = ScanResult(root=root, rg_used=rg)

    for rule in RULES:
        try:
            if rg:
                hits = rg_search(rule, root)
            else:
                hits = py_search(rule, root)
        except re.error as e:
            result.notes.append("rule {0} regex error: {1}".format(rule["rule_id"], e))
            continue

        if rule.get("negate"):
            hits = handle_negate_rule(rule, root, hits)

        result.findings.extend(hits)

    by_severity = {}
    by_category = {}
    by_rule = {}
    for f in result.findings:
        by_severity[f.severity] = by_severity.get(f.severity, 0) + 1
        by_category[f.category] = by_category.get(f.category, 0) + 1
        by_rule[f.rule_id] = by_rule.get(f.rule_id, 0) + 1

    result.summary = {
        "total": len(result.findings),
        "by_severity": by_severity,
        "by_category": by_category,
        "by_rule": by_rule,
        "rg_used": rg,
    }
    return result


def main():
    parser = argparse.ArgumentParser(description="security-audit first-pass scanner")
    parser.add_argument("--root", required=True)
    parser.add_argument("--out")
    args = parser.parse_args()

    root = args.root
    if not Path(root).exists():
        sys.stderr.write("path not found: " + root + "\n")
        return 2

    result = run_scan(root)
    payload = {
        "root": result.root,
        "summary": result.summary,
        "notes": result.notes,
        "findings": [asdict(f) for f in result.findings],
    }

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        sys.stderr.write("saved: " + args.out + "\n")
    else:
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)

    s = result.summary
    rg_label = "ON" if s["rg_used"] else "OFF"
    sys.stderr.write("\n=== Summary ===\n")
    sys.stderr.write("total: %d / ripgrep: %s\n" % (s["total"], rg_label))
    sys.stderr.write("severity: %s\n" % s.get("by_severity"))
    sys.stderr.write("category: %s\n" % s.get("by_category"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
