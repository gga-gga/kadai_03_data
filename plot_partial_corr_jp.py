"""
Deep-dive follow-up on the age hypothesis (Hypothesis 4): year_at_last_match vs win_rate.

Three additional checks to strengthen / interrogate the main finding (r=-0.237):

1. Robustness by weight class -- is the age-decline pattern consistent across
   all 9 weight classes, or driven by one or two classes?
2. Confound check: experience -- does the age effect survive after controlling
   for total fight count (a proxy for experience)? If older fighters simply
   have fought more (more "wear"), age and experience are confounded.
3. Concrete effect size -- translate r=-0.237 into "win rate points lost per
   5 years" so it's interpretable for a live audience.
"""

import numpy as np
import pandas as pd
from datetime import datetime
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["IPAexGothic", "Noto Sans CJK JP", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def parse_dob_year(s):
    if not isinstance(s, str) or s.strip() == "--":
        return None
    try:
        return datetime.strptime(s.strip(), "%b%d,%Y").year
    except Exception:
        return None


def parse_lastmatch_year(s):
    if not isinstance(s, str):
        return None
    try:
        return datetime.strptime(s.strip(), "%m-%d-%Y").year
    except Exception:
        return None


def build_dataset():
    main = pd.read_csv("ufc_analysis_data.csv")
    raw = pd.read_csv("alt_fighters_stats.csv")
    raw = raw[["url", "dob", "last_match"]].copy()
    raw["dob_year"] = raw["dob"].apply(parse_dob_year)
    raw["lastmatch_year"] = raw["last_match"].apply(parse_lastmatch_year)
    df = main.merge(raw[["url", "dob_year", "lastmatch_year"]], on="url", how="left")
    df["age_at_last_match"] = df["lastmatch_year"] - df["dob_year"]
    df = df.dropna(subset=["age_at_last_match", "win_rate"]).copy()
    df = df[(df["age_at_last_match"] >= 16) & (df["age_at_last_match"] <= 50)]
    df["total_fights"] = df["wins"] + df["losses"] + df["draws"]
    df = df[df["total_fights"] >= 3].copy()
    return df


def partial_corr(x, y, z):
    """Partial correlation of x and y, controlling for z (linear residualization)."""
    def resid(a, b):
        slope, intercept, *_ = stats.linregress(b, a)
        return a - (intercept + slope * b)
    rx = resid(x, z)
    ry = resid(y, z)
    r, p = stats.pearsonr(rx, ry)
    return r, p


def main():
    df = build_dataset()
    print(f"n = {len(df)}")

    age = df["age_at_last_match"].values.astype(float)
    win_rate = df["win_rate"].values.astype(float)
    fights = df["total_fights"].values.astype(float)

    # ---- 1. Weight-class robustness ----
    print("\n" + "=" * 70)
    print("  1. Robustness check by weight class (age vs win_rate)")
    print("=" * 70)
    rows = []
    for wc, sub in df.groupby("weight_class"):
        if len(sub) < 30:
            continue
        r, p = stats.pearsonr(sub["age_at_last_match"], sub["win_rate"])
        rows.append((wc, len(sub), sub["age_at_last_match"].mean(), r, p))
    wc_table = pd.DataFrame(rows, columns=["weight_class", "n", "mean_age", "r", "p"])
    wc_table = wc_table.sort_values("r")
    print(wc_table.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    n_negative = (wc_table["r"] < 0).sum()
    n_sig = (wc_table["p"] < 0.05).sum()
    print(f"\n  -> negative correlation in {n_negative}/{len(wc_table)} weight classes; "
          f"statistically significant (p<0.05) in {n_sig}/{len(wc_table)}")

    # ---- 2. Confound check: experience (total_fights) ----
    print("\n" + "=" * 70)
    print("  2. Confound check: controlling for experience (total fight count)")
    print("=" * 70)
    r_age_fights, p_age_fights = stats.pearsonr(age, fights)
    print(f"  age vs total_fights correlation : r={r_age_fights:.4f}  p={p_age_fights:.6f}")
    r_simple, p_simple = stats.pearsonr(age, win_rate)
    print(f"  age vs win_rate (simple, n={len(df)})      : r={r_simple:.4f}  p={p_simple:.6f}")
    r_partial, p_partial = partial_corr(age, win_rate, fights)
    print(f"  age vs win_rate (PARTIAL, controlling for total_fights): "
          f"r={r_partial:.4f}  p={p_partial:.6f}")
    pct_retained = abs(r_partial) / abs(r_simple) * 100
    print(f"  -> {pct_retained:.0f}% of the simple-correlation strength survives "
          f"after controlling for experience")

    # ---- 3. Concrete effect size ----
    print("\n" + "=" * 70)
    print("  3. Concrete effect size")
    print("=" * 70)
    slope, intercept, r, p, se = stats.linregress(age, win_rate)
    pts_per_5y = slope * 5
    print(f"  slope = {slope:.4f} win_rate points per year of age")
    print(f"  -> approx {pts_per_5y:.2f} win_rate points LOST per +5 years of age")
    age_22 = intercept + slope * 22
    age_35 = intercept + slope * 35
    print(f"  predicted win_rate at age 22 : {age_22:.1f}%")
    print(f"  predicted win_rate at age 35 : {age_35:.1f}%")
    print(f"  predicted gap (22 -> 35)     : {age_22 - age_35:.1f} points")

    # ---- plot: weight-class robustness ----
    fig, ax = plt.subplots(figsize=(7.5, 5))
    colors = ["#C00000" if v < 0 else "#2E7D32" for v in wc_table["r"]]
    ax.barh(wc_table["weight_class"], wc_table["r"], color=colors)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Pearson r (age vs win_rate)", fontsize=11)
    ax.set_title("Age x Win-rate correlation is negative\nin nearly every weight class",
                 fontsize=12, fontweight="bold")
    ax.grid(alpha=0.25, axis="x")
    fig.tight_layout()
    fig.savefig("hypothesis_age_weightclass_robustness.png", dpi=150)
    plt.close(fig)
    print("\n  -> saved plot: hypothesis_age_weightclass_robustness.png")

    with open("hypothesis_age_deepdive_results.txt", "w", encoding="utf-8") as f:
        f.write("Age hypothesis deep-dive: robustness + confound checks\n")
        f.write("=" * 70 + "\n\n")
        f.write("-- 1. Weight-class robustness --\n")
        f.write(wc_table.to_string(index=False, float_format=lambda v: f"{v:.3f}") + "\n")
        f.write(f"negative in {n_negative}/{len(wc_table)} classes, "
                f"significant (p<0.05) in {n_sig}/{len(wc_table)}\n\n")
        f.write("-- 2. Confound check (experience / total_fights) --\n")
        f.write(f"age vs total_fights: r={r_age_fights:.4f} p={p_age_fights:.6f}\n")
        f.write(f"age vs win_rate (simple): r={r_simple:.4f} p={p_simple:.6f}\n")
        f.write(f"age vs win_rate (partial, controlling total_fights): "
                f"r={r_partial:.4f} p={p_partial:.6f}\n")
        f.write(f"-> {pct_retained:.0f}% of correlation strength survives control\n\n")
        f.write("-- 3. Concrete effect size --\n")
        f.write(f"slope = {slope:.4f} pts/year -> {pts_per_5y:.2f} pts per +5 years\n")
        f.write(f"predicted win_rate at 22: {age_22:.1f}%  at 35: {age_35:.1f}%  "
                f"gap: {age_22 - age_35:.1f} pts\n")
    print("\nsaved: hypothesis_age_deepdive_results.txt")


if __name__ == "__main__":
    main()
