# 보안감사 실습 종합 결과

작성일: 2026-05-30

이 문서는 main 브랜치에 병합된 `RESULT_*.md` 결과와 각 `defend/*` 브랜치의 workflow를 참고해 팀 표준 보안 CI를 도출한 종합본입니다.

## 1. 집계 대상

| 방어 브랜치 | 결과 파일 | main 반영 여부 | 공격 PR 수 | workflow 핵심 도구 |
| --- | --- | --- | --- | --- |
| `defend/Brit` | `RESULT_Brit.md` | 반영 | 2 | Maven test, OWASP Dependency-Check, npm audit, Semgrep, Trivy, Gitleaks, CodeQL, Snyk |
| `defend/YUN` | `RESULT_YUN.md` | 반영 | 3 | Maven test, OWASP Dependency-Check, npm audit, Gitleaks, custom scan.py |
| `defend/david` | `RESULT_david.md` | 반영 | 5 | Maven test, OWASP Dependency-Check, npm audit, Semgrep, CodeQL, Gitleaks, Trivy |
| `defend/sabo` | `RESULT_sabo.md` | 반영 | 2 | Maven test, OWASP Dependency-Check, npm audit, Semgrep, Trivy, Gitleaks |
| `defend/tuni` | `RESULT_tuni.md` | 반영 | 3 | Maven test, OWASP Dependency-Check, npm audit, Semgrep, Trivy |
| `defend/tuni1` | `RESULT_tuni1.md` | 반영 | 2 | Maven test, OWASP Dependency-Check, npm audit |
| `defend/당근` | `RESULT_당근.md` | 반영 | 3 | Maven test, OWASP Dependency-Check, npm audit, Semgrep, Gitleaks |

참고: 표준 workflow 설계에는 main의 결과 파일과 `origin/defend/*` workflow를 함께 참고했습니다.

## 2. 반복 탐지된 취약점 유형

| OWASP 유형 | 실습에서 반복된 패턴 | 효과적이었던 탐지 방식 |
| --- | --- | --- |
| A01 Broken Access Control | `permitAll`, 소유자 검증 제거, role/active 필드 직접 수정 | Semgrep/CodeQL 일부 탐지, custom rule과 테스트 보강 필요 |
| A02 Cryptographic Failures | `NoOpPasswordEncoder`, MD5, `Random`, 하드코딩된 signing key/token | Gitleaks, Semgrep secrets, custom scan |
| A03 Injection | `createNativeQuery` 문자열 연결, `dangerouslySetInnerHTML`, `Runtime.exec` | Semgrep, CodeQL, custom scan |
| A05 Security Misconfiguration | CSRF disable, wildcard CORS, frame options disable | Semgrep, Trivy config, custom scan |
| A06 Vulnerable Components | log4j, snakeyaml, commons-collections, lodash, minimist, axios | OWASP Dependency-Check, npm audit, Trivy, Snyk |
| A07 Auth Failures | 토큰 만료 검증 제거, 인증 우회 | custom rule과 인증 테스트 필요 |
| A08 Integrity Failures | 외부 CDN script, SRI 없음, `latest` 버전 | custom scan, Semgrep HTML rule 보강 필요 |
| A09 Logging Failures | token/secret/password 로그 출력 | Semgrep, custom scan |
| A10 SSRF | 사용자 입력 URL fetch, preview endpoint | Semgrep/CodeQL 일부 탐지, custom allowlist 테스트 필요 |

## 3. 도구별 결론

| 도구 | 표준 포함 여부 | 이유 |
| --- | --- | --- |
| Backend test | 필수 | 보안 변경이 컴파일/테스트 실패를 유발하는 경우가 많음 |
| Frontend build/lint | 필수 | 취약 의존성 추가와 UI 빌드 깨짐을 동시에 확인 |
| OWASP Dependency-Check | 필수 | Java A06 탐지에 직접적이며 artifact가 명확함 |
| npm audit | 필수 | npm 취약 의존성 high 이상 차단에 효과적 |
| Semgrep | 필수 | A01/A03/A05/A09/A10 패턴 탐지의 중심 |
| Trivy fs/config | 권장 이상 | filesystem, secret, misconfig 보조 탐지와 SARIF 업로드 가능 |
| Gitleaks | 필수 | secret 패턴은 별도 전용 도구가 가장 안정적 |
| CodeQL | 선택 확장 | 효과적이지만 저장소/권한/시간 비용이 있어 표준 기본값에서는 제외하고 확장 옵션으로 둠 |
| Snyk | 선택 확장 | 토큰 기반 도구라 팀 공통 기본 workflow에서는 제외하고, secret 설정 시 별도 추가 |
| Custom OWASP scan | 필수 | 실습에서 드러난 도메인 패턴을 빠르게 보강 가능 |

