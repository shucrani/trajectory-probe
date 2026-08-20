# Table de décision — couverture × force de vérification × coût

État au 20/08/2026. Chaque chiffre renvoie à l'étape qui l'a produit ; les cases
non mesurées sont marquées comme telles et ne sont **jamais** estimées.

C'est le livrable central du projet : pour un budget donné, quelle force de
garantie est atteignable, et sur quelle fraction du travail.

---

## La table

| # | domaine / vérificateur | couverture | précision | coût par vérification | source |
|---|---|---|---|---|---|
| 1 | **empirique** — dispersion des tirages, seuil 0.70 | 57.6 % | **70.6 %** | ~0 | étape 10 |
| 2 | **arithmétique** — substitution, modulo, produit | **95.2 %** | 100 % | < 1 ms | étape 11 |
| 3 | **code** — syntaxe (`compile`) | *en cours* | — | ~0 ms | chantier 1 |
| 4 | **code** — exécution sans exception | *en cours* | — | **~40 ms** | chantier 1 |
| 5 | **code** — tests fournis par le benchmark | *en cours* | 100 %\* | **~40 ms** | chantier 1 |
| 6 | **Lean + Mathlib** — imports ciblés | **20.0 %** | 100 % | **14 s** | étape 12 |
| 7 | **Lean + Mathlib** — `import Mathlib` | non mesurée | 100 % | **187-220 s** | étape 12 |

\* « précision 100 % » signifie ici **conforme à la spécification exécutable
fournie**, pas correct au sens d'un noyau de preuve. Ce que les tests ne disent
pas n'est pas vérifié. C'est la différence de fond entre la ligne 5 et la ligne 6.

---

## Ce que la table dit déjà

**La ligne 1 est d'une autre nature.** C'est le seul régime où la précision n'est
pas garantie : on gradue une confiance, on ne vérifie rien. 70.6 % de précision au
prix de 42 % d'abstention. Toutes les autres lignes ont une précision de 100 %
relative à leur vérificateur — la question n'y est plus « ai-je raison ? » mais
« sur quelle fraction puis-je répondre, et à quel prix ? ».

**Le coût varie d'un facteur 350 entre les vérificateurs utilisables.**
40 ms pour exécuter des tests, 14 s pour vérifier une preuve Lean ciblée. Et un
facteur 15 supplémentaire si l'on donne au noyau un contexte non borné (ligne 7) :
le coût est une propriété du **contexte chargé**, pas du vérificateur.

**La couverture s'effondre quand le modèle n'est pas du domaine.** 20 % en Lean
avec un généraliste de 1,5 B, contre 95.2 % en arithmétique. Ce n'est pas une
propriété du régime formel : c'est le coût d'entrée d'un modèle spécialisé, non
payé ici.

**Rejeter coûte plus cher qu'accepter** — 14.0 s pour un candidat du modèle contre
6.0 s pour une preuve canonique, soit 2,3×. Les tactiques invalides déclenchent des
recherches longues avant d'échouer. Le surcoût croît donc avec le taux d'échec :
le pire couplage possible pour une politique de filtrage.

---

## Les deux lois mesurées

**1. `couverture = 1 − part systématique`** (étape 11)
Dès qu'au moins un tirage est correct, le vérificateur le trouve. L'agrégation, en
comparaison, ne capture qu'une fraction du stochastique — 95.2 % contre 76.2 %
pour un vote majoritaire sur le même corpus. C'est la différence entre **vérifier**
et **graduer**.

**2. Le rendement de l'agrégation suit la part stochastique** (étapes 10 et 10-bis)

| modèle et corpus | part stochastique | réduction d'erreur par le vote |
|---|---|---|
| GPT-2 small, factuel | 56 % | 25.3 % |
| Qwen2.5-1.5B, factuel | 100 %\*\* | 70.2 % |

\*\* plafond de corpus : les questions, écrites pour GPT-2, ne contiennent plus de
difficulté pour ce modèle. Non comparable à la ligne précédente.

---

## Ce qui manque encore

- **Lignes 3 à 5** — le run est en cours. Trois contrôles ont été déclarés avant
  lancement : couverture G2 supérieure au tirage unique ; identité de la loi 1
  retrouvée ; décroissance G4 ≥ G3 ≥ G2 (violation = bug, pas résultat).
- **Ligne 7** — la couverture avec contexte global n'a pas été mesurée : à
  187-220 s par candidat, le run aurait duré vingt heures.
- **La boucle de réparation** (chantier 3). NL2VC-60 (arXiv 2604.22601) rapporte
  0 % → 81.82 % par feedback itératif du vérificateur. Si cela se reproduit ici, la
  loi 1 cesse d'être une borne : la part systématique devient partiellement
  réductible. C'est le résultat qui déplacerait le plus la table.
- **L'indépendance du vérificateur** (chantier 2). Toutes les lignes du tableau
  supposent un vérificateur indépendant du générateur. La valeur d'une
  vérification circulaire — tests écrits par le modèle qui a écrit le code — n'est
  pas mesurée, et aucune publication ne la chiffre.
