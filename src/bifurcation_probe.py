"""Étape 1 — GPT-2 small bifurque-t-il assez pour que le protocole soit praticable ?

Protocole d'Akarlar (arXiv 2604.15400), transposé : pour chaque prompt, N
complétions échantillonnées à température fixe. Un prompt BIFURQUE si au moins
`min_per_class` complétions sont classées Correct et au moins autant
Hallucination. Seuls les prompts bifurquants donnent deux classes issues du MÊME
prompt — donc sans confond de surface possible.

Ce script ne mesure PAS la géométrie. Il répond à une seule question : y a-t-il
assez de bifurcations à cette taille de modèle pour continuer ?

Toutes les complétions brutes sont écrites sur disque pour audit manuel : la
classification par substring est une heuristique, pas une vérité terrain.

Usage :
    .venv/bin/python src/bifurcation_probe.py [--model gpt2] [--n 20]
"""
import argparse
import json
import re
from datetime import datetime
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parent.parent
SEED = 42

# Prompts à complétion courte et vérifiable. `answers` = formes acceptées comme
# correctes (substring, insensible à la casse).
PROMPTS = [
    ("The capital of France is", ["paris"]),
    ("The capital of Japan is", ["tokyo"]),
    ("The capital of Italy is", ["rome"]),
    ("The capital of Germany is", ["berlin"]),
    ("The capital of Spain is", ["madrid"]),
    ("The capital of Russia is", ["moscow"]),
    ("The capital of Egypt is", ["cairo"]),
    ("The capital of Canada is", ["ottawa"]),
    ("The largest planet in the solar system is", ["jupiter"]),
    ("The closest planet to the Sun is", ["mercury"]),
    ("The chemical symbol for gold is", ["au"]),
    ("The chemical symbol for water is", ["h2o", "h20"]),
    ("The author of Hamlet was", ["shakespeare"]),
    ("The author of the Odyssey was", ["homer"]),
    ("The inventor of the telephone was", ["bell"]),
    ("The first president of the United States was", ["washington"]),
    ("The currency of Japan is the", ["yen"]),
    ("The currency of the United Kingdom is the", ["pound", "sterling"]),
    ("The tallest mountain in the world is", ["everest"]),
    ("The longest river in the world is", ["nile", "amazon"]),
    ("The largest ocean on Earth is the", ["pacific"]),
    ("The largest desert in Africa is the", ["sahara"]),
    ("Water freezes at a temperature of", ["0", "zero", "32"]),
    ("Water boils at a temperature of", ["100", "212"]),
    ("The number of continents on Earth is", ["seven", "7"]),
    ("The number of days in a leap year is", ["366"]),
    ("The speed of light is approximately", ["300", "299", "186"]),
    ("The human body has a total of", ["206"]),
    ("The Great Wall is located in", ["china"]),
    ("The Eiffel Tower is located in", ["paris", "france"]),
]

# Corpus étendu (20/08/2026) : +52 prompts, formes syntaxiques diversifiées.
from corpus import EXTRA  # noqa: E402
PROMPTS += [(t, a) for t, a, _ in EXTRA]

DEGENERATE = re.compile(r"^[\s\W_]*$")
ENTITY = re.compile(r"\b[A-Z][a-zA-Z]{2,}\b|\b\d[\d.,]*\b")


def _matches(text, answer):
    """Correspondance par frontière de mot, pas par substring.

    Sans cela "0" matche "110" et "The capital" matche n'importe quoi. C'est le
    bug qui faisait passer 15 completions fausses pour Correct sur le prompt
    "Water freezes at a temperature of".
    """
    return re.search(r"(?<![\w.])" + re.escape(answer) + r"(?![\w.])", text) is not None


