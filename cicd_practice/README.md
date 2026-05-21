# CICD Practice

자동화된 보안 감사 job 실습을 위한 샘플 웹서비스입니다. 기본 프로젝트는 회원 관리, 콘텐츠 관리, 댓글, 관리자 대시보드를 제공하는 작은 사내 CMS 형태로 구성되어 있습니다.

## 기술 스택

- Backend: Java 17, Spring Boot 3, Spring Security, Spring Data JPA, H2
- Frontend: React, TypeScript, Vite
- CI/CD Practice: GitHub Actions, OWASP Dependency-Check, npm audit, Semgrep, Trivy 등

국내 웹서비스 실습에서 가장 많이 접하는 Java/Spring 기반 백엔드와 React 프론트엔드 조합을 선택했습니다.

## 프로젝트 구조

```text
cicd_practice
├── backend
│   ├── pom.xml
│   └── src
├── frontend
│   ├── package.json
│   └── src
└── docs
```

## 실행 방법

### Backend

```bash
cd backend
mvn spring-boot:run
```

API 서버는 `http://localhost:8080`에서 실행됩니다. H2 콘솔은 `http://localhost:8080/h2-console`입니다.

기본 계정:

| 역할 | 이메일 | 비밀번호 |
| --- | --- | --- |
| 관리자 | admin@example.com | admin1234 |
| 작성자 | editor@example.com | editor1234 |
| 일반 사용자 | user@example.com | user1234 |

### Frontend

```bash
cd frontend
npm install
npm run dev
```

프론트엔드는 `http://localhost:5173`에서 실행됩니다.

## 팀 실습 플로우

1. 각자 `defend/{name}` 브랜치를 만듭니다.
2. 상대의 `defend/{peer}` 브랜치에서 `attack/{name}` 브랜치를 만듭니다.
3. 수비자는 `defend/{name}` 브랜치에서 `.github/workflows/security-audit.yml`를 처음부터 추가합니다.
4. 수비자가 만든 workflow는 `defend/{name}`을 대상으로 들어오는 PR에서 동작하도록 구성합니다.
5. 공격자는 `attack/{name}` 브랜치에 OWASP Top 10 유형의 취약점을 하나 이상 심고, 상대의 `defend/{peer}` 브랜치로 PR을 만듭니다.
6. 보안 감사 job이 취약점을 탐지하는지 확인하고, 보고서 아티팩트를 검토합니다.

예를 들어 `alice`와 `bob`이 2인 1조라면 다음처럼 진행합니다.

| 사람 | 수비 브랜치 | 공격 브랜치 | 공격 PR 대상 |
| --- | --- | --- | --- |
| Alice | `defend/alice` | `attack/alice` | `defend/bob` |
| Bob | `defend/bob` | `attack/bob` | `defend/alice` |

## 공격 실습 아이디어

기본 코드는 의도적으로 취약하게 작성하지 않았습니다. 공격자는 PR에서 다음 유형의 실수를 추가해 보세요.

- A01 Broken Access Control: 작성자 본인 확인 없이 다른 사람의 콘텐츠 수정 허용
- A02 Cryptographic Failures: 평문 비밀번호 저장, 약한 토큰 생성
- A03 Injection: 검색 API를 문자열 연결 SQL/JPQL로 변경
- A05 Security Misconfiguration: CORS 전체 허용, H2 콘솔 운영 노출, CSRF 비활성 범위 확대
- A06 Vulnerable and Outdated Components: 취약한 npm/Maven 패키지 추가
- A07 Identification and Authentication Failures: 로그인 실패 제한 제거, JWT/세션 검증 우회
- A08 Software and Data Integrity Failures: 외부 스크립트 무결성 검증 없이 로드
- A09 Security Logging and Monitoring Failures: 인증/권한 실패 로그 제거
- A10 SSRF: 관리자 URL 미리보기 기능에 내부망 호출 허용

## 수비자가 만들 workflow 요구사항

이 저장소에는 기본 `.github` 설정이 없습니다. 수비자는 자신의 `defend/{name}` 브랜치에서 `.github/workflows/security-audit.yml` 파일을 새로 만들어야 합니다.

workflow는 상대 공격자가 `attack/{peer}`에서 내 `defend/{name}` 브랜치로 PR을 만들 때 실행되어야 합니다. 예시는 아래처럼 시작할 수 있습니다.

```yaml
name: Security Audit

on:
  pull_request:
    branches:
      - defend/alice
```

팀원이 많거나 브랜치명을 일반화하고 싶다면 아래처럼 모든 `defend/**` 대상 PR에서 실행되도록 해도 됩니다.

```yaml
on:
  pull_request:
    branches:
      - 'defend/**'
```

권장 job:

- Maven 테스트와 Java 의존성 스캔
- npm build와 `npm audit`
- Semgrep 또는 CodeQL 기반 SAST
- Trivy 파일시스템 스캔
- 결과를 `security-report` 아티팩트로 업로드
- 치명적 취약점은 실패 처리하고, 중간 심각도는 보고서로 관리

Snyk를 쓰려면 저장소 Secrets에 `SNYK_TOKEN`을 추가한 뒤 Snyk CLI 또는 Snyk GitHub Action을 workflow에 직접 추가하세요.
