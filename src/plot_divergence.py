"""Figure de la carte de divergence — MESURÉ, pas simulé.

Deux panneaux : la carte AUC (step × couche) et les deux profils marginaux.
Le titre porte explicitement la mention « mesuré » et le modèle, pour qu'aucune
figure de ce dépôt ne puisse être confondue avec une simulation.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
grid_file = sorted((ROOT / "results").glob("divergence_grid_*.npz"))[-1]
grid = np.load(grid_file)["grid"]
n_steps, n_layers = grid.shape

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.2), width_ratios=[1.35, 1])

im = ax1.imshow(grid, cmap="RdYlGn", vmin=0.5, vmax=1.0, aspect="auto")
ax1.set_xlabel("couche"); ax1.set_ylabel("step de génération")
ax1.set_xticks(range(n_layers)); ax1.set_yticks(range(n_steps))
ax1.set_title("AUC sonde linéaire, leave-one-prompt-out")
for s in range(n_steps):
    for l in range(n_layers):
        ax1.text(l, s, f"{grid[s,l]:.2f}", ha="center", va="center", fontsize=7)
fig.colorbar(im, ax=ax1, label="AUC")

ax2.plot(range(n_steps), grid.mean(axis=1), "o-", color="#b03030", label="moyenne par step")
ax2.plot(range(n_layers), grid[2], "s--", color="#30609b", label="par couche, au step 2 (pic)")
ax2.axhline(0.5, color="grey", ls=":", lw=1)
ax2.axhline(grid[2, 0], color="#30609b", ls=":", lw=1)
ax2.annotate(f"couche 0 (embedding) = {grid[2,0]:.2f}\nle token seul suffit déjà",
             xy=(0, grid[2, 0]), xytext=(3.2, 0.60), fontsize=9,
             arrowprops=dict(arrowstyle="->", color="#30609b", lw=1))
ax2.set_xlabel("step  /  couche"); ax2.set_ylabel("AUC")
ax2.set_ylim(0.45, 1.0); ax2.legend(loc="upper right", fontsize=9)
ax2.set_title("Profils marginaux")
ax2.grid(alpha=0.3)

fig.suptitle("MESURÉ — GPT-2 small, 120 trajectoires same-prompt bifurcation "
             "(60 Correct / 60 Hallucination, 10 prompts)", fontweight="bold")
fig.tight_layout()
dest = ROOT / "figures" / "gpt2" / "divergence_map.png"
fig.savefig(dest, dpi=150)
print(f"-> {dest.relative_to(ROOT)}")
