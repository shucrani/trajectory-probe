# trajectory-probe

**Question.** La géométrie de la trajectoire d'un état caché à travers les couches
d'un Transformer porte-t-elle un signal exploitable de l'hallucination — et ce
signal survit-il à une comparaison avec les métriques déjà publiées ?

Statut : **exploratoire, avec un confond de dataset non résolu** (§ 3). Aucun
résultat n'est établi comme portant sur l'hallucination.

---

## 1. Résultats mesurés (GPT-2 small, n = 50, CV 5 plis fold-safe, 200 permutations)

| Feature / méthode | AUC | p | Sens | Statut |
|---|---|---|---|---|
| `max_dwell_time` isolé | 0.628 | 0.085 | Hallu > Factual (faible) | **non significatif** |
| `mean_curvature` isolée | 0.823 | 0.005 | **Factual > Hallu** | significatif |
| 4 features (curvature, velocity, dist, ratio) | 0.938 | 0.005 | — | significatif |
| Vecteur complet (10 features) | 0.939 | 0.005 | dominé par `ratio_dist`, `dist_hallucination` | significatif |
| **CoE-R + CoE-C** (baseline publiée, Wang et al. ICLR 2025) | **0.873** | 0.005 | Factual > Hallu | **répliquée** |

Combiner nos features avec CoE apporte **+0.0008** d'AUC. C'est le même signal.

`mean_curvature` et `max_velocity` corrèlent à r = 0.81 : le « signal à 4
features » a probablement 2 dimensions réelles, pas 4.

## 2. Ce qui est réfuté

**L'hypothèse fondatrice — le dwell time au « col » — est morte.** p = 0.085 à
n = 50, après trois cycles de correction (min-max par trajectoire → fenêtre
couches 4-12 → normalisation relative à la population, fold-safe).

Cause identifiée dans les nombres bruts : GPT-2 a une **forme universelle** de
courbure/vitesse par couche (haute 0-1, creux net 3-4, remontée, explosion 10-12),
**identique chez les deux classes**. Le col défini comme « courbure et vitesse
faibles » coïncide avec ce creux universel → ne peut rien discriminer par
construction.

C'est un résultat négatif propre, obtenu avec un garde-fou synthétique qui a
répliqué l'échec réel avant de proposer le correctif. Il se garde et s'écrit.

## 3. Le confond non résolu — à traiter avant tout le reste

Les 25 prompts `label=1` **ne sont pas des hallucinations produites par GPT-2**.
Ce sont des **énoncés faux écrits à la main**. Le modèle ne génère rien ici : il
lit un texte. Ce qui est mesuré n'est donc pas « le modèle va-t-il halluciner »
mais « comment le modèle traite un texte vrai versus un texte faux qu'on lui
donne ». Ce sont deux tâches différentes.

Pire, les deux classes diffèrent systématiquement sur des dimensions qui n'ont
rien à voir avec la véracité :

- **Longueur.** Factuels : 5-12 mots (« Shakespeare wrote Hamlet. »).
  Hallucinatoires : 12-20 mots (« The Berlin Wall was rebuilt in 2015 as a
  tourist attraction and remains the tallest wall on Earth. »). Séparation
  quasi parfaite sur ce seul axe.
- **Marqueurs évidentiels.** « According to recent studies », « Scientists
  confirmed in », « Researchers proved that », « Recent archaeological evidence
  shows » — présents **uniquement** dans la classe 1.
- **Dates.** 13 des 25 prompts hallucinatoires contiennent une année récente
  (2018-2024) ; presque aucun factuel.
- **Format mélangé.** Deux prompts sont des continuations ouvertes (« The first
  person to walk on Mars was », « The capital of France is »), les 48 autres sont
  des assertions complètes — et les deux formats sont répartis entre les classes.

Un AUC de 0.938 sur ce dataset est compatible avec un classifieur qui ne détecte
que **la longueur et le registre stylistique**. Le sens contre-intuitif du signal
(courbure **plus élevée** chez les factuels) est d'ailleurs ce qu'on attendrait
d'un effet de longueur, pas d'un effet de véracité.

