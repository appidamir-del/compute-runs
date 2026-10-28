# compute-runs

Public, execution-only repository. It exists for one purpose: running
generic, sanitized compute tasks on GitHub Actions (free for public repos,
6-hour limit per job).

## Rules (hard)

- **Nothing private lives here.** No unpublished research code, no project
  data, no credentials, no financial history, no JHTDB data. Only generic,
  publishable task code.
- **Results leave only as workflow artifacts.** Results are never committed
  to this repo. After the operator fetches and verifies an artifact, the
  artifact and the workflow run are deleted from here.
- **Tasks are chunked.** Every task is split so one job stays under the
  6-hour limit. A job writes its checkpoint to `results/`; the next chunk
  resumes from it.

## How a run works

1. The operator pushes a task chunk under `tasks/<chunk-id>/` with a
   `run.sh` entrypoint.
2. The operator dispatches the `run-task` workflow with that chunk id.
3. The workflow runs `run.sh`, then uploads `results/` as an artifact
   (retention: 7 days).
4. The operator downloads the artifact, verifies it, transfers the results
   to the private project repo, then deletes the artifact and the run here.

## Layout

- `tasks/` — one folder per chunk, each with `run.sh` (and its inputs).
- `results/` — job output only; never committed (see `.gitignore`).
- `samples/` — the exception: a finished run kept in the repo as a public
  example, only when the owner explicitly asks for it. See
  `samples/lorenz-h1/` for the first sample.

## Samples

- `samples/lorenz-h1/` — first sample (2026-10-24).
- `samples/projection-method/` — Chorin projection method exercise
  (code, figure, metrics, Persian article).
- `samples/hiemenz/` — Hiemenz stagnation-point exercise
  (corrected question, RK4 code, metrics, Persian article).

The two new samples were added on 2026-10-28 at the owner's explicit
request. Samples are the exception: by default, results here leave
only as workflow artifacts.
