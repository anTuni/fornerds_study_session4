# Docker / Nginx / 배포 인프라 검출 패턴

## 1. docker-compose 호스트 포트 전 노출

검출: `ports:\s*\n\s*-\s*['"]?\d+:\d+` (127.0.0.1 prefix 없음). 특히 `5432`, `3306`, `27017`, `6379` 등 DB/캐시 포트.

위험: 호스트 IP가 외부에 열려 있으면 DB가 인터넷에 노출. 보안 그룹 misconfig 시 즉시 침해.

False positive: 개발 전용 `docker-compose.dev.yml` 같이 분리된 파일. 파일명/주석 함께 확인.

수정: `127.0.0.1:5432:5432` 또는 `expose:` 만 사용(같은 네트워크 컨테이너만 접근).

## 2. Dockerfile root 사용자

검출: `USER\s+root` 또는 `USER` 지시어 자체 부재.

위험: 컨테이너 탈출 시 호스트 권한.

수정: `RUN adduser --system app && USER app`.

## 3. base image `latest` 태그

검출: `FROM\s+\w+:latest`

위험: 빌드 재현성 손실. 보안 업데이트 추적 불가.

수정: 명시적 버전 + digest pinning(`FROM node:20.11.0@sha256:...`).

## 4. nginx CORS 헤더 + Spring 동시 설정

검출: `add_header\s+Access-Control-Allow-Origin` (nginx) + Spring `CorsConfiguration` 동시 존재.

위험: 두 곳에서 헤더가 중복 설정되면 브라우저가 헤더 다중 값으로 인식해 CORS 실패. 또는 한 곳의 화이트리스트만 보고 안심하기 쉬움.

수정: 한 군데에서만 처리. 일반적으로 애플리케이션 레벨 권장.

## 5. nginx `X-Forwarded-For` 패스스루

검출: nginx에서 `proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for` + 앱이 직접 헤더 신뢰.

위험: 클라이언트가 `X-Forwarded-For: 1.2.3.4` 헤더를 위조해 보내면 그대로 통과.

수정: `proxy_set_header X-Real-IP $remote_addr` + 앱은 `X-Real-IP`만 신뢰. 또는 `X-Forwarded-For`를 nginx에서 덮어쓰기.

## 6. HTTPS 리다이렉트 / HSTS 미적용

검출: nginx `server { listen 80; ... }` 블록에 `return 301 https://...` 없음. `Strict-Transport-Security` 헤더 없음.

위험: HTTP 평문 접속 가능, 다운그레이드 공격.

수정:
```nginx
server {
  listen 80;
  return 301 https://$host$request_uri;
}
server {
  listen 443 ssl http2;
  add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
  ...
}
```

## 7. `server_tokens` 미차단

검출: nginx 설정에 `server_tokens off;` 없음.

위험: 응답 헤더에 nginx 버전 노출 → 알려진 CVE 매칭 용이.

수정: `http { server_tokens off; }`.

## 8. 보안 헤더 누락

검출: nginx/Spring/NestJS Helmet 미사용 또는 다음 헤더 부재 — `X-Frame-Options`, `X-Content-Type-Options`, `Content-Security-Policy`, `Referrer-Policy`.

수정: `helmet()` 미들웨어(NestJS), `HttpHeadersConfigurer`(Spring), `add_header`(nginx).

## 9. EC2 / 보안 그룹 전 노출

체크: Terraform / CloudFormation / CDK에서 보안 그룹 `0.0.0.0/0` 인바운드가 80/443/22 외 포트에 적용되어 있는지.

위험: DB/관리 포트가 인터넷 노출.

수정: 80/443만 0.0.0.0/0. 22는 회사 IP/Bastion만. DB 포트는 VPC 내부만.

## 10. `.env` git 추적

검출: `.gitignore`에 `.env` 미등록 + 실제로 `.env` 파일이 git ls-files에 존재.

위험: 시크릿 리포지토리 영구 노출.

수정: `.gitignore`에 `.env*`(except `.env.example`) 추가. 이미 커밋된 경우 `git filter-repo`로 히스토리 재작성 + 키 즉시 회전.

## 11. CI/CD에 평문 시크릿

검출: GitHub Actions YAML에 `password:\s*[^${]`, GitLab CI `variables:` 평문.

위험: 워크플로 로그/PR diff에 노출.

수정: GitHub Secrets / OIDC + AWS IAM Role + Secrets Manager.