**Ce confond touche aussi la baseline CoE** : elle est calculée sur les mêmes
prompts. « Notre feature réplique CoE » signifie peut-être seulement « les deux
ramassent le même artefact ».

## 4. Ce qui n'est que simulation

Régimes factuel/créatif/hallucinatoire, paysage de potentiel U(z), certificats de
navigation V3.1/V4, carte de l'espace latent, agent topologique v3.3, et les
12 axiomes ProbatioH1 (modèle jouet d = 32, L = 8) : calculés sur un paysage
**inventé**, pas mesuré. Ces figures valident le simulateur contre lui-même.

→ `figures/gpt2/` = mesuré · `figures/synthetic/` = simulé. Ne jamais mélanger
dans un même document sans étiquette.

Statut du cadre ProbatioH1 (G0-G6, ∂V paramétrée par U/E/B/K) : **non testé**.
Aucune mesure de U, E, B ou K n'existe. Le « théorème de certification
paramétrée » est une taxonomie, pas une preuve. L'exemple « 87 % à la couche 9,
HaluEval × Llama-3-8B » est **fictif** — à ne jamais citer comme résultat.

## 5. Ordre des tests

**D'abord les contrôles de confond** (§ 3). Sans eux, tout le reste mesure
peut-être la longueur des phrases. Coût : quelques minutes sur les trajectoires
déjà extraites.

- **C1** — classifier sur le **nombre de tokens seul**. Si AUC ≳ 0.85, tous les
  résultats de la § 1 sont suspendus.
- **C2** — réapparier les deux classes en longueur (± 1 token) et en format, puis
  refaire tourner § 1. L'AUC survit-elle ?
- **C3** — passer à un dataset apparié par construction : TruthfulQA ou HaluEval,
  où vrai et faux partagent la même question porteuse.
- **C4** — le vrai design : laisser GPT-2 **générer**, annoter la sortie comme
  hallucinée ou non, et classifier depuis la trajectoire du prompt. C'est la seule
  version qui mesure ce que le projet prétend mesurer.

**Ensuite seulement**, le test de progressivité (couches 0..k, k = 2..12) qui
décide si la gradation G0-G6 a un fondement. Il est bon, mais une progressivité
magnifique sur un artefact de longueur reste un artefact.

## 6. Condition d'abandon (kill-switch)

- **K1** — dwell time : **déjà tombé** (p = 0.085, n = 50). Acté.
- **K2** — CoE fait aussi bien : **partiellement tombé**. CoE = 0.873 vs 4
  features = 0.938, écart non significatif à n = 50 (σ_AUC ≈ 0.06), et la
  combinaison n'apporte rien. Il n'y a pas de découverte, au mieux une
  réplication indépendante sur GPT-2 small.
- **K3** — pas de réplication sur un second modèle : non testé.
- **K4** (nouveau) — si C1/C2 montrent que la longueur explique le signal, le
  résultat empirique tombe entièrement et le projet se réduit à son résultat
  négatif (§ 2), qui reste publiable seul.

**Revue : 19/09/2026.** Sans contrôles de confond exécutés d'ici là, projet
déclaré dormant.

## 7. Positionnement honnête d'un éventuel écrit

Réplication méthodologiquement renforcée de Chain-of-Embedding sur GPT-2 small,
assortie d'une réfutation explicite de l'hypothèse de dwell time — **et** d'un
audit de confond de dataset. Pas une découverte. C'est déjà une contribution
réelle : peu de gens publient l'hypothèse qui meurt.

## Structure

```
notebooks/   protocole GPT-2 (PCA fold-safe, permutation, dwell isolé, baseline CoE)
docs/        ProbatioH1_Recap (synthèse de projet) + rapport v2 axiomatique
figures/gpt2/       mesures réelles
figures/synthetic/  simulations — ne valident rien du réel
results/     sorties brutes horodatées des runs (vide : aucun run archivé)
src/         code stabilisé (à extraire du notebook)
log.md       journal daté
```

**Manquant au dépôt** (existe ailleurs, à récupérer) :
`topological_navigation_agent_v33.py`, `validate_pipeline_synthetic.py`,
`validate_saddle_score.py`, et les sorties brutes du run n = 50.
