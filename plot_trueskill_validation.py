import pandas as pd
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["IPAexGothic", "Noto Sans CJK JP", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

NAVY = "#1E2761"
BLUE = "#0070C0"
RED = "#990011"
GRAY = "#7F7F7F"
CARD_BORDER = "#BFBFBF"
GREEN = "#2E7D32"

STYLE_COLORS = {"ストライカー": RED, "グラップラー": BLUE, "オールラウンダー": NAVY}
STANCE_COLORS = {"Orthodox": NAVY, "Southpaw": RED, "Switch": BLUE}

# =====================================================================
# 3.1 得意分野の分類（散布図: slpm vs td_avg, colored by style_label）
# =====================================================================
df = pd.read_csv("fighters_with_style_cluster.csv")

fig, ax = plt.subplots(figsize=(7.4, 5.6))
fig.patch.set_facecolor("white"); ax.set_facecolor("white")
for label, color in STYLE_COLORS.items():
    sub = df[df["style_label"] == label]
    ax.scatter(sub["slpm"], sub["td_avg"], s=20, alpha=0.5, color=color,
               edgecolors="white", linewidths=0.3, label=f"{label} (n={len(sub)})")

ax.set_xlabel("打撃頻度：slpm（1分あたり打撃数）", fontsize=12, color="#262626")
ax.set_ylabel("組み技頻度：td_avg（15分あたりテイクダウン数）", fontsize=12, color="#262626")
ax.set_title("得意分野の分類：打撃 × 組み技の傾向", fontsize=15, fontweight="bold", color=NAVY, pad=12)
ax.set_xlim(-0.3, 12)
ax.set_ylim(-0.3, 8)
ax.legend(loc="upper right", fontsize=10.5, frameon=True, facecolor="white", edgecolor=CARD_BORDER)
ax.grid(alpha=0.2, color=CARD_BORDER)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color(CARD_BORDER)
fig.tight_layout()
fig.savefig("style_cluster_scatter_jp.png", dpi=200, facecolor="white")
plt.close(fig)
print("saved style_cluster_scatter_jp.png")

# =====================================================================
# 3.2 スタンス × 強さ（棒グラフ + エラーバー）
# =====================================================================
final = pd.read_csv("trueskill_final.csv")
d2 = final.dropna(subset=["stance", "mu"]).copy()
d2 = d2[d2["n_fights"] >= 3]
main_stances = ["Orthodox", "Southpaw", "Switch"]
d2 = d2[d2["stance"].isin(main_stances)]

means = d2.groupby("stance")["conservative"].mean().reindex(main_stances)
sems = d2.groupby("stance")["conservative"].sem().reindex(main_stances)
ns = d2.groupby("stance")["conservative"].count().reindex(main_stances)

groups = [d2.loc[d2["stance"] == s, "conservative"].values for s in main_stances]
f_stat, p_val = stats.f_oneway(*groups)

fig, ax = plt.subplots(figsize=(6.4, 5.6))
fig.patch.set_facecolor("white"); ax.set_facecolor("white")
colors = [STANCE_COLORS[s] for s in main_stances]
bars = ax.bar(main_stances, means.values, yerr=sems.values, capsize=6,
              color=colors, width=0.55, zorder=3,
              error_kw={"ecolor": "#444444", "elinewidth": 1.3})
for i, (m, n) in enumerate(zip(means.values, ns.values)):
    ax.text(i, m + sems.values[i] + 0.4, f"{m:.2f}\n(n={n})", ha="center", fontsize=11, color="#262626")

ax.set_ylabel("平均 TrueSkill（保守的評価値 μ−3σ）", fontsize=12, color="#262626")
ax.set_title(f"スタンス × 強さ（ANOVA p={p_val:.3f}）", fontsize=15, fontweight="bold", color=NAVY, pad=12)
ax.set_ylim(0, max(means.values) + 4)
ax.grid(axis="y", alpha=0.25, color=CARD_BORDER, zorder=0)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color(CARD_BORDER)
fig.tight_layout()
fig.savefig("stance_trueskill_bar_jp.png", dpi=200, facecolor="white")
plt.close(fig)
print("saved stance_trueskill_bar_jp.png")

# =====================================================================
# 3.3 得意分野 × 強さ（棒グラフ + 有意差ブラケット）
# =====================================================================
m = pd.read_csv("style_trueskill_merged.csv")
style_order = ["ストライカー", "オールラウンダー", "グラップラー"]
means3 = m.groupby("style_label")["conservative"].mean().reindex(style_order)
sems3 = m.groupby("style_label")["conservative"].sem().reindex(style_order)
ns3 = m.groupby("style_label")["conservative"].count().reindex(style_order)

groups3 = [m.loc[m["style_label"] == s, "conservative"].values for s in style_order]
f3, p3 = stats.f_oneway(*groups3)

fig, ax = plt.subplots(figsize=(6.4, 5.6))
fig.patch.set_facecolor("white"); ax.set_facecolor("white")
colors3 = [STYLE_COLORS[s] for s in style_order]
ax.bar(style_order, means3.values, yerr=sems3.values, capsize=6,
       color=colors3, width=0.55, zorder=3,
       error_kw={"ecolor": "#444444", "elinewidth": 1.3})
for i, (mm, n) in enumerate(zip(means3.values, ns3.values)):
    ax.text(i, mm + sems3.values[i] + 0.4, f"{mm:.2f}\n(n={n})", ha="center", fontsize=11, color="#262626")

# significance brackets: striker-grappler(idx0-2), striker-allrounder(idx0-1)
y_top = max(means3.values) + 2.2
def bracket(x1, x2, y, text):
    ax.plot([x1, x1, x2, x2], [y, y+0.3, y+0.3, y], color="#333333", linewidth=1.1)
    ax.text((x1+x2)/2, y+0.4, text, ha="center", fontsize=12, color="#333333")

bracket(0, 1, y_top, "*")
bracket(0, 2, y_top + 1.6, "**")

ax.set_ylabel("平均 TrueSkill（保守的評価値 μ−3σ）", fontsize=12, color="#262626")
ax.set_title(f"得意分野 × 強さ（ANOVA p={p3:.4f}）", fontsize=15, fontweight="bold", color=NAVY, pad=12)
ax.set_ylim(0, y_top + 3.5)
ax.grid(axis="y", alpha=0.25, color=CARD_BORDER, zorder=0)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color(CARD_BORDER)
fig.tight_layout()
fig.savefig("style_trueskill_bar_jp.png", dpi=200, facecolor="white")
plt.close(fig)
print("saved style_trueskill_bar_jp.png")

# =====================================================================
# 3.4 スタンス × 得意分野 交互作用プロット
# =====================================================================
pivot = m.rename(columns={"stance_x": "stance"})
pivot = pivot[pivot["stance"].isin(main_stances)]
pv = pivot.pivot_table(index="style_label", columns="stance", values="conservative", aggfunc="mean").reindex(style_order)

fig, ax = plt.subplots(figsize=(7.4, 5.6))
fig.patch.set_facecolor("white"); ax.set_facecolor("white")
x = np.arange(len(style_order))
for stance in main_stances:
    ax.plot(x, pv[stance].values, marker="o", markersize=9, linewidth=2.6,
            color=STANCE_COLORS[stance], label=stance)

ax.set_xticks(x)
ax.set_xticklabels(style_order, fontsize=12)
ax.set_ylabel("平均 TrueSkill（保守的評価値 μ−3σ）", fontsize=12, color="#262626")
ax.set_title("スタンス × 得意分野：交互作用プロット\n（線がほぼ平行＝交互作用なし）", fontsize=14.5, fontweight="bold", color=NAVY, pad=12)
ax.legend(loc="upper left", fontsize=11, frameon=True, facecolor="white", edgecolor=CARD_BORDER)
ax.grid(alpha=0.25, color=CARD_BORDER)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color(CARD_BORDER)
fig.tight_layout()
fig.savefig("interaction_stance_style_jp.png", dpi=200, facecolor="white")
plt.close(fig)
print("saved interaction_stance_style_jp.png")
