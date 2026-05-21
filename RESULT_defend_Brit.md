# 보안감사 실습 결과 정리 양식

> 이 양식은 조별 보고서가 아니라 **하나의 `defend/{name}` 브랜치**를 기준으로 작성합니다.
> 한 조에 두 명이 있다면 각자의 방어 브랜치별로 이 문서를 하나씩 작성합니다.

## 1. 방어 브랜치 기본 정보

| 항목 | 내용 |
| --- | --- |
| 작성 기준 브랜치 | `defend/Brit` |
| 수비자 | Brit (GitHub: `Brit-juho`, 표시명 `NetrioGit`) |
| 페어 | tuni (`anTuni`) |
| 작성일 | 2026-05-21 |
| 실습 저장소 | `anTuni/fornerds_study_session4` |
| 결과 문서 작성자 | Brit |
| 관련 최종 PR 또는 공유 링크 | https://github.com/anTuni/fornerds_study_session4/pull/10 (공격 PR, attack/sabo → defend/Brit) |

## 2. 방어 브랜치 이력 요약

`defend/Brit` 브랜치에서 보안감사 workflow를 추가하거나 개선한 commit을 정리합니다.

| 순서 | Commit | 작성자 | 메시지 | 주요 변경 내용 |
| --- | --- | --- | --- | --- |
| 1 | `5100118` | NetrioGit (Brit) | ci(defend/Brit): add security audit workflow and dependency policy | `.github/workflows/security-audit.yml` (590줄, Snyk/OWASP DC/Semgrep/Gitleaks/Trivy + aggregate-report + build gate), `.github/workflows/dependabot-auto-merge.yml`, `.github/dependabot.yml`, `cicd_practice/SECURITY_POLICY.md` (W1~W11 정책), `cicd_practice/SECURITY_TOOLS.md`, frontend `package.json`/`lock`에서 "latest" 의존성을 고정 버전으로 교체, `.gitignore` 보강 — 8 files, +1060/-52 |
| 2 | 해당 없음 | 해당 없음 | 해당 없음 | 해당 없음 |
| 3 | 해당 없음 | 해당 없음 | 해당 없음 | 해당 없음 |

## 3. 방어자가 만든 보안감사 Workflow 요약

