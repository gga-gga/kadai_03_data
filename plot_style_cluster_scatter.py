import pandas as pd
from scipy import stats

pd.set_option("display.width", 150)

style = pd.read_csv("fighters_with_style_cluster.csv")
final = pd.read_csv("trueskill_final.csv")

style["key"] = style["name"].str.strip().str.upper()
final_u = final.drop_duplicates("fighter", keep="first")

merged = style.merge(final_u, left_on="key", right_on="fighter", how="inner")
print(f"style-labeled fighters: {len(style)}")
print(f"matched with TrueSkill: {len(merged)}")

# require a minimum number of fights for a stable TrueSkill estimate
m = merged[merged["n_fights"] >= 3].copy()
print(f"after n_fights>=3 filter: {len(m)}")

print("\n--- TrueSkill (conservative = mu - 3*sigma) by fight style ---")
print(m.groupby("style_label")["conservative"].agg(["mean", "std", "count"]).round(3))

groups = [m.loc[m["style_label"] == g, "conservative"].values for g in ["ストライカー", "グラップラー", "オールラウンダー"]]
f_stat, p_val = stats.f_oneway(*groups)
print(f"\nANOVA (conservative rating): F={f_stat:.3f}, p={p_val:.4g}")

print("\n--- also on raw mu ---")
print(m.groupby("style_label")["mu"].agg(["mean", "std", "count"]).round(3))
groups_mu = [m.loc[m["style_label"] == g, "mu"].values for g in ["ストライカー", "グラップラー", "オールラウンダー"]]
f_mu, p_mu = stats.f_oneway(*groups_mu)
print(f"ANOVA (mu): F={f_mu:.3f}, p={p_mu:.4g}")

# pairwise (Tukey-ish quick t-tests) if ANOVA significant
if p_val < 0.05:
    print("\npairwise t-tests (conservative):")
    labels = ["ストライカー", "グラップラー", "オールラウンダー"]
    for i in range(len(labels)):
        for j in range(i+1, len(labels)):
            a = m.loc[m["style_label"] == labels[i], "conservative"]
            b = m.loc[m["style_label"] == labels[j], "conservative"]
            t, p = stats.ttest_ind(a, b, equal_var=False)
            print(f"  {labels[i]} vs {labels[j]}: t={t:.2f}, p={p:.4g}")

m.to_csv("style_trueskill_merged.csv", index=False)
print("\nsaved style_trueskill_merged.csv")
