# Journal — trajectory-probe

Une entrée par run et par décision. Datée. Jamais réécrite : on ajoute, on ne
corrige pas l'historique.

---

## 2026-08-19 — Ouverture du projet

Création du dépôt. Le matériau existait, éparpillé et non versionné :
- notebook GPT-2 (`~/Downloads/`, 02/08, aucun output stocké — jamais exécuté depuis ce fichier)
- rapport ProbatioH1 v2 + figure (`~/Downloads/`, 05/08)
- 7 PNG (`~/Desktop/GPT2 Navigation/`, 02/08) sans code associé
Tout a été **copié** ici ; les originaux restent en place.

**État des connaissances au moment de l'ouverture**
- Réfuté : le dwell time au « col » ne discrimine pas (std=0 → correctifs v2/v3 →
  p=0.234 isolé, n=20). Cause identifiée : forme universelle de courbure/vitesse
  par couche chez GPT-2, identique aux deux classes.
- Non confirmé : AUC=0.890 (p=0.005) sur le vecteur complet, n=20, porté par
  `mean_curvature` et les distances aux centroïdes.
- Jamais exécuté : dataset élargi à 50 prompts, comparaison à la baseline CoE.
- Simulation pure : régimes, potentiel U(z), certificats V3.1/V4, carte latente,
  et les 12 axiomes ProbatioH1 (modèle jouet d=32, L=8).

**Décision** — aucune nouvelle construction théorique tant que deux nombres
n'existent pas : `auc_dwell_only` et la comparaison CoE, sur ≥50 prompts.

**Kill-switch posé** : K1 / K2 / K3 (voir README). Revue le 19/09/2026.

**Point non tranché, remonté et non décidé à ta place** : la ligne axiomatique
(ProbatioH1, 12 axiomes) et la ligne empirique visent-elles le même objet ? Les
axiomes présupposent des bassins et un col ; la mesure vient de réfuter le col.
Soit les axiomes sont révisés d'après la mesure, soit ils deviennent un objet
séparé assumé comme théorique. Tant que ce n'est pas tranché, les deux
progressent en se contredisant.

---

## 2026-08-19 (soir) — Intégration de `ProbatioH1_Recap.docx`

Le récapitulatif de projet apporte les résultats du run **n = 50**, qui n'étaient
pas dans le notebook (aucun output stocké). README réécrit en conséquence.

**Corrections des chiffres portés ce matin** (qui venaient du run n = 20) :
- dwell isolé : p = 0.085 à n = 50 (et non 0.234 à n = 20) — toujours non signif.
- `mean_curvature` isolée : AUC 0.823, p = 0.005, sens **Factual > Hallu**
- 4 features : 0.938 · 10 features : 0.939 · **CoE : 0.873**

**K2 est partiellement tombé.** CoE-R/CoE-C, baseline publiée, atteint 0.873 là
où les 4 features atteignent 0.938 — écart non significatif à n = 50 (σ_AUC ≈
0.06), et leur combinaison n'ajoute que +0.0008. Même signal. Pas de découverte ;
au mieux une réplication indépendante sur GPT-2 small.

**Nouveau problème identifié, non relevé dans le récapitulatif : confond de
dataset.** Lecture des 50 prompts (cellule 6 du notebook) :
- les `label=1` sont des **énoncés faux écrits à la main**, pas des hallucinations
  générées par le modèle. La tâche mesurée n'est pas celle annoncée.
- factuels 5-12 mots vs hallucinatoires 12-20 mots — séparables sur la longueur
  seule.
- marqueurs évidentiels (« According to recent studies », « Scientists confirmed
  in », « Researchers proved that ») présents uniquement en classe 1.
- 13/25 hallucinatoires portent une année 2018-2024, presque aucun factuel.
- deux formats mélangés (continuation ouverte vs assertion complète).

Le sens contre-intuitif du signal (courbure plus élevée chez les **factuels**)
est ce qu'on attendrait d'un effet de longueur. Le confond touche aussi CoE,
calculée sur les mêmes prompts.

**Décision** : les contrôles de confond C1-C4 passent **avant** le test de
progressivité couche par couche proposé en § 5 du récapitulatif. Une
progressivité mesurée sur un artefact de longueur reste un artefact. Ajout du
kill-switch **K4**.

**Toujours non tranché** (rappel) : ligne axiomatique vs ligne empirique. Le
récapitulatif est lucide là-dessus (∂V, G0-G6, théorème : « non testé »,
« hypothèse », « pas une preuve »), et signale de lui-même que l'exemple
« 87 % couche 9, HaluEval × Llama-3-8B » est **fictif**. Cette honnêteté est
acquise ; la question reste de savoir si les axiomes se révisent d'après la
mesure ou deviennent un objet théorique assumé.

