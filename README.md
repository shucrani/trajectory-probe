# trajectory-probe

**Combien d'hallucination peut-on retirer d'un modèle de langage sans lui apporter
la moindre connaissance extérieure — et à quel prix ?**

Ce dépôt répond par la mesure. Treize étapes, chaque protocole déclaré avant son
exécution, chaque contrôle consigné qu'il passe ou qu'il échoue.

---

## Résultat principal — la table de décision

Pour un budget donné, quelle force de garantie est atteignable, et sur quelle
fraction du travail. Détail et sources : [`docs/TABLE-DECISION.md`](docs/TABLE-DECISION.md).

| domaine / vérificateur | couverture | précision | coût par vérification |
|---|---|---|---|
| empirique — dispersion des tirages | 57.6 % | **70.6 %** | ~0 |
| arithmétique — substitution, modulo | **95.2 %** | 100 % | < 1 ms |
| code — syntaxe (`compile`) | 100 % | — | 5.3 ms |
| code — exécution sans exception | 100 % | — | 152 ms |
| **code — tests fournis** | **83.3 %** | 100 %\* | **37 ms** |
| Lean + Mathlib — imports ciblés | 20.0 % | 100 % | 14 s |
| Lean + Mathlib — `import Mathlib` | non mesurée | 100 % | 187-220 s |

\* conforme à la spécification exécutable fournie, pas correct au sens d'un noyau
de preuve.

Une ligne se lit ainsi : *avec des tests d'intégration, on répond à 83 % des
tâches avec une garantie totale relative aux tests, pour 37 ms de vérification.*

---

## Deux régularités mesurées

**`couverture = 1 − part systématique`**

Dès qu'au moins un tirage est correct, un vérificateur le trouve. Vérifiée sur
trois domaines indépendants, dont une fois à l'égalité exacte : part systématique
MBPP = 10/60 = 16.667 %, couverture mesurée = 83.333 %.

Une agrégation, elle, ne capture qu'une fraction du stochastique — 95.2 % contre
76.2 % pour un vote majoritaire sur le même corpus. C'est la différence entre
**vérifier** et **graduer**.

**Le rendement de l'agrégation suit la part stochastique**

| modèle, corpus | part stochastique | réduction d'erreur par le vote |
|---|---|---|
| GPT-2 small, factuel | 56 % | 25.3 % |
| Qwen2.5-1.5B, code MBPP | 76.7 % | — |
| Qwen2.5-1.5B, factuel | 100 %† | 70.2 % |

† plafond de corpus : les questions, écrites pour GPT-2, ne contiennent plus de
difficulté pour ce modèle.

---

## Les leviers, chiffrés

| levier | gain | prix |
|---|---|---|
| prendre le mode (vote ou greedy) | −25 % à −70 % d'erreur | nul |
| s'abstenir sur désaccord entre tirages | −60 % des erreurs | 42 % de couverture |
| vérifier par exécution de tests | 100 % de précision sur 83.3 % | 37 ms |
| vérifier par noyau de preuve | 100 % sur 20 % | 14 s |

Et une **borne** : de 23 % à 44 % des erreurs sont systématiques selon le couple
modèle-corpus — le modèle se trompe à chaque tirage. Aucune agrégation, aucun
décodage, aucune perturbation ne les corrige. Elles exigent une source externe.

Le coût de vérification dépend du **contexte chargé**, pas du vérificateur :
facteur 20 à 50 entre un import Lean ciblé et l'import global. Et **rejeter coûte
plus cher qu'accepter** — 14 s contre 6 s en Lean, timeouts à 5 s en Python — un
couplage vérifié sur deux vérificateurs sans rapport entre eux.

---

## Résultats négatifs — ils sont des résultats

**Un signal peut être entièrement porté par la longueur des phrases.** Sur un
dataset d'hallucinations écrit à la main, compter les caractères atteint
**AUC 0.942** là où un pipeline complet sur états cachés atteint 0.939. Tout
travail sur ce type de corpus doit passer ce contrôle avant d'être interprété.

**Rien dans le prompt ne prédit l'issue.** En protocole *same-prompt bifurcation*,
les deux classes partagent le même état de prompt : AUC = 0.500 exactement, au
flottant près. Ce n'est pas une mesure faible, c'est une identité — et elle ferme
toute certification préalable à la génération.

