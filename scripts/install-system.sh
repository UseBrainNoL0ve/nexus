#!/usr/bin/env bash
set -euo pipefail

PREFIX="${NEXUS_PREFIX:-/usr/local}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if [[ "${EUID}" -ne 0 ]]; then
    echo "error: run this installer with sudo" >&2
    echo "usage: sudo ./scripts/install-system.sh" >&2
    exit 1
fi

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
    echo "error: ${PYTHON_BIN} was not found" >&2
    exit 1
fi

PYTHON_MINOR="$(${PYTHON_BIN} -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
SITE_PACKAGES="${PREFIX}/lib/python${PYTHON_MINOR}/site-packages"

mkdir -p "${SITE_PACKAGES}" "${PREFIX}/bin"

# Install into the normal /usr/local Python search path. No repository-local
# venv and no pipx environment is created by this installer.
"${PYTHON_BIN}" -m pip install \
    --target "${SITE_PACKAGES}" \
    --upgrade \
    .

create_launcher() {
    local name="$1"
    local module="$2"
    cat > "${PREFIX}/bin/${name}" <<EOF
#!/usr/bin/env ${PYTHON_BIN}
from ${module} import main
raise SystemExit(main())
EOF
    chmod 0755 "${PREFIX}/bin/${name}"
}

create_launcher "nexus" "nexus.cli"
create_launcher "nexus-gui" "nexus.gui.app"
create_launcher "nexus-scheduler" "nexus.scheduler.commands"
create_launcher "nexus-observe" "nexus.observability.commands"
create_launcher "nexus-diagnose" "nexus.diagnostics.commands"
create_launcher "nexus-summary" "nexus.summary_cli"
create_launcher "nexus-plugins" "nexus.plugins.commands"

cat <<EOF
NEXUS installed system-wide.

Python: ${PYTHON_BIN}
Package path: ${SITE_PACKAGES}
Command: ${PREFIX}/bin/nexus

Verify with:
  command -v nexus
  nexus --help
EOF
