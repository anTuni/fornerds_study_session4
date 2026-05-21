# 보안감사 실습 결과 정리 — defend/david

> 이 문서는 `defend/david` 한 브랜치를 기준으로 작성합니다.

## 1. 방어 브랜치 기본 정보

| 항목 | 내용 |
| --- | --- |
| 작성 기준 브랜치 | `defend/david` |
| 수비자 | handevmin (David) |
| 페어 | 확인 필요 (실습 중 attack PR을 받은 상대: anTuni/tuni, player397/sabo) |
| 작성일 | 2026-05-21 |
| 실습 저장소 | https://github.com/anTuni/fornerds_study_session4 |
| 결과 문서 작성자 | handevmin |
| 관련 최종 PR 또는 공유 링크 | https://github.com/anTuni/fornerds_study_session4/tree/defend/david |

## 2. 방어 브랜치 이력 요약

`defend/david` 브랜치에서 보안감사 workflow를 추가하거나 개선한 commit 정리.

| 순서 | Commit | 작성자 | 메시지 | 주요 변경 내용 |
| --- | --- | --- | --- | --- |
| 1 | `4329ac7` | handevmin | Add security audit workflow for defend/david PRs | `.github/workflows/security-audit.yml` 신규. Maven test, OWASP Dependency-Check (CVSS≥9 실패), npm audit (critical 실패), Semgrep (OWASP Top 10 + framework + secrets), Gitleaks, Trivy fs+config, sticky PR comment summary 구성 |
| 2 | `8cfa2cf` | handevmin | Harden security audit workflow | CodeQL Java + JS/TS analyze (security-and-quality 쿼리) 추가, npm audit 정책 HIGH로 강화, Trivy config CRITICAL 실패로 변경, NVD_API_KEY secret 패스쓰루, PR summary 표에 CodeQL 결과 추가 |
| 3 | 해당 없음 | — | — | 공격 PR 두 건 모두 현재 workflow에서 차단됨. 추가 개선 commit 없이 라운드 종료 |

## 3. 방어자가 만든 보안감사 Workflow 요약

| 항목 | 내용 |
| --- | --- |
| workflow 파일 경로 | `.github/workflows/security-audit.yml` |
| workflow 이름 | Security Audit (defend/david) |
| 실행 트리거 | `pull_request` to `defend/david` |
| 대상 방어 브랜치 | `defend/david` |
| 사용한 도구 | Maven test, OWASP Dependency-Check (Maven plugin 10.0.4), npm ci + npm audit, Semgrep (p/owasp-top-ten, p/security-audit, p/java, p/javascript, p/typescript, p/react, p/secrets), CodeQL (java-kotlin, javascript-typescript, security-and-quality), Gitleaks (gitleaks-action v2), Trivy (filesystem + config, action 0.24.0) |
| 보고서 생성 방식 | `actions/upload-artifact@v4` (4종: backend-dependency-check, frontend-npm-audit, semgrep-report, trivy-reports) + Semgrep/CodeQL SARIF는 GitHub code scanning에 업로드 + `marocchino/sticky-pull-request-comment@v2`로 PR 상단에 결과 표 코멘트 |
| 실패 기준 | CRITICAL = 실패. npm은 HIGH도 실패. Trivy fs/config는 CRITICAL 실패, HIGH는 리포트 전용. Dependency-Check는 CVSS ≥ 9.0 실패 |
| PR 차단 방식 | 현재 branch protection 미설정. workflow 실패 시 mergeStateStatus가 UNSTABLE이지만 BLOCKED는 아님 → required status check 추가 필요 |
| required status check 이름 | 미설정 (확인 필요) |
| 평균 실행 시간 | PR #12 기준 약 90초 이내 (가장 긴 단계 마감 12:47:14 vs 시작 12:45:28) |
| 가장 느린 단계 | SAST - CodeQL (Java) (~96초, mvn compile 포함) |

### Workflow 핵심 설정

```yaml
on:
  pull_request:
    branches:
      - defend/david

permissions:
  contents: read
  pull-requests: write
  security-events: write

concurrency:
  group: security-audit-${{ github.ref }}
  cancel-in-progress: true
```

### Workflow 설계 의도

