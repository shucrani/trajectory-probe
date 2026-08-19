"""Étape 4 — Test causal : l'engagement est-il irréversible ? (D2)

Une carte de séparabilité ne peut pas trancher l'irréversibilité : elle mesure
que les états diffèrent, pas qu'on ne peut plus revenir. Le test causal, lui,
intervient.

Protocole (d'après Akarlar, arXiv 2604.15400) : sur un même prompt, on prend un
run receveur et un run donneur de l'autre classe. On rejoue le receveur en
forçant ses s premiers tokens, on REMPLACE son activation à la couche l par celle
du donneur au même (step, couche), puis on laisse continuer en greedy. On regarde
si l'issue bascule.

    corruption  : Correct  <- activation Hallucination.  L'issue devient-elle fausse ?
    correction  : Hallucination <- activation Correct.   L'issue se répare-t-elle ?

L'asymétrie entre les deux est la signature d'un bassin absorbant : facile d'y
tomber, difficile d'en sortir.

Deux contrôles, sans lesquels les taux ne veulent rien dire :
    self-patch   : patcher avec SA PROPRE activation. Doit être un no-op exact.
                   S'il ne l'est pas, le mécanisme de patch est buggé.
    random-patch : patcher avec un bruit gaussien de même moyenne et variance.
                   Donne le taux de bascule dû à la seule perturbation.

Usage :
    .venv/bin/python src/causal_patching.py [--steps 1 2 3] [--layers 4 8 12]
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from bifurcation_probe import PROMPTS, classify

ROOT = Path(__file__).resolve().parent.parent
SEED = 42


class Patcher:
    """Remplace la sortie d'un bloc au dernier token, uniquement au step visé."""

    def __init__(self, model):
        self.model = model
        self.vector = None
        self.layer = None
        self.armed = False
        self.handles = []
        blocks = model.transformer.h
        for idx, block in enumerate(blocks):
            self.handles.append(block.register_forward_hook(self._make_hook(idx + 1)))

    def _make_hook(self, layer_id):
        def hook(_module, _inp, out):
            if not self.armed or self.layer != layer_id:
                return out
            hidden = out[0] if isinstance(out, tuple) else out
            hidden = hidden.clone()
            hidden[:, -1, :] = self.vector.to(hidden.dtype).to(hidden.device)
            return (hidden,) + tuple(out[1:]) if isinstance(out, tuple) else hidden
        return hook

    def arm(self, layer, vector):
        self.layer, self.vector, self.armed = layer, vector, True

    def disarm(self):
        self.armed = False

    def remove(self):
        for h in self.handles:
            h.remove()


