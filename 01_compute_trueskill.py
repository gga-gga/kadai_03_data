"""
Chart for Slide 5 (main hypothesis): a straight linear regression line
matching the Pearson r = -0.237 stat shown on that slide. Restyled to
match the deck's design language (navy/red, Japanese labels).

(Separate from plot_age_quadratic_jp.py, which is the *curved* quadratic
fit used on Slide 6 — these are two different statistical models and must
not share the same chart image.)
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

slope, intercept, r, p, se = stats.linregress(age, win_rate)

fig, ax = plt.subplots(figsize=(7.2, 5.4))
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

ax.scatter(age, win_rate, alpha=0.35, s=24, color=BLUE,
           edgecolors="white", linewidths=0.3, label="選手（1点＝1ファイター）", zorder=2)

x_line = np.linspace(age.min(), age.max(), 200)
y_line = intercept + slope * x_line
ax.plot(x_line, y_line, color=RED, linewidth=3,
        label=f"線形回帰直線（r={r:.3f}, p<0.001）", zorder=3)

ax.set_title("年齢 × 勝率：ピアソン相関分析の結果", fontsize=15, fontweight="bold", color=NAVY, pad=12)
ax.set_xlabel("最終試合時点の年齢（歳）", fontsize=11, color="#262626")
ax.set_ylabel("勝率（%）", fontsize=11, color="#262626")
ax.tick_params(colors="#262626")
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color(CARD_BORDER)
ax.grid(alpha=0.2, color=CARD_BORDER)
ax.legend(loc="upper right", fontsize=9.5, frameon=True, facecolor="white", edgecolor=CARD_BORDER)
ax.set_ylim(28, 105)

fig.tight_layout()
fig.savefig("hypothesis_age_linear_jp.png", dpi=200, facecolor="white")
print("saved hypothesis_age_linear_jp.png")
print(f"slope={slope:.4f} intercept={intercept:.4f} r={r:.4f} p={p:.6f}")
