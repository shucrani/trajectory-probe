"""Étape 11 — Domaine vérifiable : que devient la partition quand on peut CHECKER ?

Les étapes 1-10 portent sur des faits empiriques : rien ne les vérifie de
l'intérieur, on ne peut que graduer la confiance et s'abstenir. Ici, chaque
question est construite pour que la RÉPONSE PROPOSÉE soit vérifiable sans
connaître la solution.

    « If 3x + 5 = 20, then x = »   -> on substitue le candidat et on regarde
    « A divisor of 91 other than 1 and 91 is »  -> on teste la divisibilité

C'est la condition qui rend le pattern generate-and-check non circulaire :
vérifier ne présuppose pas la bonne réponse. Recalculer « 17 + 25 » serait
circulaire, ces items sont donc exclus.

Ce que le script mesure, à comparer au domaine empirique :

    A. la partition (toujours-correct / bifurquant / toujours-faux / muet)
    B. les stratégies sans information externe (mode, vote)
    C. LA POLITIQUE VÉRIFIÉE : on ne répond que si un tirage passe le check.
       Précision 100 % par construction. La question devient la COUVERTURE.

Usage :
    .venv/bin/python src/verifiable_bound.py --model Qwen/Qwen2.5-1.5B-Instruct --dtype float16
"""
import argparse
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parent.parent
SEED = 42
NUM = re.compile(r"-?\d+")


def build_corpus():
    """Items (prompt, verify, canonique). `verify` ne connaît pas la solution :
    il teste la propriété que la réponse doit satisfaire."""
    items = []

    # 1. Équations linéaires — vérification par substitution
    for a, b, c in [(3, 5, 20), (2, 7, 19), (4, 3, 23), (5, 2, 27), (6, 4, 22),
                    (3, 8, 29), (7, 1, 36), (2, 11, 31), (8, 5, 45), (4, 9, 37),
                    (9, 2, 38), (5, 6, 41), (3, 12, 33), (6, 7, 43), (2, 15, 35)]:
        items.append((
            f"If {a}x + {b} = {c}, then x = ",
            (lambda a=a, b=b, c=c: (lambda x: a * x + b == c))(),
            (c - b) // a,
        ))

    # 2. Racines carrées — vérification par élévation au carré
    for n in [144, 169, 196, 225, 256, 289, 324, 361, 400, 441, 484, 529]:
        items.append((
            f"The square root of {n} is ",
            (lambda n=n: (lambda x: x * x == n))(),
            int(n ** 0.5),
        ))

    # 3. Diviseurs non triviaux — vérification par modulo. Plusieurs réponses
    #    valides : c'est `verify` qui définit la correction, pas une chaîne.
    for n in [91, 143, 187, 209, 221, 247, 253, 299, 319, 341, 377, 391]:
        items.append((
            f"A whole number that divides {n} exactly, other than 1 and {n}, is ",
            (lambda n=n: (lambda x: x not in (1, n, -1, -n) and x != 0 and n % x == 0))(),
            next(d for d in range(2, n) if n % d == 0),
        ))

    # 4. Complément à une somme — vérification par addition
    for a, s in [(12, 30), (17, 40), (23, 50), (8, 25), (34, 60), (19, 45),
                 (27, 55), (14, 33), (21, 48), (36, 70), (13, 29), (25, 61)]:
        items.append((
            f"If {a} plus a number equals {s}, that number is ",
            (lambda a=a, s=s: (lambda x: a + x == s))(),
            s - a,
        ))

    # 5. Facteur manquant — vérification par multiplication
    for a, p in [(7, 91), (11, 143), (13, 169), (6, 84), (9, 117), (8, 96),
                 (12, 156), (14, 182), (15, 195), (17, 221), (4, 76), (16, 208)]:
        items.append((
            f"If {a} times a number equals {p}, that number is ",
            (lambda a=a, p=p: (lambda x: a * x == p))(),
            p // a,
        ))

    return items


