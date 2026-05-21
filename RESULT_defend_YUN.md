# 보안감사 실습 결과 보고서

## 1. 방어 브랜치 기본 정보

| 항목 | 내용 |
|------|------|
| 작성 기준 브랜치 | defend/YUN |
| 수비자 | KANGPUNGYUN |
| 페어 | 확인 필요 |
| 작성일 | 2026-05-21 |
| 실습 저장소 | https://github.com/anTuni/fornerds_study_session4 |
| 결과 문서 작성자 | KANGPUNGYUN |
| 관련 최종 PR 또는 공유 링크 | PR #2, PR #11, PR #19 |

---

## 2. 방어 브랜치 이력 요약

| 순서 | Commit | 작성자 | 메시지 | 주요 변경 내용 |
|------|--------|--------|--------|----------------|
| 1 | e7c6cb8 | KANGPUNGYUN | Add security audit pipeline for defend/YUN branch | security-audit.yml 신규 작성. 6개 Job 구성: secret-scan(Gitleaks), custom-scan(scan.py), dependency-scan(OWASP Dep Check + npm audit), report(PR 코멘트 자동 게시), admin-gate, security-gate. checklist.md / infra-patterns.md / scan.py 보안 정책 파일 포함 |
| 2 | 88a4905 | KANGPUNGYUN | Replace environment-based admin gate with Branch Protection | admin-gate(environment: security-review) 제거. security-gate 단순화: has_blockers=true 시 exit 1로 머지 차단. Branch Protection Rules(Required status check + Require approvals)로 동일 효과 위임 |

---

## 3. 방어자가 만든 보안감사 Workflow 요약

| 항목 | 내용 |
|------|------|
| workflow 파일 경로 | .github/workflows/security-audit.yml |
| workflow 이름 | Security Audit (defend/YUN) |
| 실행 트리거 | pull_request to defend/YUN |
| 대상 방어 브랜치 | defend/YUN |
| 사용한 도구 | Gitleaks, scan.py(커스텀 regex), OWASP Dependency-Check(CVSS 7+), npm audit, security_report.py |
| 보고서 생성 방식 | security_report.py 실행 후 PR 코멘트 자동 게시 + scan-results.json artifact 업로드 |
| 실패 기준 | custom-scan에서 critical 또는 high 발견 시 has_blockers=true, security-gate에서 exit 1 |
| PR 차단 방식 | security-gate job 실패(exit 1). Branch Protection의 Required status check "🚦 Security Gate"로 실질 머지 차단 |
| required status check 이름 | 🚦 Security Gate |
| 평균 실행 시간 | 확인 필요 |
| 가장 느린 단계 | 확인 필요 (dependency-scan의 OWASP Dependency-Check가 Maven 빌드 포함으로 가장 느릴 것으로 추정) |

**Workflow 핵심 설정**

```yaml
on:
  pull_request:
    branches:
      - defend/YUN
```

**Workflow 설계 의도**

4단계 방어 파이프라인을 구성했다. (1) Gitleaks로 시크릿/자격증명 git 커밋 탐지, (2) scan.py로 OWASP Top 10 관련 커스텀 regex 패턴 스캔, (3) OWASP Dependency-Check(CVSS 7 이상) 및 npm audit으로 알려진 취약 의존성 탐지, (4) security_report.py로 결과를 집계해 PR 코멘트에 자동 게시. 마지막으로 security-gate job이 has_blockers=true 시 exit 1로 실패해 Branch Protection Required status check를 통해 머지를 차단하는 구조다. admin-gate(환경 승인)는 복잡도가 높아 Branch Protection의 Require approvals(1명 이상)로 대체했다.

---

## 4. 방어 브랜치로 들어온 공격 PR 목록

