# gdelt-p106 — GDELT 1.0 daily aggregates, calendar year 2025

Public, generic builder. For each calendar day in 2025-01-01..2025-12-31
it downloads the daily GDELT 1.0 GKG file
(`https://data.gdeltproject.org/gkg/YYYYMMDD.gkg.csv.zip`), parses it,
and keeps ONLY the daily aggregate: per theme, the article count and the
mean of the FIRST TONE value over articles whose THEMES contains the
theme — plus the total article count for the day. The raw file is
discarded immediately; peak disk is one file.

Themes: `ECON_GOLDPRICE`, `ECON_INFLATION`, `ECON_TRADE_DISPUTE`,
`ARMEDCONFLICT`.

## Files

- `gdelt_daily_build.py` — the builder (worker + `--finalize-public`).
  Standard library only, except pandas/pyarrow for the finalize step.
- `run.sh` — one bounded run: 400 new days or 300 minutes of wall
  clock, whichever comes first; assembles the frozen parquet when all
  365 days are present.
- `partials/` — checkpoint partials (`partial_w0.csv`, one row per day:
  `date, status, http_code, file_bytes, n_articles, count_<theme>,
  tone_<theme>`). Days that fail to download or parse are recorded
  with `status` `missing` / `parse_error:...` and `count` 0 — never
  silently skipped. The finalize step forward-fills the mean tone
  where the count is 0.

## Resume

The worker reads ALL partials at start and skips already-done days, so
a re-dispatch after an interrupted run downloads nothing twice. The
frozen file (`gdelt_daily_frozen_2025.parquet`, 365 rows) leaves the
repo ONLY as a workflow artifact — it is never committed.

## Spot-check gate

The finalize step verifies 2025-06-02 against independently checked
values before printing the sha256: 86,919 articles (±1 — a 1-row
coverage-count difference between two independent parses); theme
counts 162 / 1906 / 608 / 13456; mean tones +0.6431 / −1.2800 /
−2.2320 / −3.2973.
