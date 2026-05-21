# 보안감사 실습 결과 정리 양식

> 이 양식은 조별 보고서가 아니라 **하나의 `defend/{name}` 브랜치**를 기준으로 작성합니다.  
> 한 조에 두 명이 있다면 각자의 방어 브랜치별로 이 문서를 하나씩 작성합니다.

## 1. 방어 브랜치 기본 정보

| 항목 | 내용 |
| --- | --- |
| 작성 기준 브랜치 | `defend/` |
| 수비자 |  |
| 페어 |  |
| 작성일 |  |
| 실습 저장소 |  |
| 결과 문서 작성자 |  |
| 관련 최종 PR 또는 공유 링크 |  |

## 2. 방어 브랜치 이력 요약

`defend/{name}` 브랜치에서 보안감사 workflow를 추가하거나 개선한 commit을 정리합니다.

| 순서 | Commit | 작성자 | 메시지 | 주요 변경 내용 |
| --- | --- | --- | --- | --- |
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |

## 3. 방어자가 만든 보안감사 Workflow 요약

| 항목 | 내용 |
| --- | --- |
| workflow 파일 경로 | `.github/workflows/` |
| workflow 이름 |  |
| 실행 트리거 | `pull_request` to `defend/...` |
| 대상 방어 브랜치 | `defend/` |
| 사용한 도구 | 예: Maven test, npm audit, Semgrep, Trivy, Snyk, CodeQL |
| 보고서 생성 방식 | 예: artifact upload, PR comment, job summary |
| 실패 기준 | 예: critical/high 발견 시 실패 |
| PR 차단 방식 | 예: required status check, branch protection |
| required status check 이름 |  |
| 평균 실행 시간 |  |
| 가장 느린 단계 |  |

### Workflow 핵심 설정

```yaml
on:
  pull_request:
    branches:
      - defend/{name}
```

### Workflow 설계 의도

- 
- 
- 

## 4. 방어 브랜치로 들어온 공격 PR 목록

`defend/{name}`을 base로 생성된 PR을 모두 정리합니다.

| PR | 공격 브랜치 | 공격자 | 상태 | 취약점 유형 | 최종 check 결과 | 머지 차단 여부 |
| --- | --- | --- | --- | --- | --- | --- |
|  | `attack/` |  | Open / Closed / Merged |  | Pass / Fail | 차단 / 미차단 |
|  | `attack/` |  | Open / Closed / Merged |  | Pass / Fail | 차단 / 미차단 |
|  | `attack/` |  | Open / Closed / Merged |  | Pass / Fail | 차단 / 미차단 |

## 5. 공격/수비 사이클 기록

### Cycle 1

| 항목 | 내용 |
| --- | --- |
| base 브랜치 | `defend/` |
| 공격 브랜치 | `attack/` |
| PR 링크 |  |
| 공격자 |  |
| 수비자 |  |
| 취약점 유형 | 예: A01 Broken Access Control, A03 Injection, A06 Vulnerable Components |
| 공격 commit |  |
| 수정 파일 |  |
| 취약점 설명 |  |
| 기대 탐지 결과 |  |

#### 실행 결과

| 점검 항목 | 결과 |
| --- | --- |
| workflow 실행 여부 | 성공 / 실패 |
| 실행된 workflow 이름 |  |
| 실행된 check 이름 |  |
| 취약점 탐지 여부 | 탐지 / 미탐지 / 오탐 |
| 보고서 생성 여부 | 생성 / 미생성 |
| PR 댓글 여부 | 생성 / 미생성 |
| artifact 업로드 여부 | 생성 / 미생성 |
| job 실패 여부 | 실패 / 성공 |
| PR 머지 차단 여부 | 차단 / 차단 안 됨 |
| 실행 시간 |  |
| Actions run 링크 |  |

#### 탐지 결과 요약

```text
탐지된 파일/라인:

탐지 메시지:

보고서 또는 PR 댓글 요약:

```

#### Cycle 1 이후 방어 개선

| Commit | 개선 내용 | 개선 이유 |
| --- | --- | --- |
|  |  |  |

### Cycle 2

| 항목 | 내용 |
| --- | --- |
| base 브랜치 | `defend/` |
| 공격 브랜치 | `attack/` |
| PR 링크 |  |
| 공격자 |  |
| 수비자 |  |
| 취약점 유형 |  |
| 공격 commit |  |
| 수정 파일 |  |
| 취약점 설명 |  |
| 기대 탐지 결과 |  |

#### 실행 결과

