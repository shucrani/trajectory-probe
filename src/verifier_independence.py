"""Chantier 2 — Que vaut un vérificateur qui n'est pas indépendant du générateur ?

Les sept lignes de `docs/TABLE-DECISION.md` supposent un vérificateur indépendant.
Le terrain rapporte que les tests écrits par un LLM « renforcent le comportement
existant ». Personne ne chiffre ce que cela coûte.

Trois degrés d'indépendance, sur les MÊMES candidats :

    A   tests des auteurs de MBPP          référence, indépendance totale
    B1  tests générés depuis l'ÉNONCÉ      le modèle ne voit pas le code
    B2  tests générés depuis le CODE       circulaire

Métrique principale — sur les candidats qui PASSENT le vérificateur B :

    taux de faux vérifié = fraction qui échoue aux tests de référence A

C'est la probabilité qu'un système annonce « vérifié » sur du code faux.
Métrique secondaire : taux de vrai rejeté (passe A, échoue B) = sévérité excessive.

Usage :
    .venv/bin/python src/verifier_independence.py [--limit 40] [--n 4]
"""
import argparse
import json
import re
from datetime import datetime
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from code_bound import DATA, ROOT, SEED, check_runs, check_tests, extract_code

ASSERT = re.compile(r"^\s*assert\b.*$", re.M)


def extract_asserts(text, max_n=4):
    """Ne garde que des lignes `assert` autonomes — pas de code arbitraire."""
    out = []
    for ln in ASSERT.findall(text):
        ln = ln.strip()
        if ln and ln not in out:
            out.append(ln)
        if len(out) >= max_n:
            break
    return out


def gen(model, tok, device, prompt, n, seed, max_new_tokens=256, temperature=0.7):
    text = tok.apply_chat_template([{"role": "user", "content": prompt}],
                                   tokenize=False, add_generation_prompt=True)
    enc = tok(text, return_tensors="pt").to(device)
    torch.manual_seed(seed)
    with torch.no_grad():
        out = model.generate(**enc, do_sample=True, temperature=temperature,
                             max_new_tokens=max_new_tokens, num_return_sequences=n,
                             pad_token_id=tok.eos_token_id, top_k=0, top_p=1.0)
    return [tok.decode(o[enc["input_ids"].shape[1]:], skip_special_tokens=True)
            for o in out]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-1.5B-Instruct")
    ap.add_argument("--dtype", default="float16")
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--n", type=int, default=4, help="candidats de code par tâche")
    args = ap.parse_args()

    problems = json.load(open(DATA))[:args.limit]
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(args.model)
    tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.model, dtype=getattr(torch, args.dtype)).to(device).eval()

    rows = []
    for i, p in enumerate(problems):
        imports = p.get("test_imports", [])
        sig = p["test_list"][0]

        # 1. candidats de code
        codes = [extract_code(t) for t in gen(
            model, tok, device,
            f"{p['prompt']}\n\nYour code should satisfy this test:\n{sig}\n\n"
            "Reply with only the Python function.", args.n, SEED + i)]

        # 2. B1 — tests générés depuis l'ÉNONCÉ seul, une fois par tâche
        b1 = extract_asserts(gen(
            model, tok, device,
            f"Write 3 assert statements that test a Python function for this task:\n"
            f"{p['prompt']}\n\nThe function signature matches this example:\n{sig}\n\n"
            "Reply with only the assert lines.", 1, SEED + 1000 + i)[0])

        for j, code in enumerate(codes):
            runs, _ = check_runs(code, imports)
            if not runs:
                continue  # un code qui n'exécute pas ne teste rien

            # 3. B2 — tests générés en REGARDANT le code
            b2 = extract_asserts(gen(
                model, tok, device,
                "Write 3 assert statements that test this Python function:\n\n"
                f"```python\n{code}\n```\n\nReply with only the assert lines.",
                1, SEED + 2000 + i * 10 + j)[0])

            a_ok, _ = check_tests(code, imports, p["test_list"])
            b1_ok = check_tests(code, imports, b1)[0] if b1 else None
            b2_ok = check_tests(code, imports, b2)[0] if b2 else None

            rows.append({"task_id": p["task_id"], "cand": j, "A": a_ok,
                         "B1": b1_ok, "B2": b2_ok,
                         "n_b1": len(b1), "n_b2": len(b2)})
        print(f"  task {p['task_id']:<5} {len(codes)} candidats, "
              f"{sum(1 for r in rows if r['task_id']==p['task_id'])} exécutables")

    def stats(key):
        sub = [r for r in rows if r[key] is not None]
        if not sub:
            return None
        passed = [r for r in sub if r[key]]
        rejected = [r for r in sub if not r[key]]
        return {
            "n": len(sub),
            "n_passed": len(passed),
            # faux vérifié : le vérificateur dit OK, la référence dit non
            "faux_verifie": (sum(1 for r in passed if not r["A"]) / len(passed)) if passed else None,
            # vrai rejeté : la référence dit OK, le vérificateur dit non
            "vrai_rejete": (sum(1 for r in rejected if r["A"]) / len(rejected)) if rejected else None,
            "accord_avec_A": sum(1 for r in sub if r[key] == r["A"]) / len(sub),
        }

    s1, s2 = stats("B1"), stats("B2")
    n_a = sum(1 for r in rows if r["A"])

    lines = []
    w = lines.append
    w("CHANTIER 2 — INDÉPENDANCE DU VÉRIFICATEUR")
    w(f"date   : {datetime.now().isoformat(timespec='seconds')}")
    w(f"modèle : {args.model} · {args.limit} tâches · {args.n} candidats/tâche")
    w(f"candidats exécutables retenus : {len(rows)} · dont corrects selon A : {n_a}")
    w("")
    w("CONTRÔLE — les tests B2 passent-ils sur le code qui les a engendrés ?")
    if s2:
        w(f"   {s2['n_passed']}/{s2['n']} = {s2['n_passed']/s2['n']:.1%}")
        w("   (attendu : quasi-total. Sinon le modèle produit des tests incohérents")
        w("    avec son propre code, ce qui est un autre résultat.)")
    w("")
    w(f"{'vérificateur':<34}{'faux vérifié':>14}{'vrai rejeté':>14}{'accord/A':>11}")
    w("-" * 73)
    for name, s in (("B1  tests depuis l'énoncé", s1), ("B2  tests depuis le code", s2)):
        if not s:
            continue
        fv = f"{s['faux_verifie']:.1%}" if s['faux_verifie'] is not None else "n/a"
        vr = f"{s['vrai_rejete']:.1%}" if s['vrai_rejete'] is not None else "n/a"
        w(f"{name:<34}{fv:>14}{vr:>14}{s['accord_avec_A']:>10.1%}")
    w("")
    w("LECTURE. Le « faux vérifié » est la probabilité qu'un système annonce")
    w("VÉRIFIÉ sur du code que la référence rejette. C'est le chiffre qui manque")
    w("à la table de décision : toutes ses lignes supposent un vérificateur")
    w("indépendant. Un vérificateur avec un taux de faux vérifié élevé ne")
    w("délivre pas une garantie faible — il n'en délivre aucune, tout en")
    w("produisant l'apparence d'une vérification.")

    out = "\n".join(lines)
    print("\n" + out)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    (ROOT / "results" / f"verifier_independence_{stamp}.txt").write_text(out + "\n")
    (ROOT / "results" / f"verifier_independence_{stamp}.json").write_text(
        json.dumps({"rows": rows, "B1": s1, "B2": s2}, indent=1))
    print(f"\n-> results/verifier_independence_{stamp}.txt")


if __name__ == "__main__":
    main()
