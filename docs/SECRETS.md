# Secrets & Variables Reference (Anonymized Template)

Complete anonymized reference for every secret and variable needed across GitHub Actions, Google Cloud, and Hugging Face. Organized by where you set it, not where it ends up.

---

## GitHub Actions — Repository Variables (`vars.*`)

Set at **Settings → Secrets and variables → Actions → Variables**.  
Non-sensitive — visible in workflow logs, safe to commit as defaults.

| Name | Used in workflow | Example value |
|------|-----------------|---------------|
| `GCP_WIF_PROVIDER` | `deploy-agent-api` | `projects/000000000000/locations/global/workloadIdentityPools/pool-example/providers/provider-example` |
| `GCP_DEPLOY_SA_EMAIL` | `deploy-agent-api` | `deploy-bot@example-project.iam.gserviceaccount.com` |
| `GCP_REGION` | `deploy-agent-api` | `region-example1` |
| `GCP_PROJECT_ID` | `deploy-agent-api` | `example-project-id` |
| `GCP_ARTIFACT_REPOSITORY` | `deploy-agent-api` | `repo-example` |
| `CLOUD_RUN_SERVICE` | `deploy-agent-api` | `service-example-api` |
| `CLOUD_RUN_RUNTIME_SA_EMAIL` | `deploy-agent-api` | `runtime-sa@example-project.iam.gserviceaccount.com` |
| `HF_USERNAME` | `deploy-hf-app` | `example-hf-user` |
| `HF_SPACE_NAME` | `deploy-hf-app` | `example-space-name` |

---

## GitHub Actions — Repository Secrets (`secrets.*`)

Set at **Settings → Secrets and variables → Actions → Secrets**.

| Name | Used in workflow | Description |
|------|-----------------|-------------|
| `HF_TOKEN` | `deploy-hf-app` | Hugging Face write token with Space push permission (`write` scope on the target Space) |

> **Why only HF_TOKEN here?** All GCP secrets are fetched at runtime by Cloud Run via Secret Manager — the deploy job only needs OIDC federation (`id-token: write`), no GCP secrets in GitHub.

---

## Google Secret Manager

Secrets injected into the Cloud Run container at deploy time via `--update-secrets`.  
The runtime service account (for example `runtime-sa@...`) needs `roles/secretmanager.secretAccessor` on each.

| Secret name | Env var in container | Description |
|-------------|---------------------|-------------|
| `GOOGLE_API_KEY` | `GOOGLE_API_KEY` | API key from your LLM provider console |
| `PROXY_AUTH_TOKEN` | `PROXY_AUTH_TOKEN` | Shared relay auth token — must match the frontend value exactly |
| `TURNSTILE_SECRET_KEY` | `TURNSTILE_SECRET_KEY` | Turnstile/anti-bot server-side secret |
| `DATABASE_URL` | `DATABASE_URL` | PostgreSQL connection string (see formats below) |

### `DATABASE_URL` formats

**External provider (Supabase, Neon, Railway — SSL required over TCP):**
```
postgresql+asyncpg://db_user:db_password@db.host.example.net/app_db?ssl=require
```
The `_build_engine_kwargs()` function also injects `ssl=require` automatically for TCP connections.

**Google Cloud SQL via Auth Proxy (Unix socket — no SSL needed, already secured):**
```
postgresql+asyncpg://db_user:db_password@/app_db?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME
```
The code detects the Unix socket pattern and skips SSL injection.

**Local development fallback (no `DATABASE_URL` set):**
```
sqlite+aiosqlite:///local_dev.db
```

---

## Hugging Face Space — Settings → Variables and Secrets

Set at **Space → Settings → Variables and Secrets**.

| Name | Type | Description |
|------|------|-------------|
| `AGENT_API_URL` | Secret | Backend service URL, e.g. `https://service-example-abc-uc.a.run.app` |
| `PROXY_AUTH_TOKEN` | Secret | Must match the `PROXY_AUTH_TOKEN` in Secret Manager exactly |
| `TURNSTILE_SITE_KEY` | Variable (public) | Cloudflare Turnstile site key — safe to expose, rendered in the browser |

---

## One-time GCP Infrastructure Setup

These commands are run once when provisioning the project. They are not in CI.

### Workload Identity Federation

```bash
# Create WIF pool
gcloud iam workload-identity-pools create "github" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --display-name="GitHub Actions"

# Create provider
gcloud iam workload-identity-pools providers create-oidc "github" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --workload-identity-pool="github" \
  --display-name="GitHub Actions OIDC" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"
```

### Artifact Registry tag immutability

Prevents any tag (including SHA tags) from being overwritten after push.

```bash
gcloud artifacts repositories update "${REPO_NAME}" \
  --location="${REGION}" \
  --immutable-tags
```

Run this once after creating the Artifact Registry repository. All subsequent image pushes will be immutable.

### Cloud SQL (if using managed PostgreSQL)

```bash
# Create instance (smallest viable: db-f1-micro, ~$7/mo)
gcloud sql instances create app-db-instance \
  --database-version=POSTGRES_16 \
  --tier=db-f1-micro \
  --region="${REGION}" \
  --storage-auto-increase

# Create database and user
gcloud sql databases create app_db --instance=app-db-instance
gcloud sql users create appuser \
  --instance=app-db-instance \
  --password="${DB_PASSWORD}"

# Grant Cloud Run runtime SA access via Cloud SQL
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${CLOUD_RUN_RUNTIME_SA_EMAIL}" \
  --role="roles/cloudsql.client"

# Store connection string in Secret Manager
echo -n "postgresql+asyncpg://appuser:${DB_PASSWORD}@/app_db?host=/cloudsql/${PROJECT_ID}:${REGION}:app-db-instance" \
  | gcloud secrets create DATABASE_URL --data-file=-
```