@torch.no_grad()
def run(model, ids, forced, n_new, patcher=None, patch_step=None, patch=None):
    """Rejoue `forced` en teacher forcing puis continue en greedy.

    Le patch s'applique au forward qui PRODUIT le token d'indice `patch_step`.
    """
    seq = ids.clone()
    produced = []
    for t in range(n_new):
        if patcher is not None and patch is not None and t == patch_step:
            patcher.arm(patch[0], patch[1])
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
    ap.add_argument("--steps", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("--layers", type=int, nargs="+", default=[4, 8, 11])
    ap.add_argument("--pairs", type=int, default=6, help="paires par prompt")
    ap.add_argument("--max-new-tokens", type=int, default=8)
    args = ap.parse_args()

    tag = args.model.replace("/", "-")
    
    npz = sorted((ROOT / "results").glob(f"trajectories_{tag}_*.npz"))[-1]
    d = np.load(npz, allow_pickle=True)
    X, y, groups = d["X"], d["y"], d["groups"]
    prompts = list(d["prompts"])
    answers_of = {p: a for p, a in PROMPTS}

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(args.model)
    tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(args.model).to(device).eval()
    patcher = Patcher(model)
    rng = np.random.RandomState(SEED)

    # Les tokens générés sont appariés à leur trajectoire dans le npz : la
    # trajectoire i et les tokens i viennent du MÊME run. C'est la condition
    # pour que le self-patch puisse être un no-op.
    gen_tokens = d["tokens"]

    tally = {k: [0, 0] for k in ("corruption", "correction", "self", "random")}
    detail = []

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
                for s in args.steps:
                    if s > len(forced):
                        continue
                    base = run(model, ids, forced[:s], args.max_new_tokens)
                    base_label = classify(tok.decode(base, skip_special_tokens=True), answers, prompt)
                    for l in args.layers:
                        donor_vec = torch.tensor(X[donor_i, s, l, :], device=device)
                        recv_vec = torch.tensor(X[recv_i, s, l, :], device=device)

                        got = run(model, ids, forced[:s], args.max_new_tokens,
                                  patcher, s, (l, donor_vec))
                        lab = classify(tok.decode(got, skip_special_tokens=True), answers, prompt)
                        tally[direction][1] += 1
                        tally[direction][0] += int(lab == target and base_label != target)

                        self_out = run(model, ids, forced[:s], args.max_new_tokens,
                                       patcher, s, (l, recv_vec))
                        tally["self"][1] += 1
                        tally["self"][0] += int(self_out != base)

                        noise = torch.tensor(
                            rng.normal(float(recv_vec.mean()), float(recv_vec.std()), size=recv_vec.shape),
                            dtype=torch.float32, device=device)
                        rnd = run(model, ids, forced[:s], args.max_new_tokens,
                                  patcher, s, (l, noise))
                        rlab = classify(tok.decode(rnd, skip_special_tokens=True), answers, prompt)
                        tally["random"][1] += 1
                        tally["random"][0] += int(rlab == target and base_label != target)

                        detail.append({"prompt": prompt, "direction": direction, "step": s,
                                       "layer": l, "base": base_label, "patched": lab})
    patcher.remove()

    lines = []
    w = lines.append
    w("ÉTAPE 4 — TEST CAUSAL (activation patching)")
    w(f"date     : {datetime.now().isoformat(timespec='seconds')}")
    w(f"modèle   : {args.model} · steps {args.steps} · couches {args.layers}")
    w(f"greedy après patch (le hasard de sampling est retiré de la mesure)")
    w("")
    self_rate = tally["self"][0] / max(tally["self"][1], 1)
    w(f"CONTRÔLE self-patch : {tally['self'][0]}/{tally['self'][1]} générations modifiées "
      f"= {self_rate:.1%}")
    w(f"   attendu 0.0% — patcher avec sa propre activation doit être un no-op. "
      f"{'OK' if self_rate == 0 else 'ÉCHEC — mécanisme de patch suspect'}")
    w("")
    for k, label in (("corruption", "Correct <- Hallucination"),
                     ("correction", "Hallucination <- Correct"),
                     ("random", "patch aléatoire (contrôle)")):
        n, tot = tally[k]
        w(f"{k:<12} {label:<32} {n:>4}/{tot:<4} = {n/max(tot,1):>6.1%}")
    w("")
    w("Référence Akarlar (Qwen2.5-1.5B, 28 couches) : corruption 87.5%, "
      "correction 33.3%, random 12.5%.")
    w("")
    if tally["corruption"][1] and tally["correction"][1]:
        c = tally["corruption"][0] / tally["corruption"][1]
        r = tally["correction"][0] / tally["correction"][1]
        w(f"Asymétrie mesurée : corruption {c:.1%} vs correction {r:.1%}"
          f"  (ratio {c/r:.2f}x)" if r > 0 else
          f"Asymétrie mesurée : corruption {c:.1%} vs correction 0.0%")

    out = "\n".join(lines)
    print(out)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    (ROOT / "results" / f"causal_patching_{stamp}.txt").write_text(out + "\n")
    (ROOT / "results" / f"causal_patching_{stamp}.json").write_text(
        json.dumps(detail, indent=1, ensure_ascii=False))
    print(f"\n-> results/causal_patching_{stamp}.txt")


if __name__ == "__main__":
    main()
