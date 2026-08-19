"""Étape 6 — Le patch cross-classe transporte-t-il de l'INFORMATION, ou juste de
l'AMPLITUDE ?

L'étape 5 a montré un effet : à fenêtre ≥ 2, patcher avec un état de l'autre
classe fait basculer l'issue plus souvent qu'avec un état de la même classe
(z jusqu'à 2.96). Mais les distances L2 au receveur suivent exactement le même
ordre que les taux de bascule :

    same-classe 54.6  <  cross-classe 83.0  <  aléatoire 149.6      (couche 8)
    6.7 %             <  16.7 %             <  21.7 %               (w = 3)

Autrement dit, plus on s'éloigne de l'état d'origine, plus l'issue bascule — et
un bruit sans aucun contenu sémantique fait MIEUX que l'état de l'autre classe.

Ce script tranche : on remplace l'état du receveur par un bruit dirigé dans une
direction aléatoire mais placé EXACTEMENT à la même distance que le donneur
cross-classe. Même amplitude, aucune information de l'autre bassin.

    si les taux s'égalisent -> l'effet de l'étape 5 est un artefact d'amplitude,
                               il n'y a pas de transport d'information.
    si le cross reste au-dessus -> le contenu de l'état compte vraiment.

Usage :
    .venv/bin/python src/normmatched_patching.py [--window 3]
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from bifurcation_probe import PROMPTS, classify
from causal_patching import Patcher
from window_patching import run

ROOT = Path(__file__).resolve().parent.parent
SEED = 42


def norm_matched(recv, target, rng):
    """Vecteur à la même distance de `recv` que `target`, direction aléatoire."""
    dist = float(np.linalg.norm(target - recv))
    d = rng.normal(0, 1, size=recv.shape)
    d /= np.linalg.norm(d)
    return recv + d * dist


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

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(args.model)
    tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(args.model).to(device).eval()
    patcher = Patcher(model)
    rng = np.random.RandomState(SEED)

    tally, detail = {}, []
    def bump(key, hit):
        t = tally.setdefault(key, [0, 0]); t[1] += 1; t[0] += int(hit)

    for gi, prompt in enumerate(prompts):
        answers = answers_of[prompt]
        ids = tok(prompt, return_tensors="pt").to(device)["input_ids"]
        idx_c = np.where((groups == gi) & (y == 0))[0]
        idx_h = np.where((groups == gi) & (y == 1))[0]
        if len(idx_c) == 0 or len(idx_h) == 0:
            continue
        for direction, recv_ids, donor_ids, target in (
            ("corruption", idx_c, idx_h, "Hallucination"),
            ("correction", idx_h, idx_c, "Correct"),
        ):
            for k in range(min(args.pairs, len(recv_ids), len(donor_ids))):
                recv_i, donor_i = recv_ids[k], donor_ids[k]
                forced = gen_tokens[recv_i].tolist()
                s0 = args.start
                steps = [t for t in range(s0, s0 + args.window) if t < X.shape[1]]
                if len(steps) < args.window or s0 > len(forced):
                    continue
                base = run(model, ids, forced[:s0], args.max_new_tokens)
                base_label = classify(tok.decode(base, skip_special_tokens=True), answers, prompt)
                for l in args.layers:
                    cross_v, match_v = {}, {}
                    for t in steps:
                        r = X[recv_i, t, l, :]
                        c = X[donor_i, t, l, :]
                        cross_v[t] = torch.tensor(c, device=device)
                        match_v[t] = torch.tensor(norm_matched(r, c, rng),
                                                  dtype=torch.float32, device=device)

                    got = run(model, ids, forced[:s0], args.max_new_tokens, patcher, l, cross_v)
                    lab = classify(tok.decode(got, skip_special_tokens=True), answers, prompt)
                    bump((direction, "cross"), lab == target and base_label != target)

                    mm = run(model, ids, forced[:s0], args.max_new_tokens, patcher, l, match_v)
                    mlab = classify(tok.decode(mm, skip_special_tokens=True), answers, prompt)
                    bump((direction, "matched"), mlab == target and base_label != target)

                    detail.append({"prompt": prompt, "direction": direction, "layer": l,
                                   "base": base_label, "cross": lab, "matched": mlab})
    patcher.remove()

    def z_test(k1, n1, k2, n2):
        if not n1 or not n2:
            return float("nan")
        pp = (k1 + k2) / (n1 + n2)
        se = (pp * (1 - pp) * (1 / n1 + 1 / n2)) ** 0.5
        return ((k1 / n1) - (k2 / n2)) / se if se > 0 else float("nan")

    lines = []
    w_ = lines.append
    w_("ÉTAPE 6 — PATCH APPARIÉ EN NORME (information vs amplitude)")
    w_(f"date    : {datetime.now().isoformat(timespec='seconds')}")
    w_(f"modèle  : {args.model} · fenêtre {args.window} depuis le step {args.start} "
       f"· couches {args.layers}")
    w_("")
    w_("Le patch apparié est placé à la MÊME distance L2 de l'état du receveur que")
    w_("l'état donneur, mais dans une direction aléatoire : même amplitude, zéro")
    w_("information de l'autre classe.")
    w_("")
    w_(f"{'direction':<14}{'cross-classe':>14}{'apparié en norme':>19}{'z':>8}")
    w_("-" * 56)
    for direction in ("corruption", "correction"):
        kc, nc = tally.get((direction, "cross"), [0, 0])
        km, nm = tally.get((direction, "matched"), [0, 0])
        z = z_test(kc, nc, km, nm)
        w_(f"{direction:<14}{kc/max(nc,1):>13.1%}{km/max(nm,1):>18.1%}{z:>8.2f}"
           f"   (n={nc})")
    w_("")
    w_("LECTURE. |z| > 1.96 : le contenu de l'état compte au-delà de son amplitude.")
    w_("|z| proche de 0 : l'effet observé à l'étape 5 est un artefact d'amplitude —")
    w_("déplacer l'état assez loin suffit à faire basculer l'issue, peu importe vers")
    w_("où. Dans ce cas il n'y a pas de transport d'information entre bassins, et")
    w_("l'asymétrie corruption/correction d'Akarlar n'est pas reproduite ici.")

    out = "\n".join(lines)
    print(out)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    (ROOT / "results" / f"normmatched_{stamp}.txt").write_text(out + "\n")
    (ROOT / "results" / f"normmatched_{stamp}.json").write_text(
        json.dumps(detail, indent=1, ensure_ascii=False))
    print(f"\n-> results/normmatched_{stamp}.txt")


if __name__ == "__main__":
    main()
