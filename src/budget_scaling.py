"""Les tâches non résolues à K=10 le sont-elles à K=100 ?

    python3 src/budget_scaling.py results/code_bound_..._1045.json

Une tâche qu'aucun échantillon ne résout en K tirages peut être hors de portée
du modèle, ou seulement rare. Un budget fini ne sépare pas les deux, et c'est ce
qui interdit d'appeler « plafond » la couverture mesurée à K.

Ce script monte K sur les seules tâches restées à zéro, et sur UNE population,
pas en comparant deux runs. Pour chaque tâche il estime p, la probabilité qu'un
tirage soit correct :

  m > 0 sur 100  ->  p > 0 ÉTABLI. La tâche n'est pas un angle mort, seulement
                     rare. Aucun test nécessaire : les complétions sont observées.
  m = 0 sur 100  ->  p n'est pas établi nul. La règle de trois donne p < 3 % à
                     95 %, ce qui est une borne, pas un zéro.

La population est conditionnée : ces tâches ont été retenues parce qu'elles ont
échoué à K=10. La sélection sur un zéro observé les biaise vers le bas, et le
résultat se lit « parmi les tâches qui échouent à dix tirages », jamais comme un
taux de population.
"""
import json
import sys
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from code_bound import DATA, ROOT, SEED, check_tests, extract_code

MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
TOTAL = 100          # tirages par tâche
BATCH = 10           # par passe, pour tenir dans la mémoire de la machine


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    rows = json.loads(Path(sys.argv[1]).read_text())["rows"]
    cibles = [r["task_id"] for r in rows if r["n_ok"] == 0]
    taches = {p["task_id"]: p for p in json.loads(DATA.read_text())}
    print(f"{len(cibles)} tâches non résolues à K=10, {TOTAL} tirages chacune\n")

    ckpt = ROOT / "results" / f"checkpoint_budget_{TOTAL}.jsonl"
    fait = {}
    if ckpt.exists():
        for line in ckpt.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                fait[r["task_id"]] = r
        print(f"  reprise : {len(fait)} tâches déjà faites\n")

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(MODEL)
    tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        MODEL, dtype=torch.float16).to(device).eval()

    for tid in cibles:
        if tid in fait:
            continue
        p = taches[tid]
        imports = p.get("test_imports", [])
        msg = (f"{p['prompt']}\n\nYour code should satisfy this test:\n"
               f"{p['test_list'][0]}\n\nReply with only the Python function.")
        text = tok.apply_chat_template([{"role": "user", "content": msg}],
                                       tokenize=False, add_generation_prompt=True)
        t0 = time.perf_counter()
        m = 0
        for b in range(TOTAL // BATCH):
            enc = tok(text, return_tensors="pt").to(device)
            # Graine distincte par lot : les 100 tirages sont indépendants, et
            # les dix premiers ne rejouent pas ceux du run d'origine.
            torch.manual_seed(SEED + 1000 * tid + b)
            with torch.no_grad():
                out = model.generate(**enc, do_sample=True, temperature=0.7,
                                     max_new_tokens=256, num_return_sequences=BATCH,
                                     pad_token_id=tok.eos_token_id, top_k=0, top_p=1.0)
            for o in out:
                code = extract_code(tok.decode(o[enc["input_ids"].shape[1]:],
                                               skip_special_tokens=True))
                ok, _ = check_tests(code, imports, p["test_list"])
                m += bool(ok)
            del out, enc
            if device == "mps":
                torch.mps.empty_cache()
        row = {"task_id": tid, "m": m, "n": TOTAL,
               "secondes": round(time.perf_counter() - t0, 1)}
        with ckpt.open("a") as f:
            f.write(json.dumps(row) + "\n")
        verdict = "p > 0 ÉTABLI" if m else "toujours zéro"
        print(f"  task {tid:<5} {m:>3}/{TOTAL}   {verdict}")

    resume(ckpt, len(cibles))


def resume(ckpt, attendu):
    rows = [json.loads(l) for l in ckpt.read_text().splitlines() if l.strip()]
    if len(rows) < attendu:
        print(f"\n{len(rows)}/{attendu} tâches faites, relancer pour terminer.")
        return
    sortis = [r for r in rows if r["m"] > 0]
    lignes = ["", f"RÉSULTAT — {len(rows)} tâches non résolues à K=10, portées à {TOTAL}", ""]
    lignes.append(f"   p > 0 établi          {len(sortis):>3}/{len(rows)} = {len(sortis)/len(rows):.1%}")
    lignes.append(f"   toujours zéro         {len(rows)-len(sortis):>3}/{len(rows)}"
                  f"   -> p < 3.0% à 95% (règle de trois), pas p = 0")
    lignes.append("")
    for r in sorted(sortis, key=lambda r: -r["m"]):
        lignes.append(f"      task {r['task_id']:<5} {r['m']:>3}/{TOTAL}   p estimé {r['m']/TOTAL:.1%}")
    lignes += ["",
               "LECTURE. Chaque tâche sortie du zéro est une tâche que dix tirages",
               "comptaient hors de portée et qui ne l'était pas. Les tâches restées à",
               "zéro ne sont pas démontrées impossibles : elles sont bornées, et la",
               "borne se resserre avec le budget sans jamais atteindre zéro.",
               "",
               "Population conditionnée à un échec observé à K=10. Le taux ci-dessus",
               "se lit parmi ces tâches, et ne s'applique pas au corpus entier.", ""]
    out = "\n".join(lignes)
    print(out)
    (ROOT / "results" / f"budget_scaling_{TOTAL}.txt").write_text(out)
    print(f"-> results/budget_scaling_{TOTAL}.txt")


if __name__ == "__main__":
    main()
