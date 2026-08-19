"""Étape 2 — Extraction des trajectoires sur prompts bifurquants.

Pour chaque prompt qui bifurque, on échantillonne jusqu'à obtenir K complétions
Correct et K Hallucination, en capturant le residual stream complet à chaque
(step, couche). Les deux classes viennent du MÊME prompt : aucun confond de
surface n'est possible.

Sortie : results/trajectories_<model>_<stamp>.npz
    X       [n_traj, n_steps, n_layers, hidden]  residual stream, dernier token
    y       [n_traj]        0 = Correct, 1 = Hallucination
    groups  [n_traj]        index du prompt (pour un CV leave-one-prompt-out)

Note sur le step 0 : l'état y est celui du dernier token du PROMPT, identique
pour toutes les complétions d'un même prompt. Il doit donner AUC = 0.5. C'est le
contrôle de sanité du protocole, pas un défaut.

Usage :
    .venv/bin/python src/extract_trajectories.py [--k 6] [--budget 200]
"""
import argparse
import json
import re
from datetime import datetime
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from bifurcation_probe import PROMPTS, classify

ROOT = Path(__file__).resolve().parent.parent
SEED = 42


def latest_bifurcation_json(model_tag):
    files = sorted((ROOT / "results").glob(f"bifurcation_{model_tag}_*.json"))
    if not files:
        raise SystemExit("Aucun résultat de bifurcation. Lancer bifurcation_probe.py d'abord.")
    return files[-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gpt2")
    ap.add_argument("--k", type=int, default=6, help="trajectoires par classe et par prompt")
    ap.add_argument("--budget", type=int, default=200, help="complétions max par prompt")
    ap.add_argument("--batch", type=int, default=40)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--max-new-tokens", type=int, default=8)
    ap.add_argument("--typed", action="store_true")
    args = ap.parse_args()

    global classify
    if args.typed:
        from typed_entities import classify_typed as classify
    tag = args.model.replace("/", "-") + ("_typed" if args.typed else "")
    bif = json.loads(latest_bifurcation_json(tag).read_text())
    targets = [r["prompt"] for r in bif if r["bifurcates"]]
    answers_of = {p: a for p, a in PROMPTS}
    print(f"{len(targets)} prompts bifurquants · K={args.k}/classe · budget={args.budget}\n")

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(args.model)
    tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(args.model).to(device).eval()

    X, y, groups, tokens, report = [], [], [], [], []

    for gi, prompt in enumerate(targets):
        answers = answers_of[prompt]
        enc = tok(prompt, return_tensors="pt").to(device)
        plen = enc["input_ids"].shape[1]
        kept = {"Correct": [], "Hallucination": []}
        drawn = 0
        torch.manual_seed(SEED + gi)

        while drawn < args.budget and min(len(kept["Correct"]), len(kept["Hallucination"])) < args.k:
            n = min(args.batch, args.budget - drawn)
            with torch.no_grad():
                out = model.generate(
                    **enc, do_sample=True, temperature=args.temperature,
                    max_new_tokens=args.max_new_tokens, num_return_sequences=n,
                    pad_token_id=tok.eos_token_id, top_k=0, top_p=1.0,
                    output_hidden_states=True, return_dict_in_generate=True,
                )
            drawn += n
            # hidden_states[step][layer] -> [batch, seq_len, hidden]
            # step 0 porte tout le prompt : on prend son dernier token.
            n_steps = len(out.hidden_states)
            n_layers = len(out.hidden_states[0])
            traj = np.empty((n, n_steps, n_layers, model.config.n_embd), dtype=np.float32)
            for s in range(n_steps):
                for l in range(n_layers):
                    h = out.hidden_states[s][l][:, -1, :]
                    traj[:, s, l, :] = h.float().cpu().numpy()

            for b in range(n):
                gen_ids = out.sequences[b][plen:].tolist()
                text = tok.decode(out.sequences[b][plen:], skip_special_tokens=True)
                label = classify(text, answers, prompt)
                if label in kept and len(kept[label]) < args.k:
                    # Les tokens générés sont conservés AVEC leur trajectoire.
                    # Sans cet appariement strict, un rejeu ultérieur (patching)
                    # associerait le texte d'un run aux activations d'un autre.
                    kept[label].append((traj[b].copy(), text, gen_ids))

        n_min = min(len(kept["Correct"]), len(kept["Hallucination"]))
        for label, code in (("Correct", 0), ("Hallucination", 1)):
            for arr, _, gen_ids in kept[label][:n_min]:
                X.append(arr); y.append(code); groups.append(gi)
                tokens.append(gen_ids)
        report.append({
            "prompt": prompt, "drawn": drawn, "kept_per_class": n_min,
            "correct_found": len(kept["Correct"]), "hallucination_found": len(kept["Hallucination"]),
            "examples": {k: [t for _, t, _ in v[:2]] for k, v in kept.items()},
        })
        print(f"  {prompt[:44]:<46} tirées={drawn:>4}  gardées={n_min}/classe"
              f"  (C={len(kept['Correct'])}, H={len(kept['Hallucination'])})")

    if not X:
        raise SystemExit("Aucune trajectoire retenue.")
    X = np.stack(X); y = np.array(y); groups = np.array(groups)
    tokens = np.array(tokens, dtype=np.int32)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    dest = ROOT / "results" / f"trajectories_{tag}_{stamp}.npz"
    np.savez_compressed(dest, X=X, y=y, groups=groups, tokens=tokens,
                        prompts=np.array(targets, dtype=object), allow_pickle=True)
    (ROOT / "results" / f"trajectories_{tag}_{stamp}_report.json").write_text(
        json.dumps(report, indent=1, ensure_ascii=False))

    usable = sorted({int(g) for g in groups})
    print(f"\nX = {X.shape}  (trajectoires, steps, couches, dim)")
    print(f"classes : {int((y==0).sum())} Correct / {int((y==1).sum())} Hallucination")
    print(f"prompts exploitables : {len(usable)}/{len(targets)}")
    print(f"-> {dest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
