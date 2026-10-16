import numpy as np

from agents_lab.core.stats import bootstrap_ci, ppi_mean

MU, BIAS, n, N, REPS = 2.0, 1.5, 100, 1000, 3000


def simulate(rng):
    """Predictions f = Y + constant bias + noise, so rho is about 0.7."""
    y = rng.normal(MU, 1.0, n + N)
    f = y + BIAS + rng.normal(0, 1.0, n + N)
    return y[:n], f[:n], f[n:]


def test_ppi_unbiased_under_constant_bias_and_variance_shrinks():
    rng = np.random.default_rng(0)
    res = [ppi_mean(*simulate(rng)) for _ in range(REPS)]
    theta = np.array([r.theta for r in res])
    classical = np.array([r.classical for r in res])
    naive = np.array([r.naive for r in res])
    rho = np.mean([r.rho for r in res])

    se_mc = theta.std() / np.sqrt(REPS)
    assert abs(theta.mean() - MU) < 4 * se_mc                  # unbiased (lam estimated: O(1/n) bias only)
    assert abs(naive.mean() - (MU + BIAS)) < 0.05              # naive carries the bias
    expected_ratio = 1 - rho**2 * N / (N + n)
    assert abs(theta.var() / classical.var() - expected_ratio) < 0.1 * expected_ratio
    n_eff = np.mean([r.n_eff for r in res])
    assert abs(n_eff - n / expected_ratio) < 0.05 * n_eff
    coverage = np.mean([r.ci_low <= MU <= r.ci_high for r in res])
    assert 0.92 < coverage < 0.98


def test_fixed_lambda_is_exactly_unbiased_and_lam0_is_classical():
    rng = np.random.default_rng(1)
    y, fn, fN = simulate(rng)
    r0 = ppi_mean(y, fn, fN, lam=0.0)
    assert r0.theta == r0.classical == y.mean()
    thetas = [ppi_mean(*simulate(rng), lam=1.0).theta for _ in range(REPS)]
    assert abs(np.mean(thetas) - MU) < 4 * np.std(thetas) / np.sqrt(REPS)


def test_constant_predictions_fall_back_to_classical():
    y = np.arange(10.0)
    r = ppi_mean(y, np.ones(10), np.ones(50))
    assert r.lam == 0 and r.rho == 0 and r.n_eff == 10 and r.theta == y.mean()


def test_bootstrap_ci_brackets_and_narrows():
    rng = np.random.default_rng(2)
    est, lo, hi = bootstrap_ci(rng.normal(5, 1, 50))
    est2, lo2, hi2 = bootstrap_ci(rng.normal(5, 1, 800))
    assert lo < est < hi and lo2 < 5 < hi2
    assert (hi2 - lo2) < (hi - lo) / 2
