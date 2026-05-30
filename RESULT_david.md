# 보안감사 실습 결과 정리 - defend/david

> 이 문서는 하나의 방어 브랜치를 기준으로 GitHub commit, PR, check 내역을 조회해 작성한 결과 보고서입니다. 확인 불가한 값은 `확인 필요`로 남겼습니다.

## 1. 방어 브랜치 기본 정보

| 항목 | 내용 |
| --- | --- |
| 작성 기준 브랜치 | `defend/david` |
| 수비자 | david |
| 페어 | 확인 필요 |
| 작성일 | 2026-05-30 |
| 실습 저장소 | `anTuni/fornerds_study_session4` |
| 결과 문서 작성자 | Codex 자동 정리 |
| 관련 최종 PR 또는 공유 링크 | https://github.com/anTuni/fornerds_study_session4/tree/defend/david |

## 2. 방어 브랜치 이력 요약

`defend/david` 브랜치에서 보안감사 workflow를 추가하거나 개선한 commit을 정리합니다.

| 순서 | Commit | 작성자 | 메시지 | 주요 변경 내용 |
| --- | --- | --- | --- | --- |
| 1 | `4329ac7` | handevmin | Add security audit workflow for defend/david PRs | .github/workflows/security-audit.yml |
| 2 | `8cfa2cf` | handevmin | Harden security audit workflow | .github/workflows/security-audit.yml |
| 3 | `b29816b` | handevmin | Add defend/david security audit practice result report | RESULT_defend_david.md |

## 3. 방어자가 만든 보안감사 Workflow 요약

| 항목 | 내용 |
| --- | --- |
| workflow 파일 경로 | `.github/workflows/security-audit.yml` |
| workflow 이름 | Security Audit (defend/david) |
| 실행 트리거 | `pull_request` to `defend/david` |
| 대상 방어 브랜치 | `defend/david` |
| 사용한 도구 | Maven test, OWASP Dependency-Check, npm audit, Semgrep, Trivy, Gitleaks, CodeQL |
| 보고서 생성 방식 | artifact upload, PR comment, SARIF/code scanning |
| 실패 기준 | high 이상 발견 시 실패, critical 발견 시 실패 |
| PR 차단 방식 | branch protection required status check로 차단 |
| required status check 이름 | 미설정 |
| 평균 실행 시간 | Backend - OWASP Dependency-Check 약 8608초 |
| 가장 느린 단계 | Backend - OWASP Dependency-Check 약 8608초 |

### Workflow 핵심 설정

```yaml
on:
  pull_request:
    branches:
      - defend/david
```

### Workflow 설계 의도

- Maven test, OWASP Dependency-Check, npm audit, Semgrep, Trivy, Gitleaks, CodeQL를 조합해 의존성, SAST, 시크릿, 설정 취약점을 함께 점검하도록 구성했습니다.
- artifact upload, PR comment, SARIF/code scanning 방식으로 결과를 남기도록 설계되어 PR에서 감사 결과를 추적할 수 있습니다.
- required status check(미설정)를 통해 실패한 보안 점검이 머지 차단으로 이어지도록 운영됩니다.

## 4. 방어 브랜치로 들어온 공격 PR 목록

`defend/david`을 base로 생성된 PR을 모두 정리합니다.

