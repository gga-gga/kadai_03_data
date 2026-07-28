import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm

pd.set_option("display.width", 160)

df = pd.read_csv("style_trueskill_merged.csv")
df = df.rename(columns={"stance_x": "stance"})
df = df[df["stance"].isin(["Orthodox", "Southpaw", "Switch"])].copy()
print(f"n = {len(df)}")

print("\n--- cell means (mu) by stance x style ---")
pivot_mu = df.pivot_table(index="stance", columns="style_label", values="mu", aggfunc=["mean", "count"])
print(pivot_mu.round(2))

print("\n--- cell means (conservative) by stance x style ---")
pivot_c = df.pivot_table(index="stance", columns="style_label", values="conservative", aggfunc="mean")
print(pivot_c.round(2))
pivot_n = df.pivot_table(index="stance", columns="style_label", values="conservative", aggfunc="count")
print("\ncounts:\n", pivot_n)

# ---- two-way ANOVA: mu ~ stance * style_label ----
print("\n" + "="*70)
print("Two-way ANOVA: mu ~ stance * style_label")
print("="*70)
model = ols("mu ~ C(stance) * C(style_label)", data=df).fit()
aov = anova_lm(model, typ=2)
print(aov.round(5))

# ---- best single combo ----
combo_mean = df.groupby(["stance", "style_label"])["conservative"].agg(["mean", "count"]).sort_values("mean", ascending=False)
print("\n--- combos ranked by mean conservative rating (all n) ---")
print(combo_mean.round(2))

# ---- composition of top-25% strong group vs rest, by combo ----
q75 = df["conservative"].quantile(0.75)
df["strong"] = df["conservative"] >= q75
df["combo"] = df["stance"] + "×" + df["style_label"]
ct = pd.crosstab(df["strong"], df["combo"])
ct = ct[ct.columns[ct.sum() >= 15]]
print("\n--- strong(top25%) vs rest, by stance×style combo (n>=15 only) ---")
print(ct)
prop = (ct.T / ct.sum(axis=1)).T
print("\nproportions within group:\n", prop.round(3))
chi2, p_chi, dof, exp = stats.chi2_contingency(ct)
print(f"\nchi2={chi2:.3f}, p={p_chi:.4g}, dof={dof}")
