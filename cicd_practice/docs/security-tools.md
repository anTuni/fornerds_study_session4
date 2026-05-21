# defend/sabo 보안 스캔 도구 선정

## 1. 저장소 의존성 파일 분석

| 파일 | 위치 | 빌드/패키지 매니저 | 비고 |
| --- | --- | --- | --- |
| `pom.xml` | `cicd_practice/backend/pom.xml` | Maven | Spring Boot 3.3.6, Spring Security, Spring Data JPA, H2. OWASP `dependency-check-maven` 플러그인이 이미 선언돼 있다. |
| `package.json` | `cicd_practice/frontend/package.json` | npm | React + Vite + TypeScript. 거의 모든 의존성이 `latest` 핀이라 lockfile 기반 스캔에서 false negative가 날 수 있다. |
| `package-lock.json` | `cicd_practice/frontend/package-lock.json` | npm | `npm audit`, Snyk가 실제로 보는 진입점. |
| `application.yml` | `cicd_practice/backend/src/main/resources/application.yml` | — | secret이 들어갈 가능성이 있는 설정 파일 (gitleaks 대상). |
| 컨테이너 이미지 | (없음) | — | Dockerfile은 아직 없음 → 이미지 스캔은 보류, FS 스캔으로 대체. |

빌드 결과물로 `target/*.jar` (Maven), `frontend/dist/*` (Vite) 가 생성되지만 PR 시점에는 의존성 manifest 스캔이 우선이다.

## 2. 도구 선정

| 도구 | 대상 | 강점 | 약점 / 주의 | 구성 요구사항 |
| --- | --- | --- | --- | --- |
| **Snyk CLI** | Maven, npm (lockfile) | OSS DB가 NVD보다 빠르게 갱신, 수정 PR/upgrade path 제공, license 검사 가능, SARIF/JSON 출력 | 무료 플랜은 월 테스트 횟수 제한, 토큰 필요 | repo secret `SNYK_TOKEN`, `snyk auth`, `snyk test --severity-threshold=high` |
| **OWASP Dependency-Check (Maven plugin)** | Maven | NVD 기반, 빌드 도구에 직접 통합되어 transitive 포함, HTML/JSON 리포트 | NVD DB 다운로드로 첫 실행이 느림, false positive 다수 | `pom.xml`에 plugin 선언(이미 있음), `failBuildOnCVSS` 임계값 |
| **npm audit** | npm | 추가 설치 0, lockfile만 있으면 동작 | npm 레지스트리 advisory에 한정, transitive 정확도 떨어짐 | `npm audit --audit-level=high` |
| **Semgrep (p/owasp-top-ten, p/security-audit, p/secrets)** | 소스 코드 (Java, TS, React) | OWASP Top 10 룰 풍부, SARIF 지원, 빠른 실행 | 룰셋에 따라 noise, custom rule 필요할 수 있음 | docker image `returntocorp/semgrep`, 룰셋 URL |
| **Trivy (fs)** | 파일시스템 (lockfile, IaC) | 단일 바이너리, manifest/lockfile/IaC 모두 스캔, SARIF | npm은 lockfile에 의존, secret 룰은 gitleaks에 비해 약함 | `aquasecurity/trivy-action`, severity 필터 |
| **gitleaks** | Git 히스토리 + 작업트리 | regex 기반 secret 탐지, 빠름 | manifest 취약점은 못 봄 | `gitleaks/gitleaks-action@v2`, optional `.gitleaks.toml` |

### 무엇을 어디서 잡는가

| OWASP Top 10 카테고리 | 1차 도구 |
| --- | --- |
| A03 Injection (SQLi, XSS) | Semgrep |
| A06 Vulnerable & Outdated Components | **Snyk**, OWASP Dependency-Check, npm audit, Trivy |
| A02 Cryptographic Failures (NoOp encoder, weak random) | Semgrep |
| A05 Security Misconfiguration (CSRF disable, CORS `*`) | Semgrep |
| A01 Broken Access Control (`@PreAuthorize` 제거 등) | Semgrep |
| A09 Logging Failures / 평문 비밀 노출 | gitleaks, Semgrep |
| A10 SSRF | Semgrep |
| 평문 시크릿 커밋 | gitleaks |

## 3. 워크플로 배치 원칙

- 테스트(`mvn test`, lint)와 보안 스캔은 **병렬 실행**.
- **빌드(`mvn package`, `vite build`)는 모든 보안 스캔 job이 통과해야만 실행**된다.
  - 의존성 그래프: `*-test`, `*-scan` (병렬) → `*-build` (`needs:` 보안 잡들).
- 보안 잡 결과는 항상 artifact로 업로드 (`if: always()`).
- PR에는 sticky comment 한 건으로 요약 + 사람이 읽기 쉬운 보안 보고서 본문을 함께 게시.

## 4. 실패 기준

- Snyk: `--severity-threshold=high` → high 또는 critical 발견 시 잡 실패.
- OWASP Dependency-Check: `failBuildOnCVSS=7` → CVSS 7.0 이상에서 빌드 실패.
- npm audit: `--audit-level=high`.
- Trivy: `severity=CRITICAL,HIGH`, `exit-code=1`, `ignore-unfixed=true`.
- Semgrep: `--severity ERROR --severity WARNING --error`.
- Gitleaks: 기본 (탐지되면 실패).

## 5. 사전 준비물

| 항목 | 위치 | 비고 |
| --- | --- | --- |
| `SNYK_TOKEN` | Repository → Settings → Secrets and variables → Actions | https://app.snyk.io/account 에서 발급 |
| `GITHUB_TOKEN` | 자동 주입 | gitleaks, sticky-pull-request-comment 사용 |
| `.gitleaks.toml` | 저장소 루트 | 샘플 자격증명은 allowlist 처리 |
