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
