# 보안 감사 도구 선정 및 의존성 분석

이 문서는 `cicd_practice` 저장소의 자동 보안 감사 파이프라인이 사용하는 도구를 선정한 근거와,
현재 의존성 상태, 그리고 각 도구가 커버하는 취약점 분류(OWASP Top 10 + 「웹 보안 통합 가이드」 W1~W11)를 정리합니다.

심각도 기준과 대응 정책은 [SECURITY_POLICY.md](./SECURITY_POLICY.md)를 참조합니다.

---

## 1. 의존성 현황

### 1.1 Backend (Maven, `backend/pom.xml`)

| 항목 | 값 | 비고 |
| --- | --- | --- |
| Java | 17 | LTS |
| Parent | `spring-boot-starter-parent` 3.3.6 | 비교적 최신 |
| 보안 관련 starter | `spring-boot-starter-security`, `spring-boot-starter-validation` | OK |
| DB | `com.h2database:h2` (runtime) | 운영 환경에선 교체 권고 |
| 빌드 plugin | `org.owasp:dependency-check-maven:10.0.4` | **이미 등록됨**, `failBuildOnCVSS=9.0` |
| 그 외 | spring-boot-starter-data-jpa, web, test, spring-security-test | OK |

**관찰**

- Spring Boot 3.3.6은 2024-11 릴리스. CVE 회귀가 가끔 발생하므로 SCA 도구로 지속 점검 필요.
- OWASP Dependency-Check가 이미 plugin으로 등록돼 있어 **CI에서 `mvn verify`만 호출하면 동작**한다.
- 현재 임계값 9.0은 우리 정책(7.0/High)보다 느슨 → 워크플로에서 `-DfailBuildOnCVSS=7.0` 오버라이드한다.

### 1.2 Frontend (npm, `frontend/package.json`)

