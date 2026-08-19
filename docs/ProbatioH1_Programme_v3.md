# ProbatioH1 — Descriptif complet du programme

> Source : texte fourni par Lamar le 19/08/2026. Archivé verbatim.
> Audit de statut des énoncés : voir `log.md`, entrée 2026-08-19 (nuit).

## Résumé exécutif
ProbatioH1 est un système de certification paramétrée des trajectoires neuronales.
Il ne prédit pas la vérité d'une réponse ; il calcule couche par couche le niveau
de récupérabilité de la trajectoire dans l'espace latent, certifie soit
l'intervention possible (avec sa preuve), soit l'abstention nécessaire (avec sa
justification), et jamais une confiance non fondée.

## I. Le no-go informationnel
Dans un monde ouvert, quand plusieurs mondes possibles sont compatibles avec les
observations mais exigent des réponses incompatibles, l'intersection des réponses
garanties est vide. Aucun agent limité ne peut garantir la vérité absolue.
Axiome fondateur : quand l'intersection est vide, la seule réponse certifiée est
l'abstention.

## II. Genèse empirique — de l'hypothèse du dwell à la dérive
GPT-2 small, 50 prompts (25 factuels / 25 hallucinatoires) :
1. Dwell absolu (v1) : constant, AUC = 0.500.
2. Dwell fenêtré (v2) : quasi-dégénéré.
3. Dwell relatif à la population (v3) : AUC = 0.628, p = 0.085. Non significatif.
→ Hypothèse du « temps de séjour au col » RÉFUTÉE. Le modèle ne s'attarde pas,
il dérive vers un autre bassin.

Signal réel : `mean_curvature` AUC = 0.823 (p = 0.005) · `ratio_dist` +
`dist_hallucination` = 47 % de l'importance RF · 10 features combinées
AUC = 0.939 (p = 0.005).

Redécouvertes honnêtes : `mean_curvature` redécouvre Chain-of-Embedding (Wang et
al., ICLR 2025) ; les distances aux centroïdes redécouvrent Hallucination Basins
(2026). La valeur revendiquée est le couplage et le protocole de validation.

## III. Les cinq fondations épistémologiques
1. Le no-go — l'intersection peut être vide, il faut savoir s'arrêter.
2. L'île de certitude — certaines propriétés structurelles sont préservées par
   tous les mondes possibles.
3. La forme normale — confluence + terminaison + observabilité = canon atteignable.
4. La critique — bassin factual ≠ vérité ; il faut un pont formel α : H → Q.
5. L'irréversibilité graduée — ∂V dépend des moyens U, des infos E, du budget K.

## IV. Architecture formelle
- H = ℝⁿ : espace neuronal. Q = {PROUVÉ, RÉFUTÉ, INDÉTERMINÉ} : espace épistémique.
- α : H → Q, pont d'abstraction. Théorème de Solidité visé : si α(h) = PROUVÉ,
  alors il existe des preuves explicites E et un système formel F tels que
  E ⊢_F φ(h).

13 axiomes, tels que classés par l'auteur :
- P1 (Hypothèse) gabarit exponentiel des normes · P2 (Axiome) normalisation z-score
- G1 (Axiome) trajectoire discrète · G2 (Axiome) courbure discrète κ(l) ·
  G3 (Hypothèse) bassins comme sous-variétés
- D1 (Hypothèse) convergence unique · D2 (Conjecture) point de commitment k* ·
  D3 (Théorème) intervention minimale I telle que α(I(h)) = PROUVÉ pour h ∈ V_robuste
- V1 (Axiome) garde-fou synthétique triple · V2 (Axiome) certificat de données
- Det1 (Théorème empirique) complémentarité position/dynamique ·
  Det2 (Résultat négatif) le dwell seul ne suffit pas

## V. Niveaux de certification G0-G6
| Niveau | Nom | Signification | Action |
|---|---|---|---|
| G0 | TRAJECTOIRE_SÛRE | dans V_robuste | continue |
| G1 | CORRECTION_LÉGÈRE | steering ε_min suffit | perturbation minimale certifiée |
| G2 | CORRECTION_SOUTENUE | dérive avancée | steering maximal + monitoring |
| G3 | RÉCUPÉRABLE_AVEC_INFO | ∃ E' rouvrant la porte | suspend, vérification externe |
| G4 | RÉCUPÉRABLE_PAR_REDÉMARRAGE | trajectoire contaminée | rollback au checkpoint k* |
| G5 | ABSTENTION_CERTIFIÉE | intersection vide sous U,E,K | s'arrête |
| G6 | CONSÉQUENCE_IRRÉVERSIBLE | action déjà produite | journalise + alerte |

## VI. ProbatioLang
Langage déclaratif unifiant géométrie différentielle, statistiques empiriques et
preuves (blocs `model`, `feature`, `theorem`).

## VII. Protocole de validation
Garde-fou synthétique triple : contrôle positif (AUC > 0.75), contrôle négatif
(labels permutés, AUC < 0.75), recouvrement (couches flaguées vs signal injecté,
> 50 %).
DataTheorem : hash corpus + hash code + résultat + chaîne de vérification.

## VIII. Objectif
Réduction des hallucinations par honnêteté épistémique : détecter la dérive avant
le point de non-retour, suspendre quand l'information manque, s'abstenir quand
aucune garantie n'est possible, certifier que l'intervention est minimale.

## IX. Le test irréductible (statut : en attente)
AUC de classification en n'utilisant que les couches 0..k, pour k de 2 à 12.
- AUC > 0.75 dès k = 6-8 → ProbatioH1 tient, fenêtre d'intervention réelle.
- décollage seulement à k = 10-12 → ProbatioH1 réduit à G5-G6 (abstention/post-hoc).
- plat jusqu'à k = 11 puis saut → réfuté dans sa forme actuelle.

## X. Ce que ProbatioH1 n'est pas
Pas un détecteur post-hoc · pas une boîte noire entraînée · pas un patch sur les
poids · pas une garantie de vérité absolue · pas un assistant de preuve
généraliste, mais un système de preuve dédié aux trajectoires neuronales.

## XI. Livrables
1. Spécification formelle v3 · 2. Bibliothèque logicielle · 3. Corpus de
DataTheorems · 4. ProbatioLang · 5. Papier « ProbatioH1: A Domain-Specific Proof
System for Neural Latent Geometry ».