- **계층화된 탐지**: 같은 OWASP 카테고리를 SAST(Semgrep + CodeQL), 의존성(Dependency-Check + npm audit), 시크릿(Gitleaks), 미설정(Trivy config) 4개 축으로 중첩 검사 → 한 도구가 놓쳐도 다른 도구가 잡도록 설계.
- **심각도 정책의 합리화**: CRITICAL은 빌드 실패, HIGH/MEDIUM은 artifact로 남겨 사람이 검토. npm은 의존성 fix 가능 비율이 높아 HIGH도 실패로 강화.
- **사용자 친화 보고**: SARIF는 코드 스캐닝 탭에 기록, 표 코멘트는 PR에 sticky로 붙어 한눈에 결과를 본다. artifact는 30일 보관(action 기본).

## 4. 방어 브랜치로 들어온 공격 PR 목록

| PR | 공격 브랜치 | 공격자 | 상태 | 취약점 유형 | 최종 check 결과 | 머지 차단 여부 |
| --- | --- | --- | --- | --- | --- | --- |
| #9 | `attack/tunitodavid` | anTuni (tuni) | Open | A03 Injection (SQLi), A10 SSRF, A02 Crypto (MD5 + 하드코드 시크릿), A05 Misconfig (CSRF disable, CORS *+credentials), A06 Vuln deps (Java: commons-collections 3.2.1, log4j 1.2.17 / npm: lodash 4.17.4, minimist 1.2.0, node-fetch 2.6.0, marked 0.3.6), A08 SRI 없음 | Fail (Frontend npm audit, Semgrep, Trivy, CodeQL alerts, Semgrep OSS alerts 실패) | UNSTABLE (branch protection 없어 BLOCKED 아님) |
| #12 | `attack/sabo` | player397 (sabo) | Open | A01, A02, A03 (SQLi + XSS), A05, A06 (Java + npm), A07, A08, A09, A10, Hardcoded secrets — OWASP Top 10 묶음 | Fail (Maven test, Gitleaks, Semgrep, Trivy, Dependency-Check, npm audit, Aggregate report 실패) | UNSTABLE (branch protection 없어 BLOCKED 아님) |
| — | — | — | — | — | — | — |

## 5. 공격/수비 사이클 기록

### Cycle 1

| 항목 | 내용 |
| --- | --- |
| base 브랜치 | `defend/david` |
| 공격 브랜치 | `attack/tunitodavid` |
| PR 링크 | https://github.com/anTuni/fornerds_study_session4/pull/9 |
| 공격자 | anTuni (tuni) |
| 수비자 | handevmin (David) |
| 취약점 유형 | A03 Injection (SQLi), A10 SSRF, A02 Cryptographic Failures (MD5 + 하드코드 placeholder 시크릿), A05 Security Misconfiguration, A06 Vulnerable Components (Maven + npm), A08 Software/Data Integrity (SRI 없음) |
| 공격 commit | 확인 필요 (PR diff 기준 9개 파일 변경) |
| 수정 파일 | pom.xml, AdminUtilController.java, SecurityConfig.java, ContentController.java, ContentSearchService.java, index.html, package-lock.json, package.json, api.ts |
| 취약점 설명 | (1) ContentSearchService/Controller에 native query 문자열 연결. (2) AdminUtilController에 URL 미리보기 SSRF + MD5 fingerprint + 하드코드 placeholder 시크릿. (3) SecurityConfig CSRF disable + CORS wildcard with credentials + frameOptions disable. (4) pom.xml에 알려진 RCE 취약 commons-collections 3.2.1, log4j 1.2.17. (5) package.json에 lodash/minimist/node-fetch/marked 오래된 버전. (6) index.html jQuery/Bootstrap CDN을 SRI 없이 latest로 로드 |
| 기대 탐지 결과 | Dependency-Check가 commons-collections / log4j 검출, npm audit critical 검출, Semgrep이 SQLi/SSRF/MD5/CSRF/CORS 패턴 검출, Trivy가 vuln deps + misconfig 검출, Gitleaks가 시크릿 패턴 검출 |

#### 실행 결과

