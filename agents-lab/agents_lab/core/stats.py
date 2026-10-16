from collections.abc import Callable
from dataclasses import asdict, dataclass
from statistics import NormalDist

import numpy as np


def bootstrap_ci(x, stat: Callable = np.mean, n_boot: int = 2000, alpha: float = 0.05,
                 seed: int = 0) -> tuple[float, float, float]:
    """Percentile bootstrap. Returns (estimate, low, high)."""
    x = np.asarray(x)
    idx = np.random.default_rng(seed).integers(0, len(x), (n_boot, len(x)))
    boots = np.array([stat(x[i]) for i in idx])
    lo, hi = np.quantile(boots, [alpha / 2, 1 - alpha / 2])
    return float(stat(x)), float(lo), float(hi)


@dataclass
class PPIResult:
    theta: float      # PPI++ estimate
    ci_low: float
    ci_high: float
    se: float
    lam: float        # power-tuning parameter used
    rho: float        # corr(Y, f) on the labeled set
    n_eff: float      # n / (1 - rho^2 * N / (N + n))
    classical: float  # mean of Y_n alone
    naive: float      # mean of all simulated answers (f_n and f_N)

    def as_dict(self):
        return asdict(self)


def ppi_mean(y_n, f_n, f_N, alpha: float = 0.05, lam: float | None = None) -> PPIResult:
    """PPI++ mean: theta = mean(Y_n) + lam * (mean(f_N) - mean(f_n)).

    y_n, f_n: real and simulated answers for the same n respondents.
    f_N: simulated answers for N other respondents (disjoint from the n).
    lam=None uses lam* = Cov(Y, f) / (Var(f) * (1 + n/N)).
    """
    y_n, f_n, f_N = (np.asarray(a, float) for a in (y_n, f_n, f_N))
    n, N = len(y_n), len(f_N)
    var_f = np.var(np.concatenate([f_n, f_N]), ddof=1)
    degenerate = var_f == 0 or np.var(y_n) == 0
    if lam is None:
        lam = 0.0 if degenerate else np.cov(y_n, f_n, ddof=1)[0, 1] / (var_f * (1 + n / N))
    theta = y_n.mean() + lam * (f_N.mean() - f_n.mean())
    se = np.sqrt(np.var(y_n - lam * f_n, ddof=1) / n + lam**2 * np.var(f_N, ddof=1) / N)
    z = NormalDist().inv_cdf(1 - alpha / 2)
    rho = 0.0 if degenerate else float(np.corrcoef(y_n, f_n)[0, 1])
    return PPIResult(theta=float(theta), ci_low=float(theta - z * se), ci_high=float(theta + z * se), se=float(se),
                     lam=float(lam), rho=rho, n_eff=float(n / (1 - rho**2 * N / (N + n))),
                     classical=float(y_n.mean()), naive=float(np.concatenate([f_n, f_N]).mean()))
