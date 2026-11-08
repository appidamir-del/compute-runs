"""gdelt_daily_build — stream GDELT 1.0 daily GKG files into daily aggregates.

Public, generic builder. For each calendar day in 2015-01-01..2024-12-31 it
downloads the daily https://data.gdeltproject.org/gkg/YYYYMMDD.gkg.csv.zip,
parses it, keeps ONLY the daily aggregate (per theme: count + mean of the
FIRST TONE value over articles whose THEMES contains the theme), and
discards the file. Peak disk = one file. Themes: ECON_GOLDPRICE,
ECON_INFLATION, ECON_TRADE_DISPUTE, ARMEDCONFLICT. Also n_articles per day.

Modes:
  worker   --worker W --total-workers N [--start YYYY-MM-DD] [--end YYYY-MM-DD]
             [--build-dir DIR] [--max-days K] [--max-minutes M]
             Handles days whose index % N == W. Resumable: reads ALL partial
             CSVs in the build dir at start and skips already-done days.
             Appends one row per day (flushed) to partial_w{W}.csv.
             --max-days stops cleanly (exit 0) after K NEW days; --max-minutes
             stops cleanly once the wall-clock budget is spent. Either budget
             makes the run safe to re-run: the next run resumes from the
             committed partials.
  finalize-public --finalize-public [--build-dir DIR]
             Merges all partials, asserts 3,653 calendar days with no
             duplicates and no 2025+ rows, forward-fills mean_tone where
             count==0 or the day is missing, writes
             gdelt_daily_frozen_2024.parquet, computes sha256, and verifies
             the 2020-03-16 aggregates against the locked data-check values.
             Prints the sha256. Nothing else is written; no manifest, no
             other file is touched.

Aggregation logic (theme matching, tone parsing, row format) is identical
to the reference implementation this was adapted from; the 2020-03-16
spot-check below is the regression gate for it (150/565/133/9090 counts;
tones -1.1083/-2.0656/-2.4816/-2.8236).
"""
import argparse
import csv
import glob
import hashlib
import os
import subprocess
import sys
import time
import zipfile
from datetime import date, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
THEMES = ['ECON_GOLDPRICE', 'ECON_INFLATION', 'ECON_TRADE_DISPUTE', 'ARMEDCONFLICT']
THEMES_B = [t.encode() for t in THEMES]
START = date(2015, 1, 1)
END = date(2024, 12, 31)
EXPECTED_DAYS = (END - START).days + 1  # 3653 (2015-01-01..2024-12-31 incl.;
# spans 3 leap days: 2016/2020/2024)

# Locked data-check values for the 2020-03-16 spot-check. Rows exclude header.
SPOT = {
    'date': '2020-03-16', 'n_articles': 93737,
    'counts': {'ECON_GOLDPRICE': 150, 'ECON_INFLATION': 565,
               'ECON_TRADE_DISPUTE': 133, 'ARMEDCONFLICT': 9090},
    'tones': {'ECON_GOLDPRICE': -1.1083, 'ECON_INFLATION': -2.0656,
              'ECON_TRADE_DISPUTE': -2.4816, 'ARMEDCONFLICT': -2.8236},
}

PARTIAL_FIELDS = (['date', 'status', 'http_code', 'file_bytes', 'n_articles']
                  + [f'count_{t}' for t in THEMES]
                  + [f'tone_{t}' for t in THEMES])


def all_days(start=START, end=END):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def parse_gkg(zip_path):
    """Return (n_articles, {theme: count}, {theme: tone_sum})."""
    z = zipfile.ZipFile(zip_path)
    name = z.namelist()[0]
    cnt = {t: 0 for t in THEMES_B}
    ssum = {t: 0.0 for t in THEMES_B}
    n = 0
    with z.open(name) as f:
        header = f.readline()
        assert header.rstrip(b'\n').split(b'\t') == [
            b'DATE', b'NUMARTS', b'COUNTS', b'THEMES', b'LOCATIONS', b'PERSONS',
            b'ORGANIZATIONS', b'TONE', b'CAMEOEVENTIDS', b'SOURCES',
            b'SOURCEURLS'], header[:120]
        for ln in f:
            n += 1
            parts = ln.split(b'\t')
            th = parts[3]
            tone = parts[7]
            comma = tone.find(b',')
            tv = float(tone if comma < 0 else tone[:comma])
            for t in THEMES_B:
                if t in th:
                    cnt[t] += 1
                    ssum[t] += tv
    return n, {t: cnt[t.encode()] for t in THEMES}, \
        {t: ssum[t.encode()] for t in THEMES}