| 점검 항목 | 결과 |
| --- | --- |
| workflow 실행 여부 | 성공 |
| 실행된 workflow 이름 | Security Audit (defend/david) |
| 실행된 check 이름 | Backend - Maven test / Backend - OWASP Dependency-Check / Frontend - npm audit & build / SAST - Semgrep (OWASP Top 10) / SAST - CodeQL (Java) / SAST - CodeQL (JavaScript/TypeScript) / Secrets - Gitleaks / Trivy - filesystem & config scan / PR summary comment |
| 취약점 탐지 여부 | 부분 탐지 → 빌드 차단 성공. A03/A05/A06/A08은 도구가 잡음. A02 placeholder 시크릿은 Gitleaks 통과(SUCCESS) — 실제 형식 secret이 아닌 식별자라 패턴 미일치 |
| 보고서 생성 여부 | 생성 (artifact + SARIF code scanning) |
| PR 댓글 여부 | 확인 필요 (sticky comment job 결과 미확인) |
| artifact 업로드 여부 | 생성 (backend-dependency-check, frontend-npm-audit, semgrep-report, trivy-reports) |
| job 실패 여부 | 실패 (Frontend npm audit, Semgrep, Trivy, 코드 스캐닝 CodeQL + Semgrep OSS alerts 5개 실패) |
| PR 머지 차단 여부 | 부분 차단 — mergeStateStatus UNSTABLE. branch protection 미설정으로 BLOCKED는 아님 |
| 실행 시간 | 확인 필요 (전체 워크플로 ~90초 추정) |
| Actions run 링크 | https://github.com/anTuni/fornerds_study_session4/pull/9/checks |

#### 탐지 결과 요약

```text
탐지된 파일/라인:
- Frontend - npm audit & build: package.json의 lodash/minimist/node-fetch/marked critical/high CVE
- SAST - Semgrep: SecurityConfig CSRF disable, CORS misconfig, native SQL 문자열 연결, MD5 fingerprint, AdminUtilController SSRF, dangerouslySetInnerHTML 패턴
- Trivy: vuln deps + IaC misconfig
- 코드 스캐닝 (CodeQL + Semgrep OSS): alerts 발생 → PR 차단 트리거

탐지 메시지:
- Dependency-Check: commons-collections 3.2.1 CVE-2015-7501, log4j 1.2.17 CVE-2019-17571 등 다수 CVE (확인 필요 — Dependency-Check job 결과가 statusCheckRollup에 명시적 FAILURE/SUCCESS로 잡히지 않음)
- npm audit: critical/high 발견하여 --audit-level=high 정책으로 실패

보고서 또는 PR 댓글 요약:
- PR 본문에 공격자 anTuni가 카테고리별 자가 진단 표를 제공.
- sticky PR comment 결과는 확인 필요.
- 코드 스캐닝 탭에 CodeQL/Semgrep alert가 직접 표시됨.
```

#### Cycle 1 이후 방어 개선

| Commit | 개선 내용 | 개선 이유 |
| --- | --- | --- |
| (없음) | 현 라운드에서 추가 보강 commit 없음 | 두 PR 모두 머지 차단 + 탐지 성공으로 즉시 보강이 불필요. 단, Gitleaks가 placeholder 시크릿을 못 잡은 점은 다음 라운드 개선 후보 (custom rules 또는 단순 키워드 base detect-secrets 도입 검토). |

### Cycle 2

| 항목 | 내용 |
| --- | --- |
| base 브랜치 | `defend/david` |
| 공격 브랜치 | `attack/sabo` |
| PR 링크 | https://github.com/anTuni/fornerds_study_session4/pull/12 |
| 공격자 | player397 (sabo) |
| 수비자 | handevmin (David) |
| 취약점 유형 | A01 Broken Access Control, A02 Cryptographic Failures (NoOpPasswordEncoder, java.util.Random, 하드코드 JWT key), A03 Injection (SQLi + XSS dangerouslySetInnerHTML), A05 Security Misconfiguration (CSRF disable, CORS *+credentials), A06 Vulnerable Components (Java: log4j-core 2.14.1 Log4Shell, snakeyaml 1.30, commons-collections 3.2.1 / npm: lodash 4.17.4, minimist 1.2.0, axios 0.21.0), A07 Authentication Failures (토큰 만료 검증 제거), A08 Software/Data Integrity Failures (외부 스크립트 SRI 없이 latest 로드), A09 Logging Failures (raw 토큰 + 서명키 로그), A10 SSRF (UrlPreviewController), Hardcoded secrets (application.yml AWS/GitHub PAT/JWT) |
| 공격 commit | `d949b07` Add intentionally vulnerable changes for attack/sabo (player397 + Claude co-author) |
| 수정 파일 | pom.xml, AuthService.java, SecurityConfig.java, ContentController.java, ContentRepository.java, UrlPreviewController.java, application.yml, frontend/index.html, package.json, src/App.tsx (+ RESULT_FORM/PROMPT 동기화) |
| 취약점 설명 | OWASP Top 10 12개 카테고리 한 PR에 묶음. 실험 목적이며 "머지 금지" 명시. workflow가 어디까지 잡는지 보는 테스트 베드 |
| 기대 탐지 결과 | Dependency-Check Log4Shell, npm audit critical, Semgrep 다수 룰 hit, Gitleaks가 application.yml의 ghp_ 패턴 GitHub PAT을 즉시 검출, Trivy fs+config 실패 |

