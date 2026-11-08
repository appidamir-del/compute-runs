# GDELT 1.0 daily aggregates, 2015–2024

A public, generic build: for each calendar day 2015-01-01..2024-12-31, the
daily [GDELT 1.0 Global Knowledge Graph](https://www.gdeltproject.org/data.html)
file (`https://data.gdeltproject.org/gkg/YYYYMMDD.gkg.csv.zip`) is downloaded,
parsed, reduced to a daily aggregate, and discarded. Peak disk is one file;
total transfer is ~112 GB, done in bounded chunks.

## What each day's row holds

`partials/partial_w*.csv` — one row per calendar day:

- `date`, `status` (`ok` / `missing` / `parse_error:...`), `http_code`,
  `file_bytes`, `n_articles`
- per theme (`ECON_GOLDPRICE`, `ECON_INFLATION`, `ECON_TRADE_DISPUTE`,
  `ARMEDCONFLICT`): `count_<theme>` = articles whose `THEMES` contains the
  theme; `tone_<theme>` = mean of the first (average-tone) value of `TONE`
  over those articles (empty when the count is 0).

Two GDELT theme names that appear in some reports (`MILITARY_CONFLICT`,
`ECON_RECESSION`) do not exist in the 1.0 taxonomy — they return zero
articles on every sampled day, including 2020-03-16. `ARMEDCONFLICT` is the
recorded substitute for the former; the latter has no 1.0 equivalent and
is dropped. Tones are lexicon-based (GDELT's own TONE field), not a
fine-tuned sentiment model.

## How a run works

`.github/workflows/gdelt-p104.yml` (manual dispatch, or every 4 hours)
runs `run.sh`, which processes at most `MAX_DAYS` (default 400) new days
or `MAX_MINUTES` (default 300) of wall clock, whichever comes first, then
stops cleanly. The updated `partials/` are committed back to this repo, so
the next run resumes where this one stopped — no day is ever downloaded
twice. When all 3,653 days are present, `run.sh` assembles the frozen file
(`gdelt_daily_frozen_2024.parquet`: one row per day; `date`, per-theme
`count_*` + `mean_tone_*`, `n_articles`) and prints its sha256; the
workflow uploads the parquet as an artifact. A run that finds nothing new
to do exits quietly.

## Regression gate

The 2020-03-16 aggregates are asserted on every finalize: 93,737 articles;
counts 150 / 565 / 133 / 9,090; mean tones −1.1083 / −2.0656 / −2.4816 /
−2.8236. If they do not match, finalize fails and nothing is published.

## Layout

- `gdelt_daily_build.py` — the builder (worker + public finalize).
- `run.sh` — chunk entrypoint.
- `partials/` — checkpoint CSVs (committed; this is the resume state).
- `gdelt_daily_frozen_2024.parquet` — appears only on the final run, and
  leaves as a workflow artifact, not a commit.
