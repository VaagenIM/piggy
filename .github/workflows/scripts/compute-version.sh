#!/usr/bin/env bash
# Computes a CalVer version string: YY.MM.N, where N is the number of
# commits reachable from HEAD since the start of the current UTC month.
set -euo pipefail

YEAR=$(date -u +%y)
MONTH=$(date -u +%-m)
MONTH_START=$(date -u +%Y-%m-01T00:00:00Z)
COUNT=$(git rev-list --count --since="$MONTH_START" HEAD)
COMMIT_ID=$(git rev-parse --short HEAD)

echo "${YEAR}.${MONTH}.${COUNT}-${COMMIT_ID}"