#### 실행 결과

| 점검 항목 | 결과 |
| --- | --- |
| workflow 실행 여부 | 성공 |
| 실행된 workflow 이름 | Security Audit (defend/david) |
| 실행된 check 이름 | Backend - Maven test / Backend - OWASP Dependency-Check / Frontend - npm audit & build / SAST - Semgrep (OWASP Top 10) / SAST - CodeQL (Java) / SAST - CodeQL (JavaScript/TypeScript) / Secrets - Gitleaks / Trivy - filesystem & config scan |
| 취약점 탐지 여부 | 광범위 탐지. 거의 모든 카테고리에서 1개 이상 도구가 hit |
| 보고서 생성 여부 | 생성 (artifact + SARIF code scanning) |
| PR 댓글 여부 | gitleaks-action의 line-level review 1건 (`ghp_...` PAT 지목). sticky PR comment는 확인 필요 |
| artifact 업로드 여부 | 생성 |
| job 실패 여부 | 실패 (Maven test, npm audit & build, Semgrep, Trivy fs+config, Gitleaks, Dependency-Check, 코드 스캐닝 CodeQL/Semgrep OSS 다수 실패) |
| PR 머지 차단 여부 | 부분 차단 — mergeStateStatus UNSTABLE. branch protection 미설정으로 BLOCKED는 아님 |
| 실행 시간 | ~90초 (12:45:28 ~ 12:47:14) |
| Actions run 링크 | https://github.com/anTuni/fornerds_study_session4/pull/12/checks |

#### 탐지 결과 요약

```text
탐지된 파일/라인:
- Gitleaks: cicd_practice/backend/src/main/resources/application.yml의 GitHub PAT (rule-id github-pat) — commit d949b07.
- 코드 스캐닝 CodeQL: 4 new alerts (1 critical). SQLi, SSRF, weak random 등 추정.
- 코드 스캐닝 Semgrep OSS: 2 new alerts (2 errors).
- Trivy fs+config / Dependency-Check / npm audit: CRITICAL/HIGH severity vuln deps 검출하여 실패.
- Maven test 실패: 공격 commit이 의존성/암호화 코드를 깨뜨려 컴파일/테스트 단계에서 즉시 실패 추정 (확인 필요).

탐지 메시지:
- gitleaks-action 자동 리뷰 메시지: "🛑 Gitleaks has detected a secret with rule-id github-pat in commit d949b07."

보고서 또는 PR 댓글 요약:
- 공격자 player397이 PR 본문에서 자가진단 표 + "머지 금지" 명시.
- gitleaks-action이 secret 위치를 line-level review로 인용.
- CodeQL/Semgrep alerts는 코드 스캐닝 탭에 직접 표시됨.
- sticky summary 코멘트 (`marocchino/sticky-pull-request-comment`)는 추가 확인 필요.
```

#### Cycle 2 이후 방어 개선

| Commit | 개선 내용 | 개선 이유 |
| --- | --- | --- |
| (없음) | 현 라운드에서 추가 보강 commit 없음 | 모든 카테고리에서 최소 1개 도구가 탐지에 성공해 즉시 보강 불필요. 보강 후보: required status check 설정으로 머지 BLOCKED 보장, Gitleaks custom rules로 placeholder 시크릿 탐지 강화, custom Semgrep rule로 A07 토큰 만료 검증 패턴 탐지 |

### Cycle 3

