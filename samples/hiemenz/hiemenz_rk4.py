#!/usr/bin/env python3
"""Hiemenz stagnation-point flow, solved by RK4 shooting.

Equation:  F''' + F*F'' - (F')**2 + 1 = 0
Boundary:  F(0) = 0, F'(0) = 0, F'(inf) = 1

Method: guess s = F''(0), integrate from eta = 0 to eta = 6 with
classical 4th-order Runge-Kutta, and adjust s by bisection until
F'(6) = 1.  By eta = 6, F' is already 1 to within 1e-8, so eta = 6
is a good stand-in for infinity.  No plotting, no extra packages:
only the Python standard library is used.

Run:  python3 hiemenz_rk4.py
"""

# Right-hand side: y = [F, F', F''], y' = [F', F'', -F*F'' + (F')^2 - 1]
def rhs(y):
    f, fp, fpp = y
    return [fp, fpp, -f * fpp + fp * fp - 1.0]


def rk4_step(y, h):
    k1 = rhs(y)
    k2 = rhs([y[i] + 0.5 * h * k1[i] for i in range(3)])
    k3 = rhs([y[i] + 0.5 * h * k2[i] for i in range(3)])
    k4 = rhs([y[i] + h * k3[i] for i in range(3)])
    return [y[i] + h / 6.0 * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i])
            for i in range(3)]


def integrate(s, eta_max, h):
    """Integrate from eta = 0 with F''(0) = s; return lists of eta, F, F', F''."""
    y = [0.0, 0.0, s]
    etas, fs, fps, fpps = [0.0], [y[0]], [y[1]], [y[2]]
    n = int(round(eta_max / h))
    for i in range(1, n + 1):
        y = rk4_step(y, h)
        etas.append(i * h)
        fs.append(y[0])
        fps.append(y[1])
        fpps.append(y[2])
    return etas, fs, fps, fpps


def fp_at_eta(s, eta_max, h):
    return integrate(s, eta_max, h)[2][-1]


def shoot(eta_max=6.0, h=0.01):
    """Bisection on s in [1.0, 1.5] for F'(eta_max) = 1."""
    lo, hi = 1.0, 1.5
    flo = fp_at_eta(lo, eta_max, h) - 1.0
    for _ in range(50):
        mid = 0.5 * (lo + hi)
        fm = fp_at_eta(mid, eta_max, h) - 1.0
        if flo * fm <= 0:
            hi = mid
        else:
            lo, flo = mid, fm
        if hi - lo < 1e-10:
            break
    return 0.5 * (lo + hi)


def main():
    s = shoot()
    print(f"F''(0) = {s:.10f}")
    # Step-size check: the answer must not depend on h.
    for h in (0.02, 0.01, 0.005):
        print(f"check h = {h}: F''(0) = {shoot(h=h):.10f}")
    # Final table, eta = 0 to 6.
    etas, fs, fps, fpps = integrate(s, 6.0, 0.01)
    print(f"{'eta':>5} {'F':>12} {'Fprime':>12} {'Fdoubleprime':>14}")
    for i in range(0, len(etas), 50):  # every 0.5 in eta
        print(f"{etas[i]:5.1f} {fs[i]:12.8f} {fps[i]:12.8f} {fpps[i]:14.8f}")
    print(f"displacement delta = {6.0 - fs[-1]:.8f}  (F ~ eta - delta)")


if __name__ == "__main__":
    main()
