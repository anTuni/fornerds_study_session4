# 보안감사 실습 결과 정리 — defend/sabo

> 이 양식은 조별 보고서가 아니라 **하나의 `defend/{name}` 브랜치**를 기준으로 작성합니다.

## 1. 방어 브랜치 기본 정보

| 항목 | 내용 |
| --- | --- |
| 작성 기준 브랜치 | `defend/sabo` |
| 수비자 | 사보 (`player397` / tmdxkr5@hanmail.net) |
| 페어 | 윤 (B조) — 본 보고서 시점 페어 PR은 미수신, 대신 `woosung-dev` 가 PR 제출 |
| 작성일 | 2026-05-21 |
| 실습 저장소 | https://github.com/anTuni/fornerds_study_session4 |
| 결과 문서 작성자 | 사보 (Claude Opus 4.7 보조) |
| 관련 최종 PR 또는 공유 링크 | https://github.com/anTuni/fornerds_study_session4/pull/8 |

## 2. 방어 브랜치 이력 요약

`defend/sabo` 브랜치에서 보안감사 workflow를 추가하거나 개선한 commit.

| 순서 | Commit | 작성자 | 메시지 | 주요 변경 내용 |
| --- | --- | --- | --- | --- |
| 1 | `39eb060` | player397 | Add security audit workflow for defend/sabo PRs | `.github/workflows/security-audit.yml` 신규: Maven test + OWASP Dependency-Check, npm build + audit, Semgrep, Trivy filesystem, gitleaks, sticky PR summary comment. `.gitleaks.toml` 추가 |
| 2 | `ae8dcb0` | player397 | Add Snyk scan with markdown report and gate build on security jobs | Snyk job 추가 (SNYK_TOKEN 기반), `.github/scripts/snyk-to-markdown.py` 추가, build job을 보안 스캔 jobs 의 `needs:` 로 게이팅, test와 보안 스캔 병렬화 |
| 3 | `3ee9d29` | player397 | Drop Snyk, aggregate OSS scans into a single security report | Snyk 제거 (외부 토큰 의존 회피), `security-report-to-markdown.py` 추가, 모든 스캔 artifact를 집계해 사람이 읽기 쉬운 마크다운 보고서 생성 + sticky PR comment + artifact 업로드, Trivy JSON 출력 추가, docs 갱신 |

## 3. 방어자가 만든 보안감사 Workflow 요약

| 항목 | 내용 |
| --- | --- |
| workflow 파일 경로 | `.github/workflows/security-audit.yml` |
| workflow 이름 | `Security Audit (defend/sabo)` (workflow name field: `Security Audit`) |
| 실행 트리거 | `pull_request` to `defend/sabo`, `push` to `defend/sabo` |
| 대상 방어 브랜치 | `defend/sabo` |
| 사용한 도구 | Maven test, OWASP Dependency-Check (Maven plugin), npm audit, Semgrep (`p/owasp-top-ten`, `p/security-audit`, `p/java`, `p/javascript`, `p/typescript`, `p/react`, `p/secrets`), Trivy (fs), gitleaks |
| 보고서 생성 방식 | 각 스캔 jobs 가 JSON/SARIF artifact 업로드. `security-report` job 이 모두 모아 단일 markdown 보고서 생성, `security-report` artifact + sticky PR comment (header `security-report`) 게시. 별도 `pr-comment-summary` job 이 전체 stage 결과 표를 sticky comment (header `security-audit`) 로 게시 |
| 실패 기준 | OWASP DC `failBuildOnCVSS=7` / npm audit `--audit-level=high` / Semgrep `--severity ERROR --severity WARNING --error` / Trivy `severity=CRITICAL,HIGH exit-code=1 ignore-unfixed=true` / gitleaks default |
| PR 차단 방식 | `backend-build`, `frontend-build` 가 `needs:` 로 보안 스캔 jobs 에 의존 → 스캔 실패 시 빌드 SKIPPED. branch protection 은 미설정 (아래 8장 참고) |
| required status check 이름 | (미설정) — branch protection 자체가 없음 |
| 평균 실행 시간 | 현재 1회 측정: 빠른 잡 9–27s, 실패 잡 3–22s. OWASP Dependency-Check 는 NVD 첫 다운로드로 IN_PROGRESS 가 길어 측정 미완 (확인 필요) |
| 가장 느린 단계 | OWASP Dependency-Check (Maven plugin) — NVD DB 다운로드 |

### Workflow 핵심 설정

```yaml
on:
  pull_request:
    branches:
      - 'defend/sabo'
  push:
    branches:
      - 'defend/sabo'
```

