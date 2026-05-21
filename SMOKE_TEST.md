# defend/당근 보안 감사 워크플로우 동작 확인용 스모크 테스트 (검증 후 PR은 close)
# Security Audit Smoke Test

본 PR은 `defend/당근` 브랜치에 추가한 `.github/workflows/security-audit.yml` 워크플로우가 실제로 트리거되는지 확인하기 위한 검증용입니다.

## 확인 항목

- [ ] `pull_request` 이벤트가 `defend/**` 패턴에서 fire 되는가
- [ ] OWASP Dependency-Check 실행
- [ ] npm audit 실행
- [ ] Semgrep SAST 실행
- [ ] Gitleaks 시크릿 스캔 실행
- [ ] `security-report` 아티팩트 업로드

검증 완료 후 본 PR은 머지하지 않고 close 합니다.