| 항목 | 내용 |
| --- | --- |
| base 브랜치 | 해당 없음 |
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
해당 없음 — 실습 시간 내 3번째 공격 PR 미접수.
```

#### Cycle 3 이후 방어 개선

| Commit | 개선 내용 | 개선 이유 |
| --- | --- | --- |
| 해당 없음 | 해당 없음 | 해당 없음 |

## 6. 탐지 성공 사례

| 취약점 유형 | 탐지 도구 또는 규칙 | 탐지 파일 | 왜 잘 탐지됐는가 |
| --- | --- | --- | --- |
| Hardcoded GitHub PAT (A09 / 시크릿) | Gitleaks rule-id `github-pat` | `cicd_practice/backend/src/main/resources/application.yml` (commit d949b07) | `ghp_` prefix가 GitHub의 명확한 PAT 시그니처. Gitleaks 기본 룰에 형식 정의가 있어 false negative 거의 없음 |
| A06 Vulnerable npm Components | npm audit `--audit-level=high` | `cicd_practice/frontend/package.json` | lockfile + npm registry 메타데이터로 CVE 매칭. 정책을 critical → high로 강화한 덕에 commons CVE도 잡힘 |
| A03 SQLi / A10 SSRF / A05 CSRF·CORS | Semgrep `p/owasp-top-ten`, `p/java`, `p/security-audit` + GitHub 코드 스캐닝 CodeQL `security-and-quality` | ContentRepository(or ContentSearchService), AdminUtilController/UrlPreviewController, SecurityConfig | SAST 두 엔진이 같은 카테고리를 다른 룰셋으로 중복 검사 → 한쪽이 놓쳐도 다른 쪽이 잡음. CodeQL의 데이터플로우 분석이 결정적이었음 |

## 7. 탐지 실패 또는 오탐 사례

| 유형 | PR 또는 파일 | 원인 분석 | 다음 개선안 |
| --- | --- | --- | --- |
| 미탐 | PR #9 / AdminUtilController, api.ts의 `INTERNAL_API_KEY` `JWT_SIGNING_KEY` `DB_PASSWORD` `ADMIN_BACKDOOR_TOKEN` `ADMIN_SIGNING_SECRET` 등 placeholder 상수 | Gitleaks가 SUCCESS (탐지 없음). 값이 실제 형식 secret (예: `ghp_xxx`, AWS access key 패턴)이 아니라 일반 식별자 문자열이라 entropy/regex 룰에 안 걸림 | (a) custom gitleaks rules: 변수명 기반 (`_KEY`, `_TOKEN`, `_SECRET`, `PASSWORD` 같은 식별자 + literal string) 패턴 추가. (b) Semgrep `p/secrets` + `generic.secrets.security.detected-generic-api-key` 등의 룰이 잡는지 별도 확인. (c) detect-secrets 추가 검토 |
| 미탐 추정 | A07 토큰 만료 검증 제거 (PR #12) | 공격자도 "(룰 보강 시)"로 명시. 현재 도구셋에 토큰 만료 검사 누락을 잡는 룰 없음 | custom Semgrep rule: JWT 라이브러리 호출 시 `verifyExpiration` 또는 `expiration` 파라미터 명시 강제. 또는 인증 통합 테스트로 만료 토큰 거부 확인 |
| 미탐 추정 | A08 외부 스크립트 SRI 없이 latest 로드 (PR #9, #12) | Semgrep `p/react`는 적용했으나 HTML index.html에 대해선 룰 hit이 statusCheckRollup에서 확인 안 됨 (확인 필요) | Semgrep custom rule + Trivy config scan에 HTML/SRI 룰 적용. 또는 `eslint-plugin-html` + `sri-toolbox` 도입 |
| 차단 미보장 | PR #9, #12 모두 mergeStateStatus UNSTABLE (BLOCKED 아님) | defend/david에 branch protection 미설정 → required status check 없음 | repo Settings → Branches → defend/david rule 추가, "Security audit" 워크플로의 핵심 job들을 required status check로 지정 |

## 8. PR 차단 검증

| 항목 | 결과 |
| --- | --- |
| branch protection 설정 여부 | 미설정 (`GET /repos/.../branches/defend/david/protection` → 404) |
| required status check 이름 | 없음 |
| 실패한 check 이름 | Backend - Maven test, Frontend - npm audit & build, SAST - Semgrep (OWASP Top 10), Trivy - filesystem & config scan, Secrets - Gitleaks, Backend - OWASP Dependency-Check (PR #12), 코드 스캐닝 CodeQL / Semgrep OSS alerts |
| PR 상태 | UNSTABLE (mergeStateStatus) — 양 PR 동일 |
| 실제 머지 버튼 상태 | "Merge pull request" 버튼 활성 (확인 필요 — admin 권한 사용자 한정 가능) |
| 차단이 안 됐다면 이유 | branch protection rule을 만들지 않아서. workflow 실패는 PR 화면 표시만 변하고 머지 자체는 GitHub UI가 막지 않음 |

정리:

- workflow가 실패해도 branch protection이 없으면 실제 머지는 가능할 수 있다.
- PR을 확실히 막으려면 required status check 설정이 필요하다.
- defend/david는 다음 라운드 전에 branch protection을 추가하고 6개 핵심 job (Maven test, Dependency-Check, npm audit, Semgrep, CodeQL Java/JS, Gitleaks, Trivy)을 required로 지정해야 한다.

## 9. Lesson Learned

### 기술적으로 배운 점

- 단일 SAST에 의존하면 안 된다. Semgrep + CodeQL 두 엔진을 함께 돌렸을 때 비로소 SQLi/SSRF/weak random 같은 데이터플로우 결함을 신뢰성 있게 잡았다. CodeQL의 `security-and-quality` 쿼리는 mvn compile 시간을 추가로 쓰지만 그만한 가치가 있다.
- Gitleaks는 형식이 분명한 secret(`ghp_`, AWS key 패턴 등)에는 거의 100% hit, placeholder 식별자에는 0% hit. 즉 "시크릿 스캐너만 있으면 안전"이 아니다 — variable name 기반 custom rule을 같이 가야 한다.
- npm audit의 `--audit-level=high`는 합리적인 균형점. critical 한정은 알려진 RCE만 잡고, low까지 가면 노이즈가 너무 많다.

### workflow 설계에서 배운 점

- "심각도 정책"을 워크플로 첫머리에 코드로 명시(CRITICAL = fail, HIGH = npm만 fail, MEDIUM = report)하면 새 도구를 추가할 때 일관된 결정이 쉽다.
- sticky PR comment + SARIF 코드 스캐닝 + artifact 3중 보고는 정보 중복 같지만 각각 다른 사용자 시나리오를 커버한다 (PR 리뷰어 / 보안 팀 / 사후 감사).
- concurrency group으로 같은 ref의 워크플로를 cancel-in-progress 설정 → 공격자가 빠르게 commit 누적해도 자원 낭비 없음.

### 방어 브랜치 운영에서 배운 점

- workflow를 push했어도 **branch protection을 안 걸면 빌드는 실패해도 머지 가능**하다. "Checks 통과 없이 머지 불가"는 GitHub의 기본 동작이 아니다 — 명시적으로 설정해야 한다.
- 공격 PR이 들어오기 *전*에 workflow가 준비되어 있어야 한다. PR 만들고 나서 base 브랜치에 workflow를 push하면 기존 PR에는 자동 트리거가 안 잡혀 빈 커밋 푸시로 강제 sync 필요.
- 공격자가 코드 스캐닝에 SARIF가 누적되면 다음 PR도 "기존 알람"으로 보일 수 있어 base 브랜치에 alert가 남지 않도록 PR마다 dismissal 또는 베이스라인 관리가 필요할 수 있다.

## 10. 표준 보안감사 Workflow 제안

| 우선순위 | 항목 | 포함 여부 | 이유 |
| --- | --- | --- | --- |
| 필수 | Backend test | 포함 | 공격이 컴파일/테스트를 깨뜨리는 경우 가장 빠른 first line. PR #12 Maven test 즉시 실패 |
| 필수 | Frontend build | 포함 (npm audit job 안에 포함) | 라이브러리 교체 공격이 빌드를 깨뜨리는 경우 즉시 캐치 |
| 필수 | 의존성 취약점 스캔 | 포함 (Maven OWASP DC + npm audit + Trivy fs) | A06 핵심 방어선. 세 엔진 중첩으로 false negative 최소화 |
| 필수 | SAST | 포함 (Semgrep + CodeQL 2종) | OWASP Top 10 코드 패턴 대부분이 여기서 잡힘 |
| 권장 | Secret scan | 포함 (Gitleaks) | 명시적 형식 secret은 거의 100% 캐치. custom rule 보강 권장 |
| 권장 | Container 또는 filesystem scan | 포함 (Trivy fs + config) | IaC/Dockerfile misconfig 보완 |
| 권장 | PR 댓글 보고서 | 포함 (sticky-pull-request-comment) | 리뷰어가 한눈에 상태 확인 |
| 권장 | Artifact 업로드 | 포함 | 사후 감사 / 회고용 |
| 필수 | Required status check | **미포함 → 표준화 시 필수 추가** | 차단의 핵심. 없으면 workflow는 알람 시스템에 그침 |

### 제안하는 실패 기준

- Critical: 모든 도구에서 빌드 실패 (현 워크플로 정책 그대로)
- High: npm audit에서 실패 / Semgrep · CodeQL은 룰 자체 severity가 ERROR면 실패 / Trivy fs는 HIGH는 리포트 전용 (관리 부담 고려)
- Medium: artifact 보고만, 빌드 통과
- Low: 무시 (가능하면 dependabot/renovate에 위임)

### 제안하는 보고서 형식

- PR 댓글에 포함할 내용: job별 result 표 (성공/실패), severity 정책 1줄, artifact 이름 리스트, "BLOCKED 여부" 한 줄
- Artifact로 남길 내용: Dependency-Check HTML+JSON, npm-audit.json, semgrep.sarif, trivy table reports (CRITICAL/HIGH 분리)
- 팀 회고에서 공유할 내용: 어떤 도구가 어떤 카테고리를 잡았는지 매트릭스, 미탐 사례와 custom rule 추가 후보 리스트

## 11. 최종 결론

| 항목 | 판단 |
| --- | --- |
| 표준 workflow로 채택 가능 여부 | 보완 필요 (workflow 자체는 채택 가능. branch protection 설정 + custom rule 보강 필요) |
| 바로 적용 가능한 부분 | Maven test / Dependency-Check / npm audit / Semgrep + CodeQL 2종 SAST / Trivy fs+config / Gitleaks / sticky PR comment — 그대로 가져다 쓸 수 있음 |
| 추가 실험이 필요한 부분 | (1) placeholder/식별자 시크릿 탐지를 위한 custom Gitleaks rules, (2) A07 토큰 만료 검증 누락 detect용 custom Semgrep rule, (3) A08 외부 스크립트 SRI 강제 룰, (4) branch protection + required status check 조합의 실제 차단 검증 |
| 다음 액션 | (a) defend/david에 branch protection 설정 후 PR #12에 빈 커밋 trigger해 BLOCKED 상태 확인 / (b) Cycle 3 라운드로 A07 토큰 만료 검증 우회 단일 취약점 공격 받아보기 / (c) Gitleaks custom rules 한 묶음 추가 후 placeholder 시크릿 재시험 |

최종 의견:

- 두 라운드 모두 workflow가 핵심 OWASP 카테고리를 광범위하게 잡았고, 빌드 실패까지 도달했다. 표준 후보로 충분하지만 "차단"이 아닌 "알람"에 머문 한계가 명확하다. 다음 단계는 branch protection으로 차단 보장 + 커스텀 룰로 미탐 영역 메우기.

## 부록: 조회 명령어

```text
git fetch origin
git log --oneline --decorate origin/main..origin/defend/david
git log --stat origin/main..origin/defend/david
git ls-tree -r --name-only origin/defend/david .github
git cat-file blob <workflow-blob-hash>      # 워크플로 본문 확인
gh pr list --base defend/david --state all \
  --repo anTuni/fornerds_study_session4 \
  --json number,title,url,state,author,headRefName,baseRefName,createdAt,mergeStateStatus
gh pr view 9  --repo anTuni/fornerds_study_session4 --json number,title,body,files,statusCheckRollup,mergeStateStatus
gh pr view 12 --repo anTuni/fornerds_study_session4 --json number,title,body,files,statusCheckRollup,mergeStateStatus,comments
gh pr view 12 --repo anTuni/fornerds_study_session4 --json comments
gh api repos/anTuni/fornerds_study_session4/branches/defend/david/protection
gh api "repos/anTuni/fornerds_study_session4/actions/runs?event=pull_request&head_sha=<pr-head-sha>" --jq '.workflow_runs[]|{name,path,head_branch,head_sha,status,conclusion}'
```