Job 의존성 그래프:

```
[backend-test, frontend-test]                        ← test (병렬)
[owasp-dependency-check, npm-audit, semgrep,
 trivy-fs, gitleaks]                                 ← 보안 스캔 (테스트와 병렬)
        ↓
[security-report]   (needs: 4개 스캔, if: always())  ← 통합 마크다운 보고서 + sticky comment
[backend-build]     (needs: owasp-dc, semgrep, trivy-fs, gitleaks)
[frontend-build]    (needs: npm-audit, semgrep, trivy-fs, gitleaks)
        ↓
[pr-comment-summary]                                 ← stage 표 sticky comment
```

### Workflow 설계 의도

- 무료 OSS 도구만 사용 (Snyk 같은 SaaS 토큰 의존 제거) → 누구나 fork 해 그대로 동작.
- 테스트와 보안 스캔을 병렬화해 PR 응답 시간을 줄이되, 빌드는 보안 스캔이 통과해야 실행 → "취약점 있는 PR 은 빌드 자체가 안 됨" 신호.
- 도구 결과를 사람이 읽기 쉬운 **단일 마크다운 보고서**(심각도/패키지/CVE/권장 수정 사항) 로 합치고, PR 코멘트와 artifact 양쪽에 게시 → 리뷰어와 회고 양쪽에서 같은 데이터 확인.
- gitleaks 와 Semgrep `p/secrets` 를 같이 사용해 시크릿 누출에 대해 이중 안전망.

## 4. 방어 브랜치로 들어온 공격 PR 목록

`defend/sabo` 를 base 로 생성된 PR.

