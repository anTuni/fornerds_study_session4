---
name: team-security-ci
description: Add or adapt the team's standard GitHub Actions security CI workflow for Java/Spring and React/Vite projects, including dependency scans, SAST, secret scanning, Trivy, custom OWASP checks, PR reporting, and required status check guidance. Use when a user asks to install, create, standardize, or update a project security workflow based on this study repository.
---

# Team Security CI

Use this skill to add the team's standard security automation to a repository.

## Workflow

1. Inspect the project layout.
   - Find backend build files: `pom.xml`, `build.gradle`, or `gradlew`.
   - Find frontend build files: `package.json` and lockfile.
   - Identify project root, backend directory, frontend directory, Java version, Node version, and default protected branch.

2. Add or update these files.
   - `.github/workflows/team-security-audit.yml`
   - `.github/scripts/security_custom_scan.py`
   - `.github/scripts/security_report.py`

3. Adapt workflow `env` values.
   - `PROJECT_ROOT`: root directory to scan.
   - `BACKEND_DIR`: backend directory containing the Java build file.
   - `FRONTEND_DIR`: frontend directory containing `package.json`.
   - `JAVA_VERSION`: default `17` unless the project requires another version.
   - `NODE_VERSION`: default `20` unless the project requires another version.
   - `DEPENDENCY_CHECK_CVSS`: default `7.0`.
   - `NPM_AUDIT_LEVEL`: default `high`.

4. Keep these standard jobs unless the project does not have that layer.
   - `Backend test`
   - `Frontend build`
   - `Dependency scan`
   - `npm audit`
   - `Semgrep SAST`
   - `Trivy fs/config`
   - `Gitleaks`
   - `Custom OWASP scan`
   - `Security report`
   - `Security gate`

5. If a layer does not exist, remove only that job and remove it from `security-report.needs`.
   - No Java backend: remove `backend-test` and `dependency-scan`.
   - No Node frontend: remove `frontend-build` and `npm-audit`.
   - Keep `semgrep`, `trivy`, `gitleaks`, `custom-owasp-scan`, `security-report`, and `security-gate` for most repositories.

6. Configure branch protection after the workflow lands.
   - Required status check: `Security gate`.
   - Recommended additional checks: `Backend test`, `Frontend build`, `Semgrep SAST`, `Gitleaks`.
   - Require at least one approving review.

## Validation

After editing:

```bash
python -m py_compile .github/scripts/security_custom_scan.py .github/scripts/security_report.py
python .github/scripts/security_custom_scan.py --root "${PROJECT_ROOT:-.}" --out /tmp/security-custom-scan.json --fail-on never
git diff --check
```

If `actionlint` is installed, also run:

```bash
actionlint .github/workflows/team-security-audit.yml
```

## Notes

- Do not print raw secrets in reports. The custom scanner redacts secret-like assignment values.
- Prefer artifact + PR comment + job summary together: artifact has detail, PR comment has review signal, job summary helps Actions triage.
- Keep the final gate job name stable as `Security gate`; branch protection depends on this exact check name.