| 점검 항목 | 결과 |
| --- | --- |
| workflow 실행 여부 | 성공 / 실패 |
| 실행된 workflow 이름 |  |
| 실행된 check 이름 |  |
| 취약점 탐지 여부 | 탐지 / 미탐지 / 오탐 |
| 보고서 생성 여부 | 생성 / 미생성 |
| PR 댓글 여부 | 생성 / 미생성 |
| artifact 업로드 여부 | 생성 / 미생성 |
| job 실패 여부 | 실패 / 성공 |
| PR 머지 차단 여부 | 차단 / 차단 안 됨 |
| 실행 시간 |  |
| Actions run 링크 |  |

#### 탐지 결과 요약

```text
탐지된 파일/라인:

탐지 메시지:

보고서 또는 PR 댓글 요약:

```

#### Cycle 2 이후 방어 개선

| Commit | 개선 내용 | 개선 이유 |
| --- | --- | --- |
|  |  |  |

### Cycle 3

| 항목 | 내용 |
| --- | --- |
| base 브랜치 | `defend/` |
| 공격 브랜치 | `attack/` |
| PR 링크 |  |
| 공격자 |  |
| 수비자 |  |
| 취약점 유형 |  |
| 공격 commit |  |
| 수정 파일 |  |
| 취약점 설명 |  |
| 기대 탐지 결과 |  |

#### 실행 결과

| 점검 항목 | 결과 |
| --- | --- |
| workflow 실행 여부 | 성공 / 실패 |
| 실행된 workflow 이름 |  |
| 실행된 check 이름 |  |
| 취약점 탐지 여부 | 탐지 / 미탐지 / 오탐 |
| 보고서 생성 여부 | 생성 / 미생성 |
| PR 댓글 여부 | 생성 / 미생성 |
| artifact 업로드 여부 | 생성 / 미생성 |
| job 실패 여부 | 실패 / 성공 |
| PR 머지 차단 여부 | 차단 / 차단 안 됨 |
| 실행 시간 |  |
| Actions run 링크 |  |

#### 탐지 결과 요약

```text
탐지된 파일/라인:

탐지 메시지:

보고서 또는 PR 댓글 요약:

```

#### Cycle 3 이후 방어 개선

| Commit | 개선 내용 | 개선 이유 |
| --- | --- | --- |
|  |  |  |

## 6. 탐지 성공 사례

| 취약점 유형 | 탐지 도구 또는 규칙 | 탐지 파일 | 왜 잘 탐지됐는가 |
| --- | --- | --- | --- |
|  |  |  |  |
|  |  |  |  |

## 7. 탐지 실패 또는 오탐 사례

| 유형 | PR 또는 파일 | 원인 분석 | 다음 개선안 |
| --- | --- | --- | --- |
| 미탐 |  |  |  |
| 오탐 |  |  |  |

## 8. PR 차단 검증

| 항목 | 결과 |
| --- | --- |
| branch protection 설정 여부 | 설정 / 미설정 |
| required status check 이름 |  |
| 실패한 check 이름 |  |
| PR 상태 | 예: BLOCKED, UNSTABLE, MERGEABLE |
| 실제 머지 버튼 상태 |  |
| 차단이 안 됐다면 이유 |  |

정리:

- workflow가 실패해도 branch protection이 없으면 실제 머지는 가능할 수 있다.
- PR을 확실히 막으려면 required status check 설정이 필요하다.
- 

## 9. Lesson Learned

### 기술적으로 배운 점

- 
- 
- 

### workflow 설계에서 배운 점

- 
- 
- 

### 방어 브랜치 운영에서 배운 점

- 
- 
- 

## 10. 표준 보안감사 Workflow 제안

이 `defend/{name}` 브랜치 실습 결과를 바탕으로 팀 표준 workflow에 포함해야 한다고 생각하는 항목을 정리합니다.

| 우선순위 | 항목 | 포함 여부 | 이유 |
| --- | --- | --- | --- |
| 필수 | Backend test |  |  |
| 필수 | Frontend build |  |  |
| 필수 | 의존성 취약점 스캔 |  |  |
| 필수 | SAST |  |  |
| 권장 | Secret scan |  |  |
| 권장 | Container 또는 filesystem scan |  |  |
| 권장 | PR 댓글 보고서 |  |  |
| 권장 | Artifact 업로드 |  |  |
| 필수 | Required status check |  |  |

### 제안하는 실패 기준

- Critical: 
- High: 
- Medium: 
- Low: 

### 제안하는 보고서 형식

- PR 댓글에 포함할 내용:
- Artifact로 남길 내용:
- 팀 회고에서 공유할 내용:

## 11. 최종 결론

이 방어 브랜치에서 만든 workflow를 표준으로 채택할지 판단합니다.

| 항목 | 판단 |
| --- | --- |
| 표준 workflow로 채택 가능 여부 | 가능 / 보완 필요 / 불가 |
| 바로 적용 가능한 부분 |  |
| 추가 실험이 필요한 부분 |  |
| 다음 액션 |  |

최종 의견:

-
