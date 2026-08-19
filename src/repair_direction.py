"""Étape 7 — La direction qui répare est-elle stable entre prompts ?

L'étape 6 a établi qu'un état correct répare une trajectoire hallucinée (8.9 %)
là où un bruit de même amplitude ne répare jamais (0/180). Le contenu compte
donc. Reste la question qui décide si c'est opérationnalisable :

    cette direction est-elle PARTAGÉE entre prompts, ou propre à chaque cas ?

Partagée -> un vecteur de steering unique, calculable une fois, applicable à des
prompts jamais vus. C'est G1-G2 du programme.
Propre à chaque cas -> observable mais inutilisable : il faudrait déjà connaître
la bonne réponse pour construire la direction qui y mène.

DEUX MESURES, l'une géométrique, l'autre fonctionnelle.

A. GÉOMÉTRIE. Direction de réparation d'un prompt p :
       d_p = centroïde(Correct_p) - centroïde(Hallucination_p)
   On compare cos(d_p, d_q) entre prompts. Deux références indispensables :
   - PLAFOND : fiabilité split-half. On coupe les 6 runs de chaque classe en deux
     moitiés, on calcule une direction sur chacune, on les compare. Aucune
     similarité entre prompts ne peut raisonnablement dépasser ce plafond, qui
     mesure le bruit d'estimation à 3 runs par classe.
   - PLANCHER : cos entre vecteurs aléatoires en dimension 768, soit ~0.

B. FONCTION. Le test qui décide vraiment : on construit la direction sur les
   AUTRES prompts (leave-one-prompt-out) et on l'applique au prompt tenu à
   l'écart. Quatre conditions à NORME ÉGALE — la leçon de l'étape 6 est qu'une
   comparaison à norme libre ne mesure que l'amplitude :

       oracle-paire   : l'état du donneur correct apparié (= étape 6, 8.9 %)
       oracle-prompt  : direction moyenne DU prompt lui-même (plafond atteignable)
       transfert      : direction moyenne des AUTRES prompts (ce qui nous intéresse)
       aléatoire      : direction tirée au hasard (= étape 6, 0 %)

Usage :
    .venv/bin/python src/repair_direction.py
"""
import argparse
import json
from datetime import datetime
from itertools import combinations
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from bifurcation_probe import PROMPTS, classify
from causal_patching import Patcher
from window_patching import run

ROOT = Path(__file__).resolve().parent.parent
SEED = 42


def unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


def direction(X, idx_c, idx_h, steps, layer):
    """centroïde(Correct) - centroïde(Hallucination), moyenné sur la fenêtre."""
    c = X[np.ix_(idx_c, steps, [layer])].mean(axis=(0, 1, 2))
    h = X[np.ix_(idx_h, steps, [layer])].mean(axis=(0, 1, 2))
    return c - h


