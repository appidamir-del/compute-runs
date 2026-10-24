# H1-V2 — پروتکل همگرایی و لیاپانوف
Date: 2026-10-05. Settings fixed and published before V2 execution. Historical H1 outcomes already exposed; this is a prospective numerical verification/diagnostic protocol, not an outcome-blind independent replication.
Owner: moradi-am. Canonical repo: Homework. Source: uploaded H1.pdf, s=10,b=8/3,r=15/50, u0=(0,1,0)/(0,1.001,0).
Reuse: Research-OS EXP-2026-002 (trace ≠ detection), EXP-2026-008 (agreement ≠ convergence); prior Lorenz audit commits 13c5cde and e933ca1.
## Tests
### H1-V2-CONV
Horizon t=[0,1], sample every .001; Euler steps [.001,.0005,.00025,.000125,.0000625,.00003125,.000015625], all 4 (r,u0) cases. All simultaneous Euler updates.
Reference DOP853 with rtol=1e-11,atol=1e-13,max_step=.01; tighter comparator rtol=1e-13,atol=1e-15,max_step=.005. This reference is numerical, not analytic exact truth.
Normalize each component by fixed a priori [20,30,60].
Primary E(dt)=max over sampled times of Euclidean norm((Euler-reference)/scale).
Order p=log2(E(dt)/E(dt/2)). Reference discrepancy must be <1e-6 and <.01*smallest Euler E.
First-order gate: all last 3 p values in [.85,1.15] and errors decrease at all refinements.
Accuracy gate: smallest-step normalized E≤.001 (0.1% of stated vector scales in norm); report separately whether historical dt=.0001 meets same budget using a separate Euler evaluation, not interpolation.
No long-time pointwise convergence claim. If gate fails, retain FAIL and do not relax settings.
### H1-V2-LYAP
Full 3-exponent tangent spectrum via fixed-step RK4 state+tangent equations and QR renormalization. J=[[-10,10,0],[r-z,-1,-x],[y,x,-8/3]].
Ttotal=600, burn-in=100, accumulation=500; blocks=50; QR interval=.1.
Base initial condition (0,1,0): dt [.01,.005,.0025] at both r.
Perturbed (0,1.001,0): dt=.0025 at both r.
QR-interval comparator .05: dt=.0025, base initial condition at both r.
Total 10 independent computational units (not independent physical replications). Initial tangent identity; no random seed. Sort final exponents descending for report; keep original QR diagonal history.
Expected divergence sum = -(10+1+8/3)=-13.6666666667.
Numerical gates: abs(sum-spectrum+13.6666666667)≤.01 every unit; base largest-exponent differences between finest two steps≤.15 and QR interval comparator≤.15 at both r.
r15 analytic-control gate: sorted spectrum agrees with [-.35019310244,-.35019310244,-12.96628046178] to max absolute error≤.03 on all dt=.0025 units; largest exponent negative.
r50 chaos-evidence gate: largest exponent >.1, middle exponent abs≤.1 on all units; largest-exponent difference base versus perturbed at dt=.0025≤.15; base finest mean of last100 and last200 accumulation versus full500 each within .15.
These are finite-horizon engineering diagnostic criteria, not statistical CIs or proof of asymptotic mathematical chaos. Positive finite-time exponent alone is insufficient without the numerical/control gates.
### Delivery/reproducibility
Preserve original H1 and historical .py/JSON/figures/ZIP as imported history, not rewritten preregistration. Complete notebook implements full homework plus V2 tests; REBUILD_HOMEWORK defaults false because original figures exist, and true regenerates required Euler full-time figures in a distinct output directory.
Full V2 notebook run must succeed in a fresh kernel; checkpoints carry config/code hashes, shape/finite-value audits and atomic promotion; no invalid checkpoint silently reused. Runtime unit counters writer-owned with tqdm and heartbeat. Canonical compact evidence includes sampled convergence curves, QR log-stretch blocks, metrics, environment, hashes, progress and decision receipts.
## Red-team
K-H1-NUM: apparent chaos/order may be discretization artifact → reference convergence, Euler order and RK4 refinement gates.
K-H1-LYAP: finite horizon/QR algorithm/transient may bias exponent → analytic stable control, trace sum, QR-interval/step/initial-condition/tail checks.
K-H1-METRIC: ordinary norm or lobe switch is not effective metric/basin transition → no such promotion.
K-H1-PROVENANCE: historical intermediate versions/trajectories incomplete → preserve limitation; V2 hashes/archives separately.
Freeze verdict: freeze-allowed-with-open-killers; future failure remains failure. No retuning after V2 outcome. Debugging syntax/I/O only may preserve exact semantics and must be logged.
## Boundary
No DNS/turbulence transfer, no novel metric, no event prediction. No downloaded textbook or external literature is needed to verify the supplied ODE; solver is an implementation tool.