def extract_number(text):
    m = NUM.search(text.strip())
    return int(m.group()) if m else None


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
    ap.add_argument("--model", default="Qwen/Qwen2.5-1.5B-Instruct")
    ap.add_argument("--dtype", default="float16")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--temperature", type=float, default=0.7)
    args = ap.parse_args()

    corpus = build_corpus()
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(args.model)
    tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.model, dtype=getattr(torch, args.dtype)).to(device).eval()

    cats = Counter()
    rows = []
    for gi, (prompt, verify, canon) in enumerate(corpus):
        torch.manual_seed(SEED + gi)
        comps = sample(model, tok, prompt, args.n, args.temperature, device)
        nums = [extract_number(c) for c in comps]
        asserted = [x for x in nums if x is not None]
        oks = [verify(x) for x in asserted]
        n_ok, n_bad = sum(oks), len(oks) - sum(oks)

        if not asserted:
            cat = "MUET"
        elif n_bad == 0:
            cat = "TOUJOURS-CORRECT"
        elif n_ok == 0:
            cat = "TOUJOURS-FAUX"
        else:
            cat = "BIFURQUANT"
        cats[cat] += 1

        rec = {"prompt": prompt, "canonique": canon, "categorie": cat,
               "n_ok": n_ok, "n_bad": n_bad, "muet": args.n - len(asserted)}
        if asserted:
            rec["p_unique"] = n_ok / len(asserted)
            top = Counter(asserted).most_common(1)[0][0]
            rec["vote_ok"] = bool(verify(top))
            g = extract_number(sample(model, tok, prompt, 1, 0, device)[0])
            rec["greedy_ok"] = None if g is None else bool(verify(g))
            # politique vérifiée : on répond si AU MOINS UN tirage passe le check
            rec["verified_cover"] = n_ok > 0
            # politique vote+vérification : on répond si le vote passe le check
            rec["vote_then_verify"] = bool(rec["vote_ok"])
        rows.append(rec)

    lines = []
    w = lines.append
    w("ÉTAPE 11 — DOMAINE VÉRIFIABLE")
    w(f"date    : {datetime.now().isoformat(timespec='seconds')}")
    w(f"modèle  : {args.model} · {len(corpus)} items · N={args.n} à T={args.temperature}")
    w("")
    w("Vérification non circulaire : on teste la propriété que la réponse doit")
    w("satisfaire, sans connaître la solution (substitution, modulo, produit).")
    w("")
    w("A. PARTITION")
    w("")
    tot = sum(cats.values())
    for c in ("TOUJOURS-CORRECT", "BIFURQUANT", "TOUJOURS-FAUX", "MUET"):
        w(f"   {c:<20}{cats[c]:>4} / {tot} = {cats[c]/tot:>6.1%}")
    err = cats["BIFURQUANT"] + cats["TOUJOURS-FAUX"]
    if err:
        w("")
        w(f"   Sur les {err} items où le modèle se trompe au moins une fois :")
        w(f"     stochastique  : {cats['BIFURQUANT']/err:>6.1%}")
        w(f"     systématique  : {cats['TOUJOURS-FAUX']/err:>6.1%}")
    w("")

    ass = [r for r in rows if "p_unique" in r]
    common = [r for r in ass if r.get("greedy_ok") is not None]
    w("B. STRATÉGIES SANS VÉRIFICATION")
    w("")
    if common:
        n_c = len(common)
        m_uni = sum(r["p_unique"] for r in common) / n_c
        m_gre = sum(r["greedy_ok"] for r in common) / n_c
        m_vot = sum(r["vote_ok"] for r in common) / n_c
        w(f"   ensemble commun : {n_c} items")
        w(f"   tirage unique T={args.temperature:<28}{m_uni:>7.1%}")
        w(f"   greedy (T->0){'':<27}{m_gre:>7.1%}")
        w(f"   vote majoritaire sur {args.n}{'':<19}{m_vot:>7.1%}")
    w("")
    w("C. POLITIQUE VÉRIFIÉE — précision 100 % par construction")
    w("")
    if ass:
        cover_any = sum(r["verified_cover"] for r in ass) / len(rows)
        cover_vote = sum(r["vote_then_verify"] for r in ass) / len(rows)
        w(f"   « je réponds si un tirage passe le check »")
        w(f"       couverture {cover_any:>6.1%}   précision 100.0%   "
          f"(abstention {1-cover_any:>5.1%})")
        w(f"   « je réponds si le VOTE passe le check »")
        w(f"       couverture {cover_vote:>6.1%}   précision 100.0%   "
          f"(abstention {1-cover_vote:>5.1%})")
    w("")
    w("D. COMPARAISON DES DEUX RÉGIMES")
    w("")
    w("   domaine empirique (étape 10, seuil d'accord 0.70) :")
    w("       couverture  57.6%   précision  70.6%   -> gradué, jamais garanti")
    if ass:
        w("   domaine vérifiable (ici) :")
        w(f"       couverture {cover_any:>6.1%}   précision 100.0%   -> garanti, partiel")
    w("")
    w("LECTURE. Dans le domaine vérifiable, l'erreur ne se gradue plus : elle est")
    w("éliminée sur ce qui est accepté. Tout le problème se déplace vers la")
    w("couverture — combien de questions le système accepte de traiter. C'est le")
    w("seul endroit où le mot « certifier » est légitime.")

    out = "\n".join(lines)
    print(out)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    tag = args.model.split("/")[-1]
    (ROOT / "results" / f"verifiable_{tag}_{stamp}.txt").write_text(out + "\n")
    (ROOT / "results" / f"verifiable_{tag}_{stamp}.json").write_text(
        json.dumps({"categories": dict(cats), "rows": rows}, indent=1, ensure_ascii=False))
    print(f"\n-> results/verifiable_{tag}_{stamp}.txt")


if __name__ == "__main__":
    main()
