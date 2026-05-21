# 보안 정책 체크리스트 원문

이 문서는 팀 내 보안 사고/장애로부터 도출된 정책 모음이다. 스킬은 이 원문을 점검의 기준으로 사용한다.

## 1. 시크릿 관리

- 신규 시크릿은 `openssl rand -base64 64` 또는 `hex 32` 이상 엔트로피로 생성한다. jwt.io / 튜토리얼 예제 시크릿 재사용 금지.
- `.env` 평문 보관 금지. AWS Secrets Manager / SSM Parameter Store + IAM Role 기반 주입.
- `.env`, `.key`, `.p8`은 무조건 `.gitignore`. 추가로 pre-commit hook(gitleaks, git-secrets)으로 `AKIA…`, `BEGIN PRIVATE KEY` 등 키 패턴 차단.
- Apple `.p8`, OAuth secret은 빌드 산출물에 포함 금지.
- 키 노출 발생 시 즉시 회전 + 영향도 조사 절차 정의.
- 테스트 계정 ID/PW도 동일하게 git 커밋 금지. README, AGENTS.md, 주석 모두 금지. 이미 커밋된 경우 `git filter-repo`로 히스토리 재작성 + 즉시 무효화.

## 2. 인증 / 인가

- `dev_mode`, `?debug=1` 같은 인증 우회 파라미터 절대 금지.
- 테스트용 엔드포인트는 `@Profile("local")` 등으로 격리.
- 모든 PUT/DELETE/PATCH는 리소스 owner check 필수.
- 관리자 API는 `@PreAuthorize("hasRole('ADMIN')")` 명시. 보안 그룹/방화벽만으로 보호 금지(Next.js 미들웨어 등에서 IP 화이트리스트 또는 Basic Auth/SSO를 코드 레벨로).
- JWT secret은 64바이트 이상 고엔트로피 난수.
- Refresh token 회전(rotate-on-use) 의무화. 로그아웃 시 access/refresh 모두 블랙리스트 등록.
- 공개 경로 매칭은 `startsWith` 금지. `'/'` 한 글자 항목으로 인증 보호가 무력화됨. exact match 또는 path-to-regexp / Next.js matcher 사용. 공개 경로 목록은 별도 상수 파일로 분리.
- 인증 실패 메시지는 enumeration 방지 일반화 메시지로 통일 ("아이디 또는 비밀번호가 일치하지 않습니다"). "존재하지 않는 계정" / "비밀번호 오류" 분리 표시 금지.
- 시크릿/토큰/해시 비교는 타이밍 안전 함수 강제: Java `MessageDigest.isEqual`, Node `crypto.timingSafeEqual`. `==`, `equals()`, `===` 사용 금지.
- 소셜 로그인 audience 화이트리스트: web/ios/android clientId 모두 명시 후 비교.

## 3. 세션 / CSRF / 헤더 / 전송

- HttpOnly 쿠키 인증 사용 시 CSRF 토큰 또는 SameSite + Origin/Referer 검증 필수. `csrf.disable()`은 사유 + 보완책 PR 명시 없이 머지 금지.
- 쿠키 인증 + CORS `credentials: true` 조합은 별도 보안 리뷰 대상.
- CORS allowedOrigins는 도메인 화이트리스트만 허용. `setAllowedOriginPatterns("*")` + `allowCredentials(true)` 조합 금지.
- 환경변수 `CORS_ALLOWED_ORIGINS`로 화이트리스트 주입.
- nginx와 Spring 양쪽에서 CORS 헤더 중복 설정 금지.
- HSTS, X-Frame-Options, X-Content-Type-Options, CSP, Referrer-Policy, `server_tokens off` 적용.
- HTTPS 단독 배포만 "완료". HTTP→HTTPS 301 리다이렉트 + DNS A + TLS 인증서 + HSTS 모두 갖춰야 한다.

## 4. 결제 / 외부 연동

- PG 콜백은 서명/HMAC 검증 통과 후에만 신뢰.
- 결제 금액은 서버 DB 기준으로 재계산 후 비교. 클라이언트 페이로드 신뢰 금지.
- `txnid + orderId` UNIQUE + idempotency 키 적용.
- 콜백 redirect URL은 화이트리스트 검증.
- 에러 메시지를 redirect URL에 직접 삽입 금지(open redirect / XSS 위험).

## 5. 입력 검증 / 파일 업로드

- NestJS 컨트롤러 파라미터에 `@Body() body: any` 금지. DTO 클래스 + `class-validator` 적용. ESLint 룰로 검출.
- Spring `@RequestBody`는 항상 DTO. Entity 직접 사용 금지.
- TypeORM `Object.assign(entity, dto)` 또는 `repository.save({ ...dto })` 금지(Mass Assignment). sanitizer / 화이트리스트 함수 경유.
- 업로드 파일은 확장자 + MIME + 매직바이트 3중 검증.
- 파일명은 UUID 등 서버 생성값으로 재작성. 사용자 입력 파일명 그대로 저장 금지.
- multipart 최대 크기를 합리적 수준(예: 50MB)으로 제한.
- redirect/URL 파라미터는 화이트리스트 또는 인코딩.

