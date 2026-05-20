# CICD Practice

자동화된 보안 감사 job 실습을 위한 샘플 웹서비스입니다. 기본 프로젝트는 회원 관리, 콘텐츠 관리, 댓글, 관리자 대시보드를 제공하는 작은 사내 CMS 형태로 구성되어 있습니다.

## 기술 스택

- Backend: Java 17, Spring Boot 3, Spring Security, Spring Data JPA, H2
- Frontend: React, TypeScript, Vite
- CI/CD Practice: GitHub Actions, OWASP Dependency-Check, npm audit, Semgrep, Trivy, Dependabot

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
├── .github
│   └── workflows
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
3. 수비자는 `defend/{name}` 브랜치에서 `.github/workflows/security-audit.yml`를 추가하거나 개선합니다.
4. 공격자는 `attack/{name}` 브랜치에 OWASP Top 10 유형의 취약점을 하나 이상 심고 PR을 만듭니다.
5. 보안 감사 job이 취약점을 탐지하는지 확인하고, 보고서 아티팩트를 검토합니다.

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

## 보안 감사 workflow

`.github/workflows/security-audit.yml`는 방어 실습의 출발점입니다.

- PR 및 `defend/**` 브랜치 push에서 실행
- Maven 테스트와 의존성 스캔
- npm audit
- Semgrep SAST
- Trivy 파일시스템 스캔
- 결과를 `security-report` 아티팩트로 업로드

Snyk를 쓰려면 저장소 Secrets에 `SNYK_TOKEN`을 추가한 뒤 workflow의 Snyk step 주석을 해제하세요.
