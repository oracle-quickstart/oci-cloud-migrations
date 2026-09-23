# Bar 6: End-to-End Ready

**Purpose:** All required prerequisites for the customer's migration scenario are in place.

**Dependencies:** All other bars (this is a composite check).

**Required for:** All scenarios.

## Resources

None — this bar does not validate additional resources. It aggregates the results of bars 1-5.

## Scenario requirements

| Scenario | Bar 1 | Bar 2 | Bar 3 | Bar 4 | Bar 5 |
|----------|-------|-------|-------|-------|-------|
| VMware to OCI | Required | Required | Required | Required | Required |
| AWS to OCI | Required | Required | Required | Required | Required |
| VMware to OLVM | Required | Required | Required | Required | — |

## Validation

**Step 1:** Confirm the customer's migration scenario (VMware to OCI / AWS to OCI / VMware to OLVM).

**Step 2:** Check that every required bar for the scenario is green.

**Step 3:** Present the tracker summary.

## Tracker presentation format

Present results as a milestone tracker:

```
Migration Prerequisites — [Scenario]

  [status] Bar 1: Identity Foundation — [explanation]
  [status] Bar 2: Compartment Structure — [explanation]
  [status] Bar 3: Service Authorization — [explanation]
  [status] Bar 4: Encryption — [explanation]
  [status] Bar 5: Storage — [explanation or "not required for this scenario"]
  ────────────────────────────────────
  [status] Ready to proceed with discovery
```

Status indicators: green = complete, yellow = partial or stale, red = missing or failed, blocked = dependency failed, unavailable = evidence could not be read, not required = omitted for this scenario.

For each non-green bar, include a one-line explanation of what's wrong and what to do next.

## Status criteria

| Status | Condition |
|--------|-----------|
| Green | All required bars for the scenario are green |
| Red | At least one required bar is red or blocked; a proven failure makes overall readiness not ready even when another bar is unavailable |
| Unavailable | No required bar is red or blocked, and at least one required bar is unavailable; overall readiness is unknown |
| Yellow | No required bar is unavailable, red, or blocked, and at least one is yellow |

## After assessment

- **All green** → "Your prerequisites are in place. You can proceed with discovery and migration planning."
- **Red bars present, no stack** → "Prerequisites have not been set up yet." Guide through RMS stack creation and report any unavailable evidence separately.
- **Red bars present, stack exists** → "Your prerequisite stack has issues." Diagnose per-bar, report any unavailable evidence separately, and guide remediation.
- **Yellow bars present** → "Your prerequisites are partially in place but need updates." Guide through RMS stack update.
- **Unavailable bars present without red or blocked bars** → "Readiness is unknown because required evidence could not be read." Report the failed checks and required access; do not report the tenancy ready.
