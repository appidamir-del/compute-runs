# Sample: lorenz-h1

First sample run of this repo, kept here as a public example of what a
finished run looks like.

- Task chunk: `tasks/lorenz-h1/` (standalone Lorenz H1 script, V4)
- Workflow run: appidamir-del/compute-runs, run 40070367543
  (workflow_dispatch, 2026-10-24, completed success in about 2 minutes)
- Contents: 27 files — homework trajectories and figures (r=15 and r=50),
  convergence data and figure, Lyapunov spectra (10 units) and figure,
  sensitivity figures, and JSON verdicts.

## Verdict (honest)

- Run status: COMPLETE, 18/18 units.
- Lyapunov spectra reproduce the earlier frozen V2 numbers
  (r=15 about [-0.3501, -0.3502, -12.9663];
  r=50 finest step about [1.2598, 0.0016, -14.9281]).
- Overall decision in `decision.json`: NOT_ALL_GATES_PASS — 9 of 10 gates
  pass. The failing gate is short-horizon accuracy for r=50: in the
  chaotic regime even the finest step stays above the strict 0.001 bar.
  Convergence order stays near 1.0 and errors decrease with step size,
  so this is chaos amplifying error, not a code bug.

## Note

Samples are the exception, not the rule. By default, results of this repo
leave only as workflow artifacts and are deleted after transfer. A sample
is committed only when the owner explicitly asks for it, as happened here.