| PR | 공격 브랜치 | 공격자 | 상태 | 취약점 유형 | 최종 check 결과 | 머지 차단 여부 |
|----|------------|--------|------|-------------|-----------------|----------------|
| #2 | attack/david | handevmin | OPEN | A03 SQL Injection (createNativeQuery 문자열 연결) | 진행 중 (dependency-scan pending) | 확인 필요 (security-gate 미실행) |
| #11 | attack/sabo | player397 | OPEN | A01/A02/A03/A05/A06/A07/A08/A09/A10/Secrets 복합 | 대부분 FAILURE (security-gate 포함) | 차단됨 (security-gate FAILURE) |
| #19 | attack/Brit | Brit-juho | OPEN | A01 Broken Access Control (소유자 검증 제거), A10 SSRF (UrlPreviewController) | 미실행 (merge conflict) | 차단 안 됨 (workflow 미실행, DIRTY 상태) |

---

## 5. 공격/수비 사이클 기록

### Cycle 1

| 항목 | 내용 |
|------|------|
| base 브랜치 | defend/YUN |
| 공격 브랜치 | attack/david |
| PR 링크 | https://github.com/anTuni/fornerds_study_session4/pull/2 |
| 공격자 | handevmin |
| 수비자 | KANGPUNGYUN |
| 취약점 유형 | A03 Injection - SQL Injection |
| 공격 commit | 7881dfed (Improve content search with native SQL for case-insensitive matching) |
| 수정 파일 | cicd_practice/backend/src/main/java/com/example/cicdpractice/content/ContentRepository.java |
| 취약점 설명 | ContentRepository.searchPublished()를 안전한 JPQL 파라미터 바인딩에서 native SQL 문자열 연결 방식으로 교체. 사용자 입력(keyword)이 SQL에 직접 삽입되어 UNION-based SQL Injection이 가능해짐. 공개 검색 엔드포인트(인증 불필요)를 통해 전체 users 테이블(이메일, 비밀번호 해시)이 노출될 수 있음 |
| 기대 탐지 결과 | custom-scan(scan.py)의 createNativeQuery 패턴 탐지 또는 dependency-scan OWASP check에서 발견 기대 |

**실행 결과**

