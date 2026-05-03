# Codex Prompt 05 — Security Review

Perform a security review of the whole repository.

Check:

- no secrets in code.
- no credentials in logs.
- no unsafe file reads.
- no write operation without permission.
- no execute operation without permission.
- no destructive operation without confirmation.
- no `sensitive_info=True` by default.
- safe defaults in config.
- dataset previews are limited.
- file reads are limited.
- logs are limited.
- redaction tests exist.
- permission tests exist.

Create a `SECURITY_REVIEW_REPORT.md` with:

- findings.
- severity.
- affected files.
- recommended fixes.
- fixed/not fixed status.
