"""Le même protocole, relancé, redonne-t-il les mêmes tâches ?

    python3 src/reproduction_check.py ANCIEN.json NOUVEAU.json

Le run du 20/08 portait sur 60 tâches. Tout run plus large reprend les mêmes
tâches en tête de liste, avec la même graine. Sur MPS le déterminisme n'est pas
garanti : les noyaux flottants peuvent réordonner, et un logit qui bascule d'un
ulp change le token tiré. Ce script mesure de combien, au lieu de le supposer.

Il ne dit pas qui a raison. Deux runs qui divergent disent que la mesure porte
un bruit d'échantillonnage, et que ce bruit doit être cité à côté de
l'intervalle de confiance, pas confondu avec lui.
"""
import json
import sys
from pathlib import Path


def charger(p):
    return {r["task_id"]: r for r in json.loads(Path(p).read_text())["rows"]}


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    a, b = charger(sys.argv[1]), charger(sys.argv[2])
    communs = sorted(set(a) & set(b))
    if not communs:
        raise SystemExit("Aucune tâche commune.")

    meme_cat = sum(a[t]["categorie"] == b[t]["categorie"] for t in communs)
    meme_nok = sum(a[t]["n_ok"] == b[t]["n_ok"] for t in communs)
    ecarts = [abs(a[t]["n_ok"] - b[t]["n_ok"]) for t in communs]
    atteint = lambda d: sum(1 for t in communs if d[t]["n_ok"] > 0) / len(communs)

    print(f"\n{len(communs)} tâches communes\n")
    print(f"   même catégorie          {meme_cat:>3}/{len(communs)}  {meme_cat/len(communs):6.1%}")
    print(f"   même n_ok exactement    {meme_nok:>3}/{len(communs)}  {meme_nok/len(communs):6.1%}")
    print(f"   écart moyen sur n_ok         {sum(ecarts)/len(ecarts):5.2f} candidat(s) sur 10")
    print(f"   écart maximal                {max(ecarts):5d}")
    print(f"\n   plafond générateur, ancien   {atteint(a):6.1%}")
    print(f"   plafond générateur, nouveau  {atteint(b):6.1%}")
    d = abs(atteint(a) - atteint(b))
    print(f"   écart                        {d:6.1%}")

    # Les tâches qui basculent de catégorie sont les seules qui déplacent le
    # plafond. Une tâche qui passe de 9/10 à 8/10 ne le touche pas.
    bascules = [t for t in communs
                if (a[t]["n_ok"] == 0) != (b[t]["n_ok"] == 0)]
    print(f"\n   tâches franchissant le seuil « au moins un bon » : {len(bascules)}")
    for t in bascules:
        print(f"      task {t:<5} {a[t]['n_ok']}/10 -> {b[t]['n_ok']}/10")
    print()


if __name__ == "__main__":
    main()
