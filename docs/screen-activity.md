# NEXUS Screen Activity Capture

## Goal

NEXUS may provide an **opt-in local screen activity recorder** for incident investigation. The purpose is to help the device owner review what happened on their own desktop after an unexpected local or remote interaction.

This feature is intentionally different from covert monitoring software:

- disabled by default;
- explicit user action is required to start recording;
- a persistent local recording indicator must be visible while capture is active;
- the user can pause, resume, or permanently disable capture;
- recordings remain on the local machine and are never uploaded by NEXUS;
- recording files are protected as private user data;
- retention is configurable and automatic deletion is supported;
- NEXUS must never provide a hidden or remote-only switch that silently enables capture.

## Security model

The feature is designed around the following boundary:

```text
User consent
    ↓
Desktop capture portal
    ↓
Local recorder
    ↓
Private local storage
    ↓
Owner-controlled review
```

On Wayland, the preferred integration is the XDG Desktop Portal ScreenCast API. NEXUS first detects whether the Wayland session and the portal D-Bus endpoint are available; capability detection alone never starts a recording.

## Current implementation status

The capture foundation is implemented, but **actual frame recording is intentionally not enabled yet**.

Current pieces:

- explicit `CapturePolicy`, disabled by default;
- persistent local session metadata with restrictive permissions;
- explicit capture state machine;
- `CaptureBackend` interface with fail-closed behavior;
- `nexus-capture` lifecycle CLI;
- Wayland/XDG Portal capability detection through a short D-Bus ping;
- tests covering Pardus, Ubuntu, Fedora, Kali, Parrot, CachyOS package-manager selection and Wayland capability detection.

The `WaylandPortalBackend` refuses to enter a fake `recording` state until the PipeWire stream consumer is implemented. This is deliberate: a capability probe is not the same thing as a working recorder.

## Data handling

The default storage policy should be:

- local filesystem only;
- per-user directory with restrictive permissions;
- no network synchronization;
- no cloud API;
- no telemetry containing frames or recording metadata;
- configurable maximum retention period and storage quota;
- deletion through an explicit user action or the configured retention policy.

Because screen recordings can contain passwords, private messages, tokens, documents, and other sensitive material, NEXUS must treat recordings as sensitive user data. The UI should display this warning before first activation.

For stronger protection, the implementation should support encryption at rest using a key controlled by the user. The key must never be committed to the repository, written to the audit log, or transmitted to a remote service.

## Recording controls

The planned user-facing controls are:

```text
nexus capture status
nexus capture start
nexus capture pause
nexus capture resume
nexus capture stop
nexus capture list
nexus capture delete <id>
```

The currently installed standalone command is `nexus-capture`; integration of these subcommands into the main `nexus` CLI will happen with the recorder's user-facing activation work.

The GUI should expose the same state machine:

```text
OFF → STARTING → RECORDING → PAUSED → RECORDING → STOPPING → OFF
```

The state must be explicit and auditable. `start` and `resume` require the local user session to authorize the operation; `stop`, `pause`, and deletion must always remain available locally.

## Evidence correlation

The recorder should not try to infer intent from video. Instead, NEXUS can correlate a recording segment with its existing operational timeline:

- recording start/stop timestamps;
- NEXUS diagnostic events;
- service/package mutations;
- scheduler events;
- platform audit entries.

This allows the Incident Center to answer questions such as:

```text
What was happening on screen around this recorded NEXUS action?
```

without treating the video itself as a trusted security log.

## Platform strategy

NEXUS is distribution-agnostic at the capability layer. Screen capture therefore follows the desktop session and available portal capabilities rather than assuming one Linux distribution.

Preferred order:

1. XDG Desktop Portal ScreenCast + PipeWire on Wayland.
2. A supported desktop-specific backend only when its capability is explicitly detected.
3. A read-only `unsupported` state when no safe backend is available.

The feature must fail closed. If a backend cannot establish an interactive, user-authorized capture session, NEXUS should not silently fall back to an unrestricted screen-grabbing mechanism.

## Linux compatibility validation

The package backend mapping explicitly covers the requested distributions:

| Distribution | Package family | Service family commonly expected |
|---|---|---|
| CachyOS / Arch / Manjaro | pacman | systemd |
| Ubuntu / Debian / Mint | apt | systemd |
| Pardus | apt | systemd |
| Kali Linux | apt | systemd |
| Parrot OS | apt | systemd |
| Fedora / RHEL-family | dnf | systemd |
| openSUSE | zypper | systemd |
| Alpine | apk | OpenRC |
| Void | xbps | runit |
| Solus | eopkg | systemd |

This is **capability coverage, not a promise that every NEXUS feature is identical on every distribution**. Desktop capture also depends on the desktop session, Wayland/X11, portal implementation, PipeWire availability, permissions, and installed native tools.

## Non-goals

NEXUS will not implement:

- hidden recording;
- recording that starts without user authorization;
- remote activation of the recorder;
- bypassing Wayland/X11 desktop permissions;
- uploading recordings to GitHub, NEXUS servers, or third-party services;
- credential extraction or screen-content analysis intended to recover secrets.

## Implementation phases

1. ~~Capability detector and privacy configuration model.~~
2. ~~Capture state machine and local metadata model.~~
3. ~~Wayland portal capability foundation.~~
4. Implement the actual Portal ScreenCast + PipeWire stream recorder.
5. Add a visible GUI recording indicator and controls.
6. Add encrypted/private storage and retention management.
7. Add Incident Center correlation and tests.
8. Add X11 and other explicitly supported backends only where their security properties can be documented.
