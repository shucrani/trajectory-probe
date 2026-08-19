"""Étape 10 — Quelle fraction de l'hallucination est réductible, et par quoi ?

L'objectif du projet est de réduire les hallucinations, pas de les décrire. Les
étapes 1-9 ont établi un fait qui commande la stratégie :

    le bruit répare (6.4 %) et ne corrompt presque pas (0.8 %)
    -> l'attracteur est du côté correct, pas du côté hallucinatoire

Si la bonne réponse est le mode de la distribution, alors une part de
l'hallucination est purement STOCHASTIQUE : le même prompt produit tantôt le
vrai, tantôt le faux, et l'agrégation la supprime sans aucune information
externe. Le reste est SYSTÉMATIQUE : le modèle se trompe à chaque tirage, aucune
agrégation n'y peut rien — il faut de la connaissance.

Ce script mesure la partition, qui borne toute méthode de réduction :

    TOUJOURS-CORRECT   aucun tirage halluciné            rien à réduire
    BIFURQUANT         les deux issues apparaissent      réductible par agrégation
    TOUJOURS-FAUX      aucun tirage correct              non réductible sans savoir
    MUET               aucune assertion (NoAnswer)       hors périmètre

puis compare trois stratégies qui ne demandent AUCUNE information externe :

    tirage unique T=0.7    la baseline, ce que fait un modèle en usage normal
    greedy T→0             prendre le mode du décodage
    vote majoritaire       N tirages, on garde l'entité la plus fréquente

Usage :
    .venv/bin/python src/reduction_bound.py [--n 20]
"""
import argparse
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from bifurcation_probe import PROMPTS
from typed_entities import DISTRACTORS, classify_typed, _matches

ROOT = Path(__file__).resolve().parent.parent
SEED = 42


def extract_entity(text, answers, prompt):
    """Renvoie l'entité assertée : 'CORRECT' si une réponse attendue apparaît,
    sinon le distracteur nommé, sinon None (aucune assertion)."""
    low = text.strip().lower()
    if any(_matches(low, a) for a in answers):
        return "CORRECT"
    for dist in DISTRACTORS.get(prompt, []):
        if _matches(low, dist):
            return dist
    return None


