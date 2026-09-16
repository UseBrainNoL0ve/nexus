# NEXUS Diagnostics

This document describes the diagnostic, incident, and remediation-planning layers introduced in the NEXUS operations pipeline.

## Why a diagnostic layer?

A system monitor answers **what is happening now**. A diagnostic engine should additionally answer:

- what evidence indicates a problem;
- how severe the finding is;
- whether the condition is current or persistent;
- which findings belong to the same operational incident;
- what remediation could be considered;
- whether that remediation requires authorization.

NEXUS keeps those questions separate from execution.

## Finding model

A diagnostic finding contains structured information:

```text
id
category
severity
title
evidence
recommendation
requires_confirmation
```

Examples include:

- sustained memory pressure;
- sustained disk pressure;
- sustained CPU pressure;
- a failed systemd service;
- available package updates.

Findings are deterministic. The same evidence should produce the same finding set.

## Historical trend detection

`nexus-observe` stores snapshots as JSON Lines under `.nexus/observations.jsonl`.

Trend detection currently requires at least three observations and checks persistent conditions rather than isolated spikes:

| Metric | Persistent condition | Severity |
| --- | --- | --- |
| Memory | all of the last three observations are ≥ 90% | warning |
| Disk | all of the last three observations are ≥ 85% | warning |
| CPU | all of the last three observations are ≥ 80% | info |

These are implementation thresholds for explainable detection, not universal definitions of an unhealthy Linux system.

## Incident model

An incident is a higher-level grouping of related findings.

Conceptually:

```text
Finding A ─┐
Finding B ─┼──> Incident
Finding C ─┘
```

The incident preserves the underlying evidence instead of replacing it with a score. This allows a user or another program to inspect why NEXUS created the incident.

An incident can carry:

- stable identifier;
- severity;
- title;
- related finding identifiers;
- evidence;
- status;
- creation/update timestamps;
- confirmation requirements.

The initial grouping rules are deliberately deterministic and small. More sophisticated correlation can be added later without changing the mutation boundary.

## Remediation plans

A remediation proposal is not an executed action.

A proposal should expose:

```text
action
rationale
evidence
risk
command representation
requires_confirmation
```

For example, a failed service may produce a proposal to inspect its journal before considering a restart. A package update finding may produce a confirmation-gated update proposal.

The diagnostic and remediation layers do not invoke those commands.

## Safety boundary

The operational state machine is:

```text
OBSERVE
   ↓
DIAGNOSE
   ↓
GROUP INTO INCIDENT
   ↓
PREPARE REMEDIATION
   ↓
REQUIRE CONFIRMATION
   ↓
EXECUTE CONTROLLED ACTION
   ↓
AUDIT RESULT
```

Only the final controlled action stage may mutate the host, and existing service/package action engines enforce their own authorization rules.

A diagnostic finding must never be treated as implicit permission to execute its recommendation.

## CLI surfaces

### `nexus-diagnose`

Read-only diagnostic command with text and JSON output.

```bash
nexus-diagnose
nexus-diagnose --json
```

The JSON representation is intended to support future GUI and automation consumers without coupling them to human-readable terminal formatting.

### `nexus-observe`

Collects and persists a system observation, then reports historical trend findings.

```bash
nexus-observe
nexus-observe --limit 20
nexus-observe --json
```

## Testing

The diagnostic layer should be tested using synthetic snapshots and injected service/package evidence. Tests should verify both positive findings and the absence of findings when conditions do not meet the documented rules.

Important negative cases include:

- fewer than three observations;
- a single resource spike;
- a condition that recovers between observations;
- healthy service state;
- zero available package updates.

This keeps the detection model predictable and prevents an isolated metric spike from becoming an operational incident by accident.

## Future direction

The next architectural steps are expected to focus on:

1. integrating diagnostics into the primary `nexus diagnose` command;
2. exposing incidents in the desktop Operations Center;
3. adding historical visualization;
4. correlating service, package, network, and resource evidence more deeply;
5. connecting approved remediation plans to the existing confirmation-gated action engines;
6. expanding audit history so an incident can be traced from first observation to final action result.

The project should remain deterministic and explainable before introducing more complex automated decision-making.
