"""Étape 12 — Coût réel du régime vérifiable avec Lean + Mathlib.

L'étape 11 a montré qu'en domaine vérifiable la précision atteint 100 % sur 95 %
de couverture — mais la vérification y était de l'arithmétique, gratuite. Avec un
noyau de preuve, deux coûts apparaissent et décident si le régime tient :

    COÛT DE VÉRIFICATION   secondes de compilation par candidat
    TAUX DE COMPILATION    fraction des candidats du modèle qui passent le noyau

Le second commande la couverture : si le modèle ne produit presque jamais de
preuve valide, la garantie est parfaite et vide.

Protocole, identique à l'étape 11 : N candidats par énoncé, on accepte l'énoncé
si AU MOINS UN candidat compile. Précision 100 % par construction — le noyau ne
laisse rien passer. On mesure ce que ça coûte et ce que ça couvre.

Usage :
    .venv/bin/python src/lean_cost.py [--n 8] [--project ~/mathlib-probe]
"""
import argparse
import json
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parent.parent
SEED = 42

# Énoncés prouvables par une tactique courte. La preuve canonique sert de
# contrôle : si elle ne compile pas, l'énoncé ou l'environnement est en cause,
# pas le modèle.
STATEMENTS = [
    # (import minimal, énoncé, tactique canonique de contrôle)
    ("", "theorem t1 (a b : Nat) : a + b = b + a", "omega"),
    ("", "theorem t2 (a b c : Nat) : a + b + c = a + (b + c)", "omega"),
    ("", "theorem t3 (a : Nat) : a + 0 = a", "simp"),
    ("", "theorem t4 (n : Nat) : n <= n + 1", "omega"),
    ("", "theorem t5 (n : Nat) (h : n > 0) : n >= 1", "omega"),
    ("", "theorem t6 (a b : Nat) (h : a = b) : b = a", "omega"),
    ("", "theorem t7 (p q : Prop) (hp : p) (hq : q) : p /\\ q", "exact ⟨hp, hq⟩"),
    ("", "theorem t8 (p q : Prop) (h : p /\\ q) : p", "exact h.1"),
    ("", "theorem t9 (p q : Prop) (h : p) : p \\/ q", "exact Or.inl h"),
    ("", "theorem t10 (f : Nat -> Nat) (a : Nat) : f a = f a", "rfl"),
    ("import Mathlib.Tactic.Ring", "theorem t11 (a b : Int) : a * b = b * a", "ring"),
    ("import Mathlib.Tactic.Ring",
     "theorem t12 (a b : Int) : (a + b) ^ 2 = a ^ 2 + 2 * a * b + b ^ 2", "ring"),
    ("import Mathlib.Tactic.Ring", "theorem t13 (a : Int) : a - a = 0", "ring"),
    ("import Mathlib.Tactic.Ring", "theorem t14 (a b : Int) : a + b - b = a", "ring"),
    ("import Mathlib.Tactic.Ring", "theorem t15 (a b : Int) : (a - b) * (a + b) = a^2 - b^2", "ring"),
    ("import Mathlib.Tactic.Linarith",
     "theorem t16 (x : Int) (h : x > 0) : x >= 0", "linarith"),
    ("import Mathlib.Tactic.Linarith",
     "theorem t17 (x y : Int) (h1 : x <= y) (h2 : y <= x) : x = y", "linarith"),
    ("import Mathlib.Tactic.Linarith",
     "theorem t18 (x : Int) (h : 2 * x = 6) : x = 3", "linarith"),
    ("import Mathlib.Data.Nat.Basic", "theorem t19 (a : Nat) : a * 1 = a", "simp"),
    ("import Mathlib.Data.List.Basic", "theorem t20 (l : List Nat) : l ++ [] = l", "simp"),
]


FENCE = re.compile(r"```(?:lean4?)?\s*(.*?)```", re.S)


def clean_tactic(text):
    """Extrait un bloc de tactique exploitable de la sortie du modèle."""
    m = FENCE.search(text)
    body = m.group(1) if m else text
    lines = []
    for ln in body.strip().splitlines():
        ln = ln.rstrip()
        if not ln.strip():
            break
        if ln.strip().startswith(("theorem", "import", "--", "example", "lemma")):
            continue
        lines.append(ln.strip())
        if len(lines) >= 3:
            break
    return "\n  ".join(lines).strip()


