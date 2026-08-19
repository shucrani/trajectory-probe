"""Étape 3 — Où et quand les trajectoires divergent-elles ?

Carte de séparabilité Correct/Hallucination par (step de génération, couche),
sonde linéaire, validation croisée LEAVE-ONE-PROMPT-OUT : le prompt de test n'est
jamais vu à l'entraînement, sinon la sonde apprend l'identité du prompt.

Trois lectures, dans cet ordre :

1. CONTRÔLE DE SANITÉ — au step 0 l'état est celui du dernier token du prompt,
   identique dans les deux classes. L'AUC doit être exactement 0.5. Si elle ne
   l'est pas, il y a une fuite et rien de ce qui suit ne vaut.

2. CARTE — AUC par (step, couche). Non corrigée pour la sélection : le maximum
   d'une carte de 104 cellules est optimiste par construction. Il est rapporté
   comme descriptif, jamais comme résultat.

3. TEST PRÉ-SPÉCIFIÉ — une seule cellule, choisie AVANT de regarder la carte
   (dernier step, dernière couche), avec permutation des labels À L'INTÉRIEUR de
   chaque prompt. C'est la seule p-value qui a un sens ici.

Usage :
    .venv/bin/python src/divergence_analysis.py
"""
import argparse
from datetime import datetime
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
SEED = 42
N_PERM = 200


def probe_auc(X, y, groups):
    """AUC out-of-fold d'une sonde linéaire, leave-one-prompt-out.

    Chaque pli de test ne contient qu'un prompt (6 Correct + 6 Hallucination),
    donc l'AUC est calculée par pli puis moyennée : une AUC globale sur des
    scores non comparables entre plis n'aurait pas de sens.
    """
    logo = LeaveOneGroupOut()
    aucs = []
    for tr, te in logo.split(X, y, groups):
        if len(np.unique(y[tr])) < 2 or len(np.unique(y[te])) < 2:
            continue
        clf = make_pipeline(
            StandardScaler(),
            LogisticRegression(C=0.01, max_iter=2000, random_state=SEED),
        )
        clf.fit(X[tr], y[tr])
        s = clf.decision_function(X[te])
        aucs.append(rank_auc(s, y[te]))
    return float(np.mean(aucs)) if aucs else np.nan


def rank_auc(scores, labels):
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty(len(scores), dtype=float)
    ss = scores[order]
    i = 0
    while i < len(scores):
        j = i
        while j + 1 < len(scores) and ss[j + 1] == ss[i]:
            j += 1
        ranks[order[i:j + 1]] = 0.5 * (i + j) + 1.0
        i = j + 1
    n1 = float(labels.sum()); n0 = float(len(labels) - n1)
    if n0 == 0 or n1 == 0:
        return np.nan
    return (ranks[labels == 1].sum() - n1 * (n1 + 1) / 2.0) / (n0 * n1)


def permute_within_groups(y, groups, rng):
    """Permutation contrainte : les labels ne circulent qu'à l'intérieur d'un prompt.

    L'échangeabilité vaut au sein d'un prompt (même entrée, tirages différents),
    pas entre prompts. Une permutation globale testerait une autre hypothèse.
    """
    yp = y.copy()
    for g in np.unique(groups):
        m = groups == g
        v = yp[m]; rng.shuffle(v); yp[m] = v
    return yp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--npz", default=None)
    args = ap.parse_args()

    path = Path(args.npz) if args.npz else sorted((ROOT / "results").glob("trajectories_*.npz"))[-1]
    d = np.load(path, allow_pickle=True)
    X, y, groups = d["X"], d["y"], d["groups"]
    n_traj, n_steps, n_layers, dim = X.shape

    lines = []
    w = lines.append
    w("ÉTAPE 3 — CARTE DE DIVERGENCE")
    w(f"date     : {datetime.now().isoformat(timespec='seconds')}")
    w(f"source   : {path.name}")
    w(f"données  : {n_traj} trajectoires, {n_steps} steps, {n_layers} couches, dim {dim}")
    w(f"classes  : {int((y==0).sum())} Correct / {int((y==1).sum())} Hallucination")
    w(f"prompts  : {len(np.unique(groups))} · CV leave-one-prompt-out")
    w("")

    grid = np.full((n_steps, n_layers), np.nan)
    for s in range(n_steps):
        for l in range(n_layers):
            grid[s, l] = probe_auc(X[:, s, l, :], y, groups)

    w("AUC par (step de génération, couche) — sonde linéaire, out-of-fold")
    w("")
    w("step |" + "".join(f"{l:>6}" for l in range(n_layers)))
    w("-" * (6 + 6 * n_layers))
    for s in range(n_steps):
        w(f"{s:>4} |" + "".join(f"{grid[s,l]:>6.2f}" for l in range(n_layers)))
    w("")

    # 1. contrôle de sanité
    step0 = grid[0]
    w("1. CONTRÔLE DE SANITÉ — step 0 (état du dernier token du prompt)")
    w(f"   AUC min/max sur les couches : {np.nanmin(step0):.3f} / {np.nanmax(step0):.3f}")
    ok = np.allclose(step0, 0.5, atol=1e-9)
    w(f"   attendu exactement 0.500 (état identique dans les deux classes) : "
      f"{'OK' if ok else 'ÉCHEC — fuite à investiguer'}")
    w("")

    # 2. carte, descriptif seulement
    si, li = np.unravel_index(np.nanargmax(grid), grid.shape)
    w("2. CARTE (descriptif, non corrigé pour la sélection sur "
      f"{n_steps * n_layers} cellules)")
    w(f"   maximum : AUC = {grid[si, li]:.3f} au step {si}, couche {li}")
    w(f"   moyenne par step : " + ", ".join(f"s{s}={np.nanmean(grid[s]):.2f}" for s in range(n_steps)))
    w("")

    # 3. test pré-spécifié
    s_pre, l_pre = n_steps - 1, n_layers - 1
    obs = grid[s_pre, l_pre]
    rng = np.random.RandomState(SEED)
    Xc = X[:, s_pre, l_pre, :]
    null = np.array([probe_auc(Xc, permute_within_groups(y, groups, rng), groups)
                     for _ in range(N_PERM)])
    p = (np.sum(np.abs(null - 0.5) >= abs(obs - 0.5)) + 1) / (N_PERM + 1)
    w(f"3. TEST PRÉ-SPÉCIFIÉ — step {s_pre}, couche {l_pre} (choisis avant la carte)")
    w(f"   AUC observée      : {obs:.3f}")
    w(f"   H0 (permutation intra-prompt, {N_PERM} tirages) : "
      f"moyenne {null.mean():.3f}, écart-type {null.std():.3f}")
    w(f"   p bilatéral       : {p:.4f}")
    w("")
    w("LECTURE. Une séparation aux steps ≥ 1 est ATTENDUE : les tokens générés")
    w("diffèrent, donc les états qui les portent diffèrent. Ce n'est pas une")
    w("découverte. Ce qui informe, c'est la STRUCTURE — quelles couches portent la")
    w("séparation, et si elle persiste ou s'estompe le long de la génération.")
    w("La question de l'irréversibilité (D2) n'est PAS tranchée ici : elle demande")
    w("une intervention causale (patcher à un step, voir si l'issue bascule), pas")
    w("une mesure de séparabilité.")

    out = "\n".join(lines)
    print(out)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    (ROOT / "results" / f"divergence_{stamp}.txt").write_text(out + "\n")
    np.savez(ROOT / "results" / f"divergence_grid_{stamp}.npz", grid=grid, null=null)
    print(f"\n-> results/divergence_{stamp}.txt")


if __name__ == "__main__":
    main()