## 6. Rate Limiting / 봇 차단

- 인증 관련 글로벌 60/분 + signin 10/분, signup 5/분, reset 3/분, email-send 3/분.
- IP+계정 단위 제한.
- 이메일·닉네임 중복확인은 throttle + captcha.
- Redis + Bucket4j 등 표준 라이브러리 사용. 단일 인스턴스 인메모리 카운터는 운영 사용 금지(재시작 시 리셋).
- 임계 초과 시 알림(Slack/CloudWatch) 발생.
- Brute-force 방어 모듈은 공통 라이브러리화 — 프로젝트마다 재구현 금지.

## 7. 클라이언트 IP / 로깅 / PII

- `X-Forwarded-For` 직접 신뢰 금지. nginx에서 `$remote_addr` → `X-Real-IP` 주입 → 앱은 `X-Real-IP`만 읽음. CDN/ALB 뒤일 경우 신뢰 가능 hop 수 명시.
- URL 쿼리스트링에 PII(이름·전화·이메일) 금지. POST + body로. `?name=`, `?phone=`, `?email=` 패턴 차단.
- `console.log(user)` 패턴 금지. 식별자만 남기고 토큰·비밀번호·전화·이메일 마스킹.
- 개발 전용 로그는 `process.env.NODE_ENV !== 'production'` 가드. ESLint 룰로 검출.
- 비밀번호·토큰·카드번호·결제 페이로드 로깅 금지.
- Authorization 헤더 마스킹.
- 운영은 INFO 이상. `show_sql` / `debug` 비활성.
- 예외 응답에 stacktrace·내부 메시지 노출 금지.

## 8. XSS / 사용자 본문 렌더링

- 사용자 본문 렌더링 컴포넌트(LatexRenderer, MarkdownViewer 등)는 DOMPurify 등 sanitizer 경유 강제.
- React `dangerouslySetInnerHTML`은 정적 데이터만.

## 9. 배포 / 인프라

- DB / Redis / Cache 등 백엔드 의존 컴포넌트는 docker-compose에서 `expose:`만 사용 또는 `127.0.0.1:` prefix로 호스트 바인딩.
- `0.0.0.0:5432:5432` 같은 전 노출 금지.
- EC2 Security Group은 80/443/22 외 모두 차단.
- Swagger / api-docs는 운영 프로필에서 비활성.
- Dockerfile은 multi-stage + 비-root user.
- base image 버전 고정. `latest` 태그 금지.
- JPA `ddl-auto`는 `validate` + Flyway/Liquibase. `update`/`create-drop`/`create` 운영 사용 금지.
- TypeORM 프로덕션은 `synchronize: false` + `migrationsRun: true` + idempotent 마이그레이션(`pg_constraint` 사전 조회).

## 10. 의존성 / 코드 품질 / 프로세스

- BouncyCastle, JJWT 등 보안 라이브러리 최신 유지.
- `npm audit`, Gradle dependencyCheck CI 통합.
- 외부 키(Maps API 등)는 referrer/도메인 제한 필수.
- PR 시 보안 리뷰어 1인 필수. 분기 1회 OWASP API Top 10 정기 점검.
- 보안 사고 대응 플레이북 문서화 + 훈련.
- 신규 엔드포인트는 권한·rate-limit·검증 체크리스트 통과.

## 11. 모바일(Flutter/Dart) 특화

- DioClient `baseUrl` 규칙: `${ApiConfig.baseUrl}` 접두사를 코드에 직접 쓰지 않는다(이중 적용 방지). lint 룰화.
- `throw String` 금지: Dart에서 `throw 'message'`는 `on Exception catch (e)`로 잡히지 않음. 무조건 `throw Exception(...)` 또는 커스텀 예외.
- 토큰 저장: `flutter_secure_storage` 사용. SharedPreferences 평문 저장 금지.

## PR 머지 차단 체크리스트 (Hard Gate)

다음 중 하나라도 미통과 시 **머지 금지**:

- [ ] 신규/변경 엔드포인트에 인증·인가 적용
- [ ] 쿠키 인증 추가/변경 시 CSRF 방어 동반
- [ ] 공개 경로 목록에 prefix로 의도치 않게 포함된 경로 없음
- [ ] PII가 URL 쿼리스트링·로그에 노출되지 않음
- [ ] 자격증명·토큰·API 키·테스트 계정이 코드·문서·테스트 fixture에 평문 없음
- [ ] IP 기반 로직이 `X-Forwarded-For` 직접 신뢰하지 않음
- [ ] 사용자 입력 렌더링 시 sanitizer 경유
- [ ] 시크릿/토큰 비교가 타이밍 안전 함수 사용
- [ ] 인증 실패 메시지가 enumeration 가능한 분기 없음
- [ ] HTTPS 강제 및 HSTS 유지