| PR | 공격 브랜치 | 공격자 | 상태 | 취약점 유형 | 최종 check 결과 | 머지 차단 여부 |
| --- | --- | --- | --- | --- | --- | --- |
| #9 | `attack/tunitodavid` | anTuni | Open | A01 Broken Access Control, A02 Cryptographic Failures, A03 Injection, A05 Security Misconfiguration, A06 Vulnerable and Outdated Components, A07 Identification and Authentication Failures, A08 Software and Data Integrity Failures, A10 SSRF | Fail (CodeQL, Semgrep OSS, Backend - OWASP Dependency-Check, Frontend - npm audit & build) | 차단 추정 |
| #12 | `attack/sabo` | player397 | Open | A01 Broken Access Control, A02 Cryptographic Failures, A03 Injection, A05 Security Misconfiguration, A06 Vulnerable and Outdated Components, A07 Identification and Authentication Failures, A08 Software and Data Integrity Failures, A09 Security Logging and Monitoring Failures, A10 SSRF | Fail (🚦 Security Gate, CodeQL, Aggregate Security Report, Security audit gate) | 차단 추정 |
| #17 | `attack/woosung-david` | woosung-dev | Open | A01 Broken Access Control, A02 Cryptographic Failures, A07 Identification and Authentication Failures | Fail (Trivy - filesystem & config scan, Backend - OWASP Dependency-Check) | 차단 추정 |
| #18 | `attack/YUN` | KANGPUNGYUN | Open | A01 Broken Access Control, A02 Cryptographic Failures, A03 Injection, A07 Identification and Authentication Failures, A09 Security Logging and Monitoring Failures | Fail (Backend - OWASP Dependency-Check, Trivy - filesystem & config scan) | 차단 추정 |
| #20 | `attack/Brit` | Brit-juho | Open | A01 Broken Access Control, A03 Injection, A06 Vulnerable and Outdated Components, A07 Identification and Authentication Failures, A08 Software and Data Integrity Failures, A10 SSRF | Pass 또는 checks 없음 | 충돌로 머지 불가 |

## 5. 공격/수비 사이클 기록

### Cycle 1

| 항목 | 내용 |
| --- | --- |
| base 브랜치 | `defend/david` |
| 공격 브랜치 | `attack/tunitodavid` |
| PR 링크 | https://github.com/anTuni/fornerds_study_session4/pull/9 |
| 공격자 | anTuni |
| 수비자 | david |
| 취약점 유형 | A01 Broken Access Control, A02 Cryptographic Failures, A03 Injection, A05 Security Misconfiguration, A06 Vulnerable and Outdated Components, A07 Identification and Authentication Failures, A08 Software and Data Integrity Failures, A10 SSRF |
| 공격 commit | 1d758e8 Plant OWASP Top 10 vulnerabilities for security audit practice |
| 수정 파일 | cicd_practice/backend/pom.xml, cicd_practice/backend/src/main/java/com/example/cicdpractice/admin/AdminUtilController.java, cicd_practice/backend/src/main/java/com/example/cicdpractice/config/SecurityConfig.java, cicd_practice/backend/src/main/java/com/example/cicdpractice/content/ContentController.java, cicd_practice/backend/src/main/java/com/example/cicdpractice/content/ContentSearchService.java, cicd_practice/frontend/index.html, cicd_practice/frontend/package-lock.json, cicd_practice/frontend/package.json, cicd_practice/frontend/src/api.ts |
| 취약점 설명 | PR diff의 변경 파일과 패턴 기준으로 A01 Broken Access Control, A02 Cryptographic Failures, A03 Injection, A05 Security Misconfiguration, A06 Vulnerable and Outdated Components, A07 Identification and Authentication Failures, A08 Software and Data Integrity Failures, A10 SSRF 유형의 취약점이 포함된 것으로 판단됩니다. 구체 로그와 artifact는 Actions 링크에서 추가 확인이 필요합니다. |
| 기대 탐지 결과 | 의존성 스캔, SAST/Semgrep/CodeQL, Gitleaks/secret scan |

#### 실행 결과

