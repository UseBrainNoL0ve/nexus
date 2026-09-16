# Contributing to NEXUS

NEXUS is a learning-focused Linux engineering project. Contributions should improve the system as both software and an understandable engineering artifact.

## Development workflow

1. Create a focused feature branch from the intended base.
2. Understand the existing domain boundary before adding a new system integration.
3. Implement the smallest coherent unit of behavior.
4. Add deterministic tests for new decision logic and safety boundaries.
5. Update relevant Markdown documentation when user-visible behavior or architecture changes.
6. Run the full local test suite:

   ```bash
   python -m unittest discover -s tests -v
   ```

7. Review the diff for accidental command execution, secrets, generated files, or unrelated changes.
8. Commit with a conventional message such as `feat: add historical trend detection` or `docs: document diagnostic pipeline`.
9. Open a pull request that explains behavior, safety implications, tests, and any local validation still required.

## Architecture rules

NEXUS follows this general direction:

```text
Observation → Diagnosis → Incident → Plan → Confirmation → Action → Audit
```

Keep these responsibilities separate.

- **Observation** collects system state and must not mutate the host.
- **Diagnosis** interprets evidence using deterministic rules.
- **Incident modeling** groups findings without executing remediation.
- **Planning** proposes an operation and explains why it is relevant.
- **Confirmation** is the authorization boundary for mutation.
- **Action engines** perform only explicitly supported operations.
- **Audit** records operational decisions without leaking command output or secrets.

Do not bypass these layers merely to make a feature shorter.

## Safety requirements

Any operation capable of changing packages, services, files, permissions, or system configuration must have an explicit authorization boundary.

Avoid:

- arbitrary shell execution from high-level features;
- hidden background mutations;
- automatic package installation or removal;
- service restarts triggered solely by a diagnostic finding;
- storing command output or environment secrets in audit records.

Prefer:

- read-only inspection first;
- dry-run or proposal-only behavior;
- allow-listed operations;
- argument sequences rather than shell strings;
- injectable command runners for tests;
- explicit confirmation immediately before mutation.

## Testing system integrations

System integrations should be testable without depending on a particular live host state. Where subprocesses are required, inject a runner or isolate parsing from execution.

For historical detection and diagnostics, tests should cover both positive and negative cases. In particular, a single resource spike should not be treated as equivalent to a persistent trend unless the documented rule says so.

## Documentation expectations

Update documentation when adding:

- a CLI command or option;
- a new persistent data file;
- a safety or authorization boundary;
- a new architectural layer;
- a user-visible GUI workflow;
- a new milestone or completed roadmap item.

At minimum, consider `README.md`, `docs/architecture.md`, `docs/diagnostics.md`, and `CHANGELOG.md` where applicable.

## Pull requests

A useful PR description should include:

- **What changed** — concise implementation summary;
- **Why** — the user or engineering problem being addressed;
- **Safety** — whether the change can mutate the host;
- **Tests** — exact local validation performed;
- **Documentation** — files updated when behavior changed;
- **Follow-ups** — known limitations or next architectural steps.

Keep PRs coherent enough that another developer can understand the change without reconstructing the entire project history.
