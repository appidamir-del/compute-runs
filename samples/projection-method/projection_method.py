#!/usr/bin/env python3
"""
Projection (fractional-step) method, Chorin 1967 -- verification demo.

Convention used here is EXACTLY the doctor's first page:
    predictor :  u_hat = u^n + dt * (-(u^n . grad) u^n + nu * laplacian(u^n))
    Poisson   :  laplacian(pi) = - div(u_hat) / dt          (pi = pseudo-pressure)
    corrector :  u^{n+1} = u_hat + dt * grad(pi)
    physical pressure in this step: p^{n+1} = -pi   (density rho = 1)

With the opposite corrector sign, u = u_hat - dt * grad(p), the Poisson
right-hand side must flip sign: laplacian(p) = + div(u_hat) / dt.
Mixing the two sign pairs gives div(u^{n+1}) = 2 * div(u_hat), NOT zero.
This script checks that trap explicitly in its pure-projection test.

Domain: periodic square [0, 2*pi) x [0, 2*pi), spectral (FFT) derivatives.
Test flow: Taylor-Green vortex, u = (sin x cos y, -cos x sin y) * exp(-2 nu t),
which is an exact divergence-free solution of the incompressible
Navier-Stokes equations.  The nonlinear term of Taylor-Green is a pure
gradient, so the projection step is what removes it -- an ideal test.

Run:  python3 projection_method.py
Outputs (next to this script, under ../results/):
    figures/divergence_energy.png, tables/metrics.json, metrics.md
Only numpy and matplotlib are required.
"""

import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
OUT_FIG = HERE.parent / "results" / "figures" / "divergence_energy.png"
OUT_JSON = HERE.parent / "results" / "tables" / "metrics.json"
OUT_MD = HERE.parent / "results" / "metrics.md"

# ---- parameters (frozen before the run, cf. protocols/H2_frozen.md) ----
N = 64            # grid points per direction
L = 2.0 * math.pi
NU = 0.1          # kinematic viscosity
DT = 0.005        # explicit step; diffusion stability needs dt < 2/(nu*kmax^2) ~ 0.0196
T_END = 1.0
NSTEPS = int(round(T_END / DT))


def make_grid(n):
    dx = L / n
    x = np.linspace(0.0, L, n, endpoint=False)
    y = np.linspace(0.0, L, n, endpoint=False)
    xx, yy = np.meshgrid(x, y, indexing="ij")
    k1 = np.fft.fftfreq(n, d=dx) * 2.0 * math.pi
    kx, ky = np.meshgrid(k1, k1, indexing="ij")
    k2 = kx ** 2 + ky ** 2
    return xx, yy, kx, ky, k2


def grad(field_hat, kx, ky):
    return np.fft.ifft2(1j * kx * field_hat).real, np.fft.ifft2(1j * ky * field_hat).real


def laplacian(field_hat, k2):
    return np.fft.ifft2(-k2 * field_hat).real


def divergence(u, v, kx, ky):
    """Divergence of physical fields u, v (FFT derivatives)."""
    return np.fft.ifft2(1j * kx * np.fft.fft2(u) + 1j * ky * np.fft.fft2(v)).real


def project(u_hat, v_hat, kx, ky, k2, dt):
    """One Poisson + correction step, doctor's sign convention.

    Returns (u, v, pi, div_before, div_after_max).  The k=0 Fourier mode of
    pi is set to zero: pi is defined only up to an additive constant, and
    a constant does not change grad(pi) or the velocity.
    """
    div_hat = divergence(u_hat, v_hat, kx, ky)
    div_before = float(np.max(np.abs(div_hat)))
    rhs_hat = np.fft.fft2(-div_hat / dt)          # laplacian(pi) = -div/dt
    pi_hat = np.zeros_like(rhs_hat)
    nonzero = k2 > 0
    pi_hat[nonzero] = -rhs_hat[nonzero] / k2[nonzero]   # -k^2 pi_hat = rhs_hat
    pix, piy = grad(pi_hat, kx, ky)
    u = u_hat + dt * pix
    v = v_hat + dt * piy
    div_after = divergence(u, v, kx, ky)
    return u, v, np.fft.ifft2(pi_hat).real, div_before, float(np.max(np.abs(div_after)))


def predictor_step(u, v, kx, ky, k2, dt, nu):
    uh, vh = np.fft.fft2(u), np.fft.fft2(v)
    ux, uy = grad(uh, kx, ky)
    vx, vy = grad(vh, kx, ky)
    conv_u = u * ux + v * uy
    conv_v = u * vx + v * vy
    u_hat = u + dt * (-conv_u + nu * laplacian(uh, k2))
    v_hat = v + dt * (-conv_v + nu * laplacian(vh, k2))
    return u_hat, v_hat


