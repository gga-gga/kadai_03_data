"""
Hypothesis 1: Does defense determine win rate more than offense?
====================================================================
Hypothesis: high win-rate fighters share more in common in defensive
stats (str_def / sapm) than in offensive stats (str_acc) -> defense
matters more than offense for winning.

Method: Pearson correlation between win_rate and each stat
  Offense : str_acc (strike accuracy %), slpm (strikes landed/min)
  Defense : str_def (strike defense %), sapm (strikes absorbed/min)
  (grappling stats td_acc / td_def / sub_avg included for reference)

Usage:
  python analyze_hypothesis1.py --input ufc_analysis_data.csv
"""

import argparse
import pandas as pd
from scipy.stats import pearsonr


def corr(df, col, y="win_rate"):
    sub = df[[col, y]].dropna()
    r, p = pearsonr(sub[col], sub[y])
    return {"col": col, "n": len(sub), "r": r, "p": p}


def main():
    parser = argparse.ArgumentParser(description="Hypothesis 1: offense vs defense correlation with win_rate")
    parser.add_argument("--input", default="ufc_analysis_data.csv")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    df = df[(df["wins"] + df["losses"] + df["draws"]) >= 3].copy()
    print(f"loaded & filtered (>=3 fights): {len(df)} rows\n")

    offense_cols = ["str_acc", "slpm"]
    defense_cols = ["str_def", "sapm"]
    grappling_cols = ["td_acc", "td_def", "sub_avg"]

    print(f"{'category':<10}{'stat':<10}{'n':>6}{'r':>9}{'p':>10}  meaning")
    results = {}
    meanings = {
        "str_acc": "higher = better offense",
        "slpm": "higher = more volume (offense)",
        "str_def": "higher = better defense",
        "sapm": "higher = worse defense (more absorbed)",
        "td_acc": "grappling accuracy",
        "td_def": "grappling defense",
        "sub_avg": "submission attempts",
    }
    for cat, cols in [("offense", offense_cols), ("defense", defense_cols), ("grappling", grappling_cols)]:
        for c in cols:
            res = corr(df, c)
            results[c] = res
            print(f"{cat:<10}{c:<10}{res['n']:>6}{res['r']:>9.4f}{res['p']:>10.4f}  {meanings[c]}")

    print(f"\n{'='*60}")
    print("  Comparison: offense vs defense (absolute correlation strength)")
    print(f"{'='*60}")
    offense_abs = max(abs(results[c]["r"]) for c in offense_cols)
    defense_abs = max(abs(results[c]["r"]) for c in defense_cols)
    print(f"  max |r| offense (str_acc/slpm) : {offense_abs:.4f}")
    print(f"  max |r| defense (str_def/sapm) : {defense_abs:.4f}")

    if defense_abs > offense_abs:
        verdict = "Hypothesis 1 is supported in direction: defense stats correlate more strongly with win_rate than offense stats."
    else:
        verdict = "Hypothesis 1 is NOT supported in direction: offense stats correlate at least as strongly as defense stats."

    any_sig = any(results[c]["p"] < 0.05 for c in offense_cols + defense_cols)
    print(f"\n  {verdict}")
    print(f"  Note: statistical significance (p<0.05) present: {any_sig}")
    print(f"  Note: even where significant, r magnitudes are generally small/moderate;")
    print(f"        win_rate is influenced by many factors beyond any single stat.")

    with open("hypothesis1_results.txt", "w", encoding="utf-8") as f:
        f.write("Hypothesis 1 results: offense vs defense correlation with win_rate\n")
        f.write("=" * 60 + "\n\n")
        for c, res in results.items():
            f.write(f"{c:<10} n={res['n']:<6} r={res['r']:.4f}  p={res['p']:.4f}  ({meanings[c]})\n")
        f.write(f"\nmax|r| offense = {offense_abs:.4f}, max|r| defense = {defense_abs:.4f}\n")
        f.write(f"\nVerdict: {verdict}\n")
    print("\nsaved results: hypothesis1_results.txt")


if __name__ == "__main__":
    main()