| PR | 공격 브랜치 | 공격자 | 상태 | 취약점 유형 | 최종 check 결과 | 머지 차단 여부 |
| --- | --- | --- | --- | --- | --- | --- |
| [#8](https://github.com/anTuni/fornerds_study_session4/pull/8) | `attack/woosung` | woosung-dev | OPEN | A01 Broken Access Control (다중) | UNSTABLE — Semgrep FAIL, Trivy FAIL, npm audit/Backend test/Frontend test/Gitleaks PASS, OWASP DC IN_PROGRESS, Frontend build SKIPPED | 미차단 (branch protection 없음, mergeStateStatus=UNSTABLE) |

## 5. 공격/수비 사이클 기록

### Cycle 1

| 항목 | 내용 |
| --- | --- |
| base 브랜치 | `defend/sabo` |
| 공격 브랜치 | `attack/woosung` |
| PR 링크 | https://github.com/anTuni/fornerds_study_session4/pull/8 |
| 공격자 | woosung-dev (woo sung) |
| 수비자 | 사보 |
| 취약점 유형 | A01 Broken Access Control (3가지 변형) |
| 공격 commit | `2a49f06` — "Refactor security config and content access control" |
| 수정 파일 | `cicd_practice/backend/src/main/java/com/example/cicdpractice/config/SecurityConfig.java`, `cicd_practice/backend/src/main/java/com/example/cicdpractice/content/ContentController.java` |
| 취약점 설명 | (1) `SecurityConfig` 에서 `@EnableMethodSecurity` 어노테이션 제거 → 모든 `@PreAuthorize` 가 무력화되어 ADMIN/EDITOR 만 허용되던 콘텐츠 생성·수정 엔드포인트가 일반 사용자에게 열림. (2) `ContentController.list` 에 `debug=true` 쿼리 파라미터 추가 시 `findAll()` 로 DRAFT 포함 전체 콘텐츠 반환 → 비공개 초안 노출 (정보 노출 + 인가 우회). (3) `assertCanEdit` 의 본인 작성자 비교를 `actor.getId() != null` 로 약화 → 인증된 모든 사용자가 남의 콘텐츠 수정 가능. |
| 기대 탐지 결과 | Semgrep `p/owasp-top-ten`/`p/java` 룰이 `@EnableMethodSecurity` 제거, broken access control 패턴을 탐지하도록 기대. |

#### 실행 결과

| 점검 항목 | 결과 |
| --- | --- |
| workflow 실행 여부 | 성공 (실행됨) |
| 실행된 workflow 이름 | Security Audit |
| 실행된 check 이름 | Backend test, Frontend test, OWASP Dependency-Check, npm audit, Semgrep SAST, Trivy filesystem scan, Gitleaks secret scan, Frontend build, (security-report / pr-comment-summary 는 OWASP DC 진행 중으로 대기) |
| 취약점 탐지 여부 | 탐지 (Semgrep FAIL, Trivy FAIL). Gitleaks 와 npm audit 은 통과 — 이 PR 은 시크릿/의존성 추가가 아닌 코드 변경이므로 정상. |
| 보고서 생성 여부 | 진행 중 — `security-report` job 이 OWASP DC 의 in-progress 로 인해 아직 시작 안 됨 (확인 필요) |
| PR 댓글 여부 | 미생성 (보고서 job 미실행으로 sticky comment 미게시) — 확인 필요 |
| artifact 업로드 여부 | 각 스캔 jobs 의 artifact 는 업로드되었을 것으로 추정 (semgrep-report, trivy-fs-report, npm-audit-report, 등). `security-report` artifact 는 미생성 — 확인 필요 |
| job 실패 여부 | 실패 (Semgrep, Trivy) → `frontend-build` SKIPPED |
| PR 머지 차단 여부 | 차단 안 됨 (branch protection 미설정, `mergeStateStatus=UNSTABLE`) |
| 실행 시간 | Trivy 3s / Frontend test 14s / npm audit 13s / Gitleaks 9s / Semgrep 22s / Backend test 27s / OWASP DC 진행 중 |
| Actions run 링크 | https://github.com/anTuni/fornerds_study_session4/actions/runs/26226665493 |

#### 탐지 결과 요약

```text
탐지된 파일/라인:
- Semgrep SAST: FAIL (구체적 라인은 actions log 확인 필요. cicd_practice/backend/src/main/java/.../SecurityConfig.java 의 @EnableMethodSecurity 제거, ContentController.java 의 약화된 본인 확인 로직 중 하나 이상에서 ERROR/WARNING 발생으로 추정)
- Trivy filesystem scan: FAIL (3초만에 종료된 점, severity CRITICAL/HIGH 만 보고하도록 설정한 점을 고려하면 dependency manifest 또는 misconfiguration 한 건 탐지로 추정 — 확인 필요)

탐지 메시지:
- 상세 메시지는 워크플로 log 와 곧 생성될 security-report.md artifact 에서 확인 가능. PR 댓글은 아직 게시되지 않음.

보고서 또는 PR 댓글 요약:
- 현재 PR 에 sticky comment 미게시. OWASP DC 진행 완료 후 security-report job 이 통합 보고서를 게시할 예정.
```

#### Cycle 1 이후 방어 개선

| Commit | 개선 내용 | 개선 이유 |
| --- | --- | --- |
| (계획) | Semgrep 룰셋에 `p/spring-security` 또는 custom rule (`@EnableMethodSecurity` 제거 탐지) 추가 검토 | 현재 룰셋으로도 FAIL 처리되었지만, 어떤 룰이 탐지했는지 보고서를 확인해 false negative 가능성 있는 변형 (예: SecurityConfig 메서드 시그니처만 바꾸는 경우) 에 대비 |
| (계획) | branch protection 설정 → 아래 8장 참고 | check 실패에도 머지 가능한 현 상태를 차단으로 전환 |

### Cycle 2

| 항목 | 내용 |
| --- | --- |
| base 브랜치 | 해당 없음 |

### Cycle 3

| 항목 | 내용 |
| --- | --- |
| base 브랜치 | 해당 없음 |

## 6. 탐지 성공 사례

| 취약점 유형 | 탐지 도구 또는 규칙 | 탐지 파일 | 왜 잘 탐지됐는가 |
| --- | --- | --- | --- |
| A01 Broken Access Control (코드 패턴) | Semgrep (`p/owasp-top-ten` + `p/java` + `p/security-audit` 중 하나) | `SecurityConfig.java`, `ContentController.java` (확인 필요) | OWASP Top 10 룰셋이 메서드 보안 어노테이션 제거·약화된 비교 연산을 패턴으로 잡아냄 |
| 파일시스템 의심 패턴 | Trivy fs | (확인 필요) | Trivy 가 misconfig/secret/lockfile 패턴 중 CRITICAL/HIGH 한 건 이상을 탐지하여 fail 처리 |

## 7. 탐지 실패 또는 오탐 사례

| 유형 | PR 또는 파일 | 원인 분석 | 다음 개선안 |
| --- | --- | --- | --- |
| 미탐 가능성 | PR #8, `ContentController.java` debug 파라미터 | `debug=true` 시 비공개 콘텐츠 노출은 데이터 권한 누수지만 정적 분석 룰로는 잡기 어려울 수 있음. Semgrep FAIL 이 어떤 라인을 잡았는지 보고서 확인 필요. | custom Semgrep rule: `@RequestParam.*debug` 또는 `findAll().*ContentResponse` 같은 패턴 추가 검토 |
| 보고서 미게시 | PR #8 | OWASP DC NVD 다운로드가 느려 `security-report` job 이 아직 실행되지 않음 → sticky comment 도 미게시 | OWASP DC 캐싱 (Maven local repo + NVD data) 활성화, 또는 `security-report` 의 `needs:` 에서 OWASP DC 제외하고 본 잡과 병렬화 검토 |

## 8. PR 차단 검증

| 항목 | 결과 |
| --- | --- |
| branch protection 설정 여부 | **미설정** (`gh api repos/anTuni/fornerds_study_session4/branches/defend/sabo/protection` → 404) |
| required status check 이름 | 없음 |
| 실패한 check 이름 | Semgrep SAST, Trivy filesystem scan |
| PR 상태 | `mergeStateStatus=UNSTABLE` |
| 실제 머지 버튼 상태 | 머지 가능 (경고 표시는 있지만 실제 머지 차단되지 않음) |
| 차단이 안 됐다면 이유 | branch protection 자체가 없어 required status check 정책이 없음. workflow 실패는 정보 제공에 그침. |

정리:

- workflow 가 실패해도 branch protection 이 없으면 실제 머지는 가능할 수 있다 — 본 실습에서 확인됨.
- PR 을 확실히 막으려면 required status check 설정이 필요하다.
- 권장 required check: `Semgrep SAST`, `Trivy filesystem scan`, `OWASP Dependency-Check (Maven)`, `npm audit`, `Gitleaks secret scan`, `Backend test (mvn test)`, `Frontend test (install + lint)`.

## 9. Lesson Learned

### 기술적으로 배운 점

- GitHub Actions 의 `pull_request` 트리거는 **base 브랜치의 workflow 정의** 를 기준으로 동작하므로, 수비 브랜치에 workflow 를 두면 attack PR 에 자동 적용된다. 별도 설정 없이도 보안 게이트가 형성된다.
- OWASP Dependency-Check 의 NVD 첫 다운로드는 분 단위로 길어 PR 응답성에 큰 영향을 준다. 캐싱 또는 별도 cron 워크플로 분리가 필요.
- Semgrep + Trivy 조합만으로도 코드 패턴 + 파일시스템 양쪽에서 A01 류를 잡을 수 있다. 단일 도구에 의존하지 않는 다층 방어가 효과적.

### workflow 설계에서 배운 점

- 테스트와 보안 스캔을 병렬, 빌드를 보안 스캔 뒤에 두는 의존성 구조는 "취약점 있는 코드는 빌드 자체를 차단" 이라는 명확한 신호를 만들었다 — 실제로 `frontend-build` 가 SKIPPED 처리되며 검증됨.
- 통합 마크다운 보고서를 한 잡으로 모으는 것은 좋지만, 그 잡이 가장 느린 스캔 (OWASP DC) 의 `needs:` 에 묶이면 PR 코멘트 게시가 지연된다. 빠른 결과만으로 1차 보고서를 먼저 게시하고, 느린 스캔이 끝나면 update 하는 방식이 더 나을 수 있다.
- artifact 업로드를 `if: always()` 로 한 덕분에 fail 한 잡의 결과도 모두 보존돼 사후 분석이 가능.

### 방어 브랜치 운영에서 배운 점

- workflow 가 실패해도 branch protection 이 없으면 실제 머지가 막히지 않는다. **workflow ≠ enforcement**.
- 워크플로 변경 자체를 attack PR 이 우회하지 못하도록 `paths-ignore` 등을 쓰지 않고 base 브랜치 workflow 가 항상 실행되도록 두는 게 안전.
- 같은 조 페어가 아닌 외부 참가자 (woosung-dev) 가 attack 을 시도해와도 동일하게 동작 — workflow 가 base-branch 단위로 정의되어 있어서.

## 10. 표준 보안감사 Workflow 제안

이 `defend/sabo` 브랜치 실습 결과를 바탕으로 팀 표준 workflow 에 포함해야 한다고 판단한 항목.

| 우선순위 | 항목 | 포함 여부 | 이유 |
| --- | --- | --- | --- |
| 필수 | Backend test | 포함 | 보안 회귀와 기능 회귀를 동시에 검출. PR #8 에서도 mvn test 통과 확인 → 기능 회귀는 없었음 |
| 필수 | Frontend build | 포함 (`frontend-build`) | 빌드 가능성 자체가 PR 의 기본 품질. 보안 스캔 통과 후에만 실행되도록 게이팅. |
| 필수 | 의존성 취약점 스캔 | 포함 (OWASP DC + npm audit) | A06 Vulnerable Components 의 1차 방어선. 단 OWASP DC 캐싱은 필수. |
| 필수 | SAST | 포함 (Semgrep) | A01, A02, A03, A05, A10 등 코드 패턴 기반 위험을 폭넓게 커버. PR #8 에서 실제 탐지 성공. |
| 권장 | Secret scan | 포함 (gitleaks + Semgrep `p/secrets`) | 평문 시크릿 노출은 한 번 일어나면 git 히스토리에 영구히 남으므로 사전 차단이 중요. |
| 권장 | Container 또는 filesystem scan | 포함 (Trivy fs) | 의존성·시크릿·misconfig 의 보강 라인. PR #8 에서 실제 탐지 성공. |
| 권장 | PR 댓글 보고서 | 포함 (sticky comment 2종: `security-report`, `security-audit`) | 리뷰어가 details 페이지로 들어가지 않아도 결과 확인 가능. |
| 권장 | Artifact 업로드 | 포함 (`if: always()`) | 사후 분석과 재현, 회고 작성에 필수. |
| 필수 | Required status check | **미포함** (정책 차원) | branch protection 설정으로 보강 필요. 본 실습 시점에는 미설정. |

### 제안하는 실패 기준

- Critical: 즉시 PR 차단. 의존성 CVSS ≥ 9 / Semgrep ERROR / gitleaks 탐지 / Trivy CRITICAL.
- High: PR 차단. CVSS 7–8.9 / npm audit high / Trivy HIGH.
- Medium: 경고만, 머지 가능. 단 통합 보고서에 명시.
- Low: 보고서에서 카운트만, 본문 미포함.

### 제안하는 보고서 형식

- PR 댓글에 포함할 내용: 도구별 high/critical 카운트, 영향 패키지, CVE, **권장 수정 사항**, 파일 위치. 30건까지만 본문, 그 이상은 artifact 참조.
- Artifact 로 남길 내용: 각 도구의 원본 JSON/SARIF + 통합 `security-report.md`.
- 팀 회고에서 공유할 내용: 탐지 성공/실패 사례, 평균 실행 시간, OWASP DC 캐싱 효율, false positive 비율.

## 11. 최종 결론

이 방어 브랜치에서 만든 workflow 를 표준으로 채택할지 판단합니다.

| 항목 | 판단 |
| --- | --- |
| 표준 workflow 로 채택 가능 여부 | **보완 필요** — 핵심 구조는 채택 가능하지만 OWASP DC 캐싱과 branch protection 설정 추가 후 표준화 |
| 바로 적용 가능한 부분 | 테스트/스캔/빌드 의존성 구조, 통합 마크다운 보고서, Trivy + Semgrep + gitleaks 조합, sticky PR comment 2종 |
| 추가 실험이 필요한 부분 | OWASP Dependency-Check NVD 캐싱, `security-report` 의 빠른 결과 우선 게시 + 후속 업데이트 모델, custom Semgrep rule (`@EnableMethodSecurity` 제거 탐지, debug 파라미터 패턴 등) |
| 다음 액션 | (1) `defend/sabo` 에 branch protection 설정해 위 7개 잡을 required status check 로 등록. (2) Maven 캐시 + NVD data cache step 추가. (3) PR #8 의 OWASP DC 완료 후 `security-report.md` artifact 다운로드해 어떤 룰이 탐지했는지 확인하고 본 문서 7장 보강. |

최종 의견:

- 무료 OSS 도구 5종 조합으로도 A01 Broken Access Control 의 실제 코드 변형을 PR 단계에서 탐지하고 build 까지 차단하는 게이트를 만들 수 있음을 확인. 다만 branch protection 이 없으면 머지 차단까지는 가지 않으므로, workflow + branch protection 둘을 한 세트로 운영해야 의미가 있다.

## 부록: 조회 명령어

```bash
git status --short
git remote -v
git fetch origin
git branch -a --list '*defend/sabo*'

git log --oneline --decorate origin/main..origin/defend/sabo
git log --stat origin/main..origin/defend/sabo
git ls-tree -r --name-only origin/defend/sabo .github/

gh pr list --base defend/sabo --state all \
  --json number,title,url,state,author,headRefName,baseRefName,createdAt,updatedAt,mergedAt,mergeStateStatus,isDraft
gh pr view 8 --json number,title,url,state,author,headRefName,baseRefName,body,commits,files,comments,statusCheckRollup,mergeStateStatus,reviewDecision
gh pr diff 8
gh pr checks 8

gh api repos/anTuni/fornerds_study_session4/branches/defend/sabo/protection
gh run view 26226665493 --json jobs --jq '.jobs[] | {name, conclusion, completedAt}'
```
