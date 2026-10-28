# Sample: hiemenz

Public sample copy of a coursework exercise: Hiemenz stagnation-point
similarity solution (Falkner-Skan, beta = 1).

- Question: `question.pdf` (Persian, 2 pages), with
  `u1* = x1* F'(eta)`, `u2* = -F(eta)`.
- Code: `hiemenz_rk4.py` — a simple, student-style, no-plot
  implementation: classical 4th-order Runge-Kutta shooting
  (bisection on `F''(0)` in [1.0, 1.5] to eta = 6), Python standard
  library only. Run: `python3 hiemenz_rk4.py`.
- Result: `F''(0) = 1.2325876568`, displacement thickness
  `delta = 0.64790047` (in units of sqrt(nu/a)). Step refinement
  h = 0.02 / 0.01 / 0.005 gives 1.2325876554 / 6568 / 6569
  (see `metrics.json`).
- Full Persian article: `solution.pdf` (3 pages).

Note: this is a generic, publishable textbook method. The full
exercise, with protocol and LaTeX source, lives in the owner's
private coursework repo; this folder is the public sample the owner
explicitly asked to publish on 2026-10-28.
