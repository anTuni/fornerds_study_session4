#!/usr/bin/env python3
"""Generate security audit PR comment from scan results and post to GitHub."""

from __future__ import annotations

import json
import os
import subprocess
import urllib.request
from pathlib import Path

# ── 환경 변수 로드 ────────────────────────────────────────────────────
TOKEN = os.environ["GITHUB_TOKEN"]
PR_NUMBER = os.environ["PR_NUMBER"]
REPO = os.environ["REPO"]
BASE_SHA = os.environ.get("BASE_SHA", "HEAD~1")
HEAD_SHA = os.environ.get("HEAD_SHA", "HEAD")

SECRET_SCAN_RESULT = os.environ.get("SECRET_SCAN_RESULT", "")    # success / failure / skipped
HAS_CRITICAL = os.environ.get("HAS_CRITICAL", "false") == "true"
HAS_HIGH = os.environ.get("HAS_HIGH", "false") == "true"
BACKEND_DEP_FAILED = os.environ.get("BACKEND_DEP_FAILED", "false") == "true"
FRONTEND_DEP_FAILED = os.environ.get("FRONTEND_DEP_FAILED", "false") == "true"

SEV_ICON = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
SEV_ORDER = ["critical", "high", "medium", "low"]

# ── checklist.md Hard Gate 항목 ────────────────────────────────────
# (category는 scan.py RULES의 category 값과 매핑)
HARD_GATE_ITEMS = [
    ("신규/변경 엔드포인트에 인증·인가 적용", ["auth"]),
    ("쿠키 인증 추가/변경 시 CSRF 방어 동반", ["cors_csrf"]),
    ("공개 경로 목록에 prefix로 의도치 않게 포함된 경로 없음", ["auth"]),
    ("PII가 URL 쿼리스트링·로그에 노출되지 않음", ["logging"]),
    ("자격증명·토큰·API 키·테스트 계정이 코드에 평문 없음", ["secrets"]),
    ("X-Forwarded-For 직접 신뢰하지 않음", ["ip"]),
    ("사용자 입력 렌더링 시 sanitizer 경유", ["input"]),
    ("시크릿/토큰 비교가 타이밍 안전 함수 사용", ["auth"]),
    ("인증 실패 메시지가 enumeration 가능한 분기 없음", ["auth"]),
    ("HTTPS 강제 및 HSTS 유지", ["infra"]),
    ("Docker/인프라 포트 전체 노출 없음", ["infra"]),
    ("의존성 알려진 CVE 없음 (CVSS 7.0+)", ["dependency"]),
    ("시크릿/자격증명 Git 커밋 없음", ["secrets"]),
]

# ── infra-patterns.md 인프라 체크 항목 (scan.py INF 룰과 매핑) ────
INFRA_RULE_IDS = {"INF-801", "INF-802", "INF-803", "INF-804"}


def get_changed_files() -> list[str]:
    try:
        result = subprocess.check_output(
            ["git", "diff", "--name-only", BASE_SHA, HEAD_SHA], text=True
        )
        return [f for f in result.strip().split("\n") if f]
    except subprocess.CalledProcessError:
        return []


def load_scan_results() -> dict:
    path = Path("scan-results.json")
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {"findings": [], "summary": {"total": 0, "by_severity": {}, "by_category": {}, "by_rule": {}}}


def build_checklist_rows(findings: list[dict]) -> tuple[list[str], int]:
    """체크리스트 항목별 통과/실패 행 생성. 실패 수 반환."""
    failed_categories = {f["category"] for f in findings if f["severity"] in ("critical", "high")}

    # 시크릿 스캔 실패 → secrets 카테고리 실패로 처리
    if SECRET_SCAN_RESULT == "failure":
        failed_categories.add("secrets")

    # 의존성 스캔 실패 → dependency 카테고리 추가
    if BACKEND_DEP_FAILED or FRONTEND_DEP_FAILED:
        failed_categories.add("dependency")

    rows = []
    fail_count = 0
    for item, cats in HARD_GATE_ITEMS:
        if any(c in failed_categories for c in cats):
            rows.append(f"| ❌ 실패 | {item} |")
            fail_count += 1
        else:
            rows.append(f"| ✅ 통과 | {item} |")
    return rows, fail_count


def build_findings_section(findings: list[dict]) -> list[str]:
    lines = []
    for sev in SEV_ORDER:
        sev_findings = [f for f in findings if f["severity"] == sev]
        if not sev_findings:
            continue
        icon = SEV_ICON.get(sev, "")
        lines.append(f"#### {icon} {sev.upper()} ({len(sev_findings)}건)")
        lines.append("")
        lines.append("| Rule ID | 카테고리 | 설명 | 파일:라인 |")
        lines.append("|---------|----------|------|-----------|")
        for f in sev_findings[:15]:
            snippet = f["snippet"].replace("|", "\\|")[:80]
            test_mark = " *(test)*" if f.get("is_test_file") else ""
            lines.append(
                f"| `{f['rule_id']}` | {f['category']} | {f['title']}{test_mark} "
                f"| `{f['file']}:{f['line']}` |"
            )
        if len(sev_findings) > 15:
            lines.append(f"| ... | | 외 {len(sev_findings) - 15}건 더 있음 | |")
        lines.append("")
    return lines