---

## 2026-08-19 (nuit) — Programme ProbatioH1 v3 : audit de statut des énoncés

Document archivé verbatim : `docs/ProbatioH1_Programme_v3.md`.

### Régression d'honnêteté entre deux documents du même jour

| Énoncé | Récapitulatif (§4.2) | Programme v3 (§IV) |
|---|---|---|
| Certification paramétrée | « **non prouvé** — taxonomie, pas une preuve dérivée d'axiomes » | **D3 (Théorème)** |
| Complémentarité position/dynamique | non listé | **Det1 (Théorème empirique)** |
| Pont α : H → Q | « **non vérifié ici** » | présenté comme architecture acquise |

Le récapitulatif était plus juste. Un énoncé dont les termes primitifs ne sont pas
définis opérationnellement (V_robuste, I minimale, α) n'est pas un théorème : il
n'est même pas encore falsifiable. **Ce reclassement est le mécanisme exact qui a
coûté CARRT** (formalisme reprenant le dessus sur le substrat non testé). À
surveiller à chaque version.

Statut à conserver : D3 = **conjecture de programme**. Det1 = **observation**
sur n = 50, affaiblie par r = 0.81 entre `mean_curvature` et `max_velocity` et
par le +0.0008 de la combinaison avec CoE.

### Le confond de dataset n'est pas intégré

La § II du programme réutilise AUC = 0.939 comme fondation, et la § IX construit
le test irréductible dessus, sans le contrôle de longueur (C1). Tant que C1 n'est
pas exécuté, ces chiffres n'ont pas de statut. Priorité inchangée.

### Le trou central : α n'existe pas

Tout le vocabulaire de certification (G0-G6, « certificat », « preuve »,
« solidité ») présuppose α : H → Q avec le théorème de solidité. Personne ne sait
construire α depuis des hidden states. Sans lui, G0-G6 sont des **seuils sur un
classifieur**, pas des certificats. Un seuil renommé « certificat » reste un seuil.

Écart de vocabulaire à corriger : un AUC de 0.75 à la couche 6 = 25 % d'erreur.
On ne certifie pas avec ça. « Certifier » exige une garantie (borne, couverture),
pas un score.

### Voisinage à vérifier avant tout claim de nouveauté

- **Selective prediction / reject option** — Chow (1970), littérature continue
  depuis. C'est G5 sous un autre nom.
- **Conformal prediction** (Vovk et al.) — donne des garanties de couverture
  distribution-free et prouvées, sous échangeabilité. C'est le cadre qui délivre
  réellement ce que ProbatioH1 promet.
- **Hallucination Basins (2026)**, **Chain-of-Embedding (ICLR 2025)** — déjà
  identifiés comme redécouverts.

### D2 est testé par le mauvais test

§ IX (AUC sur couches 0..k) est **corrélationnel**. D2 (point de commitment
irréversible) est une affirmation **causale**. Le test correspondant est une
intervention : perturber à la couche k, mesurer si la classe finale change, et
comparer les taux de corruption et de correction (le design d'Akarlar, déjà cité
dans le rapport v2). Une AUC croissante n'établit aucune irréversibilité.

### Décisions

1. Ordre inchangé : **C1 (longueur) avant tout**, puis § IX sur dataset corrigé,
   puis test causal pour D2.
2. **Gel** de ProbatioLang, de la spécification formelle v3 et du papier DSPS
   jusqu'à ce qu'un résultat empirique survive à C1/C2.
3. Reclasser D3 en conjecture et Det1 en observation dans toute version future.
4. Le garde-fou synthétique triple est identifié comme **l'actif le plus solide**
   du programme (voir README § 7) — à vérifier contre la littérature avant de
   revendiquer « sans équivalent ».

---

## 2026-08-19 (nuit, suite) — Vérification des références + figure `stability`

`probatioh1_v2_report (1).txt` et `probatioh1_v2_analysis (1).png` sont
**identiques** (même MD5) aux fichiers déjà archivés. Seule nouveauté :
`probatioh1_v2_stability.png`.

### La figure `stability` ne contient pas de données

