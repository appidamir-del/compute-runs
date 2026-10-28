# Sample: projection-method

Public sample copy of a coursework exercise: Chorin's projection
(fractional-step) method, 1967, with the doctor's sign convention
(corrector `u = u_hat + dt*grad(pi)`, Poisson
`laplacian(pi) = -div(u_hat)/dt`, so `pi = -p` for density 1).

- Code: `projection_method.py` (numpy + matplotlib, periodic box,
  FFT Poisson solver)
- Verification: a pure-projection test recovers an exact Taylor-Green
  field to ~5e-16, and a Taylor-Green time run keeps
  `max |div u| ~ 1e-14` over all 200 steps, with final energy
  relative error 2.0e-4 (see `metrics.json`).
- Figure: `divergence_energy.png` (divergence before/after
  projection, Taylor-Green energy decay vs exact).
- Full Persian article: `solution.pdf` (7 pages).

Note: this is a generic, publishable textbook method. The full
exercise, with protocol and LaTeX source, lives in the owner's
private coursework repo; this folder is the public sample the owner
explicitly asked to publish on 2026-10-28.
