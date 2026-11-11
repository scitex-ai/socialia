#!/usr/bin/env bash
# Outer apptainer-exec wrapper for Socialia's configured release runner.
#
# Runs ON THE RUNNER (outside the SIF). Resolves the apptainer shim + SIF image
# from the repo Actions Variables, then `apptainer exec`s the SIF and hands off
# to an INNER script (run inside the container). Keeps every workflow job's YAML
# down to one line — `bash .github/ci/exec-in-sif.sh <inner-script> [args...]` —
# and concentrates all the HPC/SIF plumbing (shim PATH, ~-expansion, scratch,
# binds) in one version-controlled place.
#
# Required env (set by the workflow from repo Actions Variables):
#   SCITEX_CI_APPTAINER   path to the apptainer shim   (e.g. ~/.env-3.11/bin/apptainer)
#   SCITEX_CI_SIF         path to the CI SIF image     (e.g. ~/.scitex/dev/containers/ci-cpu.sif)
#
# Usage:
#   bash .github/ci/exec-in-sif.sh run-in-sif.sh 3.12
#
# Fail-loud (operator directive): a missing shim or SIF is a HARD error — never
# a silent fallback to a bare-runner install.
set -euo pipefail

INNER="${1:?inner script name required (relative to .github/ci/)}"
shift || true

# The runner's job shell is --noprofile --norc (no Lmod), so the apptainer shim
# must be put on PATH explicitly; it execs the real Apptainer binary directly.
# ~-expand the Actions-Variable paths: a quoted "~/…" is NOT tilde-expanded by
# the shell, so substitute a leading ~ with $HOME ourselves.
APPTAINER="${SCITEX_CI_APPTAINER:?SCITEX_CI_APPTAINER not set (repo Actions Variable)}"
SIF="${SCITEX_CI_SIF:?SCITEX_CI_SIF not set (repo Actions Variable)}"
APPTAINER="${APPTAINER/#\~/$HOME}"
SIF="${SIF/#\~/$HOME}"
export PATH="$(dirname "$APPTAINER"):$PATH"

[ -x "$APPTAINER" ] || {
    echo "::error::apptainer shim not executable at $APPTAINER"
    exit 1
}
[ -f "$SIF" ] || {
    echo "::error::CI SIF missing at $SIF — rebuild it: scitex-container apptainer build ci-cpu"
    exit 1
}

# Respect the container runtime's standard scratch override. Otherwise use
# the runner's writable scratch, with the normal temporary directory fallback.
export APPTAINER_TMPDIR="${APPTAINER_TMPDIR:-${RUNNER_TEMP:-${TMPDIR:-/tmp}}/scitex-socialia-apptainer}"
mkdir -p "$APPTAINER_TMPDIR"

# Mounts are host configuration, not a package-owned filesystem assumption.
# Preserve standard Apptainer bindings unless the CI-specific override is set.
if [ -n "${SCITEX_CI_BINDPATH:-}" ]; then
    export APPTAINER_BINDPATH="$SCITEX_CI_BINDPATH"
fi

# Apptainer handles its normal home/cwd mounts; additional symlink targets or
# shared filesystems must be declared by the host via the binding variables.
exec "$APPTAINER" exec --pwd "$PWD" \
    "$SIF" bash ".github/ci/$INNER" "$@"