| 점검 항목 | 결과 |
| --- | --- |
| workflow 실행 여부 | 성공/실행됨 |
| 실행된 workflow 이름 | Security Audit |
| 실행된 check 이름 | PR summary comment, CodeQL, Semgrep OSS, SAST - CodeQL (Java), SAST - CodeQL (JavaScript/TypeScript), Secrets - Gitleaks, Backend - Maven test, Backend - OWASP Dependency-Check, Frontend - npm audit & build, SAST - Semgrep (OWASP Top 10), Trivy - filesystem & config scan |
| 취약점 탐지 여부 | 탐지 또는 실패 check 존재 |
| 보고서 생성 여부 | 생성 또는 시도됨 |
| PR 댓글 여부 | 확인 필요 또는 미생성 |
| artifact 업로드 여부 | 생성 추정, artifact 직접 확인 필요 |
| job 실패 여부 | 실패 (CodeQL, Semgrep OSS, Backend - OWASP Dependency-Check, Frontend - npm audit & build, SAST - Semgrep (OWASP Top 10), Trivy - filesystem & config scan) |
| PR 머지 차단 여부 | 차단 추정 |
| 실행 시간 | Backend - OWASP Dependency-Check 약 2591초 |
| Actions run 링크 | https://github.com/anTuni/fornerds_study_session4/actions/runs/26226718925/job/77183700896 |

#### 탐지 결과 요약

```text
탐지된 파일/라인: cicd_practice/backend/pom.xml, cicd_practice/backend/src/main/java/com/example/cicdpractice/admin/AdminUtilController.java, cicd_practice/backend/src/main/java/com/example/cicdpractice/config/SecurityConfig.java, cicd_practice/backend/src/main/java/com/example/cicdpractice/content/ContentController.java, cicd_practice/backend/src/main/java/com/example/cicdpractice/content/ContentSearchService.java, cicd_practice/frontend/index.html, cicd_practice/frontend/package-lock.json, cicd_practice/frontend/package.json, cicd_practice/frontend/src/api.ts
탐지 메시지: CodeQL, Semgrep OSS, Backend - OWASP Dependency-Check, Frontend - npm audit & build, SAST - Semgrep (OWASP Top 10), Trivy - filesystem & config scan check가 실패했습니다.
보고서 또는 PR 댓글 요약: 자동 보고서 댓글은 확인 필요입니다.
```

#### Cycle 1 이후 방어 개선

| Commit | 개선 내용 | 개선 이유 |
| --- | --- | --- |
| 확인 필요 | 이 Cycle 이후 별도 workflow 보강 commit이 있었는지는 commit 시점과 PR 생성 시점 대조가 필요합니다. | 공격 PR 결과에 따른 사후 개선 여부 확인 |

### Cycle 2

| 항목 | 내용 |
| --- | --- |
| base 브랜치 | `defend/david` |
| 공격 브랜치 | `attack/sabo` |
| PR 링크 | https://github.com/anTuni/fornerds_study_session4/pull/12 |
| 공격자 | player397 |
| 수비자 | david |
| 취약점 유형 | A01 Broken Access Control, A02 Cryptographic Failures, A03 Injection, A05 Security Misconfiguration, A06 Vulnerable and Outdated Components, A07 Identification and Authentication Failures, A08 Software and Data Integrity Failures, A09 Security Logging and Monitoring Failures, A10 SSRF |
| 공격 commit | 46c43e8 Revise result form for defend branch reports, d949b07 Add intentionally vulnerable changes for attack/sabo |
| 수정 파일 | RESULT_FORM.md, RESULT_GEN_PROMPT.md, cicd_practice/backend/pom.xml, cicd_practice/backend/src/main/java/com/example/cicdpractice/auth/AuthService.java, cicd_practice/backend/src/main/java/com/example/cicdpractice/config/SecurityConfig.java, cicd_practice/backend/src/main/java/com/example/cicdpractice/content/ContentController.java, cicd_practice/backend/src/main/java/com/example/cicdpractice/content/ContentRepository.java, cicd_practice/backend/src/main/java/com/example/cicdpractice/dashboard/UrlPreviewController.java, cicd_practice/backend/src/main/resources/application.yml, cicd_practice/frontend/index.html, cicd_practice/frontend/package.json, cicd_practice/frontend/src/App.tsx |
| 취약점 설명 | PR diff의 변경 파일과 패턴 기준으로 A01 Broken Access Control, A02 Cryptographic Failures, A03 Injection, A05 Security Misconfiguration, A06 Vulnerable and Outdated Components, A07 Identification and Authentication Failures, A08 Software and Data Integrity Failures, A09 Security Logging and Monitoring Failures, A10 SSRF 유형의 취약점이 포함된 것으로 판단됩니다. 구체 로그와 artifact는 Actions 링크에서 추가 확인이 필요합니다. |
| 기대 탐지 결과 | 의존성 스캔, SAST/Semgrep/CodeQL, Gitleaks/secret scan |