def classify(completion, answers, prompt):
    """Correct / Hallucination / NoAnswer / Other.

    GPT-2 small n'est pas instruction-tuned : il CONTINUE le texte au lieu de
    repondre. La plupart de ses completions n'affirment aucune reponse. Les
    compter comme "Hallucination" gonfle artificiellement le taux de bifurcation.

    - Correct    : une forme attendue apparait (frontiere de mot).
    - Hallucination : pas de forme attendue, mais une ENTITE candidate (nom propre
      ou nombre) absente du prompt -> le modele a bien asserte quelque chose de faux.
    - NoAnswer   : continuation qui n'asserte aucune entite -> pas une hallucination.
    - Other      : vide ou degeneree.

    Heuristique assumee. Completions brutes archivees pour audit.
    """
    text = completion.strip()
    low = text.lower()
    if any(_matches(low, a) for a in answers):
        return "Correct"
    if DEGENERATE.match(text) or len(text) < 2:
        return "Other"
    prompt_words = {w.lower() for w in re.findall(r"\b\w+\b", prompt)}
    entities = [e for e in ENTITY.findall(text) if e.lower() not in prompt_words]
    return "Hallucination" if entities else "NoAnswer"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gpt2")
    ap.add_argument("--n", type=int, default=20, help="complétions par prompt")
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--max-new-tokens", type=int, default=8)
    ap.add_argument("--min-per-class", type=int, default=2)
    ap.add_argument("--typed", action="store_true",
                    help="Hallucination exige une entité du même type que la réponse")
    args = ap.parse_args()

    global classify
    if args.typed:
        from typed_entities import classify_typed as classify
    torch.manual_seed(SEED)
    device = "mps" if torch.backends.mps.is_available() else "cpu"

    tok = AutoTokenizer.from_pretrained(args.model)
    tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(args.model).to(device).eval()

    records, lines = [], []
    w = lines.append
    w("ÉTAPE 1 — TAUX DE BIFURCATION")
    w(f"date          : {datetime.now().isoformat(timespec='seconds')}")
    w(f"modèle        : {args.model} ({sum(p.numel() for p in model.parameters())/1e6:.0f}M) sur {device}")
    w(f"classes       : {'APPARIÉES EN TYPE' if args.typed else 'larges (v1)'}")
    w(f"protocole     : N={args.n} complétions, T={args.temperature}, "
      f"max_new_tokens={args.max_new_tokens}, seuil={args.min_per_class}/classe")
    w(f"prompts       : {len(PROMPTS)}")
    w("")
    w(f"{'prompt':<44}{'Corr':>6}{'Hallu':>7}{'NoAns':>7}{'Other':>7}  bifurque")
    w("-" * 82)

    n_bif = 0
    for prompt, answers in PROMPTS:
        enc = tok(prompt, return_tensors="pt").to(device)
        with torch.no_grad():
            out = model.generate(
                **enc,
                do_sample=True,
                temperature=args.temperature,
                max_new_tokens=args.max_new_tokens,
                num_return_sequences=args.n,
                pad_token_id=tok.eos_token_id,
                top_k=0,
                top_p=1.0,
            )
        completions = [
            tok.decode(o[enc["input_ids"].shape[1]:], skip_special_tokens=True)
            for o in out
        ]
        labels = [classify(c, answers, prompt) for c in completions]
        counts = {k: labels.count(k) for k in ("Correct", "Hallucination", "NoAnswer", "Other")}
        bif = counts["Correct"] >= args.min_per_class and counts["Hallucination"] >= args.min_per_class
        n_bif += bif
        short = prompt if len(prompt) <= 42 else prompt[:39] + "..."
        w(f"{short:<44}{counts['Correct']:>6}{counts['Hallucination']:>7}"
          f"{counts['NoAnswer']:>7}{counts['Other']:>7}  {'OUI' if bif else '-'}")
        records.append({
            "prompt": prompt, "answers": answers, "counts": counts,
            "bifurcates": bif,
            "completions": [{"text": c, "label": l} for c, l in zip(completions, labels)],
        })

    rate = n_bif / len(PROMPTS)
    w("")
    w(f"BIFURCATIONS : {n_bif}/{len(PROMPTS)} = {rate:.1%}")
    w(f"(référence Akarlar sur Qwen2.5-1.5B : 27/61 = 44.3%)")
    w("")
    if n_bif == 0:
        w("VERDICT : aucun prompt ne bifurque. Le protocole n'est pas praticable")
        w("à cette taille de modèle avec ce jeu de prompts. Options : monter en")
        w("taille (gpt2-medium/large, Qwen2.5-0.5B), ou revoir les prompts.")
    elif rate < 0.15:
        w("VERDICT : rendement faible. Praticable mais coûteux — il faudra")
        w("beaucoup de prompts candidats pour un échantillon exploitable.")
    else:
        w("VERDICT : rendement suffisant. Passer à l'extraction des trajectoires")
        w("(K runs par classe, residual stream complet).")
    w("")
    w("RÉSERVE : la classification par substring est une heuristique. Les")
    w("complétions brutes sont dans le .json joint — les auditer avant de bâtir")
    w("quoi que ce soit dessus.")

    out_txt = "\n".join(lines)
    print(out_txt)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    tag = args.model.replace("/", "-") + ("_typed" if args.typed else "")
    (ROOT / "results" / f"bifurcation_{tag}_{stamp}.txt").write_text(out_txt + "\n")
    (ROOT / "results" / f"bifurcation_{tag}_{stamp}.json").write_text(
        json.dumps(records, indent=1, ensure_ascii=False)
    )
    print(f"\n-> results/bifurcation_{tag}_{stamp}.{{txt,json}}")


if __name__ == "__main__":
    main()
