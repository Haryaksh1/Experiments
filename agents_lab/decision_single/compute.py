"""All arithmetic of the decision: never done by the LLM."""
from dataclasses import dataclass

import pandas as pd

from agents_lab.decision_single.schemas import Cell

SENS_COLS = ["change", "criterion", "option", "before", "after", "size", "overtaker"]


def matrices(cells: dict[str, dict[str, Cell]]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """cells[option][criterion] -> (low, mid, high) DataFrames, options x criteria."""
    return tuple(pd.DataFrame({o: {c: getattr(v, k) for c, v in row.items()} for o, row in cells.items()}).T.astype(float)
                 for k in ("low", "mid", "high"))


def dominated(E: pd.DataFrame) -> list[str]:
    """Options some other option matches or beats on every criterion and beats on at least one."""
    return [a for a in E.index
            if any((E.loc[b] >= E.loc[a]).all() and (E.loc[b] > E.loc[a]).any() for b in E.index if b != a)]


def sensitivity(E: pd.DataFrame, w: pd.Series, top: str) -> pd.DataFrame:
    """Smallest single change that lets another option overtake `top` (w sums to 1).

    EV is linear, so every threshold is closed form. Changing one raw weight then renormalizing
    rescales all EVs by the same positive factor, so it never changes the order by itself.
    """
    ev = E @ w
    rivals = [o for o in E.index if o != top]
    margin = {o: ev[top] - ev[o] for o in rivals}
    rows = []
    for c in E.columns:
        if len(E.columns) > 1:
            cands = []
            for o in rivals:
                d = E.at[top, c] - E.at[o, c]
                if d != 0 and w[c] - margin[o] / d >= 0:
                    cands.append((abs(margin[o] / d), -margin[o] / d, o))
            if cands:
                _, delta, o = min(cands)
                after = (w[c] + delta) / (1 + delta)
                rows.append(dict(change="weight", criterion=c, option="(weights)", before=w[c], after=after,
                                 size=abs(after - w[c]), overtaker=o))
        o = min(rivals, key=margin.get)  # lowering top's score shrinks every margin equally
        x = margin[o] / w[c]
        if E.at[top, c] - x >= 0:
            rows.append(dict(change="score", criterion=c, option=top, before=E.at[top, c], after=E.at[top, c] - x,
                             size=x, overtaker=o))
        for o in rivals:
            x = margin[o] / w[c]
            if E.at[o, c] + x <= 10:
                rows.append(dict(change="score", criterion=c, option=o, before=E.at[o, c], after=E.at[o, c] + x,
                                 size=x, overtaker=o))
    return pd.DataFrame(rows, columns=SENS_COLS).sort_values(["change", "size"], ignore_index=True)


@dataclass
class Analysis:
    expected: pd.DataFrame  # PERT expected score per option x criterion
    ev: pd.Series
    ev_low: pd.Series
    ev_high: pd.Series
    ranking: list[str]
    sensitivity: pd.DataFrame
    dominated: list[str]

    @property
    def margin(self) -> float:
        return float(self.ev[self.ranking[0]] - self.ev[self.ranking[1]])

    def text(self) -> str:
        lines = [f"{i}. {o}: {self.ev[o]:.2f} (range {self.ev_low[o]:.2f}-{self.ev_high[o]:.2f})"
                 for i, o in enumerate(self.ranking, 1)]
        lines.append(f"Margin of {self.ranking[0]} over {self.ranking[1]}: {self.margin:.2f}")
        for kind, fmt in [("weight", "Smallest weight change that flips the top choice: {criterion} weight "
                                     "{before:.2f} -> {after:.2f} ({overtaker} overtakes)"),
                          ("score", "Smallest score change that flips it: {option} on {criterion} "
                                    "{before:.1f} -> {after:.1f} ({overtaker} overtakes)")]:
            s = self.sensitivity[self.sensitivity.change == kind]
            if len(s):
                lines.append(fmt.format(**s.iloc[0].to_dict()))
        if self.dominated:
            lines.append("Dominated options (on expected scores): " + ", ".join(self.dominated))
        return "\n".join(lines)


def analyze(cells: dict[str, dict[str, Cell]], weights: dict[str, float]) -> Analysis:
    return analyze_lmh(*matrices(cells), weights)


def analyze_lmh(L: pd.DataFrame, M: pd.DataFrame, H: pd.DataFrame, weights: dict[str, float]) -> Analysis:
    """Same as analyze() from low/mid/high matrices (e.g. averaged over ensemble samples)."""
    w = pd.Series(weights)[M.columns]
    w = w / w.sum()
    E = (L + 4 * M + H) / 6  # PERT mean of the three-point estimate
    ev = E @ w
    ranking = ev.sort_values(ascending=False, kind="mergesort").index.tolist()
    return Analysis(E, ev, L @ w, H @ w, ranking, sensitivity(E, w, ranking[0]), dominated(E))
