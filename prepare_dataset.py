import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["IPAexGothic", "Noto Sans CJK JP", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

NAVY = "#1E2761"
RED = "#C00000"
BLUE = "#0070C0"
GRAY = "#7F7F7F"
CARD_BORDER = "#BFBFBF"

# =====================================================================
# (1) Rating trajectory example: Jon Jones' mu over his career
# =====================================================================
hist = pd.read_csv("trueskill_history.csv", parse_dates=["date"])
jj = hist[hist["fighter"] == "JON JONES"].sort_values("fight_no")
print(f"Jon Jones fights found: {len(jj)}")

fig, ax = plt.subplots(figsize=(7.6, 5.4))
fig.patch.set_facecolor("white"); ax.set_facecolor("white")

ax.plot(jj["fight_no"], jj["mu"], marker="o", markersize=6, linewidth=2.4, color=RED, zorder=3)
ax.fill_between(jj["fight_no"], jj["mu"] - jj["sigma"], jj["mu"] + jj["sigma"],
                 color=RED, alpha=0.15, zorder=1)

# annotate a couple of notable jumps/drops if visible
ax.set_xlabel("キャリア通算 試合数", fontsize=12, color="#262626")
ax.set_ylabel("TrueSkill：μ（推定スキル）", fontsize=12, color="#262626")
ax.set_title("レーティング推移の例：Jon Jones\n（帯＝μ±σ、試合を重ねるほど不確かさσが縮小）", fontsize=14.5, fontweight="bold", color=NAVY, pad=12)
ax.grid(alpha=0.25, color=CARD_BORDER)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color(CARD_BORDER)
fig.tight_layout()
fig.savefig("trueskill_trajectory_example_jp.png", dpi=200, facecolor="white")
plt.close(fig)
print("saved trueskill_trajectory_example_jp.png")

# =====================================================================
# (2) Top fighters ranking (conservative rating, n_fights>=10)
# =====================================================================
final = pd.read_csv("trueskill_final.csv")
top = final[final["n_fights"] >= 10].nlargest(12, "conservative").sort_values("conservative")

# nicer display names (title case)
def disp_name(s):
    return " ".join(w.capitalize() for w in s.split())

top = top.copy()
top["display"] = top["fighter"].apply(disp_name)

fig, ax = plt.subplots(figsize=(7.6, 6.4))
fig.patch.set_facecolor("white"); ax.set_facecolor("white")

bars = ax.barh(top["display"], top["conservative"], color=NAVY, height=0.62, zorder=3)
for b, v, n in zip(bars, top["conservative"].values, top["n_fights"].values):
    ax.text(v + 0.3, b.get_y() + b.get_height()/2, f"{v:.1f} (n={n})",
            va="center", fontsize=10.5, color="#262626")

ax.set_xlabel("TrueSkill 保守的評価値（μ−3σ）", fontsize=12, color="#262626")
ax.set_title("TrueSkill 上位選手ランキング（10試合以上）", fontsize=15, fontweight="bold", color=NAVY, pad=12)
ax.set_xlim(0, top["conservative"].max() + 4)
ax.grid(axis="x", alpha=0.25, color=CARD_BORDER, zorder=0)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color(CARD_BORDER)
fig.tight_layout()
fig.savefig("trueskill_top_ranking_jp.png", dpi=200, facecolor="white")
plt.close(fig)
print("saved trueskill_top_ranking_jp.png")
