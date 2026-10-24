# System: idea to result, zero to hundred

This repo is the public execution half of a larger loop. The loop starts
with the user, not with this repo.

## Invocation

- The user says: «ایده دارم: …» (an idea plus its goal).
- That one call means: review the idea, plan it, run it, verify it, and
  report it. Nothing else is needed from the user unless a human gate
  asks for a decision.
- «فقط بررسی» means review only, no execution.

## Roles

- Muse reviews the idea, breaks it into chunks, prepares each chunk,
  dispatches it, watches it, verifies the artifact, transfers results to
  the private project repo, cleans up here, and writes the final report.
- This repo runs only generic, publishable code on GitHub Actions.
  Private project code, private data, JHTDB data and financial history
  never come here.
- Heavy or private work stays on SciServer. This repo is for public,
  lightweight, chunkable work.

## The run loop

1. Idea arrives («ایده دارم: …»).
2. Muse reviews it and splits the work into chunks under 6 hours each.
3. Each chunk is a folder `tasks/<chunk-id>/` with a `run.sh` entrypoint.
   The chunk id is exactly the folder name, nothing else.
4. The chunk is pushed here. The `run-task` workflow is dispatched with
   that chunk id.
5. The job runs `run.sh` and uploads `results/` as an artifact
   (retention: 7 days).
6. Muse (or the user) downloads the artifact and verifies it.
7. Verified results move to the private project repo.
8. The run and its artifact are deleted here, unless the owner explicitly
   asks to keep a run as a sample under `samples/`.

## Rules that do not bend

- Public repo, public code only. Anything that must not be published
  stays out, no exceptions.
- One job, at most 6 hours. Longer work is split and checkpointed
  through `results/`.
- Results leave as artifacts by default. A sample is committed only on
  the owner's explicit request.
- Every run ends with a verdict, including a negative one. A failed gate
  is reported as it is, not smoothed over.

## First sample

- `samples/lorenz-h1/` — Lorenz H1 standalone V4, run 40070367543,
  completed success in about 2 minutes. Verdict: NOT_ALL_GATES_PASS
  (9 of 10 gates pass; short-horizon accuracy for r=50 fails because
  chaos amplifies error). See its README for the full note.
