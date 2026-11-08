#!/usr/bin/env bash
# gdelt-p104 chunk runner (public, generic).
#
# One bounded chunk of the GDELT 1.0 daily aggregate build: downloads a
# bounded number of daily GKG files, aggregates 4 themes per day
# (count + mean of the first TONE value), appends one row per day to
# partials/partial_w0.csv, and stops cleanly (exit 0) when the day or
# wall-clock budget is spent. The next run resumes from the committed
# partials — nothing is re-downloaded.
#
# Budgets come from the environment (defaults fit the 6-hour job limit
# with margin): MAX_DAYS=400 new days, MAX_MINUTES=300 wall clock.
# When all 3,653 days are present, the frozen parquet is assembled
# (public-safe finalize: merge + asserts + spot-check + sha256) and left
# next to the partials for the workflow to upload as an artifact.
set -euo pipefail
cd "$(dirname "$0")"

MAX_DAYS="${MAX_DAYS:-400}"
MAX_MINUTES="${MAX_MINUTES:-300}"

python3 gdelt_daily_build.py --worker 0 --total-workers 1 \
  --start 2015-01-01 --end 2024-12-31 \
  --max-days "$MAX_DAYS" --max-minutes "$MAX_MINUTES" \
  --build-dir partials

DAYS_DONE=$(python3 -c "import glob; print(sum(sum(1 for _ in open(f)) - 1 for f in glob.glob('partials/partial_*.csv')))")
echo "days done: $DAYS_DONE / 3653"

if [ "$DAYS_DONE" -ge 3653 ]; then
  echo "all days present — assembling frozen file"
  python3 -m pip install -q "pandas==2.2.3" "pyarrow==18.1.0"
  python3 gdelt_daily_build.py --finalize-public --build-dir partials
fi