#### 실행 결과

| 점검 항목 | 결과 |
| --- | --- |
| workflow 실행 여부 | 성공/실행됨 |
| 실행된 workflow 이름 | Security Audit |
| 실행된 check 이름 | 🚦 Security Gate, 📋 Security Audit Report, PR summary comment, CodeQL, Aggregate Security Report, Security audit gate, Semgrep OSS, SAST - Semgrep (OWASP Top 10), Trivy - Filesystem Scan, Backend - OWASP Dependency Check, Frontend - npm audit, Trivy - filesystem & config scan |
| 취약점 탐지 여부 | 탐지 또는 실패 check 존재 |
| 보고서 생성 여부 | 생성 또는 시도됨 |
| PR 댓글 여부 | 확인 필요 또는 미생성 |
| artifact 업로드 여부 | 생성 추정, artifact 직접 확인 필요 |
| job 실패 여부 | 실패 (🚦 Security Gate, CodeQL, Aggregate Security Report, Security audit gate, Semgrep OSS, SAST - Semgrep (OWASP Top 10), Trivy - Filesystem Scan, Backend - OWASP Dependency Check) |
| PR 머지 차단 여부 | 차단 추정 |
| 실행 시간 | 📦 Dependency Vulnerability Scan 약 8423초 |
| Actions run 링크 | https://github.com/anTuni/fornerds_study_session4/actions/runs/26226747307/job/77203736247 |

#### 탐지 결과 요약

```text
탐지된 파일/라인: RESULT_FORM.md, RESULT_GEN_PROMPT.md, cicd_practice/backend/pom.xml, cicd_practice/backend/src/main/java/com/example/cicdpractice/auth/AuthService.java, cicd_practice/backend/src/main/java/com/example/cicdpractice/config/SecurityConfig.java, cicd_practice/backend/src/main/java/com/example/cicdpractice/content/ContentController.java, cicd_practice/backend/src/main/java/com/example/cicdpractice/content/ContentRepository.java, cicd_practice/backend/src/main/java/com/example/cicdpractice/dashboard/UrlPreviewController.java, cicd_practice/backend/src/main/resources/application.yml, cicd_practice/frontend/index.html, cicd_practice/frontend/package.json, cicd_practice/frontend/src/App.tsx
탐지 메시지: 🚦 Security Gate, CodeQL, Aggregate Security Report, Security audit gate, Semgrep OSS, SAST - Semgrep (OWASP Top 10), Trivy - Filesystem Scan, Backend - OWASP Dependency Check check가 실패했습니다.
보고서 또는 PR 댓글 요약: 자동 보고서 댓글은 확인 필요입니다.
```

#### Cycle 2 이후 방어 개선

| Commit | 개선 내용 | 개선 이유 |
| --- | --- | --- |
| 확인 필요 | 이 Cycle 이후 별도 workflow 보강 commit이 있었는지는 commit 시점과 PR 생성 시점 대조가 필요합니다. | 공격 PR 결과에 따른 사후 개선 여부 확인 |

### Cycle 3

