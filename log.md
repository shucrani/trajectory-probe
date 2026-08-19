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
