# Controlled Failure-Recovery Evidence

## Record

- Drill ID: `FR-2026-07-23-01`
- Commit tested: `cc9e6a8` (`Trust Render external hostname`)
- Executed: `2026-07-24T02:54:19.780672+00:00` (`2026-07-23` America/New_York)
- Environment: isolated local FastAPI test application
- Operator: Codex-assisted controlled test
- Production impact: none
- Result: passed

## Objective

Verify that the API fails readiness closed when its required health dataset is
unavailable and returns to ready on the first verification request after the
dataset is restored.

## Safety controls

The application ran with `environment=test`, a temporary dataset path, no
production traffic, no production data, and no required database. The temporary
directory was removed after the drill. This was a readiness-control test, not a
production disaster-recovery exercise.

## Procedure and observations

1. Start the application with the required health dataset pointing to a missing
   temporary file.
2. Request `/ready` and verify HTTP 503 with the dataset check marked `fail`.
3. Restore a minimal valid controlled dataset at the same path.
4. Request `/ready` again and verify HTTP 200 with the dataset check marked
   `pass`.

| State | Expected | Observed | Request ID |
| --- | --- | --- | --- |
| Dataset unavailable | `503 not_ready` | `503 not_ready` | `6bd5c54f-fd41-4b60-9a89-c364067dae1a` |
| Dataset restored | `200 ready` | `200 ready` | `2e5a2672-bebe-4d0c-b78e-5ae6233fe37f` |

Failure response:

```json
{
  "status": "not_ready",
  "checks": {
    "health_dataset": {"status": "fail", "required": true},
    "database": {"status": "not_configured", "required": false}
  }
}
```

Recovery response:

```json
{
  "status": "ready",
  "checks": {
    "health_dataset": {"status": "pass", "required": true},
    "database": {"status": "not_configured", "required": false}
  }
}
```

The recovery request completed in `6.66 ms` in the isolated test environment.
The API recovered on the first verification request after restoration.

## Acceptance and limitations

The drill passed because the API rejected readiness while a required dependency
was missing and automatically recovered without a process restart after that
dependency returned. The automated regression is
`test_readiness_fails_and_recovers_when_dataset_is_restored`.

This evidence does not establish a production recovery-time objective, database
restore capability, multi-instance failover, or regional disaster recovery.
Those require separate controlled exercises before mission-critical use.
