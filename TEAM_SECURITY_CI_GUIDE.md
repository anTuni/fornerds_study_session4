# Team Security CI 공유 및 사용 가이드

이 문서는 보안감사 실습 결과를 팀 표준 GitHub CI workflow로 공유하고, 각 프로젝트에 적용하는 방법을 정리합니다.

## 공유할 산출물

| 구분 | 파일 | 용도 |
| --- | --- | --- |
| 표준 workflow | `.github/workflows/team-security-audit.yml` | PR마다 테스트, 의존성 취약점, SAST, secret, filesystem/config 스캔을 실행하고 최종 `Security gate`로 차단 |
| 커스텀 스캔 스크립트 | `.github/scripts/security_custom_scan.py` | 실습에서 반복된 OWASP Top 10 패턴을 프로젝트 규칙으로 추가 탐지 |
| 리포트 스크립트 | `.github/scripts/security_report.py` | 각 job 결과와 커스텀 스캔 결과를 `security-report.md`, PR 댓글, job summary로 집계 |
| 적용 Skill | `skills/team-security-ci/SKILL.md` | Codex가 다른 프로젝트 구조를 읽고 표준 workflow와 스크립트를 맞춰 추가할 때 사용하는 절차 |
| 종합 결과 | `RESULT_ALL.md` | 방어 브랜치별 실습 결과와 표준화 근거 |

## 표준 workflow가 하는 일

| Job | 실패 기준 | 산출물 |
| --- | --- | --- |
| `Backend test` | Maven test 실패 | Actions log |
| `Frontend build` | `npm ci`, lint, build 실패 | Actions log |
| `Dependency scan` | OWASP Dependency-Check CVSS `7.0` 이상 | HTML/JSON/SARIF artifact, code scanning |
| `npm audit` | production dependency high 이상 | `npm-audit.json` artifact |
| `Semgrep SAST` | OWASP/Java/JS/TS/React/secret rule finding | SARIF/JSON artifact, code scanning |
| `Trivy fs/config` | critical/high vuln, secret, misconfig | SARIF/JSON artifact, code scanning |
| `Gitleaks` | secret finding | Gitleaks artifact/summary |
| `Custom OWASP scan` | custom high/critical finding | `security-custom-scan.json` artifact |
| `Security report` | 항상 실행 | PR 댓글, job summary, `security-report.md` artifact |
| `Security gate` | report가 blocker를 판단하면 실패 | branch protection required check |

## 이 저장소에서 사용하기

현재 workflow는 이 저장소 구조에 맞춰 기본값이 설정되어 있습니다.

```yaml
PROJECT_ROOT: cicd_practice
BACKEND_DIR: cicd_practice/backend
FRONTEND_DIR: cicd_practice/frontend
JAVA_VERSION: "17"
NODE_VERSION: "20"
```

적용 후 GitHub 저장소 설정에서 다음을 권장합니다.

1. Settings > Branches > Branch protection rule 생성
2. 대상 브랜치: `main`
3. Require status checks 활성화
4. Required status check에 `Security gate` 추가
5. 최소 1명 approving review 요구

## 다른 프로젝트에 적용하기

1. 아래 파일을 대상 프로젝트로 복사합니다.
   - `.github/workflows/team-security-audit.yml`
   - `.github/scripts/security_custom_scan.py`
   - `.github/scripts/security_report.py`
2. 대상 프로젝트 구조에 맞춰 workflow 상단 `env` 값을 수정합니다.
3. Java backend가 없으면 `backend-test`, `dependency-scan` job과 `security-report.needs`의 해당 항목을 제거합니다.
4. Node frontend가 없으면 `frontend-build`, `npm-audit` job과 `security-report.needs`의 해당 항목을 제거합니다.
5. PR을 열어 workflow가 정상 실행되는지 확인합니다.
6. `Security gate`를 required status check로 등록합니다.

## Codex Skill로 적용하기

Codex에게 다음처럼 요청합니다.

```text
team-security-ci skill을 사용해서 이 프로젝트에 팀 표준 보안 CI workflow를 추가해줘.
프로젝트 구조에 맞춰 backend/frontend 경로와 Java/Node 버전을 조정하고,
필요 없는 job은 제거한 뒤 검증까지 해줘.
```

Skill은 다음 기준으로 동작합니다.

- 프로젝트의 `pom.xml`, `build.gradle`, `package.json`, lockfile을 먼저 찾습니다.
- 표준 workflow와 스크립트를 추가합니다.
- `PROJECT_ROOT`, `BACKEND_DIR`, `FRONTEND_DIR`, `JAVA_VERSION`, `NODE_VERSION`를 프로젝트에 맞게 조정합니다.
- Python 스크립트 문법 검증과 커스텀 스캔 dry run을 수행합니다.
- branch protection에서 `Security gate`를 required check로 설정하라고 안내합니다.

## 운영 원칙

- `Security gate` job 이름은 바꾸지 않습니다. branch protection required check 이름과 연결됩니다.
- Critical/High는 기본 차단, Medium은 리뷰 필수, Low는 기록으로 운영합니다.
- 리포트 job은 `if: always()`로 유지해서 실패 상황에서도 PR 댓글과 artifact가 남게 합니다.
- secret으로 보이는 값은 리포트에 직접 쓰지 않습니다.
- Snyk 같은 외부 유료/토큰 기반 도구는 선택 확장으로 두고, 기본 표준은 토큰 없이 실행되는 도구 위주로 유지합니다.

## 확장 후보

- CodeQL을 GitHub Advanced Security 사용 가능 저장소에 추가
- Dependabot과 patch 자동 머지 정책 추가
- Semgrep custom rule 파일 분리
- Trivy ignore 정책과 예외 승인 절차 문서화
- NVD API rate limit 완화를 위한 `NVD_API_KEY` secret 설정
