# Pilot Deployment Runbook

Project RISING Phase 5 is intended for a controlled, monitored pilot. It is
not clinically validated and must not be the sole basis for patient care,
national surveillance, or emergency-response decisions.

## Required production configuration

Set `APP_ENV=production`, `REQUIRE_API_KEY=true`, a random `API_KEY` of at
least 16 characters, explicit HTTPS dashboard origins in `CORS_ORIGINS`, and
the externally visible host names in `TRUSTED_HOSTS`. On Render, the service's
`RENDER_EXTERNAL_HOSTNAME` is added automatically; keep `TRUSTED_HOSTS` for
any additional custom domains. Keep secrets in the deployment platform's
secret manager, never in git or a container image.

`DATABASE_REQUIRED=false` is correct while the checked-in CSV remains the API's
authoritative data source. Set it to `true` only after provisioning PostgreSQL
and setting `DATABASE_URL`; `/ready` will then fail closed when PostgreSQL is
unavailable.

## Deploy and verify

```bash
cp .env.example .env
# Edit every placeholder secret and origin before continuing.
docker compose up --build -d api postgres
curl --fail http://localhost:8000/health
curl --fail http://localhost:8000/ready
curl --fail -H "X-API-Key: $API_KEY" http://localhost:8000/metrics
docker compose logs --tail=100 api
```

Use the included `render.yaml` as a Render Blueprint. Configure
`CORS_ORIGINS` and any additional custom domains in `TRUSTED_HOSTS` before
traffic is enabled. Render's generated external hostname is trusted
automatically. TLS must terminate at the managed load balancer or reverse
proxy.

After each Render deployment, run the committed live smoke test:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/smoke_render.ps1
```

## Monitoring and alert thresholds

Scrape `/metrics` with the API key. Alert when `/ready` returns 503 for two
consecutive checks, any 5xx rate exceeds 1% for five minutes, p95 latency
exceeds two seconds, an ETL run produces no usable datasets, or DLQ volume
increases unexpectedly. Logs are JSON and correlate on `request_id`; do not
log API keys, database URLs, raw sensitive payloads, or personal data.

## Backup and restore

The repository's CSV sources must be versioned or copied to immutable object
storage after each approved data release. For PostgreSQL, take encrypted daily
logical backups and test restoration at least quarterly:

```bash
docker compose exec -T postgres pg_dump -U rising_user -d project_rising -Fc > backups/project_rising.dump
docker compose exec -T postgres pg_restore -U rising_user -d project_rising --clean --if-exists < backups/project_rising.dump
```

Run restore drills against an isolated database, never the active pilot.
Document recovery time, row counts, checksums, and the operator who approved
the recovery. Volume snapshots are useful but do not replace tested logical
backups.

## Incident and rollback procedure

1. Remove pilot traffic or scale the API to zero if confidentiality or data
   integrity may be affected.
2. Preserve JSON logs, request IDs, image digest, configuration version, and
   database audit evidence without copying secrets.
3. Roll back to the last tested container digest and last approved dataset.
4. Verify `/health`, `/ready`, smoke queries, data counts, and metrics before
   reopening access.
5. Record impact, root cause, corrective action, and validation evidence.

Rotate the API key immediately after exposure or staff access changes. Apply
dependency and base-image security updates through reviewed pull requests.
External penetration testing, privacy review, epidemiological validation,
high availability, disaster-recovery exercises, and country-specific legal
approval remain Phase 6 prerequisites for mission-critical use.