| 패키지 | 선언 버전 | 위험 |
| --- | --- | --- |
| react / react-dom | `latest` | ⚠️ |
| vite / @vitejs/plugin-react | `latest` | ⚠️ |
| typescript / @types/* | `latest` | ⚠️ |
| eslint / typescript-eslint | `latest` | ⚠️ |
| lucide-react | `latest` | ⚠️ |

**관찰**

- 모든 의존성이 `"latest"` 태그 → **재현성 0, 보안 스캔 결과가 빌드마다 달라질 수 있음**
- `package-lock.json`이 없으면 `npm ci`가 실패 → CI 첫 실행이 깨질 가능성
- **조치(완료 예정)**: `npm install`로 한 번 고정 후 lockfile 커밋. package.json의 `"latest"`는 그대로 두되 lockfile이 단일 진실 소스.

### 1.3 IaC / 컨테이너

- Dockerfile, Terraform, k8s 매니페스트 **없음**
- Trivy `config` 스캔은 현재 placeholder. 향후 Dockerfile 추가 시 자동 확장.

### 1.4 시크릿 / 자격증명

- `application.yml` 평문 (DB 사용자명/비번 없음, H2 inmemory)
- `.env`, `*.pem`, `id_rsa` 등 없음
- Gitleaks를 PR 게이트에 두어 미래의 회귀를 방지한다.

---

## 2. 도구 선정

### 2.1 도구 비교 — 왜 이 조합인가

| 도구 | 영역 | 강점 | 약점 | 필요 시크릿 |
| --- | --- | --- | --- | --- |
| **Snyk Open Source** | SCA (Maven + npm) | 최신 CVE DB, fix advisor, License check, dashboard | 무료 플랜 PR 횟수 제한 | `SNYK_TOKEN` |
| **Snyk Code** (선택) | SAST | DeepCode 엔진, 빠름 | Token 공유 시 dashboard 부하 | `SNYK_TOKEN` |
| **OWASP Dependency-Check** | Java SCA 보조 | 오프라인 가능, plugin 이미 등록됨 | NVD 동기화 느림 | 없음 |
| **Semgrep** | SAST (메인) | OSS, OWASP 룰셋 풍부, SARIF 출력, 빠름 | 비즈니스 로직 결함은 못 잡음 | 없음 |
| **Gitleaks** | 시크릿 스캔 | 빠름, 룰 커스터마이즈 쉬움 | 엔트로피 기반 오탐 | 없음 |
| **Trivy fs** | 파일시스템(SBOM/시크릿/IaC) | 한 번에 다중 영역, SARIF | 자바 SCA 깊이 얕음 | 없음 |
| **Dependabot** | 자동 PR | GitHub 네이티브, 0 설정 | scan 자체는 안 함 | 없음 |
| **CodeQL** (미선택) | SAST | 강력, GitHub Security tab 통합 | 느림(5~10분+), 실습 사이클 부담 | 없음 |

**선정 조합**: Snyk(메인 SCA) + Semgrep(메인 SAST) + Gitleaks(시크릿) + Trivy fs(보조 SCA/IaC) + OWASP DC(자바 보조) + Dependabot(상시 자동 PR).

### 2.2 도구 구성 요구사항

| 도구 | 구성 | 작성 위치 |
| --- | --- | --- |
| Snyk | repo secret `SNYK_TOKEN` 등록 (snyk.io 무료 계정에서 발급) | GitHub Settings → Secrets and variables → Actions |
| OWASP DC | NVD API key 권장(속도) — 없어도 동작 | 선택적으로 `NVD_API_KEY` secret |
| Semgrep | OSS, 토큰 불필요 (Semgrep Cloud 안 씀) | 워크플로 inline |
| Gitleaks | 토큰 불필요. `.gitleaks.toml` 룰 커스터마이즈 시 추가 | 저장소 루트 |
| Trivy fs | 토큰 불필요 | 워크플로 inline |
| Dependabot | YAML만 추가 | `.github/dependabot.yml` |

---

## 3. 취약점 분류 ↔ OWASP ↔ 도구 매핑

「웹 보안 통합 가이드」 §3.1 W1~W11 분류를 기준으로 정리합니다.
"자동 탐지" 컬럼은 *현재 정책 + 도구 조합에서 PR 게이트로 잡을 수 있는지*입니다.

| 가이드 분류 | OWASP 2021 | 자동 탐지 도구 | 게이트 가능 | 보완 (수동/동적) |
| --- | --- | --- | --- | --- |
| **W1.1** 취약한 계정 | A07 Identification | Semgrep `weak-password-policy` | ⚠️ 부분 | 정책 검증 |
| **W1.2** 인증 실패 제한 | A07 | — | ❌ | 동적 점검 |
| **W1.3** 계정 정책 미흡 | A07 | — | ❌ | 정책 검증 |
| **W2.1** SQL Injection | A03 Injection | Semgrep `formatted-sql-string`, Snyk Code | ✅ | DAST |
| **W2.2** CMD Injection | A03 | Semgrep `command-injection` | ✅ | — |
| **W2.3** RFI/LFI | A03 | Semgrep `path-traversal` | ✅ | — |
| **W2.4** XQuery Injection | A03 | Semgrep `xquery-injection` | ⚠️ | 룰 보강 |
| **W2.5** XPath Injection | A03 | Semgrep `xpath-injection` | ✅ | — |
| **W2.6** LDAP Injection | A03 | Semgrep `ldap-injection` | ✅ | — |
| **W2.7** XXE | A05 Misconfig | Semgrep `xxe` | ✅ | — |
| **W3.1** 인증 우회 | A01 Access Control | Snyk Code 일부 | ⚠️ | **코드 리뷰 (비즈니스 로직)** |
| **W3.2** HTTP Response Splitting | A03 | Semgrep `crlf-injection` | ✅ | — |
| **W3.3** Open Redirect | A01 | Semgrep `open-redirect` | ✅ | — |
| **W4.1** 파일 업로드 | A04 Insecure Design | Semgrep `unrestricted-upload` | ⚠️ | MIME/확장자 정책 검증 |
| **W4.2** 파일 다운로드 (Path Traversal) | A01 | Semgrep `path-traversal` | ✅ | — |
| **W5.1** 비인증 접근 허용 | A01 | — | ❌ | **Spring Security 설정 리뷰** |
| **W5.2** ACL 미흡 | A01 | — | ❌ | `@PreAuthorize` 검증, BOLA 점검 |
| **W6.1** XSS | A03 | Semgrep `react/xss`, `dom-xss` | ✅ | DAST |
| **W6.2** CSRF | A01 | Semgrep `csrf-disabled` | ✅ | 토큰 검증 |
| **W7.1** 부적절한 메서드 | A05 | Semgrep | ⚠️ | 운영 점검 |
| **W7.2** Directory Listing | A05 | — | ❌ | 운영 점검 |
| **W7.3** 불필요 포트 | A05 | — | ❌ | 인프라 점검 |
| **W7.4** 관리자 페이지 접근제어 | A01 | — | ❌ | IP 화이트리스트/VPN |
| **W8.1** 시크릿 노출 | A07/A02 | **Gitleaks** + Trivy `secret` | ✅ | — |
| **W8.2** 인증실패 메시지 | A04 | Semgrep | ⚠️ | UX 점검 |
| **W8.3** 서버 정보 노출 | A05 | Semgrep `verbose-error` | ⚠️ | — |
| **W8.4** 부적절한 오류 처리 | A09 Logging | Semgrep `stack-trace` | ⚠️ | — |
| **W8.5** 임시/백업 파일 노출 | A05 | — | ❌ | 운영 점검 |
| **W9.1** 인증 Cache-Control | A05 | Semgrep | ⚠️ | 응답헤더 검증 |
| **W9.2** 세션 타임아웃 | A07 | Semgrep | ⚠️ | 설정 검증 |
| **W9.3** 세션 토큰 강도 | A02 | — | ❌ | 토큰 엔트로피 |
| **W10.1** 평문 전송 | A02 Crypto | Semgrep `http-uses-insecure` | ✅ | — |
| **W10.2** 취약 알고리즘 | A02 | Semgrep `weak-hash`, `weak-crypto` | ✅ | — |
| **W11** SW 패키지 취약점 | A06 Vulnerable Components | **Snyk + OWASP DC + npm audit + Trivy + Dependabot** | ✅ | — |

**해석**

- ✅ 표시 16건: PR 게이트로 차단 가능 → 핵심 자동화 영역
- ⚠️ 표시 10건: 룰 보강 또는 컨텍스트에 따라 탐지율 변동 → 정기적인 룰 업데이트가 필요
- ❌ 표시 9건: 정적 분석 본질적 한계 → **수동 코드 리뷰 + DAST + 운영 점검**으로 보완. 분기 1회 이상 수행.

---

## 4. 최근(2024~2026) 신흥 공격 동향 반영

다음 트렌드를 도구 구성에 추가 반영합니다.

| 트렌드 | 대응 |
| --- | --- |
| **OWASP API Security Top 10 (2023) — BOLA/IDOR** | Semgrep API 룰셋 + 수동 리뷰 권고. SAST 한계 명시. |
| **Supply chain (xz-utils, npm typosquatting)** | Snyk + Dependabot으로 lockfile 단위 점검. `npm install`은 lockfile 기준으로만 허용. |
| **Prototype Pollution (npm 생태계 지속 발견)** | Semgrep `javascript.lang.security.audit.prototype-pollution` |
| **Server-Side Request Forgery (A10)** | Semgrep `ssrf` 룰. 단, URL 화이트리스트 패턴은 수동 리뷰 필요. |
| **Mass Assignment / Insecure Deserialization** | Semgrep `mass-assignment`, `insecure-deserialization` |
| **JWT alg=none / 약한 시크릿** | Semgrep `jwt-none-alg`, `hardcoded-jwt-secret` |
| **CI/CD 공급망 공격 (pwn-request, third-party action)** | Dependabot의 `github-actions` ecosystem + 워크플로의 `permissions: read-all` 기본 + pinned SHA 사용 |
| **LLM Prompt Injection (OWASP LLM Top 10)** | 현재 적용 안 함 (LLM 통합 없음). 향후 추가 시 별도 정책. |

---

## 5. 워크플로 jobs 매핑

각 job이 어떤 W/OWASP 분류를 커버하는지 (수비자 워크플로 설계 기준).

| Job | 커버 분류 | 산출물 | 게이트 |
| --- | --- | --- | --- |
| `snyk-backend` | W11, A06 | `snyk-backend.sarif`, `snyk-backend.json` | high 이상 fail |
| `snyk-frontend` | W11, A06 | `snyk-frontend.sarif`, `snyk-frontend.json` | high 이상 fail |
| `owasp-dc` | W11, A06 (Java) | `dependency-check-report.html`, `.json` | CVSS 7.0+ fail |
| `semgrep` | W2, W3, W4, W6, W10, A03/A05/A02 | `semgrep.sarif` | ERROR fail |
| `gitleaks` | W8.1, A07/A02 | `gitleaks.json` | 1건이라도 fail |
| `trivy-fs` | W8.1, W11, IaC (placeholder) | `trivy.sarif` | CRITICAL/HIGH fail |
| `aggregate-report` | 위 전체 통합 | `security-report.md` | (게이트 아님) PR comment + artifact |
| `notify-critical` | Critical 1건+ | GitHub Issue 자동 생성 | (게이트 아님) |
| `build` (CI) | — | jar/dist | 위 게이트 통과 후만 실행 |
| `test` (CI) | — | surefire reports | 보안 job과 병렬 |

---

## 6. 표준화 권고 (실습 종료 후)

- 본 도구 조합은 팀 표준 후보. 단, OWASP DC와 Snyk는 영역이 겹치므로 **장기적으론 Snyk로 단일화** 권장 (OWASP DC는 백업).
- Semgrep 룰셋은 **저장소별 커스텀 룰**(`.semgrep/`)을 누적 관리.
- IaC 도입 시 Trivy `config` 모드 활성화.
- LLM 통합 시 OWASP LLM Top 10 기반 별도 정책 문서 추가.
