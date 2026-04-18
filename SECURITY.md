# Security Policy

## Design Principles

This project assumes public source code and enforces security at every boundary. See the [Security Architecture](README.md#security-architecture-devsecops) section in the README for the full threat model and design rationale.

Key properties:

- **Zero GCP secrets in GitHub** — runtime secrets live in Google Secret Manager
- **Workload Identity Federation** — no JSON service account keys
- **Fail-closed** — missing secrets cause the API to reject all requests
- **Non-root container** — Docker image runs as `appuser`
- **Immutable images** — Git SHA tags in Artifact Registry
- **SHA-pinned Actions** — no mutable tags in CI/CD

## Reporting a Vulnerability

If you discover a security issue, please report it privately:

1. **Do not** open a public GitHub issue.
2. Email the maintainer or use GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability) feature on this repository.
3. Include a description of the issue, steps to reproduce, and any relevant logs or screenshots.

You can expect an initial response within 72 hours. Accepted vulnerabilities will be patched and disclosed responsibly.