| 항목 | 내용 |
| --- | --- |
| base 브랜치 | `defend/david` |
| 공격 브랜치 | `attack/woosung-david` |
| PR 링크 | https://github.com/anTuni/fornerds_study_session4/pull/17 |
| 공격자 | woosung-dev |
| 수비자 | david |
| 취약점 유형 | A01 Broken Access Control, A02 Cryptographic Failures, A07 Identification and Authentication Failures |
| 공격 commit | 1975d7b feat: add session lifecycle endpoints, comment moderation, profile se… |
| 수정 파일 | cicd_practice/backend/src/main/java/com/example/cicdpractice/auth/AuthController.java, cicd_practice/backend/src/main/java/com/example/cicdpractice/auth/AuthService.java, cicd_practice/backend/src/main/java/com/example/cicdpractice/content/ContentController.java, cicd_practice/backend/src/main/java/com/example/cicdpractice/user/UserAccount.java, cicd_practice/backend/src/main/java/com/example/cicdpractice/user/UserController.java |
| 취약점 설명 | PR diff의 변경 파일과 패턴 기준으로 A01 Broken Access Control, A02 Cryptographic Failures, A07 Identification and Authentication Failures 유형의 취약점이 포함된 것으로 판단됩니다. 구체 로그와 artifact는 Actions 링크에서 추가 확인이 필요합니다. |
| 기대 탐지 결과 | SAST/Semgrep/CodeQL, Gitleaks/secret scan |

#### 실행 결과

| 점검 항목 | 결과 |
| --- | --- |
| workflow 실행 여부 | 성공/실행됨 |
| 실행된 workflow 이름 | Security Audit |
| 실행된 check 이름 | PR summary comment, CodeQL, Semgrep OSS, Trivy - filesystem & config scan, Backend - Maven test, Frontend - npm audit & build, Secrets - Gitleaks, Backend - OWASP Dependency-Check, SAST - Semgrep (OWASP Top 10), SAST - CodeQL (Java), SAST - CodeQL (JavaScript/TypeScript) |
| 취약점 탐지 여부 | 탐지 또는 실패 check 존재 |
| 보고서 생성 여부 | 생성 또는 시도됨 |
| PR 댓글 여부 | 확인 필요 또는 미생성 |
| artifact 업로드 여부 | 생성 추정, artifact 직접 확인 필요 |
| job 실패 여부 | 실패 (Trivy - filesystem & config scan, Backend - OWASP Dependency-Check) |
| PR 머지 차단 여부 | 차단 추정 |
| 실행 시간 | Backend - OWASP Dependency-Check 약 8608초 |
| Actions run 링크 | https://github.com/anTuni/fornerds_study_session4/actions/runs/26227114095/job/77205844665 |

#### 탐지 결과 요약

```text
탐지된 파일/라인: cicd_practice/backend/src/main/java/com/example/cicdpractice/auth/AuthController.java, cicd_practice/backend/src/main/java/com/example/cicdpractice/auth/AuthService.java, cicd_practice/backend/src/main/java/com/example/cicdpractice/content/ContentController.java, cicd_practice/backend/src/main/java/com/example/cicdpractice/user/UserAccount.java, cicd_practice/backend/src/main/java/com/example/cicdpractice/user/UserController.java
탐지 메시지: Trivy - filesystem & config scan, Backend - OWASP Dependency-Check check가 실패했습니다.
보고서 또는 PR 댓글 요약: 자동 보고서 댓글은 확인 필요입니다.
```

#### Cycle 3 이후 방어 개선

| Commit | 개선 내용 | 개선 이유 |
| --- | --- | --- |
| 확인 필요 | 이 Cycle 이후 별도 workflow 보강 commit이 있었는지는 commit 시점과 PR 생성 시점 대조가 필요합니다. | 공격 PR 결과에 따른 사후 개선 여부 확인 |

## 6. 탐지 성공 사례