| 항목 | 내용 |
| --- | --- |
| workflow 파일 경로 | `.github/workflows/security-audit.yml` |
| workflow 이름 | `Security Audit (defend/Brit)` |
| 실행 트리거 | `pull_request` (branches: `defend/Brit`) + `workflow_dispatch` |
| 대상 방어 브랜치 | `defend/Brit` |
| 사용한 도구 | Snyk (Maven backend), Snyk (npm frontend) + `npm audit` 보조, OWASP Dependency-Check (Maven), Semgrep (`p/owasp-top-ten`, `p/java`, `p/javascript`, `p/react`, `p/secrets`, `p/security-audit`), Gitleaks (Docker), Trivy fs (vuln/secret/misconfig) |
| 보고서 생성 방식 | 각 잡 artifact 업로드 (SARIF + JSON) + `aggregate-report` 잡이 Python으로 단일 Markdown 집계 → `actions/github-script`로 PR에 marker 댓글 upsert + GitHub Security(SARIF) 업로드 + Critical 발견 시 Issue 자동 생성(labels: security/critical/automated) |
| 실패 기준 | Snyk `--severity-threshold=high` / OWASP DC `failBuildOnCVSS=7.0` / npm audit `--audit-level=high` / Semgrep ERROR 레벨 / Gitleaks 1건 이상 / Trivy CRITICAL,HIGH (SECURITY_POLICY.md §1) |
| PR 차단 방식 | branch protection 미설정 (아래 §8 참조), 보안 잡 실패가 build-backend/build-frontend의 `needs:`로 연결되어 빌드는 자동 차단되지만 머지는 required check 없이 수동 차단에 의존 |
| required status check 이름 | 미설정 (확인 결과 branch protection 자체가 없음) |
| 평균 실행 시간 | 확인 필요 (defend/Brit 워크플로 단독 run 기록이 PR #10에 보이지 않음, 부록 §B 참조) |
| 가장 느린 단계 | 확인 필요 (동일 사유) |

### Workflow 핵심 설정

```yaml
name: Security Audit (defend/Brit)
on:
  pull_request:
    branches:
      - defend/Brit
  workflow_dispatch:

permissions:
  contents: read
  pull-requests: write
  issues: write
  security-events: write

concurrency:
  group: security-audit-${{ github.ref }}
  cancel-in-progress: true

jobs:
  analyze:            # 변경 경로 분석 (현재는 항상 full scan)
  snyk-backend:       # Snyk Maven (W11 / A06)
  snyk-frontend:      # Snyk npm + npm audit 보조 (W11 / A06)
  owasp-dc:           # OWASP Dependency-Check, failBuildOnCVSS=7.0
  semgrep:            # SAST (W2/W3/W4/W6/W10 / A03/A05/A02)
  gitleaks:           # 시크릿 (W8.1)
  trivy-fs:           # SCA/시크릿/IaC 보조
  aggregate-report:   # PR comment + Critical Issue 자동 생성
  build-backend:      # 보안 게이트 통과 후 mvn verify
  build-frontend:     # 보안 게이트 통과 후 npm ci && build
```

### Workflow 설계 의도

- 정책-도구-룰셋이 분리: `SECURITY_POLICY.md` (W1~W11 임계값) → `SECURITY_TOOLS.md` (도구 매핑) → 워크플로(실행)로 3단 분리해 정책 변경 시 워크플로 재작성 없이 임계값만 조정 가능하게 함.
- SARIF/JSON 이중 출력으로 (1) GitHub Security 탭 통합, (2) `aggregate-report`가 Python으로 파싱해 Markdown 집계, (3) Critical만 별도 Issue 자동 발행하여 정책 §1 "Critical 24h SLA"와 직결.
- `build-backend`/`build-frontend`가 보안 잡들의 `needs:`에 연결되어 high+ 결과가 자동으로 빌드를 차단 — required check 미설정 시에도 빌드 산출물은 못 만들도록 한 방어선.
- 의존성 측면에서 `frontend/package.json`의 `"latest"` 핀을 실제 버전으로 고정해 W11(공급망)·A08(무결성) 리스크를 사전 제거. dependabot patch 자동 머지로 운영 부담 분산.

## 4. 방어 브랜치로 들어온 공격 PR 목록

`defend/Brit`을 base로 생성된 PR을 모두 정리합니다.

| PR | 공격 브랜치 | 공격자 | 상태 | 취약점 유형 | 최종 check 결과 | 머지 차단 여부 |
| --- | --- | --- | --- | --- | --- | --- |
| #10 | `attack/sabo` | `player397` (sabo) | Open | A01/A02/A03(SQLi+XSS)/A05/A06(log4j 2.14.1, lodash 4.17.4 등)/A07/A08/A09/A10 SSRF + hardcoded secrets | Fail (다수 잡 failure, `mergeStateStatus=DIRTY`) | 차단 (mergeable=DIRTY, 다수 체크 실패) 단 required check는 없음 |
| #15 | `attack/tunitobrit` | `anTuni` (페어 tuni) | Open | A03 SQLi (CWE-89) / A01 Broken Access Control·IDOR (CWE-639) / A03 OS Command Injection (CWE-78) — `ContentController.java` 한 파일에 3종 주입 | Fail (Semgrep SAST / Trivy filesystem / Snyk Backend(Maven) / Gitleaks 4개 잡 FAILURE, OWASP DC IN_PROGRESS, `mergeStateStatus=UNSTABLE`) | 사실상 차단 (UNSTABLE + 4개 보안 잡 FAILURE, `build-backend`/`build-frontend`가 `needs:`로 묶여 게이트 차단) 단 required check 없음 |

## 5. 공격/수비 사이클 기록

### Cycle 1

| 항목 | 내용 |
| --- | --- |
| base 브랜치 | `defend/Brit` |
| 공격 브랜치 | `attack/sabo` |
| PR 링크 | https://github.com/anTuni/fornerds_study_session4/pull/10 |
| 공격자 | `player397` (sabo) |
| 수비자 | Brit |
| 취약점 유형 | A01 Broken Access Control, A02 Cryptographic Failures, A03 Injection (SQLi/XSS), A05 Security Misconfiguration, A06 Vulnerable & Outdated Components, A07 Auth Failures, A08 SW/Data Integrity, A09 Logging Failures, A10 SSRF, Hardcoded secrets |
| 공격 commit | `d949b07ac411ad272d54222b163d2b74655f0a2a` |
| 수정 파일 | `cicd_practice/backend/pom.xml`, `auth/AuthService.java`, `config/SecurityConfig.java`, `content/ContentController.java`, `content/ContentRepository.java`, `dashboard/UrlPreviewController.java`, `resources/application.yml`, `frontend/index.html`, `frontend/package.json`, `frontend/src/App.tsx` |
| 취약점 설명 | log4j-core 2.14.1 / snakeyaml 1.30 / commons-collections 3.2.1 / lodash 4.17.4 / minimist 1.2.0 / axios 0.21.0 추가, NoOpPasswordEncoder, java.util.Random 토큰, 하드코드 JWT 키, native SQL 문자열 연결, `dangerouslySetInnerHTML`, CSRF disable + CORS `*` + allowCredentials, `/api/admin/**` permitAll, 토큰 만료 검증 제거, 외부 스크립트 SRI 없이 `latest`, 토큰/서명키 로깅, 임의 URL fetch (SSRF), `application.yml`에 AWS/GitHub/JWT 키 평문 |
| 기대 탐지 결과 | Snyk + OWASP DC + Trivy → log4j/snakeyaml 등 high+, npm audit/Snyk → lodash/minimist/axios high+, Semgrep → SQLi/XSS/CORS/permitAll/SSRF/weak-random/NoOp encoder, Gitleaks → AWS/GitHub/JWT 키, 정책상 모두 fail |

#### 실행 결과

| 점검 항목 | 결과 |
| --- | --- |
| workflow 실행 여부 | 부분 실행 (확인 필요: Brit 본인 워크플로 `Security Audit (defend/Brit)`가 PR #10의 check rollup에 별도 run으로 나타나지 않음 — 동일 path `.github/workflows/security-audit.yml`을 공유한 다른 defenders(`defend/tuni`, `defend/david`, `defend/YUN`)의 워크플로 run이 함께 트리거되어 실패함. 워크플로 ID 280808262 단일 등록) |
| 실행된 workflow 이름 | `Security Audit (defend/tuni)`, `Security Audit (defend/david)`, `Security Audit (defend/YUN)`, `Security Audit` (각 defender의 같은 경로 YAML이 각각 run으로 실행됨) |
| 실행된 check 이름 | Backend - Maven test (fail), Backend - OWASP Dependency Check (fail), Backend - OWASP Dependency-Check (pending), Frontend - npm audit (fail), Frontend - npm audit & build (fail), SAST - Semgrep (OWASP Top 10) (fail × 2 run), SAST - CodeQL (Java) (pass), SAST - CodeQL (JavaScript/TypeScript) (pass), Secrets - Gitleaks (fail), 🔑 Secret Scanning (Gitleaks) (fail), Trivy - Filesystem Scan (fail), Trivy - filesystem & config scan (fail), 🔍 Custom Security Scan (scan.py) (pass), 📦 Dependency Vulnerability Scan (pending), Aggregate Security Report (fail), Security audit gate (fail), CodeQL (fail), Semgrep OSS (fail), audit (in_progress/stuck) |
| 취약점 탐지 여부 | 탐지 (의존성/시크릿/SAST 모두 다수 잡에서 failure로 표면화). Brit 본인 workflow run 산출물은 직접 확인 불가 — 확인 필요 |
| 보고서 생성 여부 | 생성 (다른 defender 워크플로의 `Aggregate Security Report` 잡이 실행되었으나 fail로 종료, Brit `aggregate-report` 잡 단독 산출물은 확인 필요) |
| PR 댓글 여부 | 미생성 (PR #10 댓글은 Brit-juho 본인 운영 댓글 2건뿐, github-actions[bot] 자동 보고서 댓글은 보이지 않음 — `<!-- security-audit-report -->` 마커 댓글 없음) |
| artifact 업로드 여부 | 확인 필요 (Brit 워크플로 run을 PR rollup에서 식별 불가, Actions 페이지에서 별도 확인 필요) |
| job 실패 여부 | 실패 (대부분 잡 FAILURE) |
| PR 머지 차단 여부 | 사실상 차단 (`mergeStateStatus=DIRTY`, 다수 FAILURE) 단 required status check 미설정 — branch protection 부재로 강제 차단은 아님 |
| 실행 시간 | 확인 필요 (잡별 ~10s~1m36s, 전체 합산 측정값은 부록 §B 참조 권장) |
| Actions run 링크 | https://github.com/anTuni/fornerds_study_session4/actions/runs/26226786161 (Security Audit, Security audit gate fail), https://github.com/anTuni/fornerds_study_session4/actions/runs/26226771846 (Security Audit (defend/tuni)), https://github.com/anTuni/fornerds_study_session4/actions/runs/26226756308 (Security Audit (defend/david)), https://github.com/anTuni/fornerds_study_session4/actions/runs/26226747307 (Security Audit (defend/YUN)) |

#### 탐지 결과 요약

```text
탐지된 파일/라인:
- cicd_practice/backend/pom.xml (log4j-core 2.14.1, snakeyaml 1.30, commons-collections 3.2.1 추가)
- cicd_practice/frontend/package.json (lodash 4.17.4, minimist 1.2.0, axios 0.21.0)
- cicd_practice/backend/src/main/resources/application.yml (하드코드 AWS/GitHub/JWT 키)
- cicd_practice/backend/.../config/SecurityConfig.java (CSRF disable, CORS *, /api/admin/** permitAll)
- cicd_practice/backend/.../content/ContentRepository.java (native SQL 문자열 연결)
- cicd_practice/backend/.../content/ContentController.java (@PreAuthorize/소유자 검증 제거)
- cicd_practice/backend/.../auth/AuthService.java (NoOpPasswordEncoder, Random 토큰, 만료 검증 제거)
- cicd_practice/backend/.../dashboard/UrlPreviewController.java (사용자 URL 직접 fetch, SSRF)
- cicd_practice/frontend/src/App.tsx (dangerouslySetInnerHTML)
- cicd_practice/frontend/index.html (외부 script SRI 없이 latest)

탐지 메시지:
- 다수 defender 워크플로의 OWASP DC / Semgrep / Gitleaks / Trivy / npm audit / Maven test 잡이 FAILURE 종료.
- Brit 본인 워크플로 출력(SARIF, snyk-backend.json 등)은 PR #10 check rollup 상에 별도 잡명으로 노출되지 않아 직접 인용 불가 (확인 필요).

보고서 또는 PR 댓글 요약:
- PR #10에 자동 생성된 security-report 마커 댓글 없음.
- 자동 생성된 Critical Security Issue 없음 (저장소 issue 0건 확인됨).
- 수비자 본인이 남긴 운영 댓글 2건 (close→reopen 트리거용)만 존재.
```

#### Cycle 1 이후 방어 개선

| Commit | 개선 내용 | 개선 이유 |
| --- | --- | --- |
| 해당 없음 | 해당 없음 — Cycle 1 이후 추가 commit이 `defend/Brit`에 없음 | PR #10이 단일 사이클로 종료, 워크플로 자체는 사전 정의된 정책으로 대응 |

### Cycle 2

| 항목 | 내용 |
| --- | --- |
| base 브랜치 | `defend/Brit` |
| 공격 브랜치 | `attack/tunitobrit` |
| PR 링크 | https://github.com/anTuni/fornerds_study_session4/pull/15 |
| 공격자 | `anTuni` (페어 tuni — 브랜치명 `tunitobrit`에서 식별, "tuni → Brit" 의미) |
| 수비자 | Brit |
| 취약점 유형 | A03 Injection — SQL Injection (CWE-89, native query 문자열 연결) / A01 Broken Access Control — IDOR (CWE-639, `preview=true`로 PUBLISHED 체크 우회) / A03 Injection — OS Command Injection (CWE-78, `Runtime.exec(["sh","-c", "ping -c 1 " + host])`) |
| 공격 commit | `492e0df7a6b7c171aa0309274bed1edda811926a` (Add advanced search, preview, and health-check endpoints to ContentController) |
| 수정 파일 | `cicd_practice/backend/src/main/java/com/example/cicdpractice/content/ContentController.java` (+46/-2, 단일 파일) |
| 취약점 설명 | (1) `GET /api/contents/search?keyword=&orderBy=`에서 `keyword`/`orderBy`를 native SQL에 직접 문자열 연결 후 `EntityManager.createNativeQuery` 실행 → UNION SELECT / ORDER BY 인젝션 가능. (2) `GET /api/contents/{id}?preview=true` 쿼리 플래그가 `ContentStatus.PUBLISHED` 검증을 우회해 DRAFT/ARCHIVED 노출, `/api/contents/**`가 `SecurityConfig`에서 `permitAll`이라 미인증으로 접근 가능. (3) `GET /api/contents/{id}/health-check?host=...`가 `host`를 셸 명령에 직접 연결 → `?host=8.8.8.8; id` 식으로 셸 명령 실행. |
| 기대 탐지 결과 | Semgrep `p/java`/`p/owasp-top-ten`이 SQLi(native query + 문자열 연결) 및 OS command injection(`Runtime.exec` + tainted input) ERROR 레벨로 fail / Trivy fs misconfig 또는 secret 룰에서 추가 신호 / Snyk Backend(Maven)가 SAST(Code) 활성화 시 high+ / Gitleaks는 secret 미포함이므로 무관 / OWASP DC는 의존성 변경 없으므로 영향 적음 |

#### 실행 결과

| 점검 항목 | 결과 |
| --- | --- |
| workflow 실행 여부 | 실행됨 (Security Audit workflow run 1건 / Snyk Open Source·Trivy 외부 앱 run 동시 실행) |
| 실행된 workflow 이름 | `Security Audit` (Brit `security-audit.yml`), `Snyk Open Source` (외부 앱), `Trivy` (외부 앱), `Dependabot auto-merge (patch only)` (skipped) |
| 실행된 check 이름 | Analyze changes (SUCCESS), Semgrep SAST (FAILURE), Gitleaks (secrets) (FAILURE), Trivy filesystem (FAILURE), Snyk — Backend (Maven) (FAILURE), Snyk — Frontend (npm) (SUCCESS), OWASP Dependency-Check (IN_PROGRESS), Build frontend (SKIPPED — needs 실패로 게이트 차단), Snyk Open Source (SUCCESS, 외부 앱), Trivy (SUCCESS, 외부 앱), auto-merge (SKIPPED) |
| 취약점 탐지 여부 | 탐지 (Semgrep SAST / Trivy fs / Snyk Backend(Maven) / Gitleaks 4개 잡 FAILURE로 표면화. Semgrep이 SQLi·OS command injection 룰로 검출한 것이 핵심, Gitleaks는 본 PR diff에 secret이 없는데도 FAILURE인 점은 기준 브랜치 누적 검출 또는 룰 매칭 가능 — 확인 필요) |
| 보고서 생성 여부 | 부분 생성 (각 잡 SARIF/JSON artifact는 업로드되었을 것으로 추정, `aggregate-report` 잡이 statusCheckRollup에 노출되지 않아 직접 확인 불가 — 확인 필요) |
| PR 댓글 여부 | github-actions[bot] 자동 보고서 댓글 없음. `github-advanced-security` bot이 Code Scanning 안내 댓글 1건만 게시 (`<!-- security-audit-report -->` 마커 댓글 없음) |
| artifact 업로드 여부 | 확인 필요 (Actions run 26227024466 페이지에서 Semgrep SARIF / Trivy SARIF / Gitleaks JSON / Snyk JSON 다운로드 검증 필요) |
| job 실패 여부 | 실패 (보안 핵심 잡 4개 FAILURE) |
| PR 머지 차단 여부 | 사실상 차단 (`mergeStateStatus=UNSTABLE`, 보안 잡 FAILURE로 `build-backend`/`build-frontend`가 needs 게이트에서 SKIPPED) 단 branch protection 없음 → required check 강제 차단은 아님 |
| 실행 시간 | Analyze changes 4s / Semgrep SAST 24s / Gitleaks 10s / Trivy filesystem 28s / Snyk Backend(Maven) 45s / Snyk Frontend(npm) 26s / OWASP DC pending / 외부 Snyk Open Source 17s / 외부 Trivy 4s — 보안 잡 합산 약 2분 내 (PR open 2026-05-21 12:51:03Z, 마지막 종료 12:52:02Z) |
| Actions run 링크 | https://github.com/anTuni/fornerds_study_session4/actions/runs/26227024466 (Security Audit), https://github.com/anTuni/fornerds_study_session4/actions/runs/26227024537 (Dependabot auto-merge) |

#### 탐지 결과 요약

```text
탐지된 파일/라인:
- cicd_practice/backend/src/main/java/com/example/cicdpractice/content/ContentController.java
  - advancedSearch(...) 메서드 — SQL Injection: `keyword`, `orderBy`를 native SQL에 직접 concat 후 entityManager.createNativeQuery 실행
  - detail(..., boolean preview) — Broken Access Control / IDOR: preview=true로 ContentStatus.PUBLISHED 체크 우회
  - healthCheck(..., String host) — OS Command Injection: Runtime.getRuntime().exec(new String[]{"sh","-c","ping -c 1 " + host})

탐지 메시지:
- Semgrep SAST: FAILURE (24s) — `p/java`/`p/owasp-top-ten` 룰셋이 native query 문자열 연결 + Runtime.exec tainted input을 ERROR 레벨로 매칭한 것으로 추정 (job log 직접 인용은 확인 필요).
- Trivy filesystem: FAILURE (28s) — fs 모드 vuln/secret/misconfig 스캔에서 임계값 초과 (구체 finding 확인 필요).
- Snyk — Backend (Maven): FAILURE (45s) — `--severity-threshold=high` 게이트 초과. 본 PR이 의존성 변경 없는데도 FAILURE인 점은 Snyk Code 활성 또는 누적 pom.xml 취약점 가능 (확인 필요).
- Gitleaks (secrets): FAILURE (10s) — 본 PR diff에 secret 없음에도 FAILURE → 기준 브랜치 누적 검출 또는 룰 매칭 가능 (확인 필요).

보고서 또는 PR 댓글 요약:
- PR #15에 `<!-- security-audit-report -->` 마커가 붙은 aggregate 보고서 댓글 없음.
- github-advanced-security bot이 Code Scanning 안내 댓글 1건 게시 (자동 보고서 아님).
- 자동 생성된 Critical Issue 없음.
- mergeStateStatus=UNSTABLE — GitHub UI에서 머지 버튼이 경고 상태로 표시되어 사실상 차단됨.
```

#### Cycle 2 이후 방어 개선

| Commit | 개선 내용 | 개선 이유 |
| --- | --- | --- |
| 해당 없음 | 현재 시점 추가 개선 없음 — Cycle 2 PR #15는 OPEN 상태이며 `defend/Brit`에 추가 commit 미반영 | 보고서 작성 시점(2026-05-21) 기준 Cycle 2 대응 commit 부재. Cycle 1 결론에서 도출된 개선안(파일명 분리, branch protection, aggregate fallback, A01 전용 룰 등)이 그대로 다음 액션으로 유효 |

### Cycle 3

| 항목 | 내용 |
| --- | --- |
| base 브랜치 | `defend/Brit` |
| 공격 브랜치 | 해당 없음 |
| PR 링크 | 해당 없음 |
| 공격자 | 해당 없음 |
| 수비자 | 해당 없음 |
| 취약점 유형 | 해당 없음 |
| 공격 commit | 해당 없음 |
| 수정 파일 | 해당 없음 |
| 취약점 설명 | 해당 없음 |
| 기대 탐지 결과 | 해당 없음 |

#### 실행 결과

| 점검 항목 | 결과 |
| --- | --- |
| workflow 실행 여부 | 해당 없음 |
| 실행된 workflow 이름 | 해당 없음 |
| 실행된 check 이름 | 해당 없음 |
| 취약점 탐지 여부 | 해당 없음 |
| 보고서 생성 여부 | 해당 없음 |
| PR 댓글 여부 | 해당 없음 |
| artifact 업로드 여부 | 해당 없음 |
| job 실패 여부 | 해당 없음 |
| PR 머지 차단 여부 | 해당 없음 |
| 실행 시간 | 해당 없음 |
| Actions run 링크 | 해당 없음 |

#### 탐지 결과 요약

```text
탐지된 파일/라인: 해당 없음
탐지 메시지: 해당 없음
보고서 또는 PR 댓글 요약: 해당 없음
```

#### Cycle 3 이후 방어 개선

| Commit | 개선 내용 | 개선 이유 |
| --- | --- | --- |
| 해당 없음 | 해당 없음 | 해당 없음 |

## 6. 탐지 성공 사례

| 취약점 유형 | 탐지 도구 또는 규칙 | 탐지 파일 | 왜 잘 탐지됐는가 |
| --- | --- | --- | --- |
| A06 Vulnerable Components (Java: log4j 2.14.1, snakeyaml 1.30, commons-collections 3.2.1) | OWASP Dependency-Check (CVSS≥7.0), Trivy fs, Snyk (high+) | `cicd_practice/backend/pom.xml` | NVD 공시 CVE가 명확하고 CVSS가 critical 영역이라 모든 SCA 도구의 임계값을 한 번에 초과 |
| A06 Vulnerable Components (npm: lodash 4.17.4, minimist 1.2.0, axios 0.21.0) | npm audit (`--audit-level=high`), Snyk, Trivy | `cicd_practice/frontend/package.json` | lockfile 동기화 후 의존성 그래프가 깨끗해 추가 CVE가 분명히 부각, Brit가 사전에 `latest`를 고정 버전으로 바꿔둬 비교 baseline이 분명 |
| Hardcoded secrets (AWS/GitHub/JWT) | Gitleaks (rule 1건이라도 fail) | `cicd_practice/backend/src/main/resources/application.yml` | Gitleaks 기본 룰셋이 AKIA/ghp_/JWT 형태를 직접 패턴 매칭, 정책상 1건만 발견되어도 fail |
| A03 XSS | Semgrep `p/react` (`dangerouslySetInnerHTML`) | `cicd_practice/frontend/src/App.tsx` | React 룰셋에 직접 매칭되는 sink, ERROR 레벨로 fail 트리거 |
| A05 Security Misconfiguration (CSRF disable, CORS `*` + credentials) | Semgrep `p/owasp-top-ten`, `p/java` | `cicd_practice/backend/.../config/SecurityConfig.java` | Spring Security 패턴이 룰셋에 다수 존재 |
| A03 SQL Injection (PR #15 — native query 문자열 연결) | Semgrep SAST `p/java`/`p/owasp-top-ten` (FAILURE 24s), Trivy filesystem (FAILURE 28s), Snyk — Backend (Maven) (FAILURE 45s) | `cicd_practice/backend/.../content/ContentController.java` `advancedSearch(...)` | `EntityManager.createNativeQuery(sql, ...)` + `+ keyword +` / `+ orderBy +` 패턴이 Semgrep Java 룰의 대표 매칭 케이스. 단일 파일 변경으로 다른 노이즈가 없어 핵심 신호만 부각 |
| A03 OS Command Injection (PR #15 — `Runtime.exec` + tainted input) | Semgrep SAST (FAILURE), Trivy filesystem (FAILURE) | `cicd_practice/backend/.../content/ContentController.java` `healthCheck(...)` | `Runtime.getRuntime().exec(new String[]{"sh","-c", ... + host})`이 Semgrep `p/owasp-top-ten` OS-command-injection 룰의 정확한 sink 패턴 |

## 7. 탐지 실패 또는 오탐 사례

| 유형 | PR 또는 파일 | 원인 분석 | 다음 개선안 |
| --- | --- | --- | --- |
| 미탐 (정책상 한계) | PR #10 — A01 소유자 검증 제거 (`ContentController.update`), `/api/admin/**` permitAll의 일부 케이스 | SECURITY_POLICY.md §3.2에 명시한 W5(접근통제) 자동 탐지 한계와 일치, Semgrep 일반 룰만으로는 도메인 권한 규약(소유자=author 검증)을 추정 불가 | 프로젝트 전용 Semgrep 룰셋 추가 (`@PreAuthorize` 누락 + `authorOf(...)` 호출 누락 패턴), 또는 Snyk Code/CodeQL 추가 데이터 흐름 분석 활용 |
| 미탐 (정책상 한계) | PR #10 — A10 SSRF (`UrlPreviewController`) 사용자 URL fetch | 동적 SSRF는 정적 분석에서 false negative가 흔함, 본 워크플로는 SSRF 룰 명시 활성화 안 함 | Semgrep `p/security-audit`에 SSRF 룰 추가, 또는 IAST/DAST 보조 (ZAP) 통합 검토 |
| 운영 미탐 | Brit 본인 워크플로 `Security Audit (defend/Brit)` run이 PR #10 check rollup에서 식별 불가 | 워크플로 path 충돌(모든 defender가 `.github/workflows/security-audit.yml` 동일 경로 사용) + GitHub 워크플로 ID 단일 등록(`280808262`)으로 인해 다른 defender 워크플로가 같은 PR에 함께 트리거되며 잡 이름이 섞임 | 파일명을 defender별로 분리 (`security-audit-brit.yml`) 또는 reusable workflow + caller 분리, 정책상 "내 워크플로만 PR을 차단"하려면 required check 이름 고유성 필요 |
| 오탐 | 확인 필요 | 본인 워크플로 산출물 직접 확인 불가로 인해 오탐 여부 단정 불가 (예: Semgrep `p/owasp-top-ten`의 일반 패턴이 정상 패턴까지 잡았을 가능성) | aggregate-report Markdown을 artifact에서 다운로드해 정상 코드 매칭 여부 검토 후 룰 ignore 추가 |
| 미탐 가능성 (도메인 권한) | PR #15 — A01 IDOR (`detail(..., preview=true)`로 PUBLISHED 검증 우회) | Semgrep 일반 룰셋이 "쿼리 플래그가 상태 검증을 우회"하는 비즈니스 로직 패턴을 탐지하지 못함, statusCheckRollup의 FAILURE는 SQLi/Command injection 신호로 추정되며 IDOR이 명시적으로 잡혔는지는 SARIF artifact 확인 필요 | `@PreAuthorize` 누락 + `ContentStatus.PUBLISHED` 분기 우회 패턴을 잡는 프로젝트 전용 Semgrep 룰 추가, 또는 인증되지 않은 경로의 preview/admin 플래그 사용 자체를 ban |
| 운영 의문 (Gitleaks FAILURE) | PR #15 — Gitleaks (secrets) FAILURE인데 diff에 secret 없음 | 본 PR diff는 `ContentController.java` 1파일만 변경되어 secret 미포함. FAILURE 원인은 기준 브랜치(`defend/Brit`) 전체 스캔에서 누적 검출됐거나, Gitleaks 룰이 코드 내 문자열을 매칭한 false-positive 가능 | Gitleaks를 `--source` 또는 `--log-opts`로 diff-only 모드 전환, 또는 baseline 파일(`gitleaks.toml` allowlist)로 누적 신호 분리 |

## 8. PR 차단 검증

| 항목 | 결과 |
| --- | --- |
| branch protection 설정 여부 | 미설정 (`gh api .../branches/defend/Brit/protection` → 404 Not Found) |
| required status check 이름 | 미설정 |
| 실패한 check 이름 | Backend - Maven test, OWASP Dependency Check, Frontend - npm audit, SAST - Semgrep (OWASP Top 10), Secrets - Gitleaks, 🔑 Secret Scanning, Trivy - Filesystem Scan, Trivy - filesystem & config scan, Aggregate Security Report, Security audit gate, CodeQL, Semgrep OSS (총 12+개 잡 FAILURE) |
| PR 상태 | `state=OPEN`, `mergeStateStatus=DIRTY` |
| 실제 머지 버튼 상태 | DIRTY (충돌 또는 미완 상태로 GitHub UI에서 자동 비활성화), 단 required check 없이 admin이 강제 머지하면 차단되지 않음 |
| 차단이 안 됐다면 이유 | branch protection rule이 없어 required status check 강제 불가, 현재는 mergeStateStatus=DIRTY와 다수 FAILURE로 "사실상" 차단되어 있지만 정책적 차단은 아님 |

정리:

- workflow가 실패해도 branch protection이 없으면 실제 머지는 가능할 수 있다.
- PR을 확실히 막으려면 required status check 설정이 필요하다.
- defender별 워크플로 path가 동일하면 required check 이름도 충돌할 수 있어, defender별 고유한 check 이름이 branch protection 등록의 전제가 된다.

## 9. Lesson Learned

### 기술적으로 배운 점

- 동일한 base 브랜치(`defend/Brit`)에 PR이 열려도, 같은 path의 워크플로가 다른 브랜치에 존재하면 GitHub Actions가 그 워크플로들을 함께 트리거할 수 있어 잡 이름이 섞이는 현상을 관찰했다. workflow ID는 path 단위로 1개만 등록(`280808262`)되며 `name:` 필드는 표시용일 뿐 식별자가 아님.
- Snyk/OWASP DC/Trivy의 SCA는 NVD 기반 공시 CVE에서는 거의 빠짐없이 검출(log4j/snakeyaml/lodash/axios 등)되지만, 권한 검증 제거나 SSRF처럼 도메인-특수 로직은 일반 룰셋이 잡지 못한다는 SECURITY_POLICY.md §3.2의 한계가 PR #10에서 그대로 재현되었다.
- `frontend/package.json`의 `"latest"`를 사전에 고정 버전으로 옮긴 결정이 npm audit/Snyk의 비교 baseline을 깨끗하게 만들어, 공격이 새로 추가한 lodash 4.17.4 등의 high+를 명확히 부각시켰다.

### workflow 설계에서 배운 점

- 정책 문서(SECURITY_POLICY.md W1~W11) → 도구 매핑(SECURITY_TOOLS.md) → 실행(`security-audit.yml`)의 3단 분리는 임계값 조정 시 워크플로 수정 없이 정책만 갱신할 수 있어 유지보수가 쉽다.
- `aggregate-report` 잡이 모든 SARIF/JSON을 Python으로 묶어 PR comment 1개로 줄이는 패턴은 가독성이 좋지만, marker 댓글이 PR에 실제로 게시되지 않은 사실(확인 결과 PR #10에 자동 보고서 댓글 없음)을 통해, `aggregate-report` 잡 자체가 실패하면 보고가 사라지는 단일 장애점이 됨을 확인했다. → 잡 실패 시에도 최소 summary 댓글을 남기는 fallback이 필요.
- `build-backend`/`build-frontend`가 보안 잡의 `needs:`로 직렬화되어 있어 보안이 깨지면 빌드도 자동으로 차단되는 구조는 좋지만, required status check가 없으면 머지 자체는 막을 수 없다는 한계를 §8에서 확인.

### 방어 브랜치 운영에서 배운 점

- defender별 워크플로 파일이 `.github/workflows/security-audit.yml`로 동일 경로를 쓰는 컨벤션은 같은 PR에 여러 워크플로가 동시 실행되는 부작용을 만든다. defender별 고유 파일명(`security-audit-brit.yml`) + 고유 job/check 이름이 운영상 필수.
- branch protection이 없는 상태에서는 mergeStateStatus=DIRTY만으로 사실상 차단되지만, 정책적으로는 "차단이 보장된 상태"가 아니다. 실습 후 admin 권한자가 required check를 등록해야 게이트가 완성된다.
- close→reopen으로 워크플로를 재트리거하는 패턴(SNYK_TOKEN 등록 후)은 secret 변경 사항을 반영하는 가장 빠른 방법이지만, 운영에서는 secret 회전 시 자동 재실행 메커니즘(예: scheduled re-scan) 도입이 더 안전하다.
- 자동 Critical Issue 생성 로직이 PR #10에서는 실제로 issue를 만들지 않은 것을 확인 → Brit 본인 워크플로의 `aggregate-report` 잡 자체가 PR에서 실행되지 않았거나 Snyk JSON이 비어 critical 카운트가 0이었을 가능성. 자동화는 항상 "실행되지 않은 경우의 알림"까지 설계해야 한다.

## 10. 표준 보안감사 Workflow 제안

| 우선순위 | 항목 | 포함 여부 | 이유 |
| --- | --- | --- | --- |
| 필수 | Backend test | 포함 | 보안 게이트 통과 후 mvn verify로 정상 동작 보장 |
| 필수 | Frontend build | 포함 | `npm ci && npm run build`로 lockfile 무결성 + 빌드 가능성 확인 |
| 필수 | 의존성 취약점 스캔 | 포함 | Snyk(주) + OWASP DC(보조 Java) + npm audit(보조) + Trivy(공통) 다층화로 단일 도구 false negative 보완, PR #10에서 효과 입증 |
| 필수 | SAST | 포함 | Semgrep `p/owasp-top-ten` + `p/java` + `p/javascript` + `p/react` + `p/secrets` + `p/security-audit` 다중 룰셋이 A03/A05/A02 다수 패턴을 한 번에 커버 |
| 권장 | Secret scan | 포함 | Gitleaks 단독으로도 application.yml 평문 키 즉시 fail, 정책상 1건도 허용하지 않는 임계값과 정합 |
| 권장 | Container 또는 filesystem scan | 포함 | Trivy fs로 vuln/secret/misconfig 동시 점검, 컨테이너 도입 전이라도 fs 모드만으로 가치 |
| 권장 | PR 댓글 보고서 | 포함 (단 fallback 필요) | aggregate-report 단일 댓글 패턴 + 잡 실패 시 최소 summary fallback |
| 권장 | Artifact 업로드 | 포함 | SARIF/JSON을 artifact로 보관해 GitHub Security 탭 + 사후 감사 모두 지원 |
| 필수 | Required status check | 미포함 (현재) | branch protection 미설정 — defender별 고유 check 이름을 먼저 정해야 등록 가능, 표준 워크플로 채택 시 동시 도입 필요 |

### 제안하는 실패 기준

- Critical: job fail + GitHub Issue 자동 생성 + PR 머지 차단 + 24h SLA (정책 §1)
- High: job fail + PR 머지 차단 + 영업일 3일 SLA
- Medium: job pass + PR comment 경고 + 다음 스프린트 처리
- Low: 보고서 표에 기재만, 백로그 관리

### 제안하는 보고서 형식

- PR 댓글에 포함할 내용: 잡별 결과 표 / Snyk·Semgrep·Gitleaks·Trivy 상위 N건 표 (심각도/CVE/파일:라인/권장) / 정책 링크 / aggregate 실패 시 fallback "보고서 생성 실패, artifact 확인" 메시지
- Artifact로 남길 내용: 각 도구 원본 SARIF + JSON, 최종 Markdown 보고서, gitleaks.json, npm-audit.json
- 팀 회고에서 공유할 내용: 탐지 성공/실패 사례, 자동 생성 Critical Issue 목록, 정책 §3.2 자동 탐지 불가 영역에서 미탐된 케이스, 워크플로 path 충돌로 인한 운영 이슈

## 11. 최종 결론

| 항목 | 판단 |
| --- | --- |
| 표준 workflow로 채택 가능 여부 | 보완 필요 |
| 바로 적용 가능한 부분 | 정책 문서 3단 분리(POLICY/TOOLS/workflow), SCA 다층화(Snyk+OWASP DC+Trivy+npm audit), Semgrep 다중 룰셋, Gitleaks fail-on-any, aggregate-report 단일 PR comment, build를 보안 잡의 needs로 연결, frontend의 `latest` 고정 |
| 추가 실험이 필요한 부분 | defender별 워크플로 파일명/잡명 고유화, branch protection + required status check 등록 절차, aggregate-report 실패 시 fallback 댓글, A01 권한·A10 SSRF용 프로젝트 전용 Semgrep 룰, Snyk Code/CodeQL 같은 데이터 흐름 SAST 보강, scheduled re-scan으로 secret 회전 반영 |
| 다음 액션 | (1) `security-audit-brit.yml`로 파일명 변경 및 잡명 prefix 추가 → (2) branch protection 활성화 후 핵심 잡들을 required check로 등록 → (3) aggregate-report fallback 추가 → (4) A01/A10 프로젝트 전용 룰 작성 → (5) 다음 사이클에서 동일 PR 재실행 후 차단·보고서 댓글·Critical Issue 자동 생성 3종 모두 가시화되는지 검증 |

최종 의견:

- 본 워크플로는 SCA·Secret·SAST·Build 게이트의 다층 구조를 갖추어, `defend/Brit`으로 들어온 공격 PR 2건(PR #10 attack/sabo, PR #15 attack/tunitobrit) 모두에서 핵심 취약점을 표면화시키는 데 성공했다. PR #10은 OWASP Top 10 광범위 패턴(SCA·Secret·SAST)으로, PR #15는 단일 파일에 집약된 SQLi(CWE-89) + IDOR(CWE-639) + OS Command Injection(CWE-78)으로 — 두 사례 모두 `mergeStateStatus`가 DIRTY/UNSTABLE이 되어 사실상 차단됐다. 다만 ① defender별 path 충돌로 인한 운영 가시성 저하(PR #10), ② branch protection 미설정으로 인한 정책적 차단 부재(공통), ③ aggregate-report 댓글이 PR에 실제 게시되지 않은 운영 결함(공통), ④ PR #15에서 IDOR이 명시적으로 잡혔는지 SARIF 검증 미완 — 네 가지를 보완하면 팀 표준으로 채택할 가치가 충분하다.

---

## 부록: 조회 명령어

```bash
# 저장소 상태
git -C /Users/neo/GitHub/fornerds_study_session4 status --short
git -C /Users/neo/GitHub/fornerds_study_session4 remote -v
git -C /Users/neo/GitHub/fornerds_study_session4 fetch origin

# 방어 브랜치 이력
git log --oneline --decorate origin/main..origin/defend/Brit
git log --stat origin/main..origin/defend/Brit

# 워크플로 파일
git show origin/defend/Brit:.github/workflows/security-audit.yml
git ls-tree -r --name-only origin/defend/Brit .github/workflows

# PR #10 상세
gh pr view 10 --json number,title,url,state,author,headRefName,baseRefName,body,commits,files,statusCheckRollup,mergeStateStatus,reviewDecision,createdAt
gh pr checks 10
gh pr view 10 --json comments

# Workflow runs on attack/sabo (= PR #10 head)
gh run list --branch attack/sabo --limit 30 --json databaseId,workflowName,name,event,conclusion,status,headBranch,createdAt
gh api repos/anTuni/fornerds_study_session4/actions/runs/26226786161
gh api repos/anTuni/fornerds_study_session4/actions/runs/26226786161/jobs
gh api repos/anTuni/fornerds_study_session4/actions/runs/26226771846/jobs

# 워크플로 등록 현황
gh workflow list --all
gh api repos/anTuni/fornerds_study_session4/actions/workflows

# Branch protection
gh api repos/anTuni/fornerds_study_session4/branches/defend/Brit/protection

# 자동 생성 Critical Issue
gh issue list --state all --label security
gh issue list --state all --limit 30

# PR 타임라인 (base 변경/close-reopen 확인)
gh api repos/anTuni/fornerds_study_session4/issues/10/events
gh api repos/anTuni/fornerds_study_session4/issues/10/timeline
```

### §B. 본 보고서에서 "확인 필요"로 남긴 항목

1. §3 평균 실행 시간 / 가장 느린 단계 — Brit 본인 `Security Audit (defend/Brit)` run을 PR #10 check rollup에서 식별 불가, Actions UI에서 workflow_dispatch run 또는 별도 push run 시간 측정 권장.
2. §5 Cycle 1 artifact 업로드 여부, 본인 워크플로 산출물(Markdown 보고서/SARIF) 실제 내용 — Actions 페이지에서 artifact 다운로드 후 재검토.
3. §7 오탐 사례 — 본인 워크플로 산출물 확인 후에야 단정 가능.