def geometry(X, y, groups, steps, layers, rng):
    out = {}
    for l in layers:
        dirs, halves = {}, {}
        for gi in np.unique(groups):
            ic = np.where((groups == gi) & (y == 0))[0]
            ih = np.where((groups == gi) & (y == 1))[0]
            if len(ic) < 4 or len(ih) < 4:
                continue
            dirs[gi] = unit(direction(X, ic, ih, steps, l))
            a = unit(direction(X, ic[: len(ic) // 2], ih[: len(ih) // 2], steps, l))
            b = unit(direction(X, ic[len(ic) // 2:], ih[len(ih) // 2:], steps, l))
            halves[gi] = float(a @ b)
        cross = [float(dirs[p] @ dirs[q]) for p, q in combinations(sorted(dirs), 2)]
        rand = [float(unit(rng.normal(size=X.shape[-1])) @ unit(rng.normal(size=X.shape[-1])))
                for _ in range(500)]
        out[l] = {
            "cross_mean": float(np.mean(cross)), "cross_std": float(np.std(cross)),
            "cross_min": float(np.min(cross)), "cross_max": float(np.max(cross)),
            "splithalf": float(np.mean(list(halves.values()))),
            "random_abs95": float(np.percentile(np.abs(rand), 95)),
            "n_pairs": len(cross),
        }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gpt2")
    ap.add_argument("--start", type=int, default=1)
    ap.add_argument("--window", type=int, default=3)
    ap.add_argument("--layers", type=int, nargs="+", default=[4, 8, 11])
    ap.add_argument("--pairs", type=int, default=6)
    ap.add_argument("--max-new-tokens", type=int, default=8)
    args = ap.parse_args()

    tag = args.model.replace("/", "-")
    npz = sorted((ROOT / "results").glob(f"trajectories_{tag}_*.npz"))[-1]
    d = np.load(npz, allow_pickle=True)
    X, y, groups, gen_tokens = d["X"], d["y"], d["groups"], d["tokens"]
    prompts = list(d["prompts"])
    answers_of = {p: a for p, a in PROMPTS}
    steps = list(range(args.start, args.start + args.window))
    rng = np.random.RandomState(SEED)

    geo = geometry(X, y, groups, steps, args.layers, rng)

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(args.model)
    tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(args.model).to(device).eval()
    patcher = Patcher(model)

    tally, detail = {}, []
    def bump(k, hit):
        t = tally.setdefault(k, [0, 0]); t[1] += 1; t[0] += int(hit)

    for gi, prompt in enumerate(prompts):
        answers = answers_of[prompt]
        ids = tok(prompt, return_tensors="pt").to(device)["input_ids"]
        ic = np.where((groups == gi) & (y == 0))[0]
        ih = np.where((groups == gi) & (y == 1))[0]
        if len(ic) == 0 or len(ih) == 0:
            continue
        others = np.unique(groups[groups != gi])
        for k in range(min(args.pairs, len(ic), len(ih))):
            recv_i, donor_i = ih[k], ic[k]          # receveur halluciné, on répare
            forced = gen_tokens[recv_i].tolist()
            if args.start > len(forced):
                continue
            base = run(model, ids, forced[:args.start], args.max_new_tokens)
            base_label = classify(tok.decode(base, skip_special_tokens=True), answers, prompt)
            if base_label == "Correct":
                continue                              # rien à réparer
            for l in args.layers:
                # direction transférée : moyenne des directions des AUTRES prompts
                dirs_other = []
                for gj in others:
                    jc = np.where((groups == gj) & (y == 0))[0]
                    jh = np.where((groups == gj) & (y == 1))[0]
                    if len(jc) and len(jh):
                        dirs_other.append(unit(direction(X, jc, jh, steps, l)))
                d_transfer = unit(np.mean(dirs_other, axis=0))
                d_self = unit(direction(X, ic, ih, steps, l))
                d_rand = unit(rng.normal(size=X.shape[-1]))

                for name, vec in (("oracle_paire", None), ("oracle_prompt", d_self),
                                  ("transfert", d_transfer), ("aleatoire", d_rand)):
                    patch = {}
                    for t in steps:
                        r = X[recv_i, t, l, :]
                        dist = float(np.linalg.norm(X[donor_i, t, l, :] - r))
                        v = X[donor_i, t, l, :] if vec is None else r + dist * vec
                        patch[t] = torch.tensor(np.asarray(v, dtype=np.float32), device=device)
                    got = run(model, ids, forced[:args.start], args.max_new_tokens,
                              patcher, l, patch)
                    lab = classify(tok.decode(got, skip_special_tokens=True), answers, prompt)
                    bump(name, lab == "Correct")
                    detail.append({"prompt": prompt, "layer": l, "condition": name,
                                   "result": lab})
    patcher.remove()

    def z_test(k1, n1, k2, n2):
        if not n1 or not n2:
            return float("nan")
        pp = (k1 + k2) / (n1 + n2)
        se = (pp * (1 - pp) * (1 / n1 + 1 / n2)) ** 0.5
        return ((k1 / n1) - (k2 / n2)) / se if se > 0 else float("nan")

    lines = []
    w = lines.append
    w("ÉTAPE 7 — STABILITÉ DE LA DIRECTION QUI RÉPARE")
    w(f"date   : {datetime.now().isoformat(timespec='seconds')}")
    w(f"modèle : {args.model} · fenêtre {args.window} depuis le step {args.start} "
      f"· couches {args.layers}")
    w("")
    w("A. GÉOMÉTRIE — similarité cosinus entre directions de prompts différents")
    w("")
    w(f"{'couche':<8}{'cross-prompt':>16}{'[min, max]':>18}{'plafond split-half':>21}"
      f"{'plancher |cos| 95%':>21}")
    w("-" * 84)
    for l in args.layers:
        g = geo[l]
        rng_txt = f"[{g['cross_min']:.2f}, {g['cross_max']:.2f}]"
        w(f"{l:<8}{g['cross_mean']:>10.3f} ±{g['cross_std']:<5.2f}{rng_txt:>18}"
          f"{g['splithalf']:>21.3f}{g['random_abs95']:>21.3f}")
    w("")
    w("B. FONCTION — taux de réparation, toutes conditions à NORME ÉGALE")
    w("")
    ko, no = tally.get("oracle_paire", [0, 0])
    kp, np_ = tally.get("oracle_prompt", [0, 0])
    kt, nt = tally.get("transfert", [0, 0])
    kr, nr = tally.get("aleatoire", [0, 0])
    for name, k, n in (("oracle-paire (étape 6)", ko, no), ("oracle-prompt (plafond)", kp, np_),
                       ("TRANSFERT (autres prompts)", kt, nt), ("aléatoire (plancher)", kr, nr)):
        w(f"  {name:<28}{k:>4}/{n:<5} = {k/max(n,1):>6.1%}")
    w("")
    w(f"  transfert vs aléatoire      z = {z_test(kt, nt, kr, nr):>6.2f}")
    w(f"  transfert vs oracle-prompt  z = {z_test(kt, nt, kp, np_):>6.2f}")
    w("")
    w("LECTURE. Si le transfert répare significativement plus que l'aléatoire, la")
    w("direction est partagée : un vecteur de steering calculé sur d'autres prompts")
    w("fonctionne sur un prompt jamais vu — G1-G2 devient opérationnalisable.")
    w("Si le transfert est au niveau de l'aléatoire alors que l'oracle-prompt")
    w("répare, la direction existe mais est PROPRE à chaque cas : observable,")
    w("inutilisable — il faudrait connaître la réponse pour construire le vecteur")
    w("qui y mène.")

    out = "\n".join(lines)
    print(out)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    (ROOT / "results" / f"repair_direction_{stamp}.txt").write_text(out + "\n")
    (ROOT / "results" / f"repair_direction_{stamp}.json").write_text(
        json.dumps({"geometry": geo, "tally": tally, "detail": detail}, indent=1,
                   ensure_ascii=False, default=float))
    print(f"\n-> results/repair_direction_{stamp}.txt")


if __name__ == "__main__":
    main()
