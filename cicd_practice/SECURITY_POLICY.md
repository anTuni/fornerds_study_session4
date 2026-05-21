# 보안 정책 (Security Policy)

이 문서는 `cicd_practice` 저장소의 자동 보안 감사 파이프라인이 따르는 정책을 정의합니다.
PR 단계의 자동 게이트, 운영 단계의 수동 점검, 국내 법령 요건을 통합한 단일 기준점입니다.

- 적용 범위: `defend/Brit` 브랜치를 base로 하는 모든 PR + 정기 수동 점검
- 최종 책임자: 방어 브랜치 소유자 (Brit)
- 최종 갱신: 본 문서가 변경될 때마다 갱신, 변경 사항은 PR로 관리

---

## 1. 심각도 3단계 기준

CVSS v3.x 점수와 도구 자체 등급(critical/high/medium/low)을 함께 사용합니다.
도구가 등급만 제공하는 경우 도구 등급을 우선합니다.

| 단계 | CVSS | 도구 등급 | PR 동작 | 머지 | 알림 | 대응 SLA |
| --- | --- | --- | --- | --- | --- | --- |
| **Critical** | 9.0–10.0 | `critical` | job **fail** | 차단 | GitHub Issue 자동 생성 + PR comment | 즉시 (24h 내 패치 또는 명시 예외) |
| **High** | 7.0–8.9 | `high` | job **fail** | 차단 | PR comment 강조 | 영업일 3일 내 |
| **Medium** | 4.0–6.9 | `medium` | warn (job pass) | 허용 | PR comment 기록 | 다음 스프린트 |
| Low / Info | 0.1–3.9 | `low`, `info` | 기록만 | 허용 | 보고서 표만 기재 | 백로그 관리 |

### 1.1 임계값 적용 위치

- **Snyk**: `--severity-threshold=high` (high 이상 발견 시 비-제로 exit)
- **OWASP Dependency-Check (Maven)**: `failBuildOnCVSS=7.0` (high+ 차단)
- **npm audit**: `--audit-level=high`
- **Semgrep**: 룰셋의 `ERROR` 레벨 → fail, `WARNING` → warn
- **Gitleaks**: 시크릿 1건이라도 발견 시 fail (등급 무관)
- **Trivy**: `--severity=CRITICAL,HIGH --exit-code=1`

### 1.2 예외 처리 (Suppression)

- 단기 예외: PR 설명에 `risk-accept: <CVE-ID> reason: <사유> expires: <YYYY-MM-DD>` 라인 포함
- 장기 예외: `cicd_practice/.security/allowlist.yml` 파일에 명시 (만료일 필수)
- 만료된 예외는 자동으로 fail 처리 (정기 점검에서 검증)

---

## 2. 국내 법령·표준 기반 요구사항

「웹 보안 통합 가이드」 §1.2 정보시스템의 기술적 보호조치 요건과 다음 법령을 반영합니다.

> 개인정보보호법 §29, 시행령 §30 / 정보통신망법 §28 / 전자금융감독규정 §32, §33 / 개인정보의 안전성 확보조치 §5 / 행안부 SW 웹개발보안가이드(2017 개정)

### 2.1 인증 / 비밀번호 (가이드 W1)

| 요구사항 | 기준 | 자동 점검 | 수동 점검 |
| --- | --- | --- | --- |
| 비밀번호 복잡도 | 3조합 8자 이상 또는 2조합 10자 이상 | Semgrep 룰 일부 | ✅ 코드 리뷰 |
| 비밀번호 저장 | SHA-256 이상 단방향 + Salt | Semgrep `weak-hash` | ✅ 구현 검증 |
| 인증 실패 잠금 | 5회 연속 실패 시 차단 | ❌ | ✅ 동적 점검 |
| 비밀번호 변경 주기 | 90일 | ❌ | ✅ 정책 검증 |
| 장기 미사용 잠금 | 90일 미접속 시 잠금 | ❌ | ✅ 정책 검증 |
| 세션 타임아웃 | 30분 권고 | Semgrep 룰 일부 | ✅ 설정 검증 |
| Default 비밀번호 | 최초 로그인 시 변경 강제 | ❌ | ✅ 시드 데이터 점검 |

### 2.2 주입 / 인증 우회 (가이드 W2, W3)

| 분류 | 자동 점검 도구 | 비고 |
| --- | --- | --- |
| W2.1 SQL Injection | Semgrep `formatted-sql-string` + Snyk Code | PreparedStatement 강제 |
| W2.2 CMD Injection | Semgrep `command-injection` | Runtime.exec 사용 최소화 |
| W2.7 XXE | Semgrep `xxe` | DocumentBuilderFactory 설정 점검 |
| W3.1 인증 우회 | Snyk Code + 코드 리뷰 | Server-Side 검증 필수 |
| W3.2 HTTP Response Splitting | Semgrep `http-response-splitting` | CR/LF 필터링 |
| W3.3 Open Redirect | Semgrep `open-redirect` | 화이트리스트 |

### 2.3 파일 / 접근 제어 (가이드 W4, W5)

