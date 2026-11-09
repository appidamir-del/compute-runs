#!/usr/bin/env bash
# gdelt-p106 chunk runner (public, generic).
#
# Single run of the GDELT 1.0 daily aggregate build for calendar 2025:
# downloads the daily GKG files for 2025-01-01..2025-12-31 (365 days),
# aggregates 4 themes per day (count + mean of the first TONE value),
# appends one row per day to partials/partial_w0.csv, and stops cleanly
# (exit 0) when the day or wall-clock budget is spent. If the run stops
# early, a re-dispatch resumes from the committed partials — nothing is
# re-downloaded. When all 365 days are present, the frozen parquet is
# assembled (public-safe finalize: merge + asserts + spot-check + sha256)
# and left next to the partials for the workflow to upload as an artifact.
set -euo pipefail
cd "$(dirname "$0")"

MAX_DAYS="${MAX_DAYS:-400}"
MAX_MINUTES="${MAX_MINUTES:-300}"

python3 gdelt_daily_build.py --worker 0 --total-workers 1 \
  --start 2025-01-01 --end 2025-12-31 \
  --max-days "$MAX_DAYS" --max-minutes "$MAX_MINUTES" \
  --build-dir partials

DAYS_DONE=$(python3 -c "import glob; print(sum(sum(1 for _ in open(f)) - 1 for f in glob.glob('partials/partial_*.csv')))")
echo "days done: $DAYS_DONE / 365"

if [ "$DAYS_DONE" -ge 365 ]; then
  echo "all days present — assembling frozen file"
  python3 -m pip install -q "pandas==2.2.3" "pyarrow==18.1.0"
  python3 gdelt_daily_build.py --finalize-public --build-dir partials
fi