@torch.no_grad()
def sample(model, tok, prompt, n, temperature, device, max_new_tokens=8):
    enc = tok(prompt, return_tensors="pt").to(device)
    plen = enc["input_ids"].shape[1]
    if temperature == 0:
        out = model.generate(**enc, do_sample=False, max_new_tokens=max_new_tokens,
                             pad_token_id=tok.eos_token_id)
    else:
        out = model.generate(**enc, do_sample=True, temperature=temperature,
                             max_new_tokens=max_new_tokens, num_return_sequences=n,
                             pad_token_id=tok.eos_token_id, top_k=0, top_p=1.0)
    return [tok.decode(o[plen:], skip_special_tokens=True) for o in out]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gpt2")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--low-temperature", type=float, default=0.3)
    ap.add_argument("--dtype", default="float32",
                    help="float16 pour les modèles >1B sur MPS")
    args = ap.parse_args()

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(args.model)
    tok.pad_token = tok.eos_token
    dt = getattr(torch, args.dtype)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, torch_dtype=dt).to(device).eval()

    cats = Counter()
    rows = []
    # compteurs de stratégie, sur les prompts où le modèle asserte quelque chose
    strat = {k: [0, 0] for k in ("tirage_unique", "greedy", "vote", "basse_temp")}

    for gi, (prompt, answers) in enumerate(PROMPTS):
        torch.manual_seed(SEED + gi)
        comps = sample(model, tok, prompt, args.n, args.temperature, device)
        ents = [extract_entity(c, answers, prompt) for c in comps]
        asserted = [e for e in ents if e is not None]
        n_correct = sum(1 for e in asserted if e == "CORRECT")
        n_wrong = len(asserted) - n_correct

        if not asserted:
            cat = "MUET"
        elif n_wrong == 0:
            cat = "TOUJOURS-CORRECT"
        elif n_correct == 0:
            cat = "TOUJOURS-FAUX"
        else:
            cat = "BIFURQUANT"
        cats[cat] += 1

        # Toutes les stratégies sont évaluées PAR PROMPT, sur le même
        # ensemble. Agréger par tirage pondérerait les prompts par leur
        # nombre d'assertions et ferait passer les prompts faciles devant.
        rec = {"p_unique": None, "vote": None, "greedy": None, "p_low": None,
               "entities": dict(Counter(asserted))}
        if asserted:
            rec["p_unique"] = n_correct / len(asserted)
            top = Counter(asserted).most_common(1)[0][0]
            rec["vote"] = int(top == "CORRECT")
            g = extract_entity(sample(model, tok, prompt, 1, 0, device)[0], answers, prompt)
            rec["greedy"] = None if g is None else int(g == "CORRECT")
            torch.manual_seed(SEED + gi)
            lows = [extract_entity(c, answers, prompt)
                    for c in sample(model, tok, prompt, args.n, args.low_temperature, device)]
            lows = [e for e in lows if e is not None]
            rec["p_low"] = (sum(1 for e in lows if e == "CORRECT") / len(lows)) if lows else None

        rows.append({"prompt": prompt, "categorie": cat, "correct": n_correct,
                     "faux": n_wrong, "muet": args.n - len(asserted), **rec})

    lines = []
    w = lines.append
    w("ÉTAPE 10 — BORNE DE RÉDUCTIBILITÉ")
    w(f"date    : {datetime.now().isoformat(timespec='seconds')}")
    w(f"modèle  : {args.model} · {len(PROMPTS)} prompts · N={args.n} tirages à T={args.temperature}")
    w("")
    w("A. PARTITION DES PROMPTS")
    w("")
    total = sum(cats.values())
    for cat in ("TOUJOURS-CORRECT", "BIFURQUANT", "TOUJOURS-FAUX", "MUET"):
        w(f"   {cat:<20}{cats[cat]:>4} / {total}  = {cats[cat]/total:>6.1%}")
    w("")
    assertive = total - cats["MUET"]
    if assertive:
        w(f"   Sur les {assertive} prompts où le modèle asserte quelque chose :")
        w(f"     réductible par agrégation (bifurquants) : "
          f"{cats['BIFURQUANT']/assertive:>6.1%}")
        w(f"     irréductible sans connaissance (toujours-faux) : "
          f"{cats['TOUJOURS-FAUX']/assertive:>6.1%}")
    w("")
    w("B. STRATÉGIES SANS INFORMATION EXTERNE")
    w("")
    w("   Comparaison PAR PROMPT, sur l'ensemble commun où les quatre stratégies")
    w("   assertent quelque chose. Agréger par tirage biaiserait vers les prompts")
    w("   faciles, qui assertent plus souvent.")
    w("")
    common = [r for r in rows if r["p_unique"] is not None and r["greedy"] is not None
              and r["p_low"] is not None]
    n_c = len(common)
    if n_c:
        m_uni = sum(r["p_unique"] for r in common) / n_c
        m_low = sum(r["p_low"] for r in common) / n_c
        m_gre = sum(r["greedy"] for r in common) / n_c
        m_vot = sum(r["vote"] for r in common) / n_c
        w(f"   ensemble commun : {n_c} prompts")
        w("")
        for label, val in ((f"tirage unique T={args.temperature} (baseline)", m_uni),
                           (f"tirage unique T={args.low_temperature}", m_low),
                           ("greedy (T->0)", m_gre),
                           (f"vote majoritaire sur {args.n} tirages", m_vot)):
            delta = val - m_uni
            w(f"   {label:<40}{val:>7.1%}"
              + ("" if abs(delta) < 1e-12 else f"   ({delta:+.1%})"))
        w("")
        if m_uni < 1:
            w(f"   Réduction relative du taux d'erreur :")
            for label, val in ((f"T={args.low_temperature}", m_low), ("greedy", m_gre),
                               ("vote", m_vot)):
                w(f"      {label:<12}{(( 1-m_uni) - (1-val))/(1-m_uni):>7.1%}")
    w("")
    w("LECTURE. La catégorie TOUJOURS-FAUX borne toute méthode qui n'apporte pas")
    w("de connaissance : aucune agrégation, aucun décodage, aucune perturbation ne")
    w("la corrige — le modèle est confiant et faux. Seule la part BIFURQUANTE est")
    w("accessible sans information externe. C'est le plafond réel de tout ce que")
    w("ce projet peut viser côté intervention pure.")

    out = "\n".join(lines)
    print(out)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    tag = args.model.split("/")[-1]
    (ROOT / "results" / f"reduction_bound_{tag}_{stamp}.txt").write_text(out + "\n")
    (ROOT / "results" / f"reduction_bound_{tag}_{stamp}.json").write_text(
        json.dumps({"categories": dict(cats), "strategies": strat, "rows": rows},
                   indent=1, ensure_ascii=False))
    print(f"\n-> results/reduction_bound_{tag}_{stamp}.txt")


if __name__ == "__main__":
    main()
