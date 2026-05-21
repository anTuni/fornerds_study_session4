# 보안감사 실습 결과 — `defend/당근`

> 본 문서는 `defend/당근` 단일 브랜치를 기준으로 실습 결과를 정리한 보고서입니다.

## 1. 방어 브랜치 기본 정보

| 항목 | 내용 |
| --- | --- |
| 작성 기준 브랜치 | `defend/당근` |
| 수비자 | 당근 (woosung-dev) |
| 페어 | 확인 필요 (PR #5는 player397(사보), PR #22는 Brit-juho(Brit)가 공격) |
| 작성일 | 2026-05-21 |
| 실습 저장소 | https://github.com/anTuni/fornerds_study_session4 |
| 결과 문서 작성자 | 당근 (woosung-dev) |
| 관련 최종 PR 또는 공유 링크 | PR #3 (smoke) / PR #5 (sabo attack) / PR #22 (Brit attack) |

## 2. 방어 브랜치 이력 요약

`origin/main..origin/defend/당근` 차이는 단일 commit.

| 순서 | Commit | 작성자 | 메시지 | 주요 변경 내용 |
| --- | --- | --- | --- | --- |
| 1 | `34cb355` | woosung | Add security audit workflow for defend branches | `.github/workflows/security-audit.yml` 신규 (+62 라인). 5개 step (Dep-Check / npm audit / Semgrep / Gitleaks / artifact). |

(이후 추가 개선 commit 없음 — 단발 baseline 상태로 실습 진입)

## 3. 방어자가 만든 보안감사 Workflow 요약

| 항목 | 내용 |
| --- | --- |
| workflow 파일 경로 | `.github/workflows/security-audit.yml` (저장소 루트) |
| workflow 이름 | `Security Audit` |
| 실행 트리거 | `pull_request` to `defend/**` |
| 대상 방어 브랜치 | `defend/**` (와일드카드. defend/당근 포함, 다른 defend도 매칭) |
| 사용한 도구 | OWASP Dependency-Check (Maven, CVSS≥7), npm audit (high+), Semgrep (p/owasp-top-ten, p/java, p/react, p/secrets, ERROR fail), Gitleaks |
| 보고서 생성 방식 | `security-report` 아티팩트 단일 업로드 (dependency-check-report.* + results.sarif) |
| 실패 기준 | Dep-Check CVSS≥7 / npm audit high+ / Semgrep ERROR / Gitleaks 발견 시 즉시 fail (단일 job, fail-fast) |
| PR 차단 방식 | required status check 미설정 — workflow fail이어도 머지 가능 |
| required status check 이름 | 미설정 |
| 평균 실행 시간 | 측정 실패 (PR #3·#5 모두 `IN_PROGRESS`로 종결됨) |
| 가장 느린 단계 | 추정: Semgrep (`pip install semgrep` + multi-config scan), 또는 OWASP DC (NVD DB 첫 다운로드) |

### Workflow 핵심 설정

```yaml
on:
  pull_request:
    branches:
      - 'defend/**'
```

### Workflow 설계 의도

- 한 job·단일 흐름으로 단순화. fail-fast 의도 — 첫 결함에서 멈춰 PR 작성자가 한 가지에 집중.
- Dep-Check 임계치를 pom 기본값(9.0)에서 7로 낮춰 high도 잡음.
- Semgrep은 ERROR severity만 fail (WARNING은 pass) — false positive 줄이려는 절충.
- Snyk·CodeQL·Trivy는 의도적으로 미채택 (도구 다양성보다 빠른 학습 루프 우선).

## 4. 방어 브랜치로 들어온 공격 PR 목록

| PR | 공격 브랜치 | 공격자 | 상태 | 취약점 유형 | 최종 check 결과 | 머지 차단 여부 |
| --- | --- | --- | --- | --- | --- | --- |
| #3  | `test/audit-smoke` | woosung-dev (본인) | CLOSED  | 없음 (smoke test, SMOKE_TEST.md 1개 추가) | `audit` IN_PROGRESS로 종결 | 미차단 (branch protection 없음, 본인 close) |
| #5  | `attack/sabo` | player397 (사보) | OPEN, UNSTABLE | A01·A02·A03·A05·A06·A07·A08·A09·A10 + 평문 시크릿 (PR 본문에 명시) | `audit` IN_PROGRESS로 종결 (완료 결과 없음) | 미차단 (workflow 종료 못함 + protection 없음) |
| #22 | `attack/Brit` | Brit-juho (Brit) | OPEN, DIRTY | A01 (PreAuthorize/author check 제거), A10 SSRF 의심 (UrlPreviewController 신규), Mass assignment 의심 (UserController +12라인) | **체크 없음** (workflow 미트리거) | 미차단 |

## 5. 공격/수비 사이클 기록

### Cycle 1 — Smoke Test

| 항목 | 내용 |
| --- | --- |
| base 브랜치 | `defend/당근` |
| 공격 브랜치 | `test/audit-smoke` |
| PR 링크 | https://github.com/anTuni/fornerds_study_session4/pull/3 |
| 공격자 | 본인 (woosung-dev) |
| 수비자 | 당근 |
| 취약점 유형 | 해당 없음 (트리거 검증용 마커 파일 추가) |
| 공격 commit | `bf41978` Add smoke test marker to verify security audit workflow fires |
| 수정 파일 | `SMOKE_TEST.md` (+15) |
| 취약점 설명 | 없음. 워크플로우 fire 여부 검증 목적. |
| 기대 탐지 결과 | 없음 (모든 스캐너 pass) |

#### 실행 결과

| 점검 항목 | 결과 |
| --- | --- |
| workflow 실행 여부 | 성공 (트리거 발화 확인) |
| 실행된 workflow 이름 | Security Audit |
| 실행된 check 이름 | `audit` |
| 취약점 탐지 여부 | 해당 없음 |
| 보고서 생성 여부 | 미확인 (PR이 종료 전 close되어 artifact 미확보) |
| PR 댓글 여부 | 미생성 |
| artifact 업로드 여부 | 미확인 |
| job 실패 여부 | IN_PROGRESS 상태로 종결 (pending 0) |
| PR 머지 차단 여부 | 미차단 |
| 실행 시간 | 미측정 |
| Actions run 링크 | https://github.com/anTuni/fornerds_study_session4/actions/runs/26226072601/job/77173335968 |

#### 탐지 결과 요약

```text
탐지된 파일/라인: 없음
탐지 메시지: 없음
보고서 또는 PR 댓글 요약: PR이 IN_PROGRESS 상태에서 close되어 결과 미확인.
```

#### Cycle 1 이후 방어 개선

| Commit | 개선 내용 | 개선 이유 |
| --- | --- | --- |
| 없음 | 개선 commit 미수행 | smoke test 결과(미완료)만으로는 개선 방향 도출 어려움 |

### Cycle 2 — 사보의 OWASP Top 10 종합 공격

| 항목 | 내용 |
| --- | --- |
| base 브랜치 | `defend/당근` |
| 공격 브랜치 | `attack/sabo` |
| PR 링크 | https://github.com/anTuni/fornerds_study_session4/pull/5 |
| 공격자 | player397 (사보) |
| 수비자 | 당근 |
| 취약점 유형 | A01 / A02 / A03(SQLi+XSS) / A05 / A06(Java+npm) / A07 / A08 / A09 / A10 / 평문 시크릿 — PR 본문에 12종 명시 |
| 공격 commit | `d949b07` Add intentionally vulnerable changes for attack/sabo |
| 수정 파일 | `pom.xml` (+18, log4j-core 2.14.1·snakeyaml 1.30·commons-collections 3.2.1), `AuthService.java` (Random PRNG + 하드코드 키 + raw token 로깅), `SecurityConfig.java` (CSRF disable, CORS `*` + credentials, /api/admin/** permitAll, NoOpPasswordEncoder), `ContentController.java` (@PreAuthorize 제거), `ContentRepository.java` (native SQL 문자열 연결), `UrlPreviewController.java` (SSRF), `application.yml` (AWS/GitHub/JWT 시크릿), `index.html` (SRI 없이 외부 script), `App.tsx` (dangerouslySetInnerHTML), `package.json` (lodash 4.17.4·minimist 1.2.0·axios 0.21.0) |
| 취약점 설명 | OWASP Top 10 거의 전 카테고리를 한 PR에 종합 주입. 의도적으로 모든 스캐너 카테고리에서 탐지를 유도 (Dep-Check / npm audit / Semgrep / Gitleaks 각각). |
| 기대 탐지 결과 | 4개 스캐너 모두 fail 필수 (Dep-Check log4j CVE-2021-44228 등 CVSS≥9, npm audit critical lodash 4.17.4, Semgrep dangerouslySetInnerHTML + native SQL + 평문 시크릿, Gitleaks AWS/GitHub/JWT 키 hit) |

#### 실행 결과

| 점검 항목 | 결과 |
| --- | --- |
| workflow 실행 여부 | 트리거됨 (job 시작 12:38:37Z) |
| 실행된 workflow 이름 | Security Audit |
| 실행된 check 이름 | `audit` (defend/당근 워크플로우) |
| 취약점 탐지 여부 | **확인 불가** — `audit` job이 IN_PROGRESS 상태로 종결됨 (정상 완료 결과 미산출) |
| 보고서 생성 여부 | 확인 필요 (artifact 미확보) |
| PR 댓글 여부 | 미생성 (워크플로우에 PR comment step 없음) |
| artifact 업로드 여부 | 확인 필요 (Actions run 페이지에서 직접 확인 필요) |
| job 실패 여부 | IN_PROGRESS — fail/success 미확정 |
| PR 머지 차단 여부 | 미차단 (branch protection 미설정, 또한 check 종료 안 됨) |
| 실행 시간 | 측정 불가 |
| Actions run 링크 | https://github.com/anTuni/fornerds_study_session4/actions/runs/26226414112/job/77174552207 |

참고: PR #5의 다른 statusCheckRollup 항목들(Backend Maven test FAILURE, OWASP DC FAILURE, npm audit FAILURE, Semgrep FAILURE, Trivy FAILURE, Gitleaks FAILURE 등)은 attack/sabo 브랜치에 동봉된 사보 본인 워크플로우의 push 트리거 결과로 추정됨(`defend/당근` 워크플로우와는 별개 run id). 즉 사보의 워크플로우는 잘 잡았지만, **defend/당근 워크플로우는 결과 산출 실패**.

#### 탐지 결과 요약

```text
탐지된 파일/라인: defend/당근 워크플로우 측 결과 없음 (job IN_PROGRESS).
탐지 메시지: 없음.
보고서 또는 PR 댓글 요약: 본 워크플로우는 PR comment step을 두지 않음. artifact는 Actions 페이지에서 수동 확인 필요.
```

#### Cycle 2 이후 방어 개선

| Commit | 개선 내용 | 개선 이유 |
| --- | --- | --- |
| 없음 | 후속 개선 미수행 | job 미완료 원인 분석이 선행 필요 (timeout / Semgrep install 실패 / runner 캡쳐 미흡 등) |

### Cycle 3 — Brit의 위장 refactor 공격

| 항목 | 내용 |
| --- | --- |
| base 브랜치 | `defend/당근` |
| 공격 브랜치 | `attack/Brit` |
| PR 링크 | https://github.com/anTuni/fornerds_study_session4/pull/22 |
| 공격자 | Brit-juho (Brit) |
| 수비자 | 당근 |
| 취약점 유형 | A01 Broken Access Control (ContentController의 `assertCanEdit` 및 가드 제거), Mass Assignment 의심 (UserController/UserAccount 변경), A10 SSRF 의심 (`UrlPreviewController` 신규) |
| 공격 commit | `c5a59ac` refactor: simplify content update flow, `ee5b404` feat: add admin URL preview endpoint, `f675995` refactor: unify user update DTO (+ tuni1 워크플로우 관련 머지 commit) |
| 수정 파일 | `.github/workflows/security-audit.yml` (defend/tuni1용 별도 워크플로우 +123, 무시되어야 함), `ContentController.java` (-11, assertCanEdit 및 가드 제거), `UserController.java` (+12), `UserAccount.java` (+15), `UrlPreviewController.java` (+46 신규) |
| 취약점 설명 | "refactor" 위장 — assertCanEdit 통째 제거(A01 IDOR 확장), 신규 UrlPreview 엔드포인트(외부 URL 검증 없이 fetch → SSRF) |
| 기대 탐지 결과 | Semgrep p/java + p/owasp-top-ten의 SSRF·removed-authz 룰 hit 기대. 단 Brit의 변경은 머지 충돌(DIRTY)이 있어 GitHub이 PR check 실행을 건너뛸 가능성 있음. |

#### 실행 결과

| 점검 항목 | 결과 |
| --- | --- |
| workflow 실행 여부 | **미실행** (`no checks reported on the 'attack/Brit' branch`) |
| 실행된 workflow 이름 | 없음 |
| 실행된 check 이름 | 없음 |
| 취약점 탐지 여부 | 미탐지 (워크플로우 자체가 안 돔) |
| 보고서 생성 여부 | 미생성 |
| PR 댓글 여부 | 미생성 |
| artifact 업로드 여부 | 미생성 |
| job 실패 여부 | 실행 안 됨 |
| PR 머지 차단 여부 | 미차단 (PR은 mergeStateStatus=DIRTY로 충돌 자체로는 막혀 있으나, security check는 무관) |
| 실행 시간 | 해당 없음 |
| Actions run 링크 | 없음 |

#### 탐지 결과 요약

```text
탐지된 파일/라인: 없음.
탐지 메시지: 없음.
보고서 또는 PR 댓글 요약: 머지 충돌 또는 트리거 정책으로 workflow 미실행. defend/** 트리거 자체는 PR 자체가 trigger 조건을 충족하면 돌아야 하므로, DIRTY 상태에서도 fire되지 않은 이유 추가 조사 필요.
```

#### Cycle 3 이후 방어 개선

| Commit | 개선 내용 | 개선 이유 |
| --- | --- | --- |
| 없음 | 후속 개선 미수행 | 머지 충돌 해소 또는 base rebase 후 재트리거 필요 |

## 6. 탐지 성공 사례

| 취약점 유형 | 탐지 도구 또는 규칙 | 탐지 파일 | 왜 잘 탐지됐는가 |
| --- | --- | --- | --- |
| (해당 없음 — defend/당근 워크플로우 측 완료된 탐지 사례 0건) |  |  |  |

## 7. 탐지 실패 또는 오탐 사례

| 유형 | PR 또는 파일 | 원인 분석 | 다음 개선안 |
| --- | --- | --- | --- |
| 미탐 (워크플로우 미완료) | PR #5 전체 | 단일 fail-fast job 구조에서 한 step이 멈추면 후속 결과 전체 미산출. Semgrep `python3 -m pip install --quiet semgrep` 단계가 컨테이너/네트워크 이슈로 지연될 수 있음. timeout-minutes 미설정. | step별 `timeout-minutes` 명시, Semgrep 공식 action(`returntocorp/semgrep-action` 또는 컨테이너 `image: returntocorp/semgrep`) 사용으로 install 단계 제거. 또는 job을 도구별로 분리해 한 도구 실패가 다른 도구 결과를 가리지 않게. |
| 미탐 (워크플로우 미트리거) | PR #22 | `no checks reported` — 머지 충돌 또는 fork/머지 정책 영향. base branch 보호 정책상 GitHub Actions가 dirty PR에 대해 workflow를 보류한 가능성. | base를 rebase한 새 PR을 요구하거나, `workflow_dispatch` 보조 트리거 추가. |
| 오탐 | 해당 없음 | 완료된 run이 없어 평가 불가 | — |

## 8. PR 차단 검증

| 항목 | 결과 |
| --- | --- |
| branch protection 설정 여부 | 미설정 (`gh api .../branches/defend%2F당근/protection` → 404) |
| required status check 이름 | 없음 |
| 실패한 check 이름 | 해당 없음 (audit job IN_PROGRESS) |
| PR 상태 | #3 CLOSED / #5 UNSTABLE / #22 DIRTY |
| 실제 머지 버튼 상태 | 머지 가능 (security 측 차단 없음) |
| 차단이 안 됐다면 이유 | branch protection 미설정 + required status check 미지정 + 우리 audit job이 결과를 산출하지 못함 |

정리

- workflow가 실패해도 branch protection이 없으면 실제 머지는 가능.
- PR을 확실히 막으려면 required status check 설정이 필요.
- 또한 single-job fail-fast 구조는 "check 자체가 안 끝남" 상태를 만들 수 있어, required check로 등록해도 머지 보류만 시킬 뿐 명확한 차단 신호를 못 줌.

## 9. Lesson Learned

### 기술적으로 배운 점

- `pull_request` 이벤트는 base 브랜치(`defend/당근`)의 workflow 파일을 사용. 공격자가 head에서 workflow를 지워도 base 워크플로우가 돈다 (tamper-proof) — Cycle 3의 attack/Brit이 자기 워크플로우 파일을 추가했지만 우리 워크플로우 트리거에 영향 못 줌.
- `--audit-level=high`와 `--audit-level=critical`은 단어 차이지만 사보 PR #5의 npm 공격(lodash 4.17.4, axios 0.21.0)을 잡느냐 못 잡느냐를 결정. 임계치 1단계가 사실상 통과/탐지를 가른다.
- `semgrep --error`는 ERROR severity 룰만 fail시킴. p/owasp-top-ten의 많은 룰이 WARNING severity라 dangerouslySetInnerHTML 같은 명백한 패턴도 통과시킬 수 있음. 다음번엔 `--severity ERROR --severity WARNING --error` 조합 필요.

### workflow 설계에서 배운 점

- **단일 job·fail-fast는 학습용으로는 위험**. 한 step의 지연·실패가 전체 결과를 묻어버려 "무엇이 잡혔고 무엇이 안 잡혔는지" 학습이 불가능. **도구별 job 분리 + `fail-fast: false`** 가 학습 효과 면에서 압도적으로 우수 (사보·tuni·david의 multi-job 워크플로우가 모두 이 형태를 채택).
- 모든 step에 `timeout-minutes` 명시 필요. Semgrep `pip install`처럼 외부 네트워크 의존이 있는 step은 특히.
- 결과 가시성을 위해 PR comment step (`marocchino/sticky-pull-request-comment` 또는 `actions/github-script`)이 사실상 필수. artifact-only 정책은 동료가 결과를 보러 Actions 페이지를 들어가지 않으면 죽은 보고서.

### 방어 브랜치 운영에서 배운 점

- **Branch protection + required status check가 없으면 workflow는 보고서일 뿐**. 차단력 0. 다음 라운드 진입 전 필수 설정.
- defend 브랜치 별로 named check ID가 다르면 required check 등록이 번거로움. `defend/**` 와일드카드 트리거 + 동일 job name 패턴이 운영 편리.
- baseline 단발 commit만 두고 cycle을 시작하면 "공격에 반응해 워크플로우를 강화" 사이클이 사실상 1회로 끝나기 쉽다. 처음부터 *나쁜 baseline*을 일부러 두고 1라운드 후 강화하는 방식이 학습 밀도가 더 높았을 듯.

## 10. 표준 보안감사 Workflow 제안

| 우선순위 | 항목 | 포함 여부 | 이유 |
| --- | --- | --- | --- |
| 필수 | Backend test | 포함 | 의도치 않은 컴파일/회귀 변경을 PR 단계에서 차단 |
| 필수 | Frontend build | 포함 | tsc + vite build 실패는 SAST 통과해도 PR 가치 없음 |
| 필수 | 의존성 취약점 스캔 | 포함 (Maven+npm 양쪽, CVSS≥7) | 공격자가 가장 쉽게 시도하는 벡터 |
| 필수 | SAST | 포함 (Semgrep + CodeQL 병행) | Semgrep 빠른 룰셋 + CodeQL 시맨틱 → IDOR류 보강 |
| 권장 | Secret scan | 포함 (Gitleaks) | 평문 시크릿 1건도 즉시 fail |
| 권장 | Container 또는 filesystem scan | 포함 (Trivy fs) | misconfig + vuln 한 번에 |
| 권장 | PR 댓글 보고서 | **필수로 격상** | artifact-only는 동료가 안 읽음 |
| 권장 | Artifact 업로드 | 포함 | 사후 분석 / 회고 자료 |
| 필수 | Required status check | **필수로 격상** | 없으면 모든 노력이 정보용 |

### 제안하는 실패 기준

- Critical: 즉시 fail
- High: 즉시 fail (npm/Maven 양쪽)
- Medium: 보고서로 PR comment 표시, fail 안 함
- Low: 정보 수준, 별도 표시 없음

### 제안하는 보고서 형식

- PR 댓글에 포함할 내용: 도구별 PASS/FAIL 표, 카테고리별 hit 수, 가장 심각한 finding 3건 발췌, Actions run 링크.
- Artifact로 남길 내용: 각 도구의 raw JSON/SARIF + 합본 markdown 요약.
- 팀 회고에서 공유할 내용: cycle별 미탐 케이스 + 채택한 보강 룰.

## 11. 최종 결론

| 항목 | 판단 |
| --- | --- |
| 표준 workflow로 채택 가능 여부 | **보완 필요** |
| 바로 적용 가능한 부분 | `defend/**` 와일드카드 트리거, OWASP DC `failBuildOnCVSS=7`, 단일 artifact 업로드 패턴 |
| 추가 실험이 필요한 부분 | (1) single-job → multi-job 분리, (2) Semgrep severity threshold 재정의 + 컨테이너 이미지 사용, (3) PR comment 자동 게시, (4) required status check 등록, (5) timeout 정책 |
| 다음 액션 | 1) defend/당근 워크플로우를 도구별 job으로 리팩토링 → 2) repo settings에 required check 등록 → 3) PR #5에 재트리거(빈 commit 또는 workflow_dispatch)로 종합 탐지 실측 → 4) Cycle 2 결과 기반 룰 강화 commit 추가 |

최종 의견

- 워크플로우가 트리거되는 것까지는 확인됐으나, **단일 job·fail-fast 구조와 외부 install 의존성**이 결합해 정작 가장 중요한 PR #5의 결과를 받지 못한 것이 이번 라운드의 핵심 실패. 다음 라운드에서는 도구별 job 분리 + 명시 timeout + PR comment를 우선 도입할 계획이다.

---

## 부록: 조회 명령어

```bash
git log --oneline origin/main..origin/defend/당근
git show 'origin/defend/당근:.github/workflows/security-audit.yml'
gh pr list --base 'defend/당근' --state all --json number,title,url,state,author,headRefName,baseRefName,createdAt,mergedAt,mergeStateStatus,isDraft
gh pr view 3 --json number,title,url,state,author,headRefName,baseRefName,body,commits,files,comments,statusCheckRollup,mergeStateStatus
gh pr view 5 --json number,title,url,state,author,headRefName,baseRefName,body,commits,files,comments,statusCheckRollup,mergeStateStatus
gh pr view 22 --json number,title,url,state,author,headRefName,baseRefName,body,commits,files,comments,statusCheckRollup,mergeStateStatus
gh pr diff 5
gh pr diff 22
gh pr checks 3
gh pr checks 5
gh pr checks 22
gh api 'repos/anTuni/fornerds_study_session4/branches/defend%2F당근/protection'
```
