import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["IPAexGothic", "Noto Sans CJK JP", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["mathtext.fontset"] = "cm"

NAVY = "#1E2761"
RED = "#C00000"
GRAY = "#7F7F7F"
CARD_BORDER = "#BFBFBF"
FORMULA_BG = "#F2F2F2"

fig, ax0 = plt.subplots(figsize=(8.6, 4.6))
fig.patch.set_facecolor("white")
ax0.set_facecolor(FORMULA_BG)
ax0.set_xticks([]); ax0.set_yticks([])
ax0.set_xlim(0, 1); ax0.set_ylim(0, 1)
for spine in ax0.spines.values():
    spine.set_edgecolor(CARD_BORDER)

ax0.text(0.5, 0.90, "TrueSkillの仕組み（Herbrich et al., 2006）", ha="center", va="top",
          fontsize=16.5, fontweight="bold", color=NAVY, transform=ax0.transAxes)

ax0.text(0.06, 0.74, r"勝率の予測：", ha="left", va="center", fontsize=13.5, color="#262626", transform=ax0.transAxes)
ax0.text(0.30, 0.74,
          r"$P(A>B)=\Phi\left(\dfrac{\mu_A-\mu_B}{c}\right)$",
          ha="left", va="center", fontsize=13.5, color=NAVY, transform=ax0.transAxes)
ax0.text(0.30, 0.58,
          r"$c=\sqrt{2\beta^{2}+\sigma_A^{2}+\sigma_B^{2}}$",
          ha="left", va="center", fontsize=13.5, color=NAVY, transform=ax0.transAxes)

ax0.text(0.06, 0.38, r"試合後の更新：", ha="left", va="center", fontsize=13.5, color="#262626", transform=ax0.transAxes)
ax0.text(0.30, 0.42,
          r"$\mu_A \leftarrow \mu_A + \dfrac{\sigma_A^{2}}{c}\,v(\cdot)$",
          ha="left", va="center", fontsize=13.5, color=RED, transform=ax0.transAxes)
ax0.text(0.30, 0.22,
          r"$\sigma_A^{2} \leftarrow \sigma_A^{2}\left(1-\dfrac{\sigma_A^{2}}{c^{2}}\,w(\cdot)\right)$",
          ha="left", va="center", fontsize=13.5, color=RED, transform=ax0.transAxes)

ax0.text(0.06, 0.06,
          "μ：推定スキル　σ：不確かさ　→ 格上に勝つほどμの上昇幅が大きく、試合を重ねるほどσは縮小する",
          ha="left", va="center", fontsize=11.5, color=GRAY, style="italic", transform=ax0.transAxes)

fig.tight_layout()
fig.savefig("trueskill_formula_jp.png", dpi=200, facecolor="white")
plt.close(fig)
print("saved trueskill_formula_jp.png")
