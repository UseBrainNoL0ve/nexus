# System-wide installation

NEXUS can be installed as a normal Linux command without requiring the repository's `.venv` and without creating a pipx-managed application environment.

## Native `/usr/local` installation

From a checked-out NEXUS repository:

```bash
cd ~/nexus
sudo ./scripts/install-system.sh
```

The installer uses the host's `python3`, installs NEXUS and its Python dependencies into `/usr/local/lib/pythonX.Y/site-packages`, and creates executable launchers under `/usr/local/bin`.

Verify:

```bash
command -v nexus
nexus --help
nexus status
nexus-capture status
```

The same installation exposes:

```text
nexus
nexus-gui
nexus-scheduler
nexus-observe
nexus-diagnose
nexus-summary
nexus-plugins
nexus-capture
```

`nexus-capture` is the current privacy-first capture lifecycle interface. Its default policy is disabled and the capture backend fails closed until an explicitly approved platform backend is installed and enabled.

## What this changes

The end-user workflow no longer requires:

```bash
source .venv/bin/activate
```

and it does not use `pipx`.

The repository `.venv` remains a development tool for tests and editable development installs. The system installer is intended for using NEXUS as a regular host command.

## Custom prefix

The installer defaults to `/usr/local`. A different prefix can be selected explicitly:

```bash
sudo NEXUS_PREFIX=/opt/nexus ./scripts/install-system.sh
```

The selected prefix must be on the user's `PATH` if commands are expected to be invoked without their full path.

## Important packaging boundary

This installer intentionally targets `/usr/local` instead of the distribution-managed `/usr/lib/pythonX.Y/site-packages`. That keeps NEXUS separate from files owned by the OS package manager while still using the system Python interpreter directly.

For distribution-integrated packaging, a future Arch/CachyOS PKGBUILD and equivalent packages for other distributions can be added without changing the NEXUS CLI contract.