## 4. PR 차단에서 배운 점

실습 결과에서 가장 큰 차이는 “탐지 성공”과 “실제 머지 차단”이 별개라는 점이었습니다.

| 항목 | 결론 |
| --- | --- |
| workflow 실패 | PR 화면에 실패가 표시되지만, branch protection이 없으면 머지를 항상 막지는 못함 |
| required status check | 최종 gate job 이름을 고정해야 팀원이 설정하기 쉬움 |
| branch protection 재확인 | 2026-05-30 기준 `defend/tuni1`만 `Security audit gate` required check가 확인됨. 나머지 `defend/*`는 API상 branch protection 미설정 |
| 표준 gate 이름 | `Security gate`로 통일 |
| 권장 보호 설정 | main 브랜치에 `Security gate` required, approving review 1명 이상 |

## 5. 표준 workflow 설계

이번 결과를 바탕으로 `.github/workflows/team-security-audit.yml`을 추가했습니다.

핵심 원칙:

- 토큰 없이 실행 가능한 오픈소스 도구를 기본으로 둔다.
- 모든 주요 scanner 결과는 artifact로 남긴다.
- SARIF가 있는 도구는 GitHub code scanning에 업로드한다.
- `Security report` job은 `if: always()`로 실패 상황에서도 보고서를 만든다.
- 최종 차단은 단일 required check인 `Security gate`로 통일한다.
- custom scan은 비즈니스 로직성 취약점의 빈틈을 빠르게 보강하는 용도로 둔다.

## 6. 추가된 표준 산출물

| 파일 | 설명 |
| --- | --- |
| `.github/workflows/team-security-audit.yml` | 팀 표준 보안 CI workflow |
| `.github/scripts/security_custom_scan.py` | 실습에서 반복된 OWASP Top 10 패턴을 탐지하는 커스텀 스캐너 |
| `.github/scripts/security_report.py` | job 결과와 커스텀 스캔 결과를 PR 댓글, job summary, artifact로 집계 |
| `skills/team-security-ci/SKILL.md` | Codex가 다른 프로젝트에 표준 보안 CI를 맞춰 추가하는 Skill |
| `TEAM_SECURITY_CI_GUIDE.md` | 팀 공유 및 사용 방법 |

## 7. 권장 실패 기준

| Severity | 처리 |
| --- | --- |
| Critical | 항상 실패, 머지 차단 |
| High | 기본 실패, 예외는 리뷰 승인 필요 |
| Medium | 보고서 기록 및 리뷰 필수 |
| Low | 보고서 기록 |

## 8. 운영 체크리스트

- `.github/workflows/team-security-audit.yml`의 `env` 경로가 프로젝트 구조와 맞는지 확인한다.
- `Security gate`를 main branch required status check로 등록한다.
- `NVD_API_KEY` secret을 설정하면 Dependency-Check 속도와 안정성이 좋아진다.
- PR 댓글과 artifact가 생성되는지 첫 PR에서 확인한다.
- 미탐/오탐은 `security_custom_scan.py` rule 또는 Semgrep custom rule로 보강한다.
- workflow/job 이름 변경 시 branch protection required check도 함께 갱신한다.

## 9. 최종 제안

팀 표준은 다음 구성을 기본값으로 채택하는 것이 좋습니다.

1. PR마다 `Backend test`, `Frontend build`, `Dependency scan`, `npm audit`, `Semgrep`, `Trivy`, `Gitleaks`, `Custom OWASP scan` 실행
2. 결과를 `Security report`에 모아 PR 댓글과 artifact로 공유
3. `Security gate` 하나를 required status check로 등록해 머지 차단을 단순화
4. CodeQL/Snyk는 팀 저장소 권한과 token 준비 상황에 따라 확장 옵션으로 추가
5. Codex Skill `team-security-ci`로 다른 프로젝트에도 같은 패턴을 반복 적용
