"""Chantier 1 — Le régime vérifiable sur du code réel (MBPP).

Les étapes 10-11 ont mesuré la partition et la politique vérifiée sur des faits
puis sur de l'arithmétique. Ici le domaine est l'ingénierie logicielle, et le
vérificateur est celui qui existe déjà dans toute chaîne de développement :
l'exécution des tests.

Trois forces de vérification croissantes, sur le MÊME corpus et les MÊMES
candidats — c'est ce qui rend la table couverture × force × coût lisible :

    G4  syntaxe    le code parse (`compile`)
    G3  exécution  le module s'exécute sans lever d'exception
    G2  tests      les assertions fournies par le benchmark passent

Le vérificateur est INDÉPENDANT du générateur : les tests viennent des auteurs
de MBPP, pas du modèle. Le chantier 2 mesurera ce que vaut la version circulaire.

Sécurité : tout code généré s'exécute dans un sous-processus séparé, avec
timeout, dans un dossier temporaire hors du dépôt. Jamais d'`exec` en processus
principal, jamais dans le cwd du projet.

Usage :
    .venv/bin/python src/code_bound.py [--n 10] [--limit 60]
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "sanitized-mbpp.json"
SEED = 42
SCRATCH = Path(os.environ.get("MBPP_SANDBOX", ROOT / "build" / "mbpp_sandbox"))
FENCE = re.compile(r"```(?:python)?\s*(.*?)```", re.S)


def extract_code(text):
    m = FENCE.search(text)
    if m:
        return m.group(1).strip()
    # pas de bloc : on garde à partir de la première def
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if ln.startswith(("def ", "import ", "from ")):
            return "\n".join(lines[i:]).strip()
    return text.strip()


def run_isolated(source, timeout=5):
    """Exécute `source` dans un sous-processus isolé. Renvoie (ok, secondes)."""
    SCRATCH.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".py", dir=SCRATCH,
                                     delete=False) as f:
        f.write(source)
        path = Path(f.name)
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, path.name], cwd=SCRATCH,
                           capture_output=True, text=True, timeout=timeout)
        ok = r.returncode == 0
    except subprocess.TimeoutExpired:
        ok = False
    dt = time.time() - t0
    path.unlink(missing_ok=True)
    return ok, dt


def check_syntax(code):
    """G4 — le code parse. `compile` ne l'exécute pas : sûr en local."""
    t0 = time.time()
    try:
        compile(code, "<candidate>", "exec")
        ok = True
    except (SyntaxError, ValueError):
        ok = False
    return ok, time.time() - t0


def check_runs(code, imports):
    """G3 — le module s'exécute sans exception (définitions évaluées)."""
    return run_isolated("\n".join(imports) + "\n" + code + "\n")


