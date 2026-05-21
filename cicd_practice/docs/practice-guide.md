# 실습 가이드

## 목표

팀원이 만든 PR에 포함된 취약점을 자동화된 보안 감사 job으로 탐지합니다.

## 권장 진행

1. 수비자는 `defend/{name}` 브랜치에서 `.github/workflows/security-audit.yml`를 새로 추가합니다.
2. 공격자는 상대의 방어 브랜치에서 `attack/{name}` 브랜치를 만듭니다.
3. 공격자는 OWASP Top 10 취약점 하나를 의도적으로 추가합니다.
4. 공격자는 `attack/{name}`에서 상대의 `defend/{peer}`로 PR을 생성합니다.
5. 수비자는 Actions 결과와 아티팩트를 보고 취약점 탐지 여부를 확인합니다.

## 브랜치 예시

| 사람 | 먼저 만드는 브랜치 | 상대 브랜치에서 만드는 공격 브랜치 | PR 대상 |
| --- | --- | --- | --- |
| Alice | `defend/alice` | `attack/alice` | `defend/bob` |
| Bob | `defend/bob` | `attack/bob` | `defend/alice` |

수비자의 workflow는 자신의 `defend/{name}` 브랜치를 대상으로 들어오는 PR에서 동작해야 합니다.

```yaml
on:
  pull_request:
    branches:
      - defend/alice
```

공통 workflow를 만들고 싶다면 모든 방어 브랜치 대상 PR에서 실행되도록 구성할 수 있습니다.

```yaml
on:
  pull_request:
    branches:
      - 'defend/**'
```

## 방어자가 추가해볼 만한 job

- Maven 테스트
- npm build
- OWASP Dependency-Check
- Snyk 의존성 스캔
- CodeQL 분석
- Gitleaks secret scan
- Checkov 또는 Trivy IaC scan
- PR 댓글 자동 작성
- `critical`은 실패, `medium/high`는 보고서만 생성하는 심각도 정책

## 공격자가 넣어볼 만한 변경

- Maven 또는 npm에 알려진 취약 패키지 추가
- 인증 필터 우회 조건 추가
- 관리자 API에서 `@PreAuthorize` 제거
- 검색 API를 native query 문자열 연결로 변경
- React에서 사용자 입력을 `dangerouslySetInnerHTML`로 출력
- CORS 허용 origin을 `*`로 변경
- 로그에 토큰 또는 비밀번호 출력

## 평가 기준

- CI가 PR에서 자동 실행되는가
- 테스트와 보안 스캔이 분리되어 원인을 파악하기 쉬운가
- 실패 기준이 너무 빡빡하거나 느슨하지 않은가
- 보고서 아티팩트가 사람이 읽기 쉬운가
- 취약점이 탐지되지 않았을 때 rule 또는 tool을 개선할 수 있는가
