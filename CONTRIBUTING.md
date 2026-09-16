# Contributing to NEXUS

NEXUS is an engineering project focused on Linux observability, diagnostics, controlled operations, and practical systems programming.

Contributions should improve **correctness, safety, maintainability, or operational value**. New functionality should have a clear reason to exist and should integrate with the existing domain model rather than creating parallel logic.

---

## Development environment

NEXUS targets Python 3.11+ and is developed primarily on CachyOS/Linux.

Create an isolated environment before installing the project:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Run the complete test suite with:

```bash
python -m unittest discover -s tests -v
```

Do not use `--break-system-packages` as a substitute for an isolated development environment.

---

## Engineering workflow

### 1. Understand the boundary

Before changing code, identify whether the change belongs to:

- observation,
- diagnostics/analysis,
- planning,
- execution,
- persistence/audit,
- scheduling,
- or presentation.

Avoid moving system-management logic into GUI code or duplicating domain behavior between CLI and GUI implementations.

### 2. Create a focused branch

Use a descriptive branch name:

```text
feat/historical-trends
fix/scheduler-error-handling
refactor/service-adapter
```

### 3. Implement the smallest complete behavior

Prefer a complete vertical slice over a collection of unrelated partial features.

A useful change should normally include:

```text
implementation → tests → documentation → commit
```

### 4. Add deterministic tests

Changes involving system commands should use injectable runners or fixtures where possible.

Do not make the test suite depend on the current state of the developer's machine.

### 5. Run verification locally

At minimum:

```bash
python -m unittest discover -s tests -v
```

If the change affects packaging, CLI entry points, scheduler behavior, or the GUI, perform an additional smoke test of the affected interface.

### 6. Update documentation

User-visible behavior belongs in the README or relevant documentation. Significant architectural changes belong in `docs/architecture.md`. Release-visible changes belong in `CHANGELOG.md`.

### 7. Commit clearly

Use concise conventional-style commit messages:

```text
feat: add historical observation store
fix: handle unavailable systemd service
refactor: isolate package command adapter
test: cover scheduler persistence failures
docs: clarify confirmation model
```

Avoid commits such as `update`, `changes`, or `stuff` because they make project history difficult to understand.

### 8. Open a pull request

A pull request should explain:

- what changed,
- why it changed,
- how it was tested,
- whether system behavior can be modified,
- and any follow-up work that remains.

Keep the PR focused enough that another developer can reason about it without reconstructing the entire project history.

---

## Safety requirements

NEXUS interacts with the host operating system. Safety is therefore an architectural requirement, not merely a documentation preference.

### Read-only by default

New inspection functionality should not mutate packages, services, files, or system configuration.

### Explicit mutation boundary

Any new mutating capability must provide:

1. a structured action proposal,
2. a clear description of the affected resource,
3. explicit user confirmation,
4. a controlled execution path,
5. deterministic tests using an injected runner where possible,
6. an audit record for the decision and result.

### No arbitrary shell execution

Do not add interfaces that accept unrestricted shell strings for convenience. Prefer structured argument lists and narrowly defined adapters.

### Scheduler restrictions

Scheduled operations must remain allow-listed. A scheduler job must not become an arbitrary command runner.

### Sensitive information

Do not commit:

- passwords,
- access tokens,
- private keys,
- personal system logs containing sensitive data,
- environment dumps,
- or machine-specific secrets.

Audit records should contain operational metadata rather than command output or secrets.

---

## Documentation standard

Documentation should describe behavior that actually exists.

Avoid claiming:

- tests passed when they were not run,
- CI succeeded without verifying the workflow result,
- support for distributions that are not implemented,
- security properties that have not been demonstrated,
- or stability beyond the current release status.

When a feature is experimental, label it as such.

---

## Design philosophy

NEXUS should become more capable without becoming less understandable.

When choosing between two implementations, prefer the one that is:

- easier to test,
- easier to explain,
- explicit about side effects,
- reusable by both CLI and GUI,
- and honest about its limitations.

The project is intentionally optimized for **learning through real systems engineering**, not for maximizing feature count.
