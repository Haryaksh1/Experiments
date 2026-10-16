"""Calibration of simulated survey answers against a small human sample (PPI++), plus spread checks."""
import pandas as pd

from agents_lab.core.stats import ppi_mean


def calibrate(real: pd.DataFrame, sim: pd.DataFrame, labeled: set, items: list[str], id_col: str = "id",
              group_col: str = "group") -> tuple[pd.DataFrame, pd.DataFrame]:
    """real: id, group, item codes (all sampled respondents; unlabeled ones are held-out truth).
    sim: id, item codes. Returns (per-item estimates, per-item per-group spread)."""
    df = real.merge(sim, on=id_col, suffixes=("_real", "_sim"))
    is_lab = df[id_col].isin(labeled)
    est, spread = [], []
    for it in items:
        r, s = f"{it}_real", f"{it}_sim"
        lab = df[is_lab & df[r].notna() & df[s].notna()]
        f_N = df[~is_lab & df[s].notna()][s]
        p = ppi_mean(lab[r], lab[s], f_N)
        truth = df[r].mean()
        est.append({"item": it, "n": len(lab), "N": len(f_N), "truth_all_real": truth, "classical_real_n": p.classical,
                    "naive_sim": p.naive, "ppi": p.theta, "ci_low": p.ci_low, "ci_high": p.ci_high,
                    "ci_covers_truth": p.ci_low <= truth <= p.ci_high, "rho": p.rho, "lam": p.lam, "n_eff": p.n_eff,
                    "agreement": (lab[r] == lab[s]).mean(),
                    "majority_baseline": lab[r].value_counts(normalize=True).max()})
        both = df[df[r].notna() & df[s].notna()]
        for g, sub in [("all", both), *both.groupby(group_col)]:
            spread.append({"item": it, "group": g, "count": len(sub), "real_mean": sub[r].mean(),
                           "sim_mean": sub[s].mean(), "real_sd": sub[r].std(), "sim_sd": sub[s].std(),
                           "sd_ratio_sim_over_real": sub[s].std() / sub[r].std() if sub[r].std() > 0 else float("nan")})
    return pd.DataFrame(est), pd.DataFrame(spread)