**La séparation inter-couches est lexicale.** La couche d'embedding atteint 0.84,
la meilleure couche 0.89 : les douze blocs transformer ajoutent 0.05.

**L'attracteur est du côté correct.** Un bruit de même amplitude répare une
trajectoire hallucinée dans 6.4 % des cas et n'en corrompt une correcte que dans
0.8 %. Contredit l'asymétrie rapportée sur un modèle plus grand
([arXiv 2604.15400](https://arxiv.org/abs/2604.15400)) — réserve d'échelle assumée.

**La direction qui répare n'est pas transférable.** Similarité cosinus de 0.36
entre prompts, mais 0.8 % de réparation en transfert contre 8.3 % avec la
direction propre au prompt. Réparer, c'est injecter la réponse — ce qui ferme le
steering correctif autonome.

---

## Méthode

Chaque mesure est précédée d'un contrôle qui peut l'invalider, et le protocole est
déclaré dans [`log.md`](log.md) **avant** le run, avec sa prédiction et son critère
de réfutation. Les degrés de liberté sont figés dans
[`docs/DEGRES-DE-LIBERTE.md`](docs/DEGRES-DE-LIBERTE.md).

Sept contrôles ont attrapé sept erreurs réelles, chacune produisant un chiffre
plausible et faux :

- `"0"` reconnu comme sous-chaîne de `"110"` → 15 faux « corrects »
- non-réponses comptées comme hallucinations → taux de bifurcation juste par accident
- texte et activation issus de runs différents → self-patch à 18 % au lieu de 0 %
- effet d'amplitude confondu avec effet de contenu → un z de 2.96 réduit à néant
- agrégation par tirage au lieu de par tâche → un vote à −10.4 % au lieu de +6.8 %
- accord approximé au lieu d'exact → une AUC de 0.436 au lieu de 0.666
- tests générés incohérents avec leur propre code → chantier 2 déclaré non concluant

Le dernier illustre le principe : sans ce contrôle, la phrase « la vérification
circulaire produit 20.8 % de faux vérifié » entrait dans le journal — citable,
plausible, et fausse.

---

## Ce qui n'est pas mesuré

- **La circularité du vérificateur.** Le chantier 2 est non concluant : le modèle
  utilisé n'écrit pas de tests cohérents avec son propre code (34 % au lieu du
  quasi-total attendu). Le chiffre reste absent de ce dépôt comme de la littérature.
- **La boucle de réparation.** [NL2VC-60](https://arxiv.org/html/2604.22601v1)
  rapporte 0 % → 81.82 % par feedback itératif du vérificateur. Si cela se
  reproduisait ici, `couverture = 1 − part systématique` cesserait d'être une
  borne. Non testé.
- **L'échelle.** Tout est mesuré sur GPT-2 small (124 M) et Qwen2.5-1.5B-Instruct,
  sur une machine unique. La partition dépend du couple modèle-corpus : elle se
  mesure par modèle, elle ne se transporte pas.

---

## Reproduire

```bash
uv venv --python 3.12 .venv && VIRTUAL_ENV=.venv uv pip install torch transformers scikit-learn numpy matplotlib
.venv/bin/python src/c1_surface_confound.py      # contrôle de confond de surface
.venv/bin/python src/reduction_bound.py          # partition + stratégies sans connaissance
.venv/bin/python src/verifiable_bound.py         # régime vérifiable, arithmétique
.venv/bin/python src/code_bound.py               # régime vérifiable, code (MBPP)
```

Lean : voir [`docs/PROTOCOLE-CIBLE.md`](docs/PROTOCOLE-CIBLE.md). Toute exécution
de code généré se fait en sous-processus isolé, avec timeout, hors du dépôt.

## Structure

```
src/        scripts de mesure, un par étape
results/    sorties brutes horodatées — jamais seulement les figures
docs/       table de décision, degrés de liberté, références vérifiées
log.md      journal daté : protocoles, prédictions, contrôles, échecs
figures/    gpt2/ = mesuré · synthetic/ = simulé, ne valide rien du réel
```

## Origine

Le dépôt part d'un programme antérieur (ProbatioH1) qui cherchait à certifier les
trajectoires latentes. Les mesures ont fermé cette voie et en ont ouvert une
autre : le régime vérifiable. L'audit de ce programme, ses axiomes et leur statut
après mesure sont conservés dans [`docs/`](docs/) — corriger une archive
falsifierait la trace.