def generate_comment(changed_files: list[str], scan_data: dict) -> tuple[str, bool]:
    findings = scan_data.get("findings", [])
    summary = scan_data.get("summary", {})
    by_sev = summary.get("by_severity", {})
    by_cat = summary.get("by_category", {})

    checklist_rows, fail_count = build_checklist_rows(findings)

    has_blockers = (
        HAS_CRITICAL
        or HAS_HIGH
        or SECRET_SCAN_RESULT == "failure"
        or BACKEND_DEP_FAILED
        or FRONTEND_DEP_FAILED
    )

    lines: list[str] = []

    # 헤더
    lines.append("## 🔒 보안 감사 리포트")
    lines.append("")
    overall = "❌ 차단 — 취약점 발견됨" if has_blockers else "✅ 통과 — 머지 가능"
    lines.append(f"**최종 판정:** {overall}")
    lines.append("")

    # ── 변경된 파일 ──────────────────────────────────────────────
    lines.append("<details>")
    lines.append(f"<summary>📁 변경된 파일 ({len(changed_files)}개)</summary>")
    lines.append("")
    for f in changed_files[:30]:
        lines.append(f"- `{f}`")
    if len(changed_files) > 30:
        lines.append(f"- ... 외 {len(changed_files) - 30}개")
    lines.append("")
    lines.append("</details>")
    lines.append("")

    # ── 스캔 도구별 요약 ──────────────────────────────────────────
    lines.append("### 📊 스캔 결과 요약")
    lines.append("")
    lines.append("| 도구 | 결과 |")
    lines.append("|------|------|")
    lines.append(f"| 🔑 Gitleaks (시크릿 탐지) | {'❌ 노출 감지' if SECRET_SCAN_RESULT == 'failure' else '✅ 이상 없음'} |")
    lines.append(f"| 🔍 scan.py (커스텀 룰) | {'❌ ' + str(summary.get('total', 0)) + '건 발견' if summary.get('total', 0) > 0 else '✅ 이상 없음'} |")
    lines.append(f"| 📦 OWASP Dep Check (백엔드) | {'❌ 취약 의존성 발견' if BACKEND_DEP_FAILED else '✅ 이상 없음'} |")
    lines.append(f"| 📦 npm audit (프론트엔드) | {'❌ 취약 패키지 발견' if FRONTEND_DEP_FAILED else '✅ 이상 없음'} |")
    lines.append("")

    # scan.py 심각도별 집계
    if summary.get("total", 0) > 0:
        lines.append("**scan.py 심각도별 집계:**")
        lines.append("")
        lines.append("| 심각도 | 건수 |")
        lines.append("|--------|------|")
        for sev in SEV_ORDER:
            cnt = by_sev.get(sev, 0)
            if cnt > 0:
                lines.append(f"| {SEV_ICON.get(sev, '')} {sev.upper()} | {cnt} |")
        lines.append("")

    # ── Hard Gate 체크리스트 ──────────────────────────────────────
    lines.append("### ✅ 보안 체크리스트 (Hard Gate)")
    lines.append("")
    lines.append(f"> 통과: **{len(HARD_GATE_ITEMS) - fail_count}/{len(HARD_GATE_ITEMS)}** 항목")
    lines.append("")
    lines.append("| 결과 | 항목 |")
    lines.append("|------|------|")
    lines.extend(checklist_rows)
    lines.append("")

    # ── 발견된 취약점 상세 ─────────────────────────────────────────
    if findings:
        lines.append("<details>")
        lines.append(f"<summary>🔍 발견된 취약점 상세 (총 {summary.get('total', 0)}건)</summary>")
        lines.append("")
        lines.extend(build_findings_section(findings))
        lines.append("</details>")
        lines.append("")

    # ── 최종 판정 ─────────────────────────────────────────────────
    lines.append("---")
    if has_blockers:
        lines.append("### ❌ 머지 차단")
        lines.append("")
        lines.append("> HIGH 또는 CRITICAL 수준의 보안 취약점이 발견되었습니다.")
        lines.append("> 취약점을 수정하거나 관리자의 검토·승인(`security-review` environment) 후 머지할 수 있습니다.")
    else:
        lines.append("### ✅ 보안 감사 통과")
        lines.append("")
        lines.append("> 심각한 취약점이 발견되지 않았습니다. 머지 가능합니다.")

    return "\n".join(lines), has_blockers


def post_pr_comment(body: str) -> None:
    url = f"https://api.github.com/repos/{REPO}/issues/{PR_NUMBER}/comments"
    payload = json.dumps({"body": body}).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req) as resp:
        if resp.status not in (200, 201):
            raise RuntimeError(f"GitHub API error: {resp.status}")


def write_output(has_blockers: bool) -> None:
    output_file = os.environ.get("GITHUB_OUTPUT", "")
    if output_file:
        with open(output_file, "a") as f:
            f.write(f"has_blockers={'true' if has_blockers else 'false'}\n")


if __name__ == "__main__":
    changed_files = get_changed_files()
    scan_data = load_scan_results()
    comment_body, has_blockers = generate_comment(changed_files, scan_data)
    post_pr_comment(comment_body)
    write_output(has_blockers)
    print(f"Report posted. has_blockers={has_blockers}")