def check(project, imports, statement, tactic, idx):
    """Compile `statement := by tactic` avec le contexte MINIMAL nécessaire.

    L'étape 12 a mesuré un facteur 20 à 50 entre un import ciblé (4-9 s) et
    `import Mathlib` (187-220 s). Le contexte est donc porté par l'énoncé.
    """
    head = imports + "\n\n" if imports else ""
    src = f"{head}set_option maxHeartbeats 20000 in\n{statement} := by\n  {tactic}\n"
    f = project / f"_probe_{idx}.lean"
    f.write_text(src)
    t0 = time.time()
    try:
        r = subprocess.run(["lake", "env", "lean", f.name], cwd=project,
                           capture_output=True, text=True, timeout=180)
        ok = r.returncode == 0
    except subprocess.TimeoutExpired:
        ok = False
    dt = time.time() - t0
    f.unlink(missing_ok=True)
    return ok, dt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-1.5B-Instruct")
    ap.add_argument("--dtype", default="float16")
    ap.add_argument("--n", type=int, default=8, help="candidats par énoncé")
    ap.add_argument("--project", default=str(Path.home() / "mathlib-probe"))
    ap.add_argument("--temperature", type=float, default=0.7)
    args = ap.parse_args()
    project = Path(args.project).expanduser()

    # Contrôle : les preuves canoniques compilent-elles ?
    print("Contrôle des preuves canoniques...")
    canon_ok, canon_times = [], []
    for i, (imp, st, tac) in enumerate(STATEMENTS):
        ok, dt = check(project, imp, st, tac, f"canon{i}")
        canon_ok.append(ok); canon_times.append(dt)
        print(f"  {st.split('(')[0].strip():<14} {'OK' if ok else 'ÉCHEC':<6} {dt:>6.1f}s")
    usable = [i for i, ok in enumerate(canon_ok) if ok]
    print(f"\n{len(usable)}/{len(STATEMENTS)} énoncés utilisables\n")
    if not usable:
        raise SystemExit("Aucun énoncé ne compile — environnement ou énoncés en cause.")

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(args.model)
    tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.model, dtype=getattr(torch, args.dtype)).to(device).eval()

    rows, all_times, n_compiled, n_tried = [], [], 0, 0
    for i in usable:
        imp, st, _ = STATEMENTS[i]
        msgs = [{"role": "user", "content":
                 "Complete this Lean 4 proof using Mathlib. Reply with ONLY the "
                 f"tactic block, no explanation, no theorem statement.\n\n{st} := by\n"}]
        text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        enc = tok(text, return_tensors="pt").to(device)
        torch.manual_seed(SEED + i)
        with torch.no_grad():
            out = model.generate(**enc, do_sample=True, temperature=args.temperature,
                                 max_new_tokens=64, num_return_sequences=args.n,
                                 pad_token_id=tok.eos_token_id, top_k=0, top_p=1.0)
        cands = [clean_tactic(tok.decode(o[enc["input_ids"].shape[1]:],
                                         skip_special_tokens=True)) for o in out]
        results = []
        for j, c in enumerate(cands):
            if not c:
                results.append((c, False, 0.0)); n_tried += 1
                continue
            ok, dt = check(project, imp, st, c, f"{i}_{j}")
            results.append((c, ok, dt))
            all_times.append(dt); n_tried += 1
            n_compiled += ok
        covered = any(ok for _, ok, _ in results)
        rows.append({"statement": st, "imports": imp, "covered": covered,
                     "candidates": [{"tactic": c, "ok": ok, "sec": round(dt, 2)}
                                    for c, ok, dt in results]})
        print(f"  {st.split('(')[0].strip():<14} "
              f"{sum(ok for _, ok, _ in results)}/{len(results)} compilent  "
              f"{'COUVERT' if covered else '-'}")

    lines = []
    w = lines.append
    w("ÉTAPE 12 — COÛT RÉEL DU RÉGIME VÉRIFIABLE (Lean + Mathlib)")
    w(f"date    : {datetime.now().isoformat(timespec='seconds')}")
    w(f"modèle  : {args.model} · N={args.n} candidats/énoncé · T={args.temperature}")
    w(f"projet  : {project}")
    w("")
    w("A. COÛT DE VÉRIFICATION")
    w("")
    if canon_times:
        w(f"   preuve canonique : {sum(canon_times)/len(canon_times):>6.1f}s en moyenne "
          f"(min {min(canon_times):.1f}s, max {max(canon_times):.1f}s)")
    if all_times:
        w(f"   candidat modèle  : {sum(all_times)/len(all_times):>6.1f}s en moyenne")
        w(f"   coût d'un énoncé : {sum(all_times)/max(len(rows),1):>6.1f}s "
          f"pour {args.n} candidats")
    w(f"   pour mémoire : arithmétique (ét. 11) < 0.001 s · "
      f"import Mathlib global (ét. 12) 187-220 s")
    w("")
    w("B. TAUX DE COMPILATION")
    w("")
    w(f"   candidats qui compilent : {n_compiled}/{n_tried} = "
      f"{n_compiled/max(n_tried,1):>6.1%}")
    cov = sum(r["covered"] for r in rows) / max(len(rows), 1)
    w(f"   énoncés couverts (>=1 candidat valide) : "
      f"{sum(r['covered'] for r in rows)}/{len(rows)} = {cov:>6.1%}")
    w("")
    w("C. COMPARAISON DES RÉGIMES VÉRIFIABLES")
    w("")
    w(f"   {'régime':<26}{'couverture':>12}{'précision':>11}{'coût/énoncé':>14}")
    w(f"   {'arithmétique (ét. 11)':<26}{'95.2%':>12}{'100%':>11}{'~0 s':>14}")
    if all_times:
        w(f"   {'Lean + Mathlib':<26}{cov:>11.1%}{'100%':>11}"
          f"{sum(all_times)/max(len(rows),1):>13.1f}s")
    w("")
    w("LECTURE. La précision reste 100 % par construction — le noyau ne laisse rien")
    w("passer. Ce qui change entre les deux régimes vérifiables, c'est la COUVERTURE")
    w("et le COÛT. Une couverture qui s'effondre signifie une garantie parfaite et")
    w("vide : le système aurait raison, sur presque rien.")

    out = "\n".join(lines)
    print("\n" + out)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    tag = args.model.split("/")[-1]
    (ROOT / "results" / f"lean_cost_{tag}_{stamp}.txt").write_text(out + "\n")
    (ROOT / "results" / f"lean_cost_{tag}_{stamp}.json").write_text(
        json.dumps(rows, indent=1, ensure_ascii=False))
    print(f"\n-> results/lean_cost_{tag}_{stamp}.txt")


if __name__ == "__main__":
    main()