def download_day(d, tmp_path, attempts=3):
    """curl the day's zip to tmp_path. Returns (http_code, bytes)."""
    url = f'https://data.gdeltproject.org/gkg/{d.strftime("%Y%m%d")}.gkg.csv.zip'
    for attempt in range(1, attempts + 1):
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        r = subprocess.run(
            ['curl', '-s', '-o', tmp_path, '-w', '%{http_code}',
             '--max-time', '600', '--retry', '3', '--retry-delay', '5',
             '-A', UA, url],
            capture_output=True, text=True)
        code = int(r.stdout.strip() or 0)
        size = os.path.getsize(tmp_path) if os.path.exists(tmp_path) else 0
        if code == 200 and size > 0:
            return code, size
        print(f'  [{d}] attempt {attempt}: http={code} bytes={size}; retrying',
              flush=True)
        time.sleep(15)
    return code, size


def worker_main(worker, total_workers, start, end, build_dir,
                max_days=None, max_minutes=None):
    os.makedirs(build_dir, exist_ok=True)
    partial_path = os.path.join(build_dir, f'partial_w{worker}.csv')
    log_path = os.path.join(build_dir, f'worker_w{worker}.log')
    log = open(log_path, 'a', buffering=1)
    done = set()
    # Global done-set: read ALL partial files, so a day finished by any
    # worker (or any earlier run) is never downloaded twice and finalize
    # never sees duplicates.
    for _p in glob.glob(os.path.join(build_dir, 'partial_w*.csv')):
        with open(_p, newline='') as f:
            for row in csv.DictReader(f):
                done.add(row['date'])
    days = [d for i, d in enumerate(all_days(start, end)) if i % total_workers == worker]
    todo = [d for d in days if d.isoformat() not in done]
    log.write(f'worker {worker}/{total_workers}: {len(days)} assigned, '
              f'{len(done)} already done, {len(todo)} to do\n')
    print(f'worker {worker}: {len(todo)} days to do', flush=True)
    write_header = not os.path.exists(partial_path) or os.path.getsize(partial_path) == 0
    out = open(partial_path, 'a', newline='', buffering=1)
    w = csv.DictWriter(out, fieldnames=PARTIAL_FIELDS)
    if write_header:
        w.writeheader()
    t_start = time.time()
    n_done = 0
    stop_reason = 'all todo days done'
    tmp_path = os.path.join(build_dir, f'tmp_w{worker}.zip')
    try:
        for d in todo:
            if max_days is not None and n_done >= max_days:
                stop_reason = f'max-days budget reached ({max_days})'
                break
            if max_minutes is not None and (time.time() - t_start) / 60 >= max_minutes:
                stop_reason = f'max-minutes budget reached ({max_minutes})'
                break
            ds = d.isoformat()
            t0 = time.time()
            code, size = download_day(d, tmp_path)
            row = {'date': ds, 'status': 'missing', 'http_code': code,
                   'file_bytes': size, 'n_articles': 0}
            for t in THEMES:
                row[f'count_{t}'] = 0
                row[f'tone_{t}'] = ''
            if code == 200 and size > 0:
                try:
                    n, cnt, ssum = parse_gkg(tmp_path)
                    row['status'] = 'ok'
                    row['n_articles'] = n
                    for t in THEMES:
                        row[f'count_{t}'] = cnt[t]
                        row[f'tone_{t}'] = (f'{ssum[t] / cnt[t]:.6f}'
                                            if cnt[t] else '')
                except Exception as e:  # corrupt zip etc. -> missing, recorded
                    row['status'] = f'parse_error:{type(e).__name__}:{e}'
                    log.write(f'[{ds}] PARSE ERROR {e}\n')
            else:
                log.write(f'[{ds}] DOWNLOAD FAILED http={code}\n')
            w.writerow(row)
            n_done += 1
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            dt = time.time() - t0
            if n_done % 25 == 0 or dt > 60:
                el = time.time() - t_start
                log.write(f'[{ds}] {n_done}/{len(todo)} done, '
                          f'{el / 60:.1f} min elapsed, last {dt:.1f}s, '
                          f'status={row["status"]}\n')
    finally:
        out.close()
        log.write(f'worker {worker} finished: {n_done} days, '
                  f'{(time.time() - t_start) / 60:.1f} min, '
                  f'stop={stop_reason}\n')
        log.close()
    print(f'worker {worker} done: {n_done} days ({stop_reason})', flush=True)


