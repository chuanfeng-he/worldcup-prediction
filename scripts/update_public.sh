#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "${SCRIPT_DIR}/.." && pwd)}"
SIMS="${SIMS:-5000}"
SEED="${SEED:-2026}"
PUBLIC_TARGET="${PUBLIC_TARGET:-}"

cd "${PROJECT_ROOT}"
python3 -m wcmodel.cli generate --sims "${SIMS}" --seed "${SEED}" --live-results espn

if [[ -n "${PUBLIC_TARGET}" ]]; then
  mkdir -p "${PUBLIC_TARGET}"
  rsync -a --delete "${PROJECT_ROOT}/public/" "${PUBLIC_TARGET}/"
fi
