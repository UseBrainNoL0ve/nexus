# NEXUS Usage Guide

This guide is the practical manual for running NEXUS on a Linux host. It explains what each command does, what it does **not** do, how to interpret the output, and where the authorization boundary begins.

## 1. What NEXUS is for

NEXUS is designed to turn common Linux maintenance and troubleshooting into a repeatable workflow:

```text
Observe → Diagnose → Understand → Plan → Authorize → Act → Audit
```

The important design rule is that inspection and diagnosis do not silently mutate the machine.

Use NEXUS when you want to answer questions such as:

- What is my system doing right now?
- Is something obviously unhealthy?
- Which signals deserve attention?
- What evidence caused NEXUS to flag them?
- What action is being proposed?
- What risk and confirmation boundary applies?
- What actions were actually executed later?

---

## 2. Installation

NEXUS requires Python 3.11 or newer.

### Recommended: system-wide command installation

For a normal end-user installation, NEXUS should be installed as an application rather than activated from the repository's development virtual environment. `pipx` keeps NEXUS isolated from the OS Python while exposing its commands on `PATH`.

For all users on a Linux machine, after cloning the repository:

```bash
git clone https://github.com/UseBrainNoL0ve/nexus.git
cd nexus
sudo pipx install --global .
sudo pipx ensurepath --global
```

Open a new terminal and verify:

```bash
command -v nexus
nexus --help
nexus-gui --help
```

This does **not** mean NEXUS runs from `.venv`. `pipx --global` creates and manages its own isolated application environment and exposes the NEXUS entry points system-wide. The repository `.venv` remains useful only for development and testing. citeturn0search1turn0search7

For a single-user installation, omit `--global` and `sudo`:

```bash
pipx install .
pipx ensurepath
```

`pipx` is the preferred application-installation model because it avoids modifying the distribution-managed Python environment while still making the command available outside the source checkout. citeturn0search2turn0search10

### Development installation

If you are actively changing NEXUS itself, a repository-local virtual environment is still appropriate:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Development and end-user installation are deliberately separate paths.

---

## 3. The recommended first command: `nexus diagnose`

If you do not know where to start, use:

```bash
nexus diagnose
```

This is the main user-facing diagnostic workflow. It collects available evidence, derives deterministic findings, groups related findings into incidents, and produces remediation proposals.

A typical flow is:

```text
Current Linux state
       ↓
Diagnostic evidence
       ↓
Findings
       ↓
Incidents
       ↓
Remediation proposals
```

The command is read-only. It does not execute the remediation proposals it prints.

### Machine-readable diagnosis

For scripts or other tools:

```bash
nexus diagnose --json
```

The JSON output contains fields such as:

- `finding_count`
- `findings`
- `incident_count`
- `incidents`
- `remediation_steps`
- `collection_errors`
- `read_only`

The JSON form is intended to be stable enough for local integrations while remaining human-readable.

---

## 4. Understanding `nexus status`

Run:

```bash
nexus status
```

This is the fastest live snapshot. It reports:

- operating-system/platform information
- kernel
- hostname
- CPU load percentage
- logical CPU count
