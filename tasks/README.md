# tasks

One folder per chunk: `tasks/<chunk-id>/run.sh` is the entrypoint.
`run.sh` must write everything it produces under the repo-root `results/`
folder (the workflow uploads that folder as an artifact).

Keep each chunk under 6 hours of runtime. If a job would run longer,
split it and checkpoint through `results/`.
