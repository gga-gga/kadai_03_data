"""
Regenerate the age x win_rate quadratic-fit chart, restyled to match the
deck's design language (navy/red, Japanese labels), for use in Slide 6.
"""
import numpy as np
import pandas as pd
from datetime import datetime
import statsmodels.api as sm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["IPAexGothic", "Noto Sans CJK JP", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

NAVY = "#002060"
BLUE = "#0070C0"
RED = "#C00000"
GRAY = "#7F7F7F"
CARD_BORDER = "#BFBFBF"


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


def build_dataset(input_path, raw_path):
    main = pd.read_csv(input_path)
    raw = pd.read_csv(raw_path)
    raw = raw[["url", "dob", "last_match"]].copy()
    raw["dob_year"] = raw["dob"].apply(parse_dob_year)
    raw["lastmatch_year"] = raw["last_match"].apply(parse_lastmatch_year)
    df = main.merge(raw[["url", "dob_year", "lastmatch_year"]], on="url", how="left")
    df["age_at_last_match"] = df["lastmatch_year"] - df["dob_year"]
    df = df.dropna(subset=["age_at_last_match", "win_rate"]).copy()
    df = df[(df["age_at_last_match"] >= 16) & (df["age_at_last_match"] <= 50)]
    return df


df = build_dataset("ufc_analysis_data.csv", "alt_fighters_stats.csv")
df = df[(df["wins"] + df["losses"] + df["draws"]) >= 3].copy()

age = df["age_at_last_match"].values.astype(float)
win_rate = df["win_rate"].values.astype(float)

X = sm.add_constant(np.column_stack([age, age ** 2]))
model = sm.OLS(win_rate, X).fit()
b0, b1, b2 = model.params
r2 = model.rsquared
f_p = model.f_pvalue
p2 = model.pvalues[2]
vertex_age = -b1 / (2 * b2)
vertex_y = b0 + b1 * vertex_age + b2 * vertex_age ** 2

fig, ax = plt.subplots(figsize=(7.2, 5.4))
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

ax.scatter(age, win_rate, alpha=0.35, s=24, color=BLUE,
           edgecolors="white", linewidths=0.3, label="選手（1点＝1ファイター）", zorder=2)

x_line = np.linspace(age.min(), age.max(), 200)
y_line = b0 + b1 * x_line + b2 * x_line ** 2
ax.plot(x_line, y_line, color=RED, linewidth=3, label=f"二次回帰曲線（R²={r2:.3f}, p={f_p:.4f}）", zorder=3)

ax.axvline(vertex_age, color=GRAY, linestyle="--", linewidth=1.3, zorder=1)
ax.scatter([vertex_age], [vertex_y], color=RED, s=160, zorder=5, marker="*",
           edgecolors="white", linewidths=0.8, label=f"転換点（最小）年齢 ~{vertex_age:.1f}歳")

ax.annotate("U字カーブ\n（逆U字ではない）",
            xy=(vertex_age, vertex_y), xytext=(vertex_age + 4.5, vertex_y - 11),
            fontsize=11, color=NAVY, fontweight="bold", ha="center",
            arrowprops=dict(arrowstyle="->", color=NAVY, lw=1.4))

# Highlight the sparse 40+ tail
ax.axvspan(40, age.max() + 0.5, color=RED, alpha=0.06, zorder=0)
ax.text(age.max() - 1, 33, "n=64（少数）\n慎重な解釈が必要", fontsize=9.3, color=RED,
        ha="right", va="bottom", fontweight="bold")

ax.set_title("年齢 × 勝率：二次回帰分析の結果", fontsize=15, fontweight="bold", color=NAVY, pad=12)
ax.set_xlabel("最終試合時点の年齢（歳）", fontsize=11, color="#262626")
ax.set_ylabel("勝率（%）", fontsize=11, color="#262626")
ax.tick_params(colors="#262626")
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color(CARD_BORDER)
ax.grid(alpha=0.2, color=CARD_BORDER)
ax.legend(loc="upper right", fontsize=9, frameon=True, facecolor="white", edgecolor=CARD_BORDER)
ax.set_ylim(28, 105)

fig.tight_layout()
fig.savefig("hypothesis_age_quadratic_jp.png", dpi=200, facecolor="white")
print("saved hypothesis_age_quadratic_jp.png")
print(f"b0={b0:.4f} b1={b1:.4f} b2={b2:.6f} p2={p2:.4f} r2={r2:.4f} f_p={f_p:.4f} vertex={vertex_age:.2f}")