| 점검 항목 | 결과 |
|-----------|------|
| workflow 실행 여부 | 실행됨 (run #26226542524) |
| 실행된 workflow 이름 | Security Audit (defend/YUN) |
| 실행된 check 이름 | 🔑 Secret Scanning (Gitleaks), 🔍 Custom Security Scan (scan.py), 📦 Dependency Vulnerability Scan |
| 취약점 탐지 여부 | 확인 필요 (dependency-scan 진행 중, report/security-gate 미실행) |
| 보고서 생성 여부 | 확인 필요 (report job 미실행) |
| PR 댓글 여부 | 없음 (bot 댓글 없음, 공격자 handevmin이 직접 공격 공개 댓글 작성) |
| artifact 업로드 여부 | 확인 필요 (dependency-scan pending으로 인해 report job 미도달) |
| job 실패 여부 | 없음 (Secret Scanning: SUCCESS, Custom Scan: SUCCESS, Dependency Scan: pending) |
| PR 머지 차단 여부 | 확인 필요 (security-gate 미실행) |
| 실행 시간 | Secret Scanning: 6s, Custom Scan: 19s, Dependency Scan: 진행 중 |
| Actions run 링크 | https://github.com/anTuni/fornerds_study_session4/actions/runs/26226542524 |

**탐지 결과 요약**

탐지된 파일/라인: 확인 필요 (dependency-scan 미완료로 report job 미실행)

탐지 메시지: 확인 필요

보고서 또는 PR 댓글 요약: bot 자동 댓글 없음. 공격자(handevmin)가 직접 "공격 공개" 댓글을 남겨 A03 SQL Injection 시나리오를 설명함. Custom Scan은 SUCCESS이지만 SQL Injection 패턴(createNativeQuery 문자열 연결)이 탐지됐는지는 artifact 미확인으로 판단 불가.

**Cycle 1 이후 방어 개선**

| Commit | 개선 내용 | 개선 이유 |
|--------|-----------|-----------|
| 88a4905 | admin-gate 제거, security-gate 단순화(exit 1), Branch Protection 위임 | environment 기반 관리자 승인이 복잡해 Branch Protection Required status check + Require approvals로 동일 효과를 더 간단하게 구현 |

---

### Cycle 2

| 항목 | 내용 |
|------|------|
| base 브랜치 | defend/YUN |
| 공격 브랜치 | attack/sabo |
| PR 링크 | https://github.com/anTuni/fornerds_study_session4/pull/11 |
| 공격자 | player397 |
| 수비자 | KANGPUNGYUN |
| 취약점 유형 | A01 Broken Access Control, A02 Cryptographic Failures, A03 SQL Injection + XSS, A05 Security Misconfiguration, A06 Vulnerable Components, A07 Authentication Failures, A08 Software/Data Integrity, A09 Logging Failures, A10 SSRF, Hardcoded Secrets |
| 공격 commit | d949b07a (Add intentionally vulnerable changes for attack/sabo) |
| 수정 파일 | pom.xml, AuthService.java, SecurityConfig.java, ContentController.java, ContentRepository.java, UrlPreviewController.java, application.yml, index.html, package.json, App.tsx |
| 취약점 설명 | OWASP Top 10 전체를 망라한 복합 공격. log4j-core 2.14.1(Log4Shell), NoOpPasswordEncoder, CSRF disable, CORS *(allowCredentials), dangerouslySetInnerHTML, 평문 토큰 로그, 외부 URL fetch(SSRF), SRI 없는 외부 스크립트 등 다수 취약점 동시 삽입 |
| 기대 탐지 결과 | Gitleaks(하드코딩 시크릿), Semgrep(XSS/SQLi/SSRF/Logging), OWASP Dep Check(log4j-core 등), npm audit(lodash/axios/minimist) |

**실행 결과**

| 점검 항목 | 결과 |
|-----------|------|
| workflow 실행 여부 | 실행됨 (복수 runs: #26226747307, #26226756308, #26226771846, #26226786161 등) |
| 실행된 workflow 이름 | Security Audit (defend/YUN) |
| 실행된 check 이름 | 🔑 Secret Scanning, 🔍 Custom Security Scan, 📦 Dependency Vulnerability Scan, Security audit gate, SAST - Semgrep, Backend - OWASP Dependency Check, Frontend - npm audit, Trivy - Filesystem Scan, Aggregate Security Report 등 다수 |
| 취약점 탐지 여부 | 탐지됨 (다수 check FAILURE) |
| 보고서 생성 여부 | 생성됨 (Aggregate Security Report job 실행, FAILURE) |
| PR 댓글 여부 | 확인 필요 (bot 자동 댓글 미확인) |
| artifact 업로드 여부 | 확인 필요 |
| job 실패 여부 | FAILURE: Secret Scanning, Backend - Maven test, Frontend - npm audit, SAST - Semgrep, OWASP Dependency Check, Trivy, Aggregate Security Report, Security audit gate, CodeQL, Semgrep OSS |
| PR 머지 차단 여부 | 차단됨 (Security audit gate FAILURE) |
| 실행 시간 | Secret Scanning: 10-12s, Custom Scan: 11s, SAST Semgrep: 13-19s, OWASP Dep Check: 27s, Security audit gate: 28s |
| Actions run 링크 | https://github.com/anTuni/fornerds_study_session4/actions/runs/26226786161 (security-gate) |

**탐지 결과 요약**

탐지된 파일/라인: pom.xml(log4j-core 2.14.1 등 취약 의존성), application.yml(하드코딩 시크릿), SecurityConfig.java(CSRF disable/CORS), App.tsx(dangerouslySetInnerHTML), ContentRepository.java(native SQL), package.json(lodash 4.17.4 등)

탐지 메시지: Gitleaks가 application.yml의 하드코딩 시크릿 탐지(FAILURE). SAST Semgrep이 XSS/SQLi/SSRF/Logging 패턴 탐지(FAILURE). OWASP Dependency-Check가 log4j-core 2.14.1(Log4Shell CVE-2021-44228 CVSS 10.0) 등 CVSS 7 이상 취약 의존성 탐지(FAILURE). npm audit이 lodash/minimist/axios 고위험 취약점 탐지(FAILURE). Trivy가 filesystem/config 스캔에서 추가 탐지(FAILURE).

보고서 또는 PR 댓글 요약: Aggregate Security Report job이 FAILURE로 종료. security-gate가 FAILURE로 PR 머지 차단. SAST - CodeQL(Java)과 SAST - CodeQL(JavaScript/TypeScript)은 SUCCESS.

**Cycle 2 이후 방어 개선**

| Commit | 개선 내용 | 개선 이유 |
|--------|-----------|-----------|
| 해당 없음 | - | - |

---

### Cycle 3

| 항목 | 내용 |
|------|------|
| base 브랜치 | defend/YUN |
| 공격 브랜치 | attack/Brit |
| PR 링크 | https://github.com/anTuni/fornerds_study_session4/pull/19 |
| 공격자 | Brit-juho |
| 수비자 | KANGPUNGYUN |
| 취약점 유형 | A01 Broken Access Control (소유자 검증 제거, UserController /me 권한 상승), A10 SSRF (UrlPreviewController - 관리자 권한 필요하나 임의 URL fetch) |
| 공격 commit | c5a59ac0 (refactor: simplify content update flow), ee5b4041 (feat: add admin URL preview endpoint), f675995a (refactor: unify user update DTO) |
| 수정 파일 | ContentController.java (assertCanEdit 제거), UrlPreviewController.java (신규, SSRF), UserController.java (/me PUT 추가), UserAccount.java (updateProfile 추가) |
| 취약점 설명 | ContentController.update()에서 assertCanEdit() 호출 제거로 소유자 검증 없이 타인 콘텐츠 수정 가능(A01). /me 엔드포인트에서 role/active 필드도 클라이언트가 직접 변경 가능해 권한 상승 가능(A01). UrlPreviewController는 @PreAuthorize("hasRole('ADMIN')")가 있으나 임의 URL fetch로 내부망 탐지에 악용 가능(A10 SSRF). |
| 기대 탐지 결과 | custom-scan(scan.py)의 assertCanEdit 제거 패턴이나 SSRF 관련 규칙 탐지 기대 |

**실행 결과**

| 점검 항목 | 결과 |
|-----------|------|
| workflow 실행 여부 | 미실행 (merge conflict - DIRTY 상태) |
| 실행된 workflow 이름 | - |
| 실행된 check 이름 | - |
| 취약점 탐지 여부 | 미탐지 (workflow 미실행) |
| 보고서 생성 여부 | 미생성 |
| PR 댓글 여부 | 없음 |
| artifact 업로드 여부 | 없음 |
| job 실패 여부 | 해당 없음 |
| PR 머지 차단 여부 | merge conflict으로 DIRTY 상태, 기술적으로 머지 불가 |
| 실행 시간 | - |
| Actions run 링크 | - |

**탐지 결과 요약**

탐지된 파일/라인: 없음 (workflow 미실행)

탐지 메시지: 없음

보고서 또는 PR 댓글 요약: PR #19는 merge conflict(DIRTY)으로 workflow가 한 번도 실행되지 않았음. no checks reported 확인. 공격 내용은 diff 분석으로 파악됨.

**Cycle 3 이후 방어 개선**

| Commit | 개선 내용 | 개선 이유 |
|--------|-----------|-----------|
| 해당 없음 | - | - |

---

## 6. 탐지 성공 사례

| 취약점 유형 | 탐지 도구 또는 규칙 | 탐지 파일 | 왜 잘 탐지됐는가 |
|------------|--------------------|-----------|--------------------|
| A06 Vulnerable Components (Log4Shell CVE-2021-44228) | OWASP Dependency-Check (CVSS 7+) | pom.xml (log4j-core 2.14.1) | CVSS 10.0으로 임계값 7을 크게 초과. Dependency-Check의 NVD 데이터베이스에 등록된 CVE여서 명확히 검출됨 |
| A06 Vulnerable Components (npm) | npm audit | package.json (lodash 4.17.4, minimist 1.2.0, axios 0.21.0) | npm audit이 공개 취약점 DB 기반으로 패키지 버전을 정확히 매칭함 |
| Hardcoded Secrets | Gitleaks | application.yml | Gitleaks의 사전 정의 규칙(AWS/GitHub/JWT 패턴)으로 커밋 이력 스캔 시 즉시 탐지 |
| A03 XSS + SQL Injection, A09 Logging Failures, A10 SSRF | SAST Semgrep (OWASP Top 10) | App.tsx, ContentRepository.java, 다수 | Semgrep OWASP Top 10 룰셋이 dangerouslySetInnerHTML, createNativeQuery 문자열 연결, 토큰 로그 출력, URL fetch 패턴을 직접 매칭 |

---

## 7. 탐지 실패 또는 오탐 사례

| 유형 | PR 또는 파일 | 원인 분석 | 다음 개선안 |
|------|------------|-----------|------------|
| 미탐 | PR #2 (attack/david) - SQL Injection | dependency-scan이 장시간 pending 상태로 report/security-gate job이 실행되지 않아 최종 차단 여부 미결 | dependency-scan에 타임아웃 설정 추가. 또는 custom-scan 단독으로도 security-gate가 실행되도록 needs 조건 조정 |
| 미탐 | PR #19 (attack/Brit) - A01/A10 | merge conflict(DIRTY)으로 workflow 자체가 미실행됨. 소유자 검증 제거, 권한 상승 가능한 /me 엔드포인트는 regex 탐지가 어려움 | assertCanEdit 제거, role/active 직접 수정 허용 패턴 등 A01 탐지 규칙 scan.py에 추가. merge conflict 발생 시 별도 안내 메시지 추가 |
| 미탐 | PR #11 attack/sabo - A07 Authentication Failures (토큰 만료 검증 제거) | 공격자가 PR 설명에서 "룰 보강 시"라고 명시. scan.py에 토큰 만료 검증 제거 패턴 부재 | AuthService의 isTokenExpired / expiry check 삭제 패턴을 scan.py 규칙에 추가 |
| 오탐 | 확인 필요 | - | - |

---

## 8. PR 차단 검증

| 항목 | 결과 |
|------|------|
| branch protection 설정 여부 | 미설정 (GitHub API 404 응답) |
| required status check 이름 | 🚦 Security Gate (workflow에 명시되어 있으나 Branch Protection에 미등록) |
| 실패한 check 이름 | Security audit gate (PR #11), 🔑 Secret Scanning, Frontend - npm audit, SAST - Semgrep 등 다수 (PR #11) |
| PR 상태 | PR #2: OPEN(UNSTABLE), PR #11: OPEN(UNSTABLE), PR #19: OPEN(DIRTY) |
| 실제 머지 버튼 상태 | 확인 필요 |
| 차단이 안 됐다면 이유 | Branch Protection이 미설정된 상태. security-gate job이 FAILURE여도 Branch Protection Required status check가 없으면 GitHub UI에서 실제 머지가 가능할 수 있음. PR #19는 merge conflict으로 workflow가 아예 실행되지 않음 |

정리:
- workflow가 실패해도 branch protection이 없으면 실제 머지는 가능할 수 있다.
- PR을 확실히 막으려면 required status check 설정이 필요하다.
- 현재 defend/YUN 브랜치에는 branch protection이 설정되어 있지 않으므로, security-gate가 실패해도 GitHub UI 상으로는 머지 가능 상태일 수 있다.

---

## 9. Lesson Learned

**기술적으로 배운 점**

- Gitleaks, OWASP Dependency-Check, Semgrep, npm audit, Trivy를 조합하면 OWASP Top 10의 상당 부분을 자동 탐지할 수 있다.
- SQL Injection(createNativeQuery 문자열 연결), 하드코딩 시크릿, 취약 의존성(Log4Shell)처럼 패턴이 명확한 취약점은 자동 탐지 성공률이 높다.
- A01 Broken Access Control처럼 비즈니스 로직과 얽힌 취약점(소유자 검증 로직 제거)은 regex 기반 스캔으로 탐지하기 어렵다.
- dependency-scan이 장시간 실행될 경우 후속 report/security-gate job이 지연되어 차단 타이밍을 놓칠 수 있다.

**workflow 설계에서 배운 점**

- needs 조건을 `if: always()`와 함께 조합하면 일부 job이 실패해도 report job이 반드시 실행되도록 보장할 수 있다.
- admin-gate(environment 승인) 방식은 복잡하고 관리 비용이 크다. Branch Protection의 Required status check + Require approvals 조합이 더 실용적이다.
- scan.py 커스텀 규칙은 범용 도구가 놓치는 프로젝트 특화 패턴을 보완할 수 있다.
- merge conflict(DIRTY) 상태의 PR은 workflow가 아예 실행되지 않아 보안 사각지대가 된다.

**방어 브랜치 운영에서 배운 점**

- workflow 작성만으로는 충분하지 않다. Branch Protection(Required status check)을 반드시 함께 설정해야 실질적인 머지 차단이 보장된다.
- 공격 PR의 merge conflict는 workflow 회피 수단이 될 수 있다. base 브랜치와의 충돌 여부와 무관하게 보안 검사를 수행하는 방안(예: push 이벤트도 트리거에 추가)을 고려해야 한다.

---

## 10. 표준 보안감사 Workflow 제안

| 우선순위 | 항목 | 포함 여부 | 이유 |
|----------|------|-----------|------|
| 필수 | Backend test | 포함 (dependency-scan job 내 mvn test) | 빌드/테스트 실패 시 취약점 분석 신뢰도 저하 방지 |
| 필수 | Frontend build | 포함 (dependency-scan job 내 npm ci + npm run build) | 빌드 실패 PR은 기능 분석 불가 |
| 필수 | 의존성 취약점 스캔 | 포함 (OWASP Dependency-Check CVSS 7+, npm audit --audit-level=high) | A06 취약 의존성은 탐지 효율이 가장 높음 |
| 필수 | SAST | 포함 (scan.py 커스텀 규칙) | A01/A03/A09/A10 등 코드 패턴 탐지 |
| 권장 | Secret scan | 포함 (Gitleaks) | 시크릿 노출은 즉각적 피해로 이어짐 |
| 권장 | Container 또는 filesystem scan | 부분 포함 (Trivy - PR #11 run에서 확인) | OS/패키지 레벨 취약점 추가 탐지 |
| 권장 | PR 댓글 보고서 | 포함 (security_report.py) | 검토자가 별도 로그 없이 PR에서 바로 결과 확인 가능 |
| 권장 | Artifact 업로드 | 포함 (scan-results.json) | 감사 추적 및 재검토 목적 |
| 필수 | Required status check | 미설정 (Branch Protection 404) | workflow 실패만으로는 머지 차단 불가. GitHub Branch Protection 설정 필수 |

**제안하는 실패 기준**
- Critical: 즉시 job 실패, 머지 차단 (Gitleaks 시크릿 탐지, CVSS 9.0+, scan.py critical)
- High: job 실패, 머지 차단 (CVSS 7.0-8.9, scan.py high, npm audit high)
- Medium: warning으로 보고, 머지는 허용하되 PR 코멘트에 명시
- Low: 정보성 보고만 수행

**제안하는 보고서 형식**
- PR 댓글에 포함할 내용: 탐지된 취약점 목록(유형/파일/라인/심각도), 통과/실패 체크리스트, 수정 권장 사항 요약
- Artifact로 남길 내용: 전체 스캔 JSON 결과(scan-results.json), OWASP Dependency-Check HTML 리포트
- 팀 회고에서 공유할 내용: 탐지된 취약점 유형 분류, 미탐/오탐 사례, 스캔 도구별 효과 비교

---

## 11. 최종 결론

| 항목 | 판단 |
|------|------|
| 표준 workflow로 채택 가능 여부 | 조건부 채택 가능. Branch Protection 설정 후 채택 권장 |
| 바로 적용 가능한 부분 | Gitleaks + scan.py + OWASP Dependency-Check + npm audit 조합, PR 코멘트 자동 보고, security-gate exit 1 패턴 |
| 추가 실험이 필요한 부분 | Branch Protection Required status check 실제 적용 및 머지 차단 검증, dependency-scan 타임아웃 처리, A01 Broken Access Control 탐지 규칙 보강, merge conflict PR 대응 방안 |
| 다음 액션 | (1) GitHub Branch Protection에 "🚦 Security Gate"를 Required status check로 등록, (2) scan.py에 소유자 검증 제거 패턴 및 role/active 직접 수정 허용 패턴 추가, (3) dependency-scan에 타임아웃 설정, (4) push 이벤트도 workflow 트리거에 추가 검토 |

최종 의견:

defend/YUN의 security-audit workflow는 4개 스캔 도구(Gitleaks, scan.py, OWASP Dependency-Check, npm audit)를 조합하고 PR 코멘트 자동 보고와 security-gate 차단 패턴을 포함하는 견고한 구조다. OWASP Top 10 복합 공격(PR #11)에 대해 다수의 check가 정상적으로 FAILURE를 반환했다. 다만 Branch Protection이 미설정된 상태로, workflow 실패가 실질적인 머지 차단으로 이어지지 않을 수 있다. 또한 merge conflict 상태의 PR은 workflow가 아예 실행되지 않는 사각지대가 있다. Branch Protection 등록과 A01 탐지 규칙 보강이 가장 시급한 개선 과제다.

---

## 부록: 조회 명령어

```bash
# 저장소 상태 확인
git status --short
git remote -v

# 브랜치 확인
git fetch origin
git branch -a --list '*defend/YUN*'

# commit 이력 조회
git log --oneline --decorate origin/main..origin/defend/YUN
git log --stat origin/main..origin/defend/YUN
git log --format="%H %ae %an %s" origin/main..origin/defend/YUN

# workflow 파일 확인
git show origin/defend/YUN:.github/workflows/security-audit.yml
git show origin/defend/YUN:scan.py
git show origin/defend/YUN:checklist.md

# 방어 브랜치 대상 PR 목록 조회
gh pr list --base defend/YUN --state all --json number,title,url,state,author,headRefName,baseRefName,createdAt,updatedAt,mergedAt,mergeStateStatus,isDraft

# 각 PR 상세 조회
gh pr view 2 --json number,title,url,state,author,headRefName,baseRefName,body,commits,files,comments,statusCheckRollup,mergeStateStatus,reviewDecision
gh pr view 11 --json number,title,url,state,author,headRefName,baseRefName,body,commits,files,comments,statusCheckRollup,mergeStateStatus,reviewDecision
gh pr view 19 --json number,title,url,state,author,headRefName,baseRefName,body,commits,files,comments,statusCheckRollup,mergeStateStatus,reviewDecision

# PR diff 확인
gh pr diff 2
gh pr diff 19

# PR check 상태 조회
gh pr checks 2
gh pr checks 11
gh pr checks 19

# PR 댓글 조회
gh pr view 2 --json comments
gh api repos/anTuni/fornerds_study_session4/issues/2/comments --jq '.[] | {login: .user.login, created_at, body: .body[:1000]}'
gh api repos/anTuni/fornerds_study_session4/issues/11/comments --jq '.[] | {author: .user.login, body: .body[:800]}'

# Actions run 상세 조회
gh api repos/anTuni/fornerds_study_session4/actions/runs/26226542524
gh api repos/anTuni/fornerds_study_session4/actions/runs/26226542524/jobs --jq '.jobs[] | {name, conclusion, started_at, completed_at}'
gh api repos/anTuni/fornerds_study_session4/check-runs/77175020008 --jq '{name, conclusion, output: .output}'
gh api repos/anTuni/fornerds_study_session4/check-runs/77175858314 --jq '{name, conclusion, output: .output}'

# branch protection 확인
gh api repos/anTuni/fornerds_study_session4/branches/defend%2FYUN/protection
```