| 분류 | 자동 점검 | 수동 |
| --- | --- | --- |
| W4.1 파일 업로드 | Semgrep `unrestricted-upload` | ✅ 확장자/MIME/저장경로 |
| W4.2 파일 다운로드 | Semgrep `path-traversal` | ✅ `../` 필터 |
| W5.1 비인증 접근 허용 | ❌ | ✅ Spring Security 설정 검토 |
| W5.2 ACL 미흡 | ❌ | ✅ @PreAuthorize 검증 |

### 2.4 악성 스크립트 (가이드 W6)

| 분류 | 자동 점검 |
| --- | --- |
| W6.1 XSS (Stored/Reflected) | Semgrep `react/xss`, `dom-xss` |
| W6.2 CSRF | Semgrep `csrf-disabled` |

### 2.5 보안 설정 (가이드 W7)

| 분류 | 자동 점검 | 수동 |
| --- | --- | --- |
| W7.1 부적절한 HTTP 메서드 | Semgrep | ✅ |
| W7.2 Directory Listing | ❌ | ✅ 인프라 점검 |
| W7.3 불필요 포트 | ❌ | ✅ 운영 점검 |
| W7.4 관리자 페이지 접근제어 | ❌ | ✅ IP 화이트리스트/VPN/MFA |

### 2.6 정보 노출 (가이드 W8)

| 분류 | 자동 점검 |
| --- | --- |
| W8.1 소스 내 시크릿 | **Gitleaks** + Trivy fs |
| W8.3 서버 정보 노출 | Semgrep `verbose-error` |
| W8.4 부적절한 오류 처리 | Semgrep `stack-trace` |

### 2.7 세션 관리 (가이드 W9)

| 분류 | 자동 점검 | 수동 |
| --- | --- | --- |
| W9.1 Cache-Control | Semgrep | ✅ 응답 헤더 검증 |
| W9.2 세션 타임아웃 | Semgrep | ✅ 30분 설정 |
| W9.3 세션 토큰 강도 | ❌ | ✅ 토큰 엔트로피 |

### 2.8 데이터 암호화 (가이드 W10)

| 분류 | 자동 점검 |
| --- | --- |
| W10.1 평문 전송 | Semgrep `http-uses-insecure` |
| W10.2 취약 알고리즘 | Semgrep `weak-crypto`, `weak-hash` |

### 2.9 SW 패키지 취약점 (가이드 W11) — **자동화 핵심 영역**

| 영역 | 도구 |
| --- | --- |
| Java/Maven SCA | Snyk + OWASP Dependency-Check (보조) |
| npm SCA | Snyk + npm audit (보조) |
| 자동 패치 PR | Dependabot (patch auto-merge) |
| GitHub Actions 버전 | Dependabot |

---

## 3. 자동화 범위와 한계

### 3.1 자동 게이트 가능 영역

- 의존성 취약점 (W11) — Snyk, OWASP DC, npm audit, Trivy
- 소스 시크릿 노출 (W8.1) — Gitleaks
- SAST로 탐지 가능한 코드 패턴 (W2 일부, W3.2, W3.3, W6, W8.3, W10) — Semgrep
- IaC 설정 오류 — 현재 IaC 없음, 향후 Dockerfile/Terraform 추가 시 Trivy config로 확장

### 3.2 자동 점검 불가, 수동 필수

- 인증 실패 횟수 제한 (W1.2)
- 권한 검증 누락 (W5.1, W5.2) — 비즈니스 로직 의존
- 관리자 페이지 접근제어 (W7.4)
- 세션 토큰 엔트로피 (W9.3)
- 비밀번호 정책 운영 (W1.1 일부, 90일 변경)

수동 점검은 **분기 1회** 코드 리뷰 + 운영 점검으로 보완합니다.

---

## 4. 알림 정책

| 트리거 | 채널 | 내용 |
| --- | --- | --- |
| Critical 발견 (PR) | GitHub Issue 자동 생성 + PR comment | CVE/규칙ID, 파일, 권장 조치, 관련 PR 링크 |
| High 발견 (PR) | PR comment | 마크다운 표로 요약 |
| Medium / Low | PR comment, artifact | 보고서 표에 기재 |
| 정기 점검 결과 | (생략 — 정기 cron 미운영) | — |

---

## 5. 보고서 산출물

- `security-report.md` — 모든 도구 결과 통합 마크다운 (artifact + PR comment 본문)
- `snyk-backend.sarif`, `snyk-frontend.sarif`, `semgrep.sarif`, `trivy.sarif` — SARIF (GitHub Security tab 업로드)
- `gitleaks.json`, `owasp-dc-report.html` — 도구 원본 보고서
- 보관 기간: artifact 90일 (GitHub 기본)

---

## 6. 검토 / 갱신

- 본 정책은 `defend/Brit` 브랜치에 PR로만 변경합니다.
- 임계값(§1) 변경 시 사유와 도구 출력 예시를 PR 설명에 포함합니다.
- 가이드 본문 변경 시(W 항목 추가/제거) §2의 매핑표도 같은 PR에서 갱신합니다.
