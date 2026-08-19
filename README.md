# trajectory-probe

**Question.** La géométrie de la trajectoire d'un état caché à travers les couches
d'un Transformer porte-t-elle un signal exploitable de l'hallucination — et ce
signal survit-il à une comparaison avec les métriques déjà publiées ?

Statut : **exploratoire**. Aucun résultat n'est établi. Ce README dit ce qui est
mesuré, ce qui est réfuté, et ce qui n'est encore que de la simulation.

---

## Ce qui est déjà réfuté (le résultat le plus solide du lot)

L'hypothèse fondatrice — *les prompts hallucinatoires s'attardent plus longtemps
dans une zone ambiguë (« col ») entre les couches* — **ne tient pas** sur GPT-2
small, après trois tentatives de correction :

1. `max_dwell_time` constant sur 20 prompts (std = 0.000, AUC dwell seul = 0.500,
   importance = 0.000) — normalisation min-max par trajectoire.
2. Fenêtre couches 4-12 + normalisation globale fold-safe : saturation seulement
   partiellement réduite.
3. Diagnostic brut couche par couche : GPT-2 a une **forme universelle** de
   courbure/vitesse (haute aux couches 0-1, creux net aux couches 3-4, remontée,
   explosion aux couches 10-12), **identique chez les prompts factuels et
   hallucinatoires**. Le « col » tel que défini coïncide avec ce creux universel.
   Il ne peut rien discriminer *par construction*.
4. Après correctif relatif-à-la-population : dwell isolé toujours non significatif
   (p = 0.234, n = 20).

**Conclusion provisoire : le col n'est pas un discriminant.** C'est un résultat
négatif propre, obtenu avec un garde-fou synthétique qui a d'abord répliqué
l'échec réel avant de proposer le correctif. Il est publiable comme tel et ne
doit pas être enterré sous le reste.

## Ce qui reste debout, sous réserve

Sur les mêmes 20 prompts, le vecteur complet à 10 features atteint
**AUC = 0.890 (p = 0.005, 200 permutations, CV fold-safe)** — mais le signal vient
de `mean_curvature`, `max_curvature`, `dist_factual`, `max_velocity`, `ratio_dist`,
**pas** du dwell time (importance ≈ 0.02).

Réserves à ne pas oublier avant tout claim :
- n = 20, 10 features, Random Forest — surface d'overfit large.
- Les versions v1 → v2 → v3 ont itéré en regardant **les mêmes 20 points**. Le
  p-value ne couvre pas ces degrés de liberté du chercheur.
- Le dataset élargi à 50 prompts **n'a jamais été exécuté** (le notebook ne
  contient aucun output).
- La comparaison à la baseline publiée **Chain-of-Embedding** (Wang et al.,
  ICLR 2025 — CoE-R / CoE-C) est codée mais **jamais lancée**. C'est le juge :
  si `mean_curvature` ne bat pas CoE, il n'y a pas de contribution empirique,
  seulement une reformulation.

## Ce qui n'est que simulation

Tout ce qui touche aux **régimes** (factuel / créatif / hallucinatoire), au
**paysage de potentiel U(z)**, aux **certificats de navigation V3.1 / V4**, aux
scores ADMISSIBLE / REJECTED et à la **carte de navigation de l'espace latent**
est calculé sur un paysage **inventé** (mélange de gaussiennes choisi à la main),
pas mesuré sur un modèle. Ces figures valident le simulateur contre lui-même.

→ `figures/synthetic/` = simulation · `figures/gpt2/` = mesures réelles.
Ne jamais mélanger les deux dans un même document sans étiquette.

Idem pour `docs/probatioh1_v2_report.txt` : 12 axiomes + modèle jouet (d=32, L=8,
trajectoires générées). Les papiers tiers qui y sont cités sont **compatibles**
avec les axiomes ; ils ne les valident pas. Une compatibilité narrative n'est pas
une preuve.

## Condition d'abandon (kill-switch)

Ce projet s'arrête, ou change de question, si **l'un** de ces faits est établi :

- **K1** — sur ≥ 50 prompts stratifiés, l'AUC du sous-ensemble de 4 features
  tombe sous 0.65, ou le test de permutation donne p > 0.05.
- **K2** — CoE-R / CoE-C (baseline publiée) fait aussi bien ou mieux que les
  features géométriques proposées, sur le même dataset et le même protocole.
- **K3** — le signal ne se réplique pas sur un second modèle (`gpt2-medium`, puis
  une famille différente).

Si K2 tombe seul : le cadre reste utile comme reformulation pédagogique, mais il
n'y a pas de papier. Le dire, ne pas le contourner.

**Échéance de revue : 19/09/2026.** Si aucun run réel n'a été exécuté d'ici là,
le projet est déclaré dormant — pas « en cours ».

## Structure

```
notebooks/   protocole GPT-2 (PCA fold-safe, permutation, dwell isolé, baseline CoE)
docs/        rapport axiomatique ProbatioH1 v2 (modèle jouet)
figures/gpt2/       mesures réelles
figures/synthetic/  simulations — ne valident rien du réel
results/     sorties horodatées des runs réels (vide : aucun run archivé)
src/         code extrait du notebook quand il sera stabilisé
log.md       journal daté des décisions et des runs
```

## Prochaine action, unique

Exécuter le notebook tel quel sur les 50 prompts, archiver la sortie brute dans
`results/`, et **lire d'abord** `auc_dwell_only`, puis la comparaison CoE.
Rien d'autre — pas de nouvelle feature, pas de nouvelle figure, pas de nouvel
axiome — avant que ces deux nombres existent.
