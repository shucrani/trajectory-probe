"""Étape 5 — Window patching : l'intervention soutenue change-t-elle quelque chose ?

Le patch ponctuel (étape 4) n'a rien donné au-dessus du bruit : corruption 6.7 %
contre 6.5 % pour un patch aléatoire. Akarlar note que la CORRECTION exige une
intervention soutenue multi-étapes, là où la corruption suffit en un coup. Le test
ponctuel ne pouvait donc pas trancher.

Ici on patche une FENÊTRE de w steps consécutifs à partir du step 1 (le point de
divergence observé), à une couche donnée.

PIÈGE À NE PAS OUBLIER : plus w est grand, plus on impose la trajectoire du
donneur. À la limite, patcher tous les steps restants produit la sortie du donneur
par construction — un taux de « corruption » de 100 % qui ne dirait rien. C'est
pourquoi les contrôles portent la MÊME fenêtre : seul l'écart à w constant est
informatif.

POURQUOI LE SELF-PATCH NE SERT QUE POUR w = 1. Au step s0 le replay suit encore
la trajectoire d'origine, donc patcher avec sa propre activation est un no-op
exact et valide le mécanisme. Dès le step suivant, le replay (greedy) a produit un
token différent de l'original (échantillonné) : l'activation stockée provient d'un
contexte qui n'existe plus. Le self-patch ne PEUT PAS être un no-op au-delà de
w = 1. Ce n'est pas un bug, c'est la définition.

D'où le contrôle qui reste valide à toute fenêtre : SAME-CLASS PATCH, un donneur
tiré de la MÊME classe que le receveur. Il subit exactement le même décalage de
contexte que le patch cross-classe. La question devient donc :

    patcher avec un état de l'AUTRE classe fait-il basculer l'issue plus souvent
    que patcher avec un état de la MÊME classe ?

C'est cet écart-là qui teste l'existence d'un bassin, et lui seul.

Usage :
    .venv/bin/python src/window_patching.py [--windows 1 2 3 4] [--layers 4 8 11]
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

ROOT = Path(__file__).resolve().parent.parent
SEED = 42


@torch.no_grad()
def run(model, ids, forced, n_new, patcher=None, layer=None, vectors=None):
    """`vectors` : dict {step -> vecteur}. Le patch s'applique au forward qui
    produit le token de ce step."""
    seq = ids.clone()
    produced = []
    for t in range(n_new):
        if patcher is not None and vectors and t in vectors:
            patcher.arm(layer, vectors[t])
        out = model(seq)
        if patcher is not None:
            patcher.disarm()
        if t < len(forced):
            nxt = torch.tensor([[forced[t]]], device=seq.device)
        else:
            nxt = out.logits[:, -1, :].argmax(dim=-1, keepdim=True)
        produced.append(int(nxt.item()))
        seq = torch.cat([seq, nxt], dim=1)
    return produced


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gpt2")
    ap.add_argument("--start", type=int, default=1, help="premier step patché")
    ap.add_argument("--windows", type=int, nargs="+", default=[1, 2, 3, 4])
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

    # tally[(direction, w)] = [succès, total]
    tally, detail = {}, []
    def bump(key, hit):
        t = tally.setdefault(key, [0, 0])
        t[1] += 1; t[0] += int(hit)

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
                if s0 > len(forced):
                    continue
                base = run(model, ids, forced[:s0], args.max_new_tokens)
                base_label = classify(tok.decode(base, skip_special_tokens=True), answers, prompt)
                for w in args.windows:
                    steps = [t for t in range(s0, s0 + w) if t < X.shape[1]]
                    if len(steps) < w:
                        continue
                    # donneur de la MÊME classe que le receveur : même décalage de
                    # contexte, mais aucune information de l'autre bassin.
                    same_i = recv_ids[(k + 1) % len(recv_ids)]
                    if same_i == recv_i:
                        continue
                    for l in args.layers:
                        donor_v = {t: torch.tensor(X[donor_i, t, l, :], device=device) for t in steps}
                        recv_v = {t: torch.tensor(X[recv_i, t, l, :], device=device) for t in steps}
                        same_v = {t: torch.tensor(X[same_i, t, l, :], device=device) for t in steps}
                        noise_v = {}
                        for t in steps:
                            r = recv_v[t]
                            noise_v[t] = torch.tensor(
                                rng.normal(float(r.mean()), float(r.std()), size=r.shape),
                                dtype=torch.float32, device=device)

                        got = run(model, ids, forced[:s0], args.max_new_tokens, patcher, l, donor_v)
                        lab = classify(tok.decode(got, skip_special_tokens=True), answers, prompt)
                        bump((direction, w), lab == target and base_label != target)

                        same_out = run(model, ids, forced[:s0], args.max_new_tokens, patcher, l, same_v)
                        slab = classify(tok.decode(same_out, skip_special_tokens=True), answers, prompt)
                        bump((f"sameclass_{direction}", w), slab == target and base_label != target)

                        if w == 1:  # seule fenêtre où le no-op est défini
                            self_out = run(model, ids, forced[:s0], args.max_new_tokens,
                                           patcher, l, recv_v)
                            bump(("self", w), self_out != base)

                        rnd = run(model, ids, forced[:s0], args.max_new_tokens, patcher, l, noise_v)
                        rlab = classify(tok.decode(rnd, skip_special_tokens=True), answers, prompt)
                        bump((f"random_{direction}", w), rlab == target and base_label != target)

                        detail.append({"prompt": prompt, "direction": direction, "window": w,
                                       "layer": l, "base": base_label, "patched": lab,
                                       "sameclass": slab, "random": rlab})
    patcher.remove()

    def rate(key):
        n, tot = tally.get(key, [0, 0])
        return (n / tot if tot else float("nan")), n, tot

    def z_test(k1, n1, k2, n2):
        if not n1 or not n2:
            return float("nan")
        p1, p2 = k1 / n1, k2 / n2
        pp = (k1 + k2) / (n1 + n2)
        se = (pp * (1 - pp) * (1 / n1 + 1 / n2)) ** 0.5
        return (p1 - p2) / se if se > 0 else float("nan")

    lines = []
    w_ = lines.append
    w_("ÉTAPE 5 — WINDOW PATCHING")
    w_(f"date     : {datetime.now().isoformat(timespec='seconds')}")
    w_(f"modèle   : {args.model} · start=step {args.start} · fenêtres {args.windows} "
       f"· couches {args.layers}")
    w_(f"source   : {npz.name}")
    w_("")
    r, n, tot = rate(("self", 1))
    w_(f"CONTRÔLE self-patch (fenêtre 1 uniquement) : {n}/{tot} = {r:.1%} "
       f"{'OK — mécanisme validé' if n == 0 else '<-- ÉCHEC'}")
    w_("  au-delà de w=1 le no-op n'est pas défini (contexte divergent) : voir docstring")
    w_("")
    w_("Comparaison décisive : patch CROSS-classe vs patch SAME-classe, à fenêtre égale.")
    w_("")
    w_(f"{'fen.':<5}{'corruption':>11}{'same-cl.':>10}{'aléat.':>9}{'z(x/same)':>11}   "
       f"{'correction':>11}{'same-cl.':>10}{'aléat.':>9}{'z(x/same)':>11}")
    w_("-" * 98)
    for w in args.windows:
        rc, kc, nc = rate(("corruption", w))
        rsc, ksc, nsc = rate(("sameclass_corruption", w))
        rrc, _, _ = rate(("random_corruption", w))
        rr, kr, nr = rate(("correction", w))
        rsr, ksr, nsr = rate(("sameclass_correction", w))
        rrr, _, _ = rate(("random_correction", w))
        zc = z_test(kc, nc, ksc, nsc)
        zr = z_test(kr, nr, ksr, nsr)
        w_(f"{w:<5}{rc:>10.1%}{rsc:>10.1%}{rrc:>9.1%}{zc:>11.2f}   "
           f"{rr:>10.1%}{rsr:>10.1%}{rrr:>9.1%}{zr:>11.2f}")
    w_("")
    w_("LECTURE. Le taux brut monte mécaniquement avec la fenêtre : on impose de plus")
    w_("en plus la trajectoire du donneur. Seul compte l'écart CROSS vs SAME à fenêtre")
    w_("égale — les deux subissent le même décalage de contexte, seul le contenu de")
    w_("l'état diffère. |z| > 1.96 = écart significatif à 5 %.")
    w_("")
    w_("Référence Akarlar (Qwen2.5-1.5B) : corruption en un seul coup ; correction")
    w_("nécessitant une intervention soutenue. Si l'asymétrie existe ici, la")
    w_("correction doit progresser avec la fenêtre plus vite que la corruption.")

    out = "\n".join(lines)
    print(out)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    (ROOT / "results" / f"window_patching_{stamp}.txt").write_text(out + "\n")
    (ROOT / "results" / f"window_patching_{stamp}.json").write_text(
        json.dumps(detail, indent=1, ensure_ascii=False))
    print(f"\n-> results/window_patching_{stamp}.txt")


if __name__ == "__main__":
    main()
