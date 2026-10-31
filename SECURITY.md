# Security policy

Hisaab handles sensitive financial documents, so please report vulnerabilities privately.

- Do **not** open a public issue with exploit details or real documents.
- Use your hosting platform's private vulnerability reporting for the repository (e.g. GitHub "Report a vulnerability"), or the contact address the maintainers publish.
- Include steps to reproduce using synthetic data.

## Built-in protections
Signature-based file validation, size/page limits, random job IDs plus per-job secret tokens, private temp storage with expiry, narrow CORS, rate limiting, safe error messages, CSV/XLSX formula-injection protection, no document contents in logs.

## Known limits
In-memory rate limiting is per-process; results live in server memory; deletion cannot reach host-level backups or snapshots; the app has no user accounts. See `docs/ARCHITECTURE.md`.
