# Security Audit Workflow — `defend/tuni`

## 동작 조건

`defend/tuni` 브랜치를 **대상으로 하는 PR**이 열리거나 업데이트되면 자동 실행됩니다.

```yaml
on:
  pull_request:
    branches:
      - defend/tuni
```

## 실행되는 검사

| 잡 | 도구 | 대상 |
| --- | --- | --- |
| `backend-dependency-check` | OWASP Dependency-Check (Maven) | Java 의존성 CVE |
| `frontend-npm-audit` | `npm audit` | npm 의존성 CVE |
| `semgrep-sast` | Semgrep (OWASP Top 10 + Java/JS/TS 룰) | 소스코드 SAST |
| `trivy-fs-scan` | Trivy (vuln + secret + misconfig) | FS 전체 — 의존성·시크릿·설정 |
| `build-final-report` | 통합 리포트 생성 | 결과 집계 / PR 코멘트 |

## 머지 차단 정책

다음 조건이 하나라도 발생하면 `build-final-report` 잡이 실패하고, 결과적으로 PR check가 빨간색이 되어 머지가 막힙니다.

- OWASP Dependency-Check가 CVSS 7.0 이상 발견 (`-DfailBuildOnCVSS=7.0`)
- `npm audit --audit-level=high` 가 high/critical 발견
- Semgrep 룰셋 위반 1건 이상 (`--error`)
- Trivy가 CRITICAL/HIGH (fixed 가능) 1건 이상 발견 (`exit-code: '1'`)

> GitHub repo Settings → Branches → `defend/tuni` Branch protection rule 에서
> "Require status checks to pass before merging"을 켜고 위 잡들을 필수로 지정하면
> 실제로 Merge 버튼이 비활성화됩니다. workflow 만으로도 Check는 실패하지만,
> "관리자 우회 머지"까지 막으려면 보호 규칙 설정이 필요합니다.

## 리포트 확인 방법

PR 마다 다음 두 위치에서 결과를 확인할 수 있습니다.

1. **PR 코멘트** — 봇이 자동으로 요약 리포트를 코멘트로 남기고, 재실행 시 같은 코멘트를 업데이트합니다.
2. **Workflow run → Artifacts** — 다음 아티팩트가 매 실행마다 30일간 보관됩니다.
   - `security-report` (Markdown 통합 리포트 + 전체 원본)
   - `backend-owasp-report` (HTML/JSON/SARIF)
   - `frontend-npm-audit-report` (JSON/TXT)
   - `semgrep-sast-report` (SARIF/JSON)
   - `trivy-fs-report` (SARIF/JSON)
3. **Job Summary** — 통합 Markdown 리포트가 워크플로우 실행 화면 하단의 Summary에도 인라인으로 표시됩니다.

리포트 각 항목은 다음을 포함합니다.

- 심각도 (Critical/High/Medium/Low)
- 취약점 ID (CVE / GHSA / Semgrep rule id)
- 위치 (파일 경로, 패키지명, 라인)
- 설명
- **조치 방법** (업그레이드 버전, `npm audit fix`, Semgrep fix-suggestion, 시크릿 회수 절차 등)