def check_tests(code, imports, tests):
    """G2 — les assertions du benchmark passent."""
    src = "\n".join(imports) + "\n" + code + "\n" + "\n".join(tests) + "\n"
    return run_isolated(src)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-1.5B-Instruct")
    ap.add_argument("--dtype", default="float16")
    ap.add_argument("--n", type=int, default=10, help="candidats par tâche")
    ap.add_argument("--limit", type=int, default=60, help="tâches MBPP")
    ap.add_argument("--temperature", type=float, default=0.7)
    args = ap.parse_args()

    problems = json.load(open(DATA))[:args.limit]

    # CONTRÔLE : les solutions de référence passent-elles leurs propres tests ?
    # Si non, l'exécuteur est en cause, pas le modèle.
    print("Contrôle des solutions de référence...")
    ref_ok, ref_times = [], []
    for p in problems:
        ok, dt = check_tests(p["code"], p.get("test_imports", []), p["test_list"])
        ref_ok.append(ok); ref_times.append(dt)
    usable = [i for i, ok in enumerate(ref_ok) if ok]
    print(f"  {len(usable)}/{len(problems)} références passent "
          f"({sum(ref_times)/len(ref_times)*1000:.0f} ms en moyenne)")
    if len(usable) < len(problems) * 0.8:
        raise SystemExit("Trop de références échouent — exécuteur suspect.")

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(args.model)
    tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.model, dtype=getattr(torch, args.dtype)).to(device).eval()

    cats = Counter()
    rows = []
    times = {"G4": [], "G3": [], "G2": []}

    for i in usable:
        p = problems[i]
        imports = p.get("test_imports", [])
        # Protocole MBPP standard : le premier test sert de spécification (il
        # donne la signature). Les trois tests servent à la vérification.
        msg = (f"{p['prompt']}\n\nYour code should satisfy this test:\n"
               f"{p['test_list'][0]}\n\nReply with only the Python function.")
        text = tok.apply_chat_template([{"role": "user", "content": msg}],
                                       tokenize=False, add_generation_prompt=True)
        enc = tok(text, return_tensors="pt").to(device)
        torch.manual_seed(SEED + i)
        with torch.no_grad():
            out = model.generate(**enc, do_sample=True, temperature=args.temperature,
                                 max_new_tokens=256, num_return_sequences=args.n,
                                 pad_token_id=tok.eos_token_id, top_k=0, top_p=1.0)
        cands = [extract_code(tok.decode(o[enc["input_ids"].shape[1]:],
                                         skip_special_tokens=True)) for o in out]

        res = []
        for c in cands:
            s_ok, s_dt = check_syntax(c)
            times["G4"].append(s_dt)
            r_ok = t_ok = False
            if s_ok:
                r_ok, r_dt = check_runs(c, imports)
                times["G3"].append(r_dt)
                if r_ok:
                    t_ok, t_dt = check_tests(c, imports, p["test_list"])
                    times["G2"].append(t_dt)
            res.append({"syntax": s_ok, "runs": r_ok, "tests": t_ok})

        n_ok = sum(r["tests"] for r in res)
        cat = ("TOUJOURS-CORRECT" if n_ok == len(res)
               else "TOUJOURS-FAUX" if n_ok == 0 else "BIFURQUANT")
        cats[cat] += 1
        rows.append({"task_id": p["task_id"], "categorie": cat, "n_ok": n_ok,
                     "n": len(res), "results": res})
        print(f"  task {p['task_id']:<5} {n_ok}/{len(res)} passent  {cat}")

    lines = []
    w = lines.append
    w("CHANTIER 1 — RÉGIME VÉRIFIABLE SUR DU CODE RÉEL (MBPP)")
    w(f"date    : {datetime.now().isoformat(timespec='seconds')}")
    w(f"modèle  : {args.model} · {len(usable)} tâches · N={args.n} · T={args.temperature}")
    w(f"vérificateur : tests fournis par MBPP — INDÉPENDANT du générateur")
    w("")
    w("A. PARTITION")
    w("")
    tot = sum(cats.values())
    for c in ("TOUJOURS-CORRECT", "BIFURQUANT", "TOUJOURS-FAUX"):
        w(f"   {c:<20}{cats[c]:>4} / {tot} = {cats[c]/tot:>6.1%}")
    err = cats["BIFURQUANT"] + cats["TOUJOURS-FAUX"]
    if err:
        w("")
        w(f"   Sur les {err} tâches échouées au moins une fois :")
        w(f"     stochastique : {cats['BIFURQUANT']/err:>6.1%}")
        w(f"     systématique : {cats['TOUJOURS-FAUX']/err:>6.1%}")
    w("")
    w("B. COUVERTURE PAR FORCE DE VÉRIFICATION (au moins un candidat passe)")
    w("")
    w(f"   {'niveau':<26}{'couverture':>12}{'coût/vérif':>14}")
    for key, label in (("syntax", "G4  syntaxe"), ("runs", "G3  exécution"),
                       ("tests", "G2  tests fournis")):
        cov = sum(any(r[key] for r in row["results"]) for row in rows) / len(rows)
        tk = {"syntax": "G4", "runs": "G3", "tests": "G2"}[key]
        ms = (sum(times[tk]) / len(times[tk]) * 1000) if times[tk] else 0
        w(f"   {label:<26}{cov:>11.1%}{ms:>12.1f} ms")
    w("")
    w("C. STRATÉGIES SANS VÉRIFICATION")
    w("")
    m_uni = sum(r["n_ok"] / r["n"] for r in rows) / len(rows)
    w(f"   tirage unique (espérance)              {m_uni:>7.1%}")
    w("")
    w("D. TABLE COUVERTURE × FORCE × COÛT — les trois domaines mesurés")
    w("")
    w(f"   {'domaine':<28}{'couverture':>12}{'précision':>11}{'coût/vérif':>14}")
    w(f"   {'arithmétique (ét. 11)':<28}{'95.2%':>12}{'100%':>11}{'< 1 ms':>14}")
    cov_t = sum(any(r["tests"] for r in row["results"]) for row in rows) / len(rows)
    ms_t = (sum(times["G2"]) / len(times["G2"]) * 1000) if times["G2"] else 0
    w(f"   {'code MBPP (G2, ici)':<28}{cov_t:>11.1%}{'100%':>11}{ms_t:>11.1f} ms")
    w(f"   {'Lean ciblé (ét. 12)':<28}{'?':>12}{'100%':>11}{'4-9 s':>14}")
    w(f"   {'Lean global (ét. 12)':<28}{'?':>12}{'100%':>11}{'187-220 s':>14}")
    w("")
    w("LECTURE. La précision est 100 % dans les trois cas — le vérificateur ne")
    w("laisse rien passer. Ce qui distingue les domaines, c'est la couverture et")
    w("le coût. « 100 % de précision » ne signifie ici que : conforme à la")
    w("spécification exécutable fournie. Ce que les tests ne disent pas n'est pas")
    w("vérifié — c'est la limite structurelle du régime hors noyau de preuve.")

    out = "\n".join(lines)
    print("\n" + out)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    tag = args.model.split("/")[-1]
    (ROOT / "results" / f"code_bound_{tag}_{stamp}.txt").write_text(out + "\n")
    (ROOT / "results" / f"code_bound_{tag}_{stamp}.json").write_text(
        json.dumps({"categories": dict(cats), "rows": rows}, indent=1))
    print(f"\n-> results/code_bound_{tag}_{stamp}.txt")


if __name__ == "__main__":
    main()
