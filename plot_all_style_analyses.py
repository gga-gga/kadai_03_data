import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf

pd.set_option("display.width", 140)

hist = pd.read_csv("trueskill_history.csv", parse_dates=["date", "dob_dt"])
final = pd.read_csv("trueskill_final.csv", parse_dates=["date", "dob_dt"])

# ============================================================
# 1. Age x TrueSkill (linear mixed model, random intercept per fighter)
# ============================================================
print("="*70)
print("1. 年齢 × TrueSkill（線形混合モデル）")
print("="*70)

d1 = hist.dropna(subset=["age", "mu"]).copy()
d1 = d1[(d1["age"] >= 16) & (d1["age"] <= 50)]
print(f"n observations: {len(d1)}, n fighters: {d1['fighter'].nunique()}")

# center age for numerical stability / interpretability
d1["age_c"] = d1["age"] - d1["age"].mean()
d1["age_c2"] = d1["age_c"] ** 2

m_lin = smf.mixedlm("mu ~ age_c", d1, groups=d1["fighter"]).fit()
print("\n--- Linear model: mu ~ age ---")
print(f"age coef = {m_lin.params['age_c']:.4f}   p = {m_lin.pvalues['age_c']:.4g}")
print(f"intercept = {m_lin.params['Intercept']:.4f}")

m_quad = smf.mixedlm("mu ~ age_c + age_c2", d1, groups=d1["fighter"]).fit()
print("\n--- Quadratic model: mu ~ age + age^2 ---")
print(f"age coef   = {m_quad.params['age_c']:.4f}   p = {m_quad.pvalues['age_c']:.4g}")
print(f"age^2 coef = {m_quad.params['age_c2']:.6f}  p = {m_quad.pvalues['age_c2']:.4g}")
b1, b2 = m_quad.params['age_c'], m_quad.params['age_c2']
if b2 != 0:
    vertex_c = -b1 / (2*b2)
    print(f"vertex (centered) = {vertex_c:.2f}  -> actual age = {vertex_c + d1['age'].mean():.2f}")

# ============================================================
# 2. Stance x TrueSkill (group comparison on final rating)
# ============================================================
print("\n" + "="*70)
print("2. スタンス × TrueSkill（群間比較）")
print("="*70)

d2 = final.dropna(subset=["stance", "mu"]).copy()
d2 = d2[d2["n_fights"] >= 3]
d2["stance"] = d2["stance"].replace({"": np.nan}).dropna()
counts = d2["stance"].value_counts()
print("stance counts (n_fights>=3):\n", counts)

main_stances = counts[counts >= 20].index.tolist()
print(f"\nmain stances (n>=20): {main_stances}")
groups = [d2.loc[d2["stance"] == st, "mu"].values for st in main_stances]
f_stat, p_val = stats.f_oneway(*groups)
print(f"\nANOVA on mu across {main_stances}: F={f_stat:.3f}, p={p_val:.4g}")
for st, g in zip(main_stances, groups):
    print(f"  {st:10s} n={len(g):4d}  mean_mu={g.mean():.3f}  sd={g.std():.3f}")

# also on conservative rating
groups_c = [d2.loc[d2["stance"] == st, "conservative"].values for st in main_stances]
f_stat_c, p_val_c = stats.f_oneway(*groups_c)
print(f"\nANOVA on conservative(mu-3sigma): F={f_stat_c:.3f}, p={p_val_c:.4g}")

# ============================================================
# 3. Common traits of strong fighters (top 25% vs rest)
# ============================================================
print("\n" + "="*70)
print("3. 強い選手の共通点（上位25% vs それ以外）")
print("="*70)

d3 = final[final["n_fights"] >= 5].copy()
print(f"n fighters (n_fights>=5): {len(d3)}")
q75 = d3["conservative"].quantile(0.75)
d3["strong"] = d3["conservative"] >= q75
print(f"threshold (75th pct conservative rating): {q75:.3f}")
print(f"strong group n={d3['strong'].sum()}, other n={(~d3['strong']).sum()}")

# age at last fight
d3v = d3.dropna(subset=["age"])
t_age, p_age = stats.ttest_ind(d3v.loc[d3v["strong"], "age"], d3v.loc[~d3v["strong"], "age"], equal_var=False)
print(f"\nAge at last observed fight: strong mean={d3v.loc[d3v['strong'],'age'].mean():.2f}, "
      f"other mean={d3v.loc[~d3v['strong'],'age'].mean():.2f}  (t={t_age:.2f}, p={p_age:.4g})")

# n_fights
t_nf, p_nf = stats.ttest_ind(d3.loc[d3["strong"], "n_fights"], d3.loc[~d3["strong"], "n_fights"], equal_var=False)
print(f"N fights: strong mean={d3.loc[d3['strong'],'n_fights'].mean():.2f}, "
      f"other mean={d3.loc[~d3['strong'],'n_fights'].mean():.2f}  (t={t_nf:.2f}, p={p_nf:.4g})")

# stance distribution (chi-square)
d3s = d3.dropna(subset=["stance"])
ct = pd.crosstab(d3s["strong"], d3s["stance"])
ct = ct[ct.columns[ct.sum() >= 10]]
print("\nStance crosstab (strong x stance):\n", ct)
chi2, p_chi, dof, exp = stats.chi2_contingency(ct)
print(f"chi2={chi2:.3f}, p={p_chi:.4g}, dof={dof}")
print("stance proportions within group:\n", (ct.T / ct.sum(axis=1)).T.round(3))

d3.to_csv("trueskill_strong_vs_rest.csv", index=False)
print("\nsaved trueskill_strong_vs_rest.csv")

# ============================================================
# Robustness check: does the age effect survive controlling for
# fight_no (experience / how many fights already fought)?
# TrueSkill mu tends to rise mechanically with more fights, so this
# mirrors the earlier "partial correlation" confound check.
# ============================================================
print("\n" + "="*70)
print("Robustness: age effect controlling for fight_no (experience)")
print("="*70)
d1["fight_no_c"] = d1["fight_no"] - d1["fight_no"].mean()
m_ctrl = smf.mixedlm("mu ~ age_c + age_c2 + fight_no_c", d1, groups=d1["fighter"]).fit()
print(m_ctrl.summary().tables[1])
corr_age_fightno = d1[["age", "fight_no"]].corr().iloc[0,1]
print(f"\ncorr(age, fight_no) = {corr_age_fightno:.3f}")
