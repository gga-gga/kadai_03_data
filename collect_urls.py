import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["IPAexGothic", "Noto Sans CJK JP", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

NAVY = "#1E2761"
RED = "#C00000"
BLUE = "#0070C0"
GREEN = "#1E8A3E"
CARD_BORDER = "#BFBFBF"

# colors spread apart on the color wheel (red / blue / green) instead of two blues
STYLE_COLORS = {"ストライカー": RED, "グラップラー": BLUE, "オールラウンダー": GREEN}

df = pd.read_csv("fighters_with_style_cluster.csv")

fig, ax = plt.subplots(figsize=(7.4, 5.6))
fig.patch.set_facecolor("white"); ax.set_facecolor("white")

plot_order = ["オールラウンダー", "グラップラー", "ストライカー"]
for label in plot_order:
    color = STYLE_COLORS[label]
    sub = df[df["style_label"] == label]
    ax.scatter(sub["slpm"], sub["td_avg"], s=30, alpha=0.85, color=color,
               edgecolors="white", linewidths=0.4, label=f"{label} (n={len(sub)})", zorder=3)

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
print("saved style_cluster_scatter_jp.png (separated colors: red/blue/green)")
