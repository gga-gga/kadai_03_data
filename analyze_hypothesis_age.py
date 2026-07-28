"""
Hypothesis 2: Does the southpaw advantage vary by weight class?
==================================================================
Hypothesis: lighter weight classes benefit more from the southpaw's
angle advantage, while in heavier classes KO power offsets that benefit
-> a "structural difference" across weight classes.

Method: Chi-square test of independence
  For each weight class, build a 2x2 contingency table:
    stance (Southpaw / Orthodox)  x  win_rate tier (High / Low, split at
    the median win_rate within that weight class)
  Run a chi-square test per weight class, then compare the pattern
  between lighter and heavier classes.

Usage:
  python analyze_hypothesis2.py --input ufc_analysis_data.csv
"""

import argparse
import pandas as pd
from scipy.stats import chi2_contingency

ORDER = ["Strawweight", "Flyweight", "Bantamweight", "Featherweight", "Lightweight",
         "Welterweight", "Middleweight", "Light Heavyweight", "Heavyweight"]
LIGHT_CLASSES = ["Strawweight", "Flyweight", "Bantamweight"]
HEAVY_CLASSES = ["Light Heavyweight", "Heavyweight"]


def chi_square_for_class(df, weight_class):
    sub = df[df["weight_class"] == weight_class].copy()
    sub = sub[sub["stance"].isin(["Orthodox", "Southpaw"])]
    sub = sub.dropna(subset=["win_rate"])
    if len(sub) < 20:
        return None

    median_wr = sub["win_rate"].median()
    sub["win_tier"] = sub["win_rate"].apply(lambda x: "High" if x >= median_wr else "Low")

    table = pd.crosstab(sub["stance"], sub["win_tier"])
    if table.shape != (2, 2):
        return None

    chi2, p, dof, expected = chi2_contingency(table)

    south = sub[sub["stance"] == "Southpaw"]
    ortho = sub[sub["stance"] == "Orthodox"]
    south_high_rate = (south["win_tier"] == "High").mean() if len(south) else None
    ortho_high_rate = (ortho["win_tier"] == "High").mean() if len(ortho) else None

    return {
        "weight_class": weight_class,
        "n": len(sub),
        "n_southpaw": len(south),
        "n_orthodox": len(ortho),
        "median_win_rate": median_wr,
        "southpaw_high_pct": south_high_rate,
        "orthodox_high_pct": ortho_high_rate,
        "chi2": chi2,
        "p_value": p,
        "table": table,
    }


def main():
    parser = argparse.ArgumentParser(description="Hypothesis 2: chi-square test for southpaw advantage by weight class")
    parser.add_argument("--input", default="ufc_analysis_data.csv")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    df = df[(df["wins"] + df["losses"] + df["draws"]) >= 3].copy()
    print(f"loaded & filtered (>=3 fights): {len(df)} rows")
    print(f"stance distribution:\n{df['stance'].value_counts(dropna=False)}\n")

    results = []
    print(f"{'weight_class':<20}{'n':>5}{'n_SP':>6}{'n_OR':>6}{'SP_High%':>10}{'OR_High%':>10}{'chi2':>8}{'p':>9}")
    for wc in ORDER:
        res = chi_square_for_class(df, wc)
        if res is None:
            print(f"{wc:<20}  (insufficient data, skipped)")
            continue
        results.append(res)
        sp_pct = res["southpaw_high_pct"] * 100 if res["southpaw_high_pct"] is not None else float("nan")
        or_pct = res["orthodox_high_pct"] * 100 if res["orthodox_high_pct"] is not None else float("nan")
        print(f"{res['weight_class']:<20}{res['n']:>5}{res['n_southpaw']:>6}{res['n_orthodox']:>6}"
              f"{sp_pct:>10.1f}{or_pct:>10.1f}{res['chi2']:>8.3f}{res['p_value']:>9.4f}")

    print(f"\n{'='*70}")
    print("  Light-class vs heavy-class comparison")
    print(f"{'='*70}")
    light_res = [r for r in results if r["weight_class"] in LIGHT_CLASSES]
    heavy_res = [r for r in results if r["weight_class"] in HEAVY_CLASSES]

    def summarize(group, label):
        if not group:
            print(f"  {label}: insufficient data")
            return
        avg_gap = sum((r["southpaw_high_pct"] - r["orthodox_high_pct"]) for r in group) / len(group)
        sig_count = sum(1 for r in group if r["p_value"] < 0.05)
        print(f"  {label}: avg(Southpaw High% - Orthodox High%) = {avg_gap*100:+.1f}pt, "
              f"significant classes = {sig_count}/{len(group)}")

    summarize(light_res, "Light classes (Straw/Fly/Bantam)")
    summarize(heavy_res, "Heavy classes (LightHeavy/Heavy)")

    any_significant = any(r["p_value"] < 0.05 for r in results)
    print(f"\nOverall verdict:")
    if not any_significant:
        verdict = ("Hypothesis 2 is NOT supported: no weight class showed a statistically "
                    "significant association between stance and win-rate tier.")
    else:
        verdict = ("Hypothesis 2 is partially supported: some weight classes show a "
                    "significant stance/win-rate association, see per-class results above.")
    print(f"  {verdict}")

    with open("hypothesis2_results.txt", "w", encoding="utf-8") as f:
        f.write("Hypothesis 2 results: Southpaw advantage by weight class (chi-square test)\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"{'weight_class':<20}{'n':>5}{'n_SP':>6}{'n_OR':>6}{'SP_High%':>10}{'OR_High%':>10}{'chi2':>8}{'p':>9}\n")
        for r in results:
            sp_pct = r["southpaw_high_pct"] * 100
            or_pct = r["orthodox_high_pct"] * 100
            f.write(f"{r['weight_class']:<20}{r['n']:>5}{r['n_southpaw']:>6}{r['n_orthodox']:>6}"
                    f"{sp_pct:>10.1f}{or_pct:>10.1f}{r['chi2']:>8.3f}{r['p_value']:>9.4f}\n")
        f.write("\n")
        if light_res:
            avg_gap_l = sum((r["southpaw_high_pct"] - r["orthodox_high_pct"]) for r in light_res) / len(light_res)
            f.write(f"Light classes avg gap (Southpaw - Orthodox High%): {avg_gap_l*100:+.1f}pt\n")
        if heavy_res:
            avg_gap_h = sum((r["southpaw_high_pct"] - r["orthodox_high_pct"]) for r in heavy_res) / len(heavy_res)
            f.write(f"Heavy classes avg gap (Southpaw - Orthodox High%): {avg_gap_h*100:+.1f}pt\n")
        f.write(f"\nVerdict: {verdict}\n")
    print("\nsaved results: hypothesis2_results.txt")


if __name__ == "__main__":
    main()
