"""C1 — Contrôle de confond de surface.

Question : les 50 prompts du dataset sont-ils separables par des proprietes de
SURFACE (longueur, marqueurs evidentiels, presence d'une annee) qui n'ont rien a
voir avec la veracite ? Si oui, l'AUC de 0.939 obtenue sur les hidden states
n'est pas attribuable a la geometrie des trajectoires.

Aucun modele n'est charge. Pour une feature unique, l'AUC est exactement la
statistique de Mann-Whitney : AUC = P(x_hallu > x_factual) + 0.5 P(egalite).
Significativite par permutation exacte des labels.

Usage : python3 src/c1_surface_confound.py
"""
import ast
import json
import re
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOK = ROOT / "notebooks" / "gpt2_navigation_certificate_validation.ipynb"
N_PERM = 20000
SEED = 42


def load_prompts():
    """Extrait la liste PROMPTS du notebook, sans la recopier a la main."""
    nb = json.loads(NOTEBOOK.read_text())
    for cell in nb["cells"]:
        src = "".join(cell["source"])
        if "PROMPTS = [" in src:
            start = src.index("PROMPTS = [") + len("PROMPTS = ")
            depth, end = 0, None
            for i, ch in enumerate(src[start:], start):
                if ch == "[":
                    depth += 1
                elif ch == "]":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            return ast.literal_eval(src[start:end])
    raise RuntimeError("cellule PROMPTS introuvable dans le notebook")


EVIDENTIAL = re.compile(
    r"according to|recent stud|scientists (confirmed|discovered)|researchers (proved|found)"
    r"|archaeological evidence|studies show|it was (revealed|reported)",
    re.I,
)
YEAR = re.compile(r"\b(19|20)\d{2}\b")


def features(text):
    return {
        "n_words": float(len(text.split())),
        "n_chars": float(len(text)),
        "has_evidential": float(bool(EVIDENTIAL.search(text))),
        "has_year": float(bool(YEAR.search(text))),
    }


def auc(scores, labels):
    """AUC exacte via les rangs (Mann-Whitney), egalites traitees par rang moyen."""
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty(len(scores), dtype=float)
    sorted_scores = scores[order]
    i = 0
    while i < len(scores):
        j = i
        while j + 1 < len(scores) and sorted_scores[j + 1] == sorted_scores[i]:
            j += 1
        ranks[order[i : j + 1]] = 0.5 * (i + j) + 1.0
        i = j + 1
    n1 = float(labels.sum())
    n0 = float(len(labels) - n1)
    return (ranks[labels == 1].sum() - n1 * (n1 + 1) / 2.0) / (n0 * n1)


def perm_p(scores, labels, observed, rng):
    """p bilateral : P(|AUC_permutee - 0.5| >= |AUC_observee - 0.5|)."""
    y = labels.copy()
    extreme = 0
    target = abs(observed - 0.5)
    for _ in range(N_PERM):
        rng.shuffle(y)
        if abs(auc(scores, y) - 0.5) >= target:
            extreme += 1
    return (extreme + 1) / (N_PERM + 1)


def main():
    prompts = load_prompts()
    labels = np.array([p["label"] for p in prompts])
    feats = [features(p["text"]) for p in prompts]
    names = list(feats[0])
    rng = np.random.RandomState(SEED)

    lines = []
    w = lines.append
    w("C1 — CONTROLE DE CONFOND DE SURFACE")
    w(f"date            : {datetime.now().isoformat(timespec='seconds')}")
    w(f"source          : {NOTEBOOK.relative_to(ROOT)}")
    w(f"n               : {len(prompts)} ({int((labels==0).sum())} factuels / {int((labels==1).sum())} hallucinatoires)")
    w(f"permutations    : {N_PERM} (seed {SEED})")
    w("aucun modele charge — proprietes de surface uniquement")
    w("")
    w(f"{'feature':<18}{'AUC':>8}{'p':>10}   {'factuels':>16}{'hallucinatoires':>18}")
    w("-" * 74)

    for name in names:
        scores = np.array([f[name] for f in feats])
        a = auc(scores, labels)
        p = perm_p(scores, labels, a, rng)
        m0, s0 = scores[labels == 0].mean(), scores[labels == 0].std()
        m1, s1 = scores[labels == 1].mean(), scores[labels == 1].std()
        w(f"{name:<18}{a:>8.3f}{p:>10.5f}   {m0:>8.2f} ± {s0:<5.2f}{m1:>10.2f} ± {s1:<5.2f}")

    w("")
    w("Lecture : AUC = 1.000 signifie separation parfaite par cette seule propriete")
    w("de surface. Toute AUC obtenue sur les hidden states qui n'excede pas ces")
    w("valeurs ne demontre rien sur la geometrie des trajectoires.")
    w("")
    w("Limite : le comptage en mots approxime le comptage en tokens BPE (correlation")
    w("elevee sur de l'anglais standard, mais non identique). Refaire avec le")
    w("tokenizer GPT-2 quand transformers sera installe.")

    out = "\n".join(lines)
    print(out)
    stamp = datetime.now().strftime("%Y%m%d")
    dest = ROOT / "results" / f"c1_surface_confound_{stamp}.txt"
    dest.write_text(out + "\n")
    print(f"\n-> {dest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