def main():
    xx, yy, kx, ky, k2 = make_grid(N)

    # ---- Test A: pure projection.  u_hat = exact TG field + grad(phi) ----
    phi = 0.3 * np.sin(xx) * np.sin(yy)
    phi_hat = np.fft.fft2(phi)
    phix, phiy = grad(phi_hat, kx, ky)
    u_tg0 = np.sin(xx) * np.cos(yy)
    v_tg0 = -np.cos(xx) * np.sin(yy)
    u_rec, v_rec, _, div_before, div_after = project(
        u_tg0 + phix, v_tg0 + phiy, kx, ky, k2, DT
    )
    test_a = {
        "max_div_before": div_before,
        "max_div_after": div_after,
        "max_recovery_error_u": float(np.max(np.abs(u_rec - u_tg0))),
        "max_recovery_error_v": float(np.max(np.abs(v_rec - v_tg0))),
    }
    assert div_after < 1e-10, div_after
    assert test_a["max_recovery_error_u"] < 1e-10
    assert test_a["max_recovery_error_v"] < 1e-10

    # ---- Test B: time stepping of the Taylor-Green vortex ----
    u, v = u_tg0.copy(), v_tg0.copy()
    times, div_hat_hist, div_hist, energy, energy_exact = [], [], [], [], []
    for step in range(NSTEPS + 1):
        t = step * DT
        times.append(t)
        energy.append(float(0.5 * np.mean(u ** 2 + v ** 2)))
        energy_exact.append(0.25 * math.exp(-4.0 * NU * t))  # E(0)=1/4
        if step == NSTEPS:
            break
        u_hat, v_hat = predictor_step(u, v, kx, ky, k2, DT, NU)
        div_hat_hist.append(float(np.max(np.abs(divergence(u_hat, v_hat, kx, ky)))))
        u, v, _, _, div_after_step = project(u_hat, v_hat, kx, ky, k2, DT)
        div_hist.append(div_after_step)

    energy = np.array(energy)
    energy_exact = np.array(energy_exact)
    metrics = {
        "method": "Chorin projection, doctor's sign convention (pi = -p, rho=1)",
        "grid": f"{N}x{N} periodic, L=2*pi",
        "nu": NU, "dt": DT, "nsteps": NSTEPS, "t_end": T_END,
        "test_A_pure_projection": test_a,
        "test_B_taylor_green": {
            "max_div_after_correction_over_all_steps": float(max(div_hist)),
            "max_div_of_intermediate_field": float(max(div_hat_hist)),
            "energy_final_numeric": float(energy[-1]),
            "energy_final_exact": float(energy_exact[-1]),
            "energy_relative_error_final": float(
                abs(energy[-1] - energy_exact[-1]) / energy_exact[-1]),
            "energy_max_relative_error": float(
                np.max(np.abs(energy - energy_exact) / energy_exact)),
        },
    }
    assert metrics["test_B_taylor_green"]["max_div_after_correction_over_all_steps"] < 1e-10

    OUT_FIG.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].semilogy(div_hat_hist, label="intermediate $\\hat{u}$")
    axes[0].semilogy(div_hist, label="corrected $u^{n+1}$")
    axes[0].set_xlabel("step")
    axes[0].set_ylabel("max |div u|")
    axes[0].set_title("Divergence: before vs after projection")
    axes[0].legend()
    axes[0].grid(True, which="both", alpha=0.3)
    axes[1].plot(times, energy, label="projection method")
    axes[1].plot(times, energy_exact, "--", label="exact exp(-4 nu t)")
    axes[1].set_xlabel("t")
    axes[1].set_ylabel("kinetic energy")
    axes[1].set_title("Taylor-Green energy decay")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_FIG, dpi=200)
    plt.close(fig)

    rows = [
        "| quantity | value |",
        "|---|---|",
        f"| pure-projection max div before | {test_a['max_div_before']:.3e} |",
        f"| pure-projection max div after | {test_a['max_div_after']:.3e} |",
        f"| pure-projection recovery error | {max(test_a['max_recovery_error_u'], test_a['max_recovery_error_v']):.3e} |",
        f"| TG max div after correction (all steps) | {metrics['test_B_taylor_green']['max_div_after_correction_over_all_steps']:.3e} |",
        f"| TG final energy, numeric / exact | {energy[-1]:.6f} / {energy_exact[-1]:.6f} |",
        f"| TG final energy relative error | {metrics['test_B_taylor_green']['energy_relative_error_final']:.3e} |",
    ]
    OUT_MD.write_text("# Projection-method verification metrics\n\n" + "\n".join(rows) + "\n",
                      encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"figure: {OUT_FIG}")


if __name__ == "__main__":
    main()