Titrée « Données DeepSearch », elle ne reproduit rien de mesuré : droites
parfaitement linéaires, courbes lisses sans n ni barre d'erreur, triangle
AUROC symétrique dessiné sur 9 couches alors que le rapport v2 situe le pic
ICR aux couches 10-15 sur 28. L'encadré coche ✓ des axiomes classés
« hypothèse » et « conjecture » dans le programme v3. Archivée sous
`figures/synthetic/ILLUSTRATION_probatioh1_stability_NON-MESURE.png`.

### Vérification web des références (détail dans `docs/REFERENCES.md`)

- **Akarlar 2026 EXISTE** — arXiv 2604.15400, code sur GitHub. 87.5 % (couche 20)
  / 33.3 % (couche 24) sur 28 couches : confirmés.
- **Hallucination Basins EXISTE** — arXiv 2604.04743.
- **ICR Probe : non retrouvé sous ce nom.** Voisins réels : PRISM (ACL 2025),
  ReDeEP (ICLR 2025). À re-sourcer avant citation.
- **ARS, H-Neurons, Global Evolutionary Steering : non vérifiés.**
- **Découvert : arXiv 2606.12476**, « Quickest Detection of Hallucination Onset:
  Delay Bounds and Learned CUSUM Statistics ». Traite le test irréductible (§ IX)
  avec des bornes de délai prouvées, par détection séquentielle classique.
  Antériorité directe sur la certification précoce.

### Deux conséquences

1. **« L'interstice est vierge » est faux.** Avril-juin 2026 : bassins, asymétrie
   causale, interventions sur attracteurs, détection séquentielle bornée. Le champ
   est chaud. Ce qui reste éventuellement libre est plus étroit — le garde-fou
   triple et la gradation — et seulement s'ils sont testés.

2. **Akarlar résout notre confond.** Son protocole *same-prompt bifurcation*
   (même prompt, échantillonnages répétés, classes définies par ce que le modèle
   produit réellement) existe explicitement pour isoler la dynamique des confonds
   de prompt. L'adopter règle C1-C4 d'un coup et rend les résultats comparables.
   **Décision : abandonner le dataset de 50 prompts écrits à la main.**

---

## 2026-08-19 (nuit) — C1 EXÉCUTÉ : le confond est confirmé

Script `src/c1_surface_confound.py`, sortie `results/c1_surface_confound_20260819.txt`.
Aucun modèle chargé. AUC exacte par rangs (Mann-Whitney), p par permutation
bilatérale à 20 000 tirages, seed 42. Les prompts sont lus directement depuis le
notebook, pas recopiés.

| Propriété de surface | AUC | p | factuels | hallucinatoires |
|---|---|---|---|---|
| `n_words` | **0.939** | 0.00005 | 7.28 ± 1.99 | 11.84 ± 2.39 |
| `n_chars` | **0.942** | 0.00005 | 42.9 ± 12.0 | 72.0 ± 11.2 |
| `has_year` | 0.720 | 0.0009 | 0.04 | 0.48 |
| `has_evidential` | 0.620 | 0.023 | 0.00 | 0.24 |

**Comparaison directe :**

| Méthode | AUC |
|---|---|
| Vecteur complet, 10 features sur hidden states | 0.939 |
| **Nombre de mots, sans modèle** | **0.939** |
| **Nombre de caractères, sans modèle** | **0.942** |
| Baseline CoE (états bruts) | 0.873 |
| `mean_curvature` isolée | 0.823 |

**Verdict.** Sur ce dataset, la géométrie des trajectoires n'apporte rien qu'un
comptage de caractères ne donne déjà. Les deux métriques géométriques sont
*inférieures* au contrôle trivial. **K4 est tombé.**

Ce résultat n'invalide pas le projet : il invalide le dataset. Le résultat
négatif sur le dwell time (§ 2 du README) reste valide — il était négatif, donc
non menacé par un confond qui aurait aidé à séparer les classes.

Il invalide en revanche la § II du programme ProbatioH1 v3 (« le signal réel »)
et rend caduque la § IX (test irréductible) telle qu'écrite : mesurer la
progressivité couche par couche de ce signal reviendrait à mesurer à quelle
couche GPT-2 encode la longueur de la phrase.

**Décision confirmée** : passer au protocole *same-prompt bifurcation*
(Akarlar, arXiv 2604.15400) où les deux classes viennent du même prompt et ne
peuvent donc pas différer en surface. Un deep search est en cours pour cadrer
l'implémentation et le choix des datasets.

**Limite** : le comptage en mots approxime le comptage en tokens BPE. À refaire
avec le tokenizer GPT-2 une fois `transformers` installé — mais avec un écart de
cette taille (7.3 mots contre 11.8), la conclusion ne bougera pas.