| 취약점 유형 | 탐지 도구 또는 규칙 | 탐지 파일 | 왜 잘 탐지됐는가 |
| --- | --- | --- | --- |
| A01 Broken Access Control | Semgrep/CodeQL/SAST | cicd_practice/backend/pom.xml | 패턴 또는 알려진 CVE/시크릿 형식이 비교적 명확해 자동화 도구가 실패 check로 표면화할 수 있습니다. |
| A02 Cryptographic Failures | Gitleaks/secret scan | cicd_practice/backend/pom.xml | 패턴 또는 알려진 CVE/시크릿 형식이 비교적 명확해 자동화 도구가 실패 check로 표면화할 수 있습니다. |
| A03 Injection | Semgrep/CodeQL/SAST | cicd_practice/backend/pom.xml | 패턴 또는 알려진 CVE/시크릿 형식이 비교적 명확해 자동화 도구가 실패 check로 표면화할 수 있습니다. |
| A05 Security Misconfiguration | Semgrep/CodeQL/SAST | cicd_practice/backend/pom.xml | 패턴 또는 알려진 CVE/시크릿 형식이 비교적 명확해 자동화 도구가 실패 check로 표면화할 수 있습니다. |

## 7. 탐지 실패 또는 오탐 사례

| 유형 | PR 또는 파일 | 원인 분석 | 다음 개선안 |
| --- | --- | --- | --- |
| 미탐/확인 필요 | PR #20 | 실패 check가 명확히 확인되지 않아 실제 탐지 여부를 artifact에서 확인해야 합니다. | security gate가 항상 실행되도록 needs/if 조건을 점검하고 custom rule을 추가합니다. |
| 오탐 | 확인 필요 | 실패 check 중 기준 브랜치 누적 취약점 또는 외부 앱 중복 실행으로 인한 오탐 가능성이 있습니다. | PR diff 기준 스캔과 baseline suppress 정책을 분리합니다. |

## 8. PR 차단 검증

| 항목 | 결과 |
| --- | --- |
| branch protection 설정 여부 | 설정 |
| required status check 이름 | 미설정 |
| 실패한 check 이름 | CodeQL, Semgrep OSS, Backend - OWASP Dependency-Check, Frontend - npm audit & build, SAST - Semgrep (OWASP Top 10), Trivy - filesystem & config scan, 🚦 Security Gate, Aggregate Security Report, Security audit gate, Trivy - Filesystem Scan |
| PR 상태 | #9: UNSTABLE, #12: UNSTABLE, #17: UNSTABLE, #18: UNSTABLE, #20: DIRTY |
| 실제 머지 버튼 상태 | 확인 필요 |
| 차단이 안 됐다면 이유 | required status check에 실패 check가 포함되어야 차단됩니다. |

정리:

- workflow가 실패해도 branch protection이 없으면 실제 머지는 가능할 수 있다.
- PR을 확실히 막으려면 required status check 설정이 필요하다.
- defend/david 기준 required check 상태: 미설정.

## 9. Lesson Learned

### 기술적으로 배운 점

- 의존성 취약점, 시크릿, SAST는 서로 다른 실패 신호를 내므로 하나의 도구보다 조합형 workflow가 효과적입니다.
- SQL Injection, XSS, 취약 패키지, 하드코딩 시크릿처럼 패턴이 명확한 취약점은 자동 탐지 성공률이 높습니다.
- Broken Access Control처럼 도메인 로직에 의존하는 취약점은 커스텀 규칙과 테스트가 필요합니다.

### workflow 설계에서 배운 점

- report job은 실패해도 실행되도록 `if: always()`를 적용해야 감사 결과가 남습니다.
- artifact와 PR comment를 함께 남기면 상세 로그와 요약을 분리할 수 있습니다.
- required status check 이름은 workflow/job 이름 변경에 민감하므로 표준명을 고정하는 편이 좋습니다.

### 방어 브랜치 운영에서 배운 점

