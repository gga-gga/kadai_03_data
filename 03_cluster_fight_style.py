import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["IPAexGothic", "Noto Sans CJK JP", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

NAVY = "#1E2761"
RED = "#990011"
BLUE = "#0070C0"
GRAY = "#7F7F7F"
CARD_BORDER = "#BFBFBF"

labels = ["単純相関\n(年齢 → 勝率)", "偏相関\n(試合数を統制)"]
values = [-0.237, -0.164]

fig, ax = plt.subplots(figsize=(6.2, 5.6))
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

bars = ax.bar(labels, values, color=[BLUE, RED], width=0.5, zorder=3)
for b, v in zip(bars, values):
    ax.text(b.get_x() + b.get_width()/2, v - 0.018, f"{v:.3f}", ha="center", va="top",
            fontsize=18, fontweight="bold", color="white", zorder=4)

ax.axhline(0, color="#444444", linewidth=1)
ax.set_ylim(-0.30, 0.02)
ax.set_ylabel("相関係数 r", fontsize=13, color="#262626")
ax.set_title("年齢 × 勝率：交絡要因（試合数）の統制", fontsize=15, fontweight="bold", color=NAVY, pad=14)
ax.tick_params(axis="x", labelsize=13, colors="#262626")
ax.tick_params(axis="y", colors="#262626")
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color(CARD_BORDER)
ax.grid(axis="y", alpha=0.25, color=CARD_BORDER, zorder=0)

fig.tight_layout()
fig.savefig("partial_corr_comparison_jp.png", dpi=200, facecolor="white")
print("saved partial_corr_comparison_jp.png")
