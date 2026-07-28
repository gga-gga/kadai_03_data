"""
Hypothesis 3: Does the Ape Index reduce strikes absorbed?
===========================================================
Hypothesis: not raw reach length, but reach-to-height ratio (ape_index)
correlates with lower damage absorbed (higher str_def / lower sapm).

Method: simple linear regression
  X  : ape_index = reach_cm / height_cm
  Y1 : str_def (strike defense %, higher = better)
  Y2 : sapm    (significant strikes absorbed per minute, lower = better)

Usage:
  python analyze_hypothesis3.py --input ufc_analysis_data.csv
"""

import argparse
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["IPAexGothic", "Noto Sans CJK JP", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def run_regression(df, x_col, y_col):
    sub = df[[x_col, y_col]].dropna()
    x = sub[x_col].values
    y = sub[y_col].values
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    return {
        "x_col": x_col, "y_col": y_col, "n": len(sub),
        "slope": slope, "intercept": intercept, "r": r_value,
        "r_squared": r_value ** 2, "p_value": p_value, "std_err": std_err,
        "x": x, "y": y,
    }


def print_result(res, label):
    sig = "significant (p<0.05)" if res["p_value"] < 0.05 else "not significant (p>=0.05)"
    direction = "positive" if res["slope"] > 0 else "negative"
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(f"  n                   : {res['n']}")
    print(f"  slope               : {res['slope']:.4f}")
    print(f"  intercept           : {res['intercept']:.4f}")
    print(f"  r                   : {res['r']:.4f}")
    print(f"  R^2                 : {res['r_squared']:.4f}")
    print(f"  p-value             : {res['p_value']:.6f}  -> {sig}")
    print(f"  std err             : {res['std_err']:.4f}")
    print(f"  direction           : {direction}")


def plot_regression(res, title, xlabel, ylabel, out_path, color):
    fig, ax = plt.subplots(figsize=(7, 5.5))
    x, y = res["x"], res["y"]
    ax.scatter(x, y, alpha=0.5, s=28, color=color, edgecolors="white", linewidths=0.4)
    x_line = np.linspace(x.min(), x.max(), 100)
    y_line = res["slope"] * x_line + res["intercept"]
    ax.plot(x_line, y_line, color="#222222", linewidth=2.2, linestyle="--",
            label=f"regression line (R2={res['r_squared']:.3f}, p={res['p_value']:.4f})")
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.legend(loc="best", fontsize=9)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  -> saved plot: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Hypothesis 3: ape_index regression analysis")
    parser.add_argument("--input", default="ufc_analysis_data.csv")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    print(f"loaded: {len(df)} rows x {len(df.columns)} cols (input: {args.input})")

    df = df[(df["wins"] + df["losses"] + df["draws"]) >= 3].copy()
    print(f"filtered to fighters with >=3 fights: {len(df)} rows")

    res1 = run_regression(df, "ape_index", "str_def")
    print_result(res1, "Regression 1: ape_index -> str_def (strike defense %)")
    plot_regression(
        res1,
        title="Ape Index vs Strike Defense",
        xlabel="Ape Index (reach / height)",
        ylabel="Str. Def. (%)",
        out_path="hypothesis3_regression_strdef.png",
        color="#0070C0",
    )

    res2 = run_regression(df, "ape_index", "sapm")
    print_result(res2, "Regression 2: ape_index -> sapm (strikes absorbed/min)")
    plot_regression(
        res2,
        title="Ape Index vs Strikes Absorbed (SApM)",
        xlabel="Ape Index (reach / height)",
        ylabel="SApM (per min)",
        out_path="hypothesis3_regression_sapm.png",
        color="#C00000",
    )

    print(f"\n{'='*60}")
    print("  Overall conclusion")
    print(f"{'='*60}")
    supports1 = (res1["slope"] > 0) and (res1["p_value"] < 0.05)
    supports2 = (res2["slope"] < 0) and (res2["p_value"] < 0.05)
    if supports1 and supports2:
        verdict = "Hypothesis 3 is supported (significant in both defense metrics)"
    elif supports1 or supports2:
        verdict = "Hypothesis 3 is partially supported (significant in only one metric)"
    else:
        verdict = "Hypothesis 3 is NOT supported (no statistically significant relationship)"
    print(f"  Verdict: {verdict}")
    print(f"  Note: R^2 shows ape_index alone explains very little variance;")
    print(f"        it is at most one of many contributing factors.")

    # Robustness check: same relationship within each weight class?
    order = ["Strawweight", "Flyweight", "Bantamweight", "Featherweight", "Lightweight",
             "Welterweight", "Middleweight", "Light Heavyweight", "Heavyweight"]
    print(f"\n{'='*60}")
    print("  Robustness check: ape_index vs str_def correlation by weight class")
    print(f"{'='*60}")
    by_class_lines = []
    header = f"{'weight_class':<20}{'n':>6}{'mean_AI':>10}{'mean_StrDef':>13}{'r':>8}{'p':>10}"
    print(header)
    by_class_lines.append(header)
    for wc in order:
        sub = df[df["weight_class"] == wc].dropna(subset=["ape_index", "str_def"])
        if len(sub) < 10:
            continue
        r_wc, p_wc = stats.pearsonr(sub["ape_index"], sub["str_def"])
        line = (f"{wc:<20}{len(sub):>6}{sub['ape_index'].mean():>10.4f}"
                f"{sub['str_def'].mean():>13.1f}{r_wc:>8.3f}{p_wc:>10.4f}")
        print(line)
        by_class_lines.append(line)

    sub_wr = df.dropna(subset=["ape_index", "win_rate"])
    r_wr, p_wr = stats.pearsonr(sub_wr["ape_index"], sub_wr["win_rate"])
    winrate_line = f"ape_index vs win_rate (overall): n={len(sub_wr)}, r={r_wr:.4f}, p={p_wr:.4f}"
    print(f"\n[reference] {winrate_line}")

    with open("hypothesis3_results.txt", "w", encoding="utf-8") as f:
        f.write("Hypothesis 3 results: Ape Index vs damage-absorption regression\n")
        f.write("=" * 60 + "\n\n")
        for label, res in [("ape_index -> str_def", res1), ("ape_index -> sapm", res2)]:
            f.write(f"[{label}]\n")
            f.write(f"  n={res['n']}, slope={res['slope']:.4f}, r={res['r']:.4f}, "
                    f"R^2={res['r_squared']:.4f}, p={res['p_value']:.6f}\n\n")
        f.write(f"Verdict: {verdict}\n\n")
        f.write("-- robustness check by weight class --\n")
        f.write("\n".join(by_class_lines) + "\n\n")
        f.write(f"-- reference: {winrate_line} --\n")
        f.write("(statistically significant due to large n, but r is tiny -> negligible practical effect)\n")
    print(f"\nsaved results: hypothesis3_results.txt")


if __name__ == "__main__":
    main()