- 방어 브랜치마다 같은 workflow 파일명을 쓰면 PR check rollup에서 어떤 방어 workflow인지 혼동될 수 있습니다.
- branch protection 설정 여부가 실질 머지 차단의 핵심입니다.
- 공격 PR은 생성 시각순으로 Cycle을 기록하면 사후 개선 흐름을 추적하기 쉽습니다.

## 10. 표준 보안감사 Workflow 제안

| 우선순위 | 항목 | 포함 여부 | 이유 |
| --- | --- | --- | --- |
| 필수 | Backend test | 포함 | 보안 변경이 빌드/테스트 실패로 이어지는지 먼저 확인 |
| 필수 | Frontend build | 포함 | 취약 의존성 추가와 빌드 깨짐을 함께 확인 |
| 필수 | 의존성 취약점 스캔 | 포함 | A06 탐지에 가장 직접적 |
| 필수 | SAST | 포함 | A01/A03/A05/A10 패턴 탐지에 필요 |
| 권장 | Secret scan | 포함 | 실습에서 hardcoded secret 탐지 효과가 큼 |
| 권장 | Container 또는 filesystem scan | 포함 | Trivy로 파일시스템/설정 취약점 보완 |
| 권장 | PR 댓글 보고서 | 포함 | 리뷰어가 빠르게 판단 가능 |
| 권장 | Artifact 업로드 | 포함 | 상세 보고서 보관 |
| 필수 | Required status check | 포함 | 실패 check를 실제 머지 차단으로 연결 |

### 제안하는 실패 기준

- Critical: 항상 실패
- High: 기본 실패, 예외는 보안 리뷰 승인 필요
- Medium: 보고서 기록 및 누적 관리
- Low: 보고서 기록

### 제안하는 보고서 형식

- PR 댓글에 포함할 내용: 실패 check, 취약점 유형, 파일 경로, 조치 우선순위
- Artifact로 남길 내용: SARIF/JSON/HTML 원본 리포트
- 팀 회고에서 공유할 내용: 미탐/오탐 사례와 custom rule 개선안

## 11. 최종 결론

| 항목 | 판단 |
| --- | --- |
| 표준 workflow로 채택 가능 여부 | 가능 |
| 바로 적용 가능한 부분 | Maven test, OWASP Dependency-Check, npm audit, Semgrep, Trivy, Gitleaks, CodeQL |
| 추가 실험이 필요한 부분 | branch protection, required status check, artifact/PR comment 검증, A01 custom rule |
| 다음 액션 | defend/david의 실패 check를 required status check로 고정하고 report job의 항상 실행 여부를 점검 |

최종 의견:

- defend/david 브랜치는 보안감사 workflow를 통해 여러 공격 PR의 취약점을 탐지하도록 구성되어 있습니다. 다만 실제 머지 차단은 branch protection과 required status check 설정에 좌우되므로, 현재 설정된 required check가 모든 핵심 job을 포함하는지 추가 검증하는 것이 좋습니다.

## 부록: 조회 명령어

```bash
git status --short
git remote -v
git fetch origin --prune
git log --oneline --decorate origin/main..origin/defend/david
git log --stat origin/main..origin/defend/david
git ls-tree -r --name-only origin/defend/david .github/workflows
git show origin/defend/david:.github/workflows/security-audit.yml
gh pr list --repo anTuni/fornerds_study_session4 --base defend/david --state all --json number,title,url,state,author,headRefName,baseRefName,createdAt,updatedAt,mergedAt,mergeStateStatus,isDraft
gh pr view <number> --repo anTuni/fornerds_study_session4 --json number,title,url,state,author,headRefName,baseRefName,body,commits,files,comments,mergeStateStatus,reviewDecision
gh pr checks <number> --repo anTuni/fornerds_study_session4 --json name,state,workflow,link,startedAt,completedAt
gh pr diff <number> --repo anTuni/fornerds_study_session4
gh api repos/anTuni/fornerds_study_session4/branches/defend/david/protection
```