def finalize_public(build_dir):
    """Assemble the frozen daily aggregate from the partials (public-safe).

    No manifest, no other file is touched. Writes
    gdelt_daily_frozen_2024.parquet next to the partials and prints sha256.
    """
    import pandas as pd
    rows = []
    for wi in range(10):  # read whatever partials exist (w0..wN)
        p = os.path.join(build_dir, f'partial_w{wi}.csv')
        if os.path.exists(p):
            rows.append(pd.read_csv(p, dtype={'date': str}))
    assert rows, 'no partial files found'
    df = pd.concat(rows, ignore_index=True)
    assert df['date'].is_unique, 'duplicate days across partials!'
    assert len(df) == EXPECTED_DAYS, (f'got {len(df)} days, expected '
                                      f'{EXPECTED_DAYS}')
    df['date'] = pd.to_datetime(df['date'])
    assert df['date'].min() == pd.Timestamp('2015-01-01')
    assert df['date'].max() == pd.Timestamp('2024-12-31')
    assert (df['date'].dt.year <= 2024).all(), '2025+ rows present!'
    # Full calendar coverage (no gaps in the date index itself).
    full = pd.date_range('2015-01-01', '2024-12-31', freq='D')
    assert (df['date'].sort_values().reset_index(drop=True) == full).all()
    df = df.sort_values('date').reset_index(drop=True)

    missing = sorted(df.loc[df['status'] != 'ok', 'date'].dt.strftime('%Y-%m-%d'))
    parse_errors = sorted(df.loc[df['status'].str.startswith('parse_error', na=False),
                               'date'].dt.strftime('%Y-%m-%d'))
    # Tones: forward-fill where count==0 or day missing; leading NaNs
    # backfilled from the first available value (recorded, not hidden).
    filled = {}
    for t in THEMES:
        tone = pd.to_numeric(df[f'tone_{t}'], errors='coerce')
        tone = tone.where(pd.to_numeric(df[f'count_{t}'], errors='coerce') > 0)
        n_ffill = int(tone.isna().sum())
        tone = tone.ffill().bfill()
        assert tone.notna().all(), f'theme {t}: no tone value at all'
        df[f'tone_{t}'] = tone
        filled[t] = {'n_days_filled': n_ffill,
                     'filled_dates': sorted(df.loc[
                         pd.to_numeric(df[f'count_{t}'], errors='coerce') == 0,
                         'date'].dt.strftime('%Y-%m-%d'))[:50]}
    out = pd.DataFrame({'date': df['date']})
    for t in THEMES:
        out[f'count_{t}'] = df[f'count_{t}'].astype('int64')
        out[f'mean_tone_{t}'] = df[f'tone_{t}'].astype('float64')
    out['n_articles'] = df['n_articles'].astype('int64')
    out_path = os.path.join(build_dir, 'gdelt_daily_frozen_2024.parquet')
    out.to_parquet(out_path, index=False)

    sha = hashlib.sha256(open(out_path, 'rb').read()).hexdigest()
    # Spot-check 2020-03-16 against the locked data-check values.
    spot = out[out['date'] == pd.Timestamp(SPOT['date'])].iloc[0]
    assert int(spot['n_articles']) == SPOT['n_articles'], spot['n_articles']
    for t in THEMES:
        assert int(spot[f'count_{t}']) == SPOT['counts'][t], (t, spot[f'count_{t}'])
        assert abs(float(spot[f'mean_tone_{t}']) - SPOT['tones'][t]) < 5e-5, \
            (t, spot[f'mean_tone_{t}'])

    print(f'FINALIZE OK: {len(out)} days, sha256={sha}')
    print(f'missing days ({len(missing)}): {missing}')
    print(f'parse-error days ({len(parse_errors)}): {parse_errors}')
    print(f'filled per theme: {{t: filled[t]["n_days_filled"] for t in THEMES}}')
    return sha


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--worker', type=int, default=None)
    ap.add_argument('--total-workers', type=int, default=1)
    ap.add_argument('--start', default='2015-01-01')
    ap.add_argument('--end', default='2024-12-31')
    ap.add_argument('--build-dir', default=None,
                    help='partials dir (default: partials/ next to this script)')
    ap.add_argument('--max-days', type=int, default=None,
                    help='stop cleanly (exit 0) after this many NEW days')
    ap.add_argument('--max-minutes', type=float, default=None,
                    help='stop cleanly once this wall-clock budget is spent')
    ap.add_argument('--finalize-public', action='store_true')
    args = ap.parse_args()
    bdir = args.build_dir or os.path.join(SCRIPT_DIR, 'partials')
    if args.finalize_public:
        finalize_public(bdir)
    else:
        assert args.worker is not None
        worker_main(args.worker, args.total_workers,
                    date.fromisoformat(args.start), date.fromisoformat(args.end),
                    bdir, max_days=args.max_days, max_minutes=args.max_minutes)
