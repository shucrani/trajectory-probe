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

---

## 2026-08-19 (nuit) — Étape 1 : GPT-2 small bifurque à 33.3 %

Environnement monté : `.venv` (Python 3.12.13 via uv), torch 2.13, transformers
5.15, scikit-learn. Script `src/bifurcation_probe.py` : N = 20 complétions par
prompt, T = 0.7, 30 prompts factuels à réponse courte, exécution MPS.

**Résultat : 10/30 prompts bifurquent (33.3 %)**, contre 27/61 (44.3 %) chez
Akarlar sur Qwen2.5-1.5B — un modèle douze fois plus gros. Le protocole est
praticable à cette taille.

### La première version de la classification était fausse

L'audit des complétions brutes a révélé deux défauts, corrigés :

1. **Substring naïf.** « Water freezes at a temperature of » → *"about 16 degrees
   C (about 110 degrees"* était compté **Correct**, parce que `"0"` est un
   substring de `"110"`. Les 15 « Correct » de ce prompt étaient faux. Corrigé
   par correspondance à frontière de mot.
2. **Non-réponses comptées comme hallucinations.** GPT-2 small n'est pas
   instruction-tuned : il *continue le texte* au lieu de répondre. « The capital
   of Italy is **still a very popular place to be.** » n'est pas une
   hallucination, c'est une absence de réponse. Classe `NoAnswer` ajoutée —
   Hallucination exige désormais qu'une **entité** (nom propre ou nombre) absente
   du prompt soit assertée.

Sans ces corrections, le taux de bifurcation était juste par accident. C'est la
justification concrète d'avoir archivé les complétions brutes.

### Conséquence structurelle : la promesse forte de ProbatioH1 devient intestable

Dans le protocole same-prompt bifurcation, les deux classes viennent du **même
prompt**. Les hidden states du prompt sont donc **identiques** dans les deux
classes. Aucune feature calculée sur la trajectoire du prompt ne peut les
séparer : AUC = 0.5 par construction.

Ce n'est pas une limite du protocole, c'est un fait sur le phénomène. Si un même
prompt produit les deux issues, alors **l'information qui décide de l'issue n'est
pas dans le prompt** — elle est dans l'échantillonnage. La version forte de
ProbatioH1 (« certifier avant que la réponse ne soit produite », § V du
programme) est donc réfutée par construction sur les cas bifurquants.

Ce qui reste, et qui est testable : la divergence apparaît **dès le premier token
généré** (Akarlar). La question devient « à quel step la trajectoire s'engage-t-elle
irréversiblement ? » — c'est exactement D2, le point de commitment. La fenêtre
d'intervention existe, mais elle est *pendant* la génération, pas avant.

**Reformulation de la question du projet, à valider par Lamar :**
> ~~la trajectoire du prompt prédit-elle l'hallucination ?~~
> à quel moment de la génération l'engagement devient-il irréversible, et
> l'intervention y est-elle encore possible ?

### Suite

1. Extraire K = 6 trajectoires par classe sur les 10 prompts bifurquants
   (residual stream complet à chaque couche et chaque step) → 120 trajectoires.
2. Mesurer la divergence step par step et couche par couche.
3. Comparer à la sonde linéaire avant toute autre feature.
4. Option si le rendement devient limitant : Qwen2.5-0.5B-Instruct, qui répond
   réellement aux questions et tourne sur MPS.

---

## 2026-08-19 (nuit) — Étapes 2 et 3 : trajectoires extraites, carte de divergence

Reformulation validée par Lamar. Question du projet désormais : *à quel moment de
la génération l'engagement devient-il irréversible, et l'intervention y est-elle
encore possible ?*

**Extraction** (`src/extract_trajectories.py`) : 10/10 prompts bifurquants
exploités, K = 6 par classe, **120 trajectoires** `[120, 8 steps, 13 couches, 768]`,
60 Correct / 60 Hallucination. Entre 40 et 160 tirages par prompt pour atteindre
le quota. Sortie `results/trajectories_gpt2_20260819_2350.npz`.

**Carte** (`src/divergence_analysis.py`) : sonde linéaire (régression logistique
C = 0.01, standardisation fold-safe), CV **leave-one-prompt-out** — le prompt de
test n'est jamais vu à l'entraînement. Figure : `figures/gpt2/divergence_map.png`.

### 1. Contrôle de sanité : réussi exactement

Step 0, toutes couches : **AUC = 0.500** au flottant près. L'état du dernier
token du prompt est identique dans les deux classes, la sonde ne peut rien en
tirer. Le pipeline ne fuit pas, et le point structurel du tour précédent est
confirmé empiriquement : **rien dans le prompt ne prédit l'issue**.

### 2. Profil temporel : montée, pic, décroissance

| step | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| AUC moyenne | 0.50 | 0.62 | **0.87** | 0.84 | 0.81 | 0.72 | 0.68 | 0.70 |

La séparabilité culmine au **step 2** puis **décroît**. Ce profil est en tension
avec D1 (convergence vers un bassin attracteur stable) : deux bassins absorbants
distincts devraient maintenir ou accroître la séparation, pas la voir s'éroder de
0.87 à 0.70.

**Réserve, à lever avant toute conclusion** : la variance intra-classe croît
mécaniquement avec la longueur de génération, ce qui suffit à faire baisser une
AUC sans qu'aucun rapprochement des classes n'ait lieu. Distinguer les deux
demande de normaliser la distance inter-classes par la dispersion intra-classe
(effect size), pas de lire l'AUC brute. **Non fait à ce stade.**

### 3. Le résultat dur : la séparation est lexicale, pas géométrique

Au step 2 (le pic), le profil **par couche est plat** :

| couche | 0 (embedding) | 2 | 8-9 (max) | 12 |
|---|---|---|---|---|
| AUC | **0.84** | 0.89 | 0.89 | 0.86 |

La couche 0 des `hidden_states` de GPT-2 est la sortie de la couche
d'embedding — `wte + wpe`, avant tout bloc transformer. Elle encode donc
**uniquement l'identité et la position du token courant**, sans aucun traitement.

Elle atteint déjà 0.84. Les douze blocs transformer complets n'ajoutent que
**+0.05**.

Autrement dit : ce que la sonde sépare, c'est *quel token vient d'être émis*, pas
une dynamique inter-couches. Sur ce protocole, la géométrie des trajectoires
n'apporte quasiment rien au-dessus de la lecture du token. C'est le pendant, dans
le protocole propre, de ce que C1 avait montré dans le protocole confondu.

### 4. Test pré-spécifié

Step 7, couche 12 (cellule choisie **avant** de regarder la carte) :
AUC = **0.733**, H0 par permutation intra-prompt (200 tirages) centrée à 0.498
(σ = 0.073), **p = 0.005**. La séparation résiduelle en fin de génération est
réelle et significative — mais elle reste de nature lexicale au vu du point 3.

### Ce qui est établi, ce qui ne l'est pas

- **Établi** : le protocole est propre (contrôle 0.500) ; une séparation existe
  et culmine tôt (step 2) ; elle est portée dès l'embedding.
- **Non établi** : l'irréversibilité (D2). Une carte de séparabilité ne peut pas
  la trancher — elle mesure que les états diffèrent, pas qu'on ne peut plus
  revenir. Seule une **intervention causale** (patcher l'activation à un step,
  observer si l'issue bascule) y répond. C'est le protocole d'Akarlar
  (corruption 87.5 % / correction 33.3 %), et c'est la prochaine étape.
- **Non établi** : que la décroissance après le step 2 soit un rapprochement des
  classes plutôt qu'une dispersion intra-classe.

---

## 2026-08-20 — Étape 4 : test causal. D2 n'est pas soutenu sur GPT-2 small

`src/causal_patching.py`. Sur un même prompt : un run receveur, un run donneur de
l'autre classe ; on force les s premiers tokens du receveur, on remplace son
activation à la couche l par celle du donneur au même (step, couche), puis greedy.
Steps 1-3, couches 4/8/11, 6 paires par prompt, 10 prompts.

### Le premier run était faux — le contrôle l'a dit

Self-patch (patcher avec sa propre activation, qui doit être un no-op exact) :
**18.1 % de générations modifiées → ÉCHEC.** Cause trouvée en relisant
`extract_trajectories.py` : le rapport ne conservait que **2 textes par classe**
pour **6 trajectoires**, si bien que le texte rejoué et le vecteur d'activation
provenaient de runs différents. Corrigé en appariant strictement les tokens
générés à leur trajectoire dans le `.npz`.

Couche 12 également retirée du patch : dans `hidden_states`, elle est prise
**après `ln_f`**, qu'un hook posé sur un bloc ne peut pas reproduire. Patch
restreint aux couches 1-11.

Second run — **self-patch : 0/1080 = 0.0 %. Mécanisme validé.**

### Résultats

| Intervention | taux | IC 95 % |
|---|---|---|
| corruption (Correct ← Hallucination) | **6.7 %** | [4.6 %, 8.8 %] |
| correction (Hallucination ← Correct) | **4.4 %** | [2.7 %, 6.2 %] |
| **patch aléatoire (contrôle)** | **6.5 %** | [5.0 %, 7.9 %] |

**corruption vs contrôle aléatoire : z = 0.14.** Aucune différence.

Le patch dirigé ne fait **rien de plus qu'un bruit gaussien de même moyenne et
variance**. L'asymétrie apparente (6.7 % contre 4.4 %, « ratio 1.5× ») est sans
objet une fois le contrôle pris en compte : le numérateur est au niveau du bruit.

Référence Akarlar sur Qwen2.5-1.5B : corruption 87.5 %, correction 33.3 %,
aléatoire 12.5 % — soit 7× le contrôle. Ici : 1.03× le contrôle.

### Ce que ça établit

**D2 (point de commitment irréversible) n'est pas soutenu sur GPT-2 small par une
intervention ponctuelle.** Il n'y a pas de bassin absorbant détectable : injecter
l'état d'une trajectoire hallucinée dans une trajectoire correcte ne la fait pas
basculer plus souvent que du bruit.

Trois explications concurrentes, non départagées :

1. **GPT-2 small n'a pas ces bassins.** 124M paramètres, non instruction-tuned —
   le phénomène d'Akarlar pourrait n'émerger qu'à plus grande échelle.
2. **L'intervention ponctuelle est trop faible.** Akarlar note explicitement que
   la *correction* exige une intervention soutenue multi-étapes, là où la
   corruption suffit en un coup. Notre patch est ponctuel sur les deux
   directions. Le **window patching** (plusieurs steps consécutifs) est le test
   qui manque.
3. **Notre définition de Hallucination est plus lâche** (toute entité assertée
   différente de la réponse attendue), ce qui dilue le contraste.

L'explication 2 est la plus testable et la moins coûteuse : c'est la prochaine
étape. Tant qu'elle n'est pas faite, **ne pas conclure que le phénomène est
absent** — conclure que l'intervention ponctuelle ne le fait pas apparaître.

### Bilan de la nuit pour ProbatioH1

| Élément du programme | Statut après mesure |
|---|---|
| Dwell time au col | réfuté (p = 0.085, n = 50) |
| Signal géométrique sur le dataset artisanal | invalidé par C1 (longueur seule : 0.939) |
| « Certifier avant production de la réponse » (§ V) | réfuté par construction (step 0 = AUC 0.500) |
| Séparation inter-couches | quasi entièrement lexicale (embedding 0.84 / max 0.89) |
| D2, irréversibilité | non soutenu par patch ponctuel (6.7 % vs 6.5 % aléatoire) |
| D1, convergence vers bassin | en tension avec la décroissance après le step 2 |
| Garde-fou synthétique triple | **reste le seul actif non entamé** |

Cinq mesures, cinq résultats négatifs ou nuls — tous obtenus avec des contrôles
qui ont chacun attrapé une erreur réelle (substring `"0"` dans `"110"`,
non-réponses comptées comme hallucinations, appariement rompu entre texte et
activation). C'est la méthode qui tient, pas les hypothèses.

---

## 2026-08-20 — Étapes 5 et 6 : window patching, puis le contrôle qui tranche

### Étape 5 — window patching (`src/window_patching.py`)

Le self-patch **ne peut pas** servir de contrôle au-delà de w = 1 : dès le second
step, le replay en greedy a produit un token différent de l'original
(échantillonné), donc l'activation stockée provient d'un contexte qui n'existe
plus. Ce n'est pas un bug, c'est la définition. Premier run abandonné pour cette
raison (self-patch 38 %, 61 %, 77 % à w = 2, 3, 4).

Contrôle remplacé par le **same-class patch** — un donneur de la même classe que
le receveur, qui subit exactement le même décalage de contexte. Self-patch à
w = 1 : **0/360, mécanisme validé.**

| fenêtre | corruption | same-classe | aléatoire | z (cross/same) |
|---|---|---|---|---|
| 1 | 11.7 % | 8.3 % | 15.0 % | 1.05 |
| 2 | 15.0 % | 6.7 % | 18.3 % | **2.54** |
| 3 | 16.7 % | 6.7 % | 21.7 % | **2.96** |
| 4 | 15.6 % | 8.3 % | 17.2 % | **2.11** |

Correction : z = 0.00 / 1.45 / 1.22 / 2.28. Avec correction de Bonferroni pour
8 comparaisons (seuil |z| > 2.73), seule la corruption à w = 3 survit.

Effet apparent, donc — mais **le patch aléatoire fait toujours au moins aussi
bien que le patch dirigé** (18.3 contre 15.0 ; 21.7 contre 16.7). Signal d'alarme.

### L'ordre des distances explique l'ordre des taux

Distance L2 moyenne à l'état du receveur (couche 8) :

| | same-classe | cross-classe | aléatoire |
|---|---|---|---|
| distance | 54.6 | 83.0 | 149.6 |
| taux de bascule (w = 3) | 6.7 % | 16.7 % | 21.7 % |

Monotone dans les deux cas. Hypothèse à écarter : ce n'est pas le *contenu* de
l'état injecté qui fait basculer l'issue, c'est la *distance* dont on déplace
l'état.

### Étape 6 — patch apparié en norme (`src/normmatched_patching.py`)

Le test qui tranche : injecter un vecteur placé à la **même distance L2** de
l'état du receveur que le donneur cross-classe, mais dans une **direction
aléatoire**. Même amplitude, aucune information de l'autre classe. Fenêtre 3,
couches 4/8/11, n = 180 par cellule.

| direction | cross-classe | apparié en norme | z |
|---|---|---|---|
| corruption | 16.7 % | 11.1 % | **1.52** — non significatif |
| correction | 8.9 % | **0.0 %** (0/180) | **4.09** — significatif |

### Ce que ça établit, et c'est le premier résultat positif du projet

**Corrompre ne demande aucune information.** L'écart entre patch cross-classe et
bruit de même amplitude n'est pas significatif (z = 1.52) — et un bruit non
apparié, donc plus violent, fait *mieux* (21.7 %). Déplacer l'état assez loin
suffit à faire dérailler la génération, peu importe la direction. Ce que l'étape 5
mesurait sous le nom de « corruption » était pour l'essentiel de la dégradation.
**Il n'y a pas de transport d'information vers un bassin hallucinatoire.**

**Réparer en demande.** Un bruit de même amplitude ne répare **jamais** (0/180),
là où l'état d'une trajectoire correcte répare dans 8.9 % des cas (z = 4.09,
survit à Bonferroni). Ici, le contenu de l'état compte.

L'asymétrie existe donc bien, mais elle ne dit pas ce que D2 supposait. Elle ne
dit pas « le bassin hallucinatoire est absorbant ». Elle dit :

> il y a beaucoup de façons d'être faux et peu d'être juste. Sortir de la justesse
> se fait par n'importe quelle perturbation suffisante ; y revenir exige une
> direction précise, qu'un tirage aléatoire ne trouve pas.

### Réserve à ne pas enterrer

Cette asymétrie peut tenir en partie à la **largeur des classes de mesure** :
« Correct » exige qu'une chaîne précise apparaisse (« Tokyo »), « Hallucination »
accepte n'importe quelle entité assertée. Une classe étroite est plus difficile à
atteindre par hasard qu'une classe large — indépendamment de toute géométrie.

Ce n'est pas une objection fatale : le patch aléatoire non apparié atteignait
1.1-1.7 % de « correction » à l'étape 5, donc la probabilité de base n'est pas
nulle. Mais départager « asymétrie du phénomène » et « asymétrie de la mesure »
demanderait des classes de largeur comparable — par exemple en imposant à
« Hallucination » de nommer une entité d'un type déterminé. **Non fait.**

### Où en est ProbatioH1

| Élément | Statut |
|---|---|
| Dwell time au col | réfuté |
| Signal géométrique (dataset artisanal) | invalidé par C1 |
| Certifier avant production (§ V) | réfuté par construction |
| Séparation inter-couches | quasi entièrement lexicale |
| D2, bassin absorbant côté hallucination | **non soutenu** — la corruption est de la dégradation |
| Asymétrie corruption/correction | **soutenue, mais réinterprétée** : la correction exige une direction spécifique |
| G1/G2 (steering pour corriger) | plausible pour la première fois — un état correct répare, un bruit non |

Le seul élément du programme que la mesure ait renforcé est **l'intervention
corrective dirigée** (G1-G2) : il existe une direction qui répare et que le
hasard ne trouve pas. C'est étroit, c'est à 8.9 %, mais c'est réel et contrôlé.

---

## 2026-08-20 — Étape 7 : la direction qui répare n'est pas transférable

`src/repair_direction.py`. Direction de réparation d'un prompt :
`d_p = centroïde(Correct_p) − centroïde(Hallucination_p)`, moyennée sur la
fenêtre (steps 1-3).

### A. Géométrie — une composante partagée existe

| couche | cos cross-prompt | [min, max] | plafond split-half | plancher \|cos\| 95 % |
|---|---|---|---|---|
| 4 | 0.230 ± 0.17 | [-0.05, 0.61] | 0.489 | 0.073 |
| 8 | 0.323 ± 0.18 | [0.06, 0.68] | 0.487 | 0.067 |
| 11 | 0.360 ± 0.17 | [0.06, 0.73] | 0.467 | 0.073 |

Nettement au-dessus du plancher aléatoire (0.07), nettement sous le plafond de
fiabilité split-half (0.47-0.49). Corrigé de l'atténuation, cela suggérerait une
direction largement partagée (0.36/0.47 ≈ 0.77). **La géométrie dit oui.**

### B. Fonction — mais elle ne répare pas

Toutes conditions à norme égale, n = 132 (les cas déjà corrects à la baseline
sont exclus : il n'y a rien à y réparer).

| condition | réparation |
|---|---|
| oracle-paire (l'état correct apparié) | **12.1 %** |
| oracle-prompt (direction du prompt lui-même) | **8.3 %** |
| **transfert (direction des autres prompts)** | **0.8 %** (1/132) |
| aléatoire (plancher) | 2.3 % |

`transfert vs aléatoire : z = −1.01` — le transfert ne fait pas mieux que le
hasard. Il fait même numériquement moins bien.
`transfert vs oracle-prompt : z = −2.95` — il fait significativement moins bien
que la direction propre au prompt.

**La fonction dit non.**

### Ce que la dissociation signifie

Une similarité cosinus de 0.36 sans aucun effet fonctionnel veut dire que la
composante *partagée* de la direction n'est pas celle qui répare. Le partagé est
probablement générique — un déplacement vers un registre plus assertif ou plus
factuel. Ce qui répare est la composante *spécifique au prompt* : l'information
« Tokyo ».

Autrement dit : **réparer une trajectoire, c'est y injecter la réponse.**

### Conséquence pour ProbatioH1 — un no-go interne

G1-G2 (« dérive détectée, un steering minimal suffit », « steering maximal +
monitoring ») supposent qu'on puisse corriger une trajectoire sans disposer de
la réponse. La mesure dit le contraire : la seule direction qui corrige est celle
qui porte déjà la réponse. Un système qui saurait construire ce vecteur n'aurait
plus besoin de corriger — il connaîtrait la réponse.

C'est exactement le **no-go informationnel** que le programme pose en § I comme
axiome fondateur : quand l'information n'est pas disponible, aucune manipulation
géométrique ne la crée. Le programme démontre son propre axiome — appliqué à sa
propre couche d'intervention.

Ce qui reste debout de G0-G6, sous cette contrainte : **G5, l'abstention
certifiée**, et lui seul. Détecter qu'on dérive et s'arrêter ne demande aucune
information supplémentaire. Corriger, si.

### Réserves

- GPT-2 small, 124M, non instruction-tuned. Les vecteurs de steering transférables
  documentés dans la littérature le sont sur des modèles bien plus grands ; ce
  résultat ne se généralise pas au-delà de cette échelle.
- 10 prompts, tous de forme « The X of Y is », tous en anglais. La composante
  partagée mesurée est donc celle d'une famille syntaxique très étroite — ce qui
  rend l'absence de transfert d'autant plus notable, mais limite la portée.
- La direction est estimée sur 6 runs par classe. Le plafond split-half à 0.47
  montre que l'estimation est bruitée ; avec plus de runs, la similarité
  cross-prompt monterait mécaniquement — sans que cela change le résultat
  fonctionnel, qui est mesuré, pas estimé.

---

## 2026-08-20 — DÉCLARATION DE PROTOCOLE (avant exécution)

Conformément à `docs/DEGRES-DE-LIBERTE.md` § 7, item 1 : le changement est
déclaré, avec sa prédiction, **avant** de lancer le run.

### Ce qui change

`Hallucination` cesse d'accepter n'importe quelle entité assertée. Elle exige
désormais une entité **du même type que la réponse attendue** — une ville pour
une capitale, une planète pour une planète, un océan pour un océan. Les listes de
distracteurs sont écrites maintenant, avant tout résultat, et figées dans
`src/typed_entities.py`.

Motif : `Correct` exigeait une chaîne précise tandis que `Hallucination` acceptait
une classe large. Une classe étroite est plus difficile à atteindre par hasard,
indépendamment de toute géométrie. Cette asymétrie de mesure est la première
explication concurrente du seul résultat positif du projet.

### Ce qui est attaqué

Étape 6, patch apparié en norme, direction correction : **cross-classe 8.9 %
contre bruit de même amplitude 0/180, z = 4.09.**

### Prédictions, posées avant de voir quoi que ce soit

- **Si le résultat était un artefact de largeur** : avec des classes appariées en
  type, l'écart entre patch cross-classe et bruit apparié se réduit fortement,
  voire disparaît (z < 1.96). Le seul résultat positif du projet tombe.
- **S'il tient** : l'écart reste significatif malgré l'appariement. Le contenu de
  l'état compte bien, et la réserve principale est levée.
- **Cas intermédiaire attendu comme le plus probable** : l'écart diminue mais
  reste significatif. Il faudra alors rapporter les deux mesures côte à côte,
  sans choisir celle qui arrange.

### Effet de bord accepté

La classe `Hallucination` devient rare. Il faudra un budget de tirage nettement
plus élevé pour atteindre K = 6, et certains prompts deviendront inexploitables.
Une baisse du nombre de prompts n'est **pas** un motif de revenir à l'ancienne
définition.

### Nouveau degré de liberté introduit, et assumé

Les listes de distracteurs sont écrites par moi. Elles sont figées avant le run
et versionnées ; elles ne seront pas retouchées après avoir vu les résultats.

---

## 2026-08-20 — Étape 8 : résultat du test. L'effet survit, affaibli, et ne passe plus Bonferroni

`src/typed_entities.py` (30 listes de distracteurs, écrites avant le run),
options `--typed` sur les trois scripts concernés.

**Effet de bord mesuré** : bifurcations 10/30 → **6/30**. Trajectoires 120 → **72**
(36 Correct / 36 Hallucination sur 6 prompts). Budget porté à 800 tirages par
prompt. Comme annoncé, la baisse d'effectif n'a pas servi de prétexte à revenir
en arrière.

### Comparaison directe, classes larges contre classes appariées

| | classes larges (v1) | **classes appariées en type** |
|---|---|---|
| corruption : cross | 16.7 % | **2.8 %** |
| corruption : apparié en norme | 11.1 % | 0.9 % |
| corruption : z | 1.52 | 1.01 |
| **correction : cross** | 8.9 % | **6.5 %** |
| **correction : apparié en norme** | 0.0 % | 0.9 % |
| **correction : z** | **4.09** | **2.16** |

Effectifs bruts, n = 108 par cellule. Test exact de Fisher, unilatéral :
- corruption : 3/108 contre 1/108 — **p = 0.31**
- correction : 7/108 contre 1/108 — **p = 0.033**

### Verdict, selon les prédictions déposées avant le run

C'est le **cas intermédiaire**, celui que j'avais annoncé comme le plus probable :
l'effet diminue mais ne disparaît pas. Les deux mesures sont rapportées côte à
côte, sans choisir celle qui arrange.

- **z passe de 4.09 à 2.16.** Encore au-dessus de 1.96, donc significatif à 5 %
  brut. **En dessous du seuil de Bonferroni pour 2 comparaisons (2.24).**
- Fisher : p = 0.033, au-dessus du seuil corrigé de 0.025.

**Le résultat positif du projet ne survit donc plus à une correction pour
comparaisons multiples.** Il n'est pas éliminé — il est ramené au statut de
tendance, sur 7 succès contre 1.

### Ce que le test a aussi révélé, et qui n'était pas la question posée

La corruption s'effondre de 16.7 % à 2.8 %. C'est une confirmation frontale du
diagnostic de l'étape 6 : ce qui était compté comme « corruption » était pour
l'essentiel de la **dégradation** captée par une classe large. Dès qu'on exige de
l'hallucination qu'elle nomme une entité du bon type, casser l'état ne suffit
plus à produire une hallucination — il faut produire une *autre ville plausible*,
ce qu'une perturbation ne fait pas.

L'asymétrie corruption/correction d'Akarlar n'est donc **pas** reproduite ici,
sous aucune des deux définitions. Ce n'était pas le sujet du test, mais c'est
maintenant établi sur les deux mesures.

### Ce qu'il faudrait pour trancher

Plus de prompts typés. Avec 6 prompts et 7 succès contre 1, l'estimation est
fragile ; le protocole est correct mais sous-alimenté. Étendre la liste de
prompts (et donc de distracteurs) à 60-80 candidats devrait donner assez de
prompts bifurquants pour un test qui passe ou casse franchement. **Non fait.**

Tant que ce n'est pas fait, le statut honnête de la seule direction positive du
projet est : **tendance non confirmée**.

---

## 2026-08-20 — DÉCLARATION DE PROTOCOLE (avant exécution) : extension du corpus

### Ce qui change

Le corpus passe de 30 à ~82 prompts. Les nouveaux sont écrits maintenant, avec
leurs réponses acceptées et leurs distracteurs typés, **avant tout run**, dans
`src/corpus.py`.

Deux objectifs, dont un qui n'était pas demandé :

1. **Puissance.** 6 prompts et 8 cas positifs ne permettent pas de trancher. Il
   faut assez de prompts bifurquants pour que le test passe ou casse franchement.
2. **Diversité syntaxique.** `docs/DEGRES-DE-LIBERTE.md` § 1 signalait que les 30
   prompts partageaient tous la forme « The X of Y is ». Le corpus étendu ajoute
   « X is located in », « The official language of X is », « X was painted by »,
   « The largest/fastest X is the ». Cela attaque simultanément le degré de
   liberté n° 4 de la liste.

### Ce qui ne change pas

Tout le reste : température 0.7, `max_new_tokens` 8, K = 6, fenêtre 3 depuis le
step 1, couches 4/8/11, seed 42, comparaison à norme égale, Fisher exact avec
Bonferroni pour 2 comparaisons. Aucun de ces réglages n'est retouché.

### Prédiction déposée

Si l'effet de l'étape 8 (correction : 7/108 contre 1/108, p = 0.033) est réel,
un corpus 2 à 3 fois plus grand doit le faire passer **sous** le seuil corrigé de
0.025 tout en gardant un taux comparable. S'il s'agissait d'un accident
d'échantillonnage, le taux cross-classe doit se rapprocher du bruit apparié et
p remonter.

**Critère d'arrêt fixé maintenant** : quel que soit le résultat, ce run est le
dernier sur GPT-2 small pour cette question. Si l'effet ne passe pas Bonferroni
avec ~3× plus de données, il est déclaré non établi à cette échelle de modèle, et
la suite se joue sur un modèle plus grand ou pas du tout.

---

## 2026-08-20 — Étape 9 : corpus étendu. L'effet passe, et il inverse le cadre

87 prompts (30 + 52 nouveaux, formes syntaxiques diversifiées), **20/87
bifurquent** en mode typé (23 %). **238 trajectoires**, 119 Correct / 119
Hallucination, 20 prompts exploitables — 3,3× le run précédent.

### Résultat, n = 357 par cellule

| direction | cross-classe | apparié en norme | z | Fisher exact | Bonferroni (0.025) |
|---|---|---|---|---|---|
| corruption | **9.2 %** (33/357) | 0.8 % (3/357) | 5.13 | **6.0 × 10⁻⁸** | **PASSE** |
| correction | **14.6 %** (52/357) | 6.4 % (23/357) | 3.54 | **2.8 × 10⁻⁴** | **PASSE** |

**Les deux directions passent, largement.** Le contenu de l'état injecté compte
au-delà de son amplitude, dans les deux sens. La prédiction déposée avant le run
est vérifiée : l'effet était réel et le test précédent était sous-alimenté.

### Correction d'une conclusion antérieure

À l'étape 6 j'écrivais : « corrompre ne demande aucune information » (cross 16.7 %
contre apparié 11.1 %, z = 1.52). **C'était un artefact de la classe large.**
Avec `Hallucination` non typée, un bruit suffisait à produire du texte compté
comme hallucination — le bruit apparié montait à 11.1 % et plafonnait l'écart.
Une fois le type imposé, le bruit apparié tombe à 0.8 % : casser un état ne
produit pas une entité du bon type. L'écart devient alors massif (ratio 11,5×).

Corrompre demande donc bien de l'information. La conclusion de l'étape 6 sur ce
point est retirée.

### Ce que le tableau dit, et qui inverse le cadre théorique

Deux faits, tous deux contrôlés :

1. **Réparer est plus facile que corrompre** : 14.6 % contre 9.2 %.
2. **Le bruit répare (6.4 %) mais ne corrompt presque pas (0.8 %).**

Le second est le plus parlant. Perturber une trajectoire hallucinée la ramène
vers la bonne réponse dans 6.4 % des cas ; perturber une trajectoire correcte ne
produit un distracteur plausible que dans 0.8 % des cas.

Autrement dit, quand on secoue le système au hasard, **il retombe du côté
correct**. C'est la signature d'un attracteur — mais du côté de la réponse juste,
pas du côté de l'hallucination.

Cela contredit frontalement le modèle qui sous-tend ProbatioH1 et l'asymétrie
d'Akarlar (corruption 87.5 % ≫ correction 33.3 % sur Qwen2.5-1.5B). Ici,
l'asymétrie existe mais **pointe dans l'autre sens**.

### Réserves, à ne pas enterrer

- **GPT-2 small, 124M, non instruction-tuned.** La réponse correcte y est
  probablement le mode de la distribution, ce qui suffirait à expliquer qu'une
  perturbation y ramène. Sur un modèle plus grand, entraîné à suivre des
  instructions, rien ne dit que ce soit encore le cas.
- **Pas de cache KV** (voir `docs/DEGRES-DE-LIBERTE.md` § 6). Un patch n'agit ici
  que par le token qu'il fait produire. Akarlar mesure autre chose.
- **Les distracteurs sont écrits par moi.** Une liste plus large rendrait la
  classe Hallucination plus facile à atteindre et remonterait mécaniquement le
  taux de corruption. La liste est figée et versionnée, mais c'est un paramètre.
- Le critère d'arrêt déclaré est respecté : c'est le dernier run sur GPT-2 small
  pour cette question.

### Statut révisé

| Élément | Statut |
|---|---|
| Dwell time au col | réfuté |
| Signal du dataset artisanal | invalidé (C1) |
| Certifier avant production (§ V) | réfuté par construction |
| Séparation inter-couches | quasi entièrement lexicale |
| Le contenu de l'état a un effet causal | **établi** (p = 6 × 10⁻⁸ et 2.8 × 10⁻⁴) |
| Bassin absorbant côté hallucination | **contredit** — l'attracteur est du côté correct |
| Direction de réparation transférable | **non** (étape 7 : 0.8 % contre 8.3 %) |
| G1-G2 opérationnalisables | non — réparer exige l'information de la réponse |
| G5, abstention certifiée | seul niveau qui survit |

---

## 2026-08-20 — Étape 10 : recadrage sur l'objectif réel (réduire), et bornes

Lamar recadre : l'objectif n'est pas de décrire l'hallucination mais de la
réduire. Le programme repart de ce que les étapes 1-9 ont établi — l'attracteur
est du côté correct — et en tire les conséquences opérationnelles.

`src/reduction_bound.py`, 87 prompts, N = 20 à T = 0.7.

### A. Partition — la borne de toute méthode sans connaissance

| catégorie | prompts | part |
|---|---|---|
| TOUJOURS-CORRECT | 20/87 | 23.0 % |
| **BIFURQUANT** (stochastique) | 22/87 | 25.3 % |
| **TOUJOURS-FAUX** (systématique) | 17/87 | 19.5 % |
| MUET (aucune assertion) | 28/87 | 32.2 % |

Sur les 39 prompts où le modèle se trompe au moins une fois :
**56 % sont stochastiques** (le vrai apparaît parfois → accessible par
agrégation) et **44 % sont systématiques** (le modèle est faux à chaque tirage →
aucune agrégation, aucun décodage, aucune perturbation ne le corrigera).

**C'est le plafond dur.** Toute méthode qui n'apporte pas de connaissance
extérieure plafonne à la moitié environ du problème.

### B. Stratégies sans information externe

Erreur de mesure au premier run, corrigée : j'agrégeais par tirage, ce qui
pondérait les prompts par leur nombre d'assertions et faisait apparaître le vote
à −10.4 %. Comparaison refaite **par prompt, sur l'ensemble commun** (25 prompts
où les quatre stratégies assertent).

| stratégie | correct | vs baseline | réduction relative d'erreur |
|---|---|---|---|
| tirage unique T = 0.7 | 73.2 % | — | — |
| tirage unique T = 0.3 | 78.1 % | +4.9 | 18.3 % |
| greedy (T → 0) | 80.0 % | +6.8 | **25.3 %** |
| vote majoritaire sur 20 | 80.0 % | +6.8 | **25.3 %** |

Vote et greedy convergent exactement — attendu si la bonne réponse est le mode.
C'est la confirmation opérationnelle de l'inversion d'attracteur de l'étape 9 :
**un quart des erreurs disparaît sans aucune connaissance, juste en prenant le
mode.**

### C. Le désaccord entre tirages prédit-il l'erreur ?

Première mesure fausse, à signaler : j'ai approximé l'accord par
`max(correct, faux) / total`, ce qui suppose que toutes les réponses fausses sont
la même entité. AUC obtenue : 0.436, soit un anti-signal — et une conclusion
« l'auto-cohérence ne détecte rien » que j'ai failli écrire.

Recalcul sur les **vraies distributions d'entités** :

| | accord (part de la modalité dominante) | entités distinctes |
|---|---|---|
| vote juste | 0.845 | 1.5 |
| vote faux | 0.693 | 2.0 |

**AUC = 0.666** pour prédire l'erreur du vote. Le signal existe.

### D. Politique d'abstention — l'échange couverture/précision

| seuil d'accord | couverture | précision | erreurs évitées |
|---|---|---|---|
| aucun | 100 % | 57.6 % | 0 % |
| 0.60 | 69.5 % | 68.3 % | 48.0 % |
| **0.70** | **57.6 %** | **70.6 %** | **60.0 %** |
| 0.80 | 50.8 % | 70.0 % | 64.0 % |

À seuil 0.70, on répond à 58 % des questions et **on évite 60 % des erreurs**,
en faisant passer la précision de 57.6 % à 70.6 %. Sans aucune source externe,
sans aucun entraînement.

### Ce que ces trois mesures dessinent

Une architecture de réduction en trois étages, dont chaque étage est mesuré :

1. **Prendre le mode** (greedy ou vote) — −25 % d'erreur, coût nul.
2. **S'abstenir sur désaccord** — −60 % d'erreurs restantes au prix de 42 % de
   couverture. C'est **G5, l'abstention certifiée**, enfin opérationnalisée : le
   critère d'abstention est la dispersion inter-tirages, qui ne demande aucune
   connaissance.
3. **Le résidu systématique (44 %)** est hors d'atteinte de toute méthode interne.
   Il exige une source externe : récupération documentaire, vérification, ou
   refus explicite du domaine.

Le programme ProbatioH1 visait la certification par la géométrie. La mesure dit
que le levier utile est ailleurs : **dans la dispersion de l'échantillonnage, pas
dans la trajectoire latente**. Et que le plafond de toute approche sans
connaissance est d'environ la moitié du problème.

### Réserves

- 59 prompts assertifs, dont 25 dans l'ensemble commun. Petits effectifs.
- GPT-2 small : le taux de MUET (32 %) et de TOUJOURS-FAUX (19.5 %) est
  spécifique à un modèle faible. La partition stochastique/systématique doit être
  refaite sur un modèle instruction-tuned avant d'être généralisée.
- L'auto-cohérence comme signal d'abstention est un procédé connu
  (SelfCheckGPT et suivants). Ce qui est propre ici, c'est la **partition
  quantifiée** qui en borne le rendement.

---

## 2026-08-20 — Étapes 10-bis et 11 : Qwen, puis le domaine vérifiable

### Qwen2.5-1.5B-Instruct sur le corpus factuel — un plafond de corpus, pas un résultat

| | GPT-2 small | Qwen2.5-1.5B-Instruct |
|---|---|---|
| TOUJOURS-CORRECT | 23.0 % | 44.8 % |
| BIFURQUANT | 25.3 % | 55.2 % |
| TOUJOURS-FAUX | 19.5 % | **0.0 %** |
| MUET | 32.2 % | 0.0 % |
| réduction d'erreur par le vote | 25.3 % | **70.2 %** |

**Le zéro n'est pas une découverte.** Le corpus a été écrit pour GPT-2 small
(capitales, planètes) ; pour un 1.5B instruction-tuned il ne contient plus de
difficulté. La partition mesure le couple (modèle, corpus), pas le modèle. Les
deux colonnes ne sont pas comparables et ne seront pas présentées comme telles.
C'est précisément pourquoi HACK (arXiv 2510.24222) construit un dataset
**spécifique à chaque modèle**.

Ce qui reste valide, sur deux points : **le rendement de l'agrégation est
gouverné par la part stochastique** (56 % → 25.3 % ; 100 % → 70.2 %).

### Étape 11 — corpus vérifiable (`src/verifiable_bound.py`)

63 items, cinq familles (équation linéaire, racine carrée, diviseur non trivial,
complément de somme, facteur manquant). **Vérification non circulaire** : on teste
la propriété que la réponse doit satisfaire, sans disposer de la solution — les
items du type « 17 + 25 = » sont exclus, les recalculer reviendrait à connaître la
réponse. Chaque `verify` a été validé contre sa réponse canonique avant le run.

Effet de bord bienvenu : **plus de listes de distracteurs**. Les deux classes sont
« un entier », leur largeur est identique par construction. Le degré de liberté qui
gênait depuis l'étape 8 disparaît.

**Partition** (Qwen2.5-1.5B-Instruct) : TOUJOURS-CORRECT 22.2 % · BIFURQUANT
73.0 % · TOUJOURS-FAUX 4.8 % · MUET 0 %.
Sur les 49 items avec erreur : **93.9 % stochastique, 6.1 % systématique**.

**Résultat**

| | tirage unique | greedy | vote | politique vérifiée |
|---|---|---|---|---|
| précision | 65.0 % | 76.2 % | 76.2 % | **100 %** |
| couverture | 100 % | 100 % | 100 % | **95.2 %** |

Seconde politique, plus stricte (« je réponds si le **vote** passe le check ») :
couverture 76.2 %, précision 100 %. L'écart entre les deux montre que les 20
tirages contiennent une bonne réponse bien plus souvent que le vote ne la
désigne — le modèle **a** la réponse, il ne sait pas laquelle c'est.

### Une identité, pas une coïncidence

Couverture de la politique vérifiée = 95.2 %. Part TOUJOURS-FAUX = 4.8 %.
Exactement complémentaires, et ce n'est pas un hasard : dès qu'au moins un tirage
est correct, le vérificateur le trouve. D'où :

> **couverture atteignable en domaine vérifiable = 1 − part systématique**

L'agrégation, elle, ne capture qu'une fraction du stochastique. Le vérificateur le
capture **en entier**. C'est la différence structurelle entre graduer et vérifier.

### Comparaison des deux régimes

| | couverture | précision | nature |
|---|---|---|---|
| empirique (étape 10, seuil 0.70) | 57.6 % | 70.6 % | gradué, jamais garanti |
| **vérifiable (étape 11)** | **95.2 %** | **100 %** | garanti, partiel |

Et le domaine vérifiable est le **plus difficile** des deux pour ce modèle
(65.0 % contre 88.0 % en tirage unique). Un domaine plus dur, un résultat
strictement meilleur : ce n'est pas un gain de facilité, c'est un changement de
nature de la garantie.

### Conséquence pour l'architecture

L'étage 3-bis (vérification) n'est pas un complément des étages 1-3, il les
**domine** partout où il s'applique. La spécification du système se reformule :

> maximiser la fraction des questions traitables en régime vérifiable

Ce qui donne leur place aux trois usages discutés : Lean/Mathlib étendent le
régime vérifiable aux énoncés formels ; la récupération documentaire l'étend aux
faits sourçables (vérifier = retrouver la source) ; l'abstention graduée ne sert
que pour le résidu qui n'entre dans aucun des deux.

### Réserves

- Corpus différents entre les deux régimes (faits encyclopédiques vs arithmétique).
  La comparaison porte sur la **nature de la garantie**, pas sur un même matériau.
- 63 items, une seule famille de difficulté arithmétique. À étendre avant tout
  claim de généralité.
- La vérification arithmétique est bon marché. En Lean, le coût de vérification
  et le taux d'échec de compilation changeraient la couverture — non mesuré.

---

## 2026-08-20 — Étape 12 : coût réel du régime vérifiable (Lean + Mathlib)

Mathlib installé dans `~/mathlib-probe` (7,4 Go, 8 690 fichiers de cache, build
réussi). Lean 4.33.0, `.venv` inchangé.

### Le coût dépend du contexte, pas du noyau

| contexte donné au vérificateur | temps par compilation |
|---|---|
| `import Mathlib` — candidat **valide**, cold | **207 s** |
| `import Mathlib` — candidat valide, warm | **187 s** |
| `import Mathlib` — candidat **invalide** | **220 s** |
| `Mathlib.Data.Nat.Basic` | **3.8 s** |
| core Lean seul (`omega`) | **6.8 s** |
| `Mathlib.Tactic.Linarith` | **7.3 s** |
| `Mathlib.Tactic.Ring` | **9.0 s** |

**Facteur 20 à 50** entre un import ciblé et l'import global. Le coût de
vérification n'est pas une propriété du noyau : c'est une propriété de la
**taille du contexte** qu'on lui donne à charger.

Erreur de conception de ma part, corrigée par la mesure : `lean_cost.py` écrivait
`import Mathlib`, soit le pire cas possible. À 200 s par candidat, 8 candidats sur
20 énoncés coûtaient 20 heures. Avec imports ciblés : ~20 minutes.

### Deux faits structurels

1. **Rejeter coûte autant qu'accepter** (220 s contre 207 s ; l'invalide est même
   plus cher). Le noyau doit charger tout le contexte avant de pouvoir dire non.
   Donc, en régime vérifiable, **le coût est proportionnel au nombre de candidats
   testés, pas au nombre retenus**. La politique « je réponds si un tirage passe »,
   gratuite à l'étape 11, coûte ici N × le prix unitaire.
2. **Pas d'amortissement entre invocations** (187 s contre 207 s). Les `.olean`
   sont rechargés à chaque fois. Un serveur Lean persistant changerait cela ; ce
   n'est pas le comportement par défaut, donc c'est bien le prix qu'un système
   naïf paierait.

### Échelle des trois régimes vérifiables mesurés

| régime | coût par vérification |
|---|---|
| arithmétique (étape 11) | < 0.001 s |
| Lean, imports ciblés | 4 - 9 s |
| Lean, import global | 187 - 220 s |

Environ **1 000×** entre l'arithmétique et Lean ciblé, **20 à 50×** entre Lean
ciblé et Lean global.

### Ce que ça dit du recadrage vers l'ingénierie

Le régime vérifiable est viable côté ingénierie logicielle non pas parce que ses
vérificateurs seraient meilleurs, mais parce que **le contexte y est déjà
découpé** : `tsc` type-check un fichier avec ses imports, `pytest` exécute une
suite ciblée. C'est le même geste que `import Mathlib.Tactic.Ring` plutôt que
`import Mathlib` — borner ce que le vérificateur doit charger. Découper le
contexte est le geste central, dans les deux domaines.

### Ce qui n'est PAS mesuré

**La couverture.** Le taux de candidats produits par le modèle qui compilent
réellement n'a pas été mesuré — le run a été interrompu par le coût de l'import
global. Sans ce chiffre, on connaît le prix du régime mais pas ce qu'il rapporte,
et la table couverture × force × coût reste incomplète sur sa colonne principale.

C'est faisable maintenant : à 8 s par vérification, 20 énoncés × 8 candidats
tiennent en ~20 minutes. `src/lean_cost.py` doit d'abord être corrigé pour
émettre des imports ciblés au lieu de `import Mathlib`.

---

## 2026-08-20 — Étape 12 : coût réel du régime vérifiable (Lean + Mathlib)

Mathlib installé dans `~/mathlib-probe` (7,4 Go, 8 690 fichiers de cache, build
réussi). Lean 4.33.0.

### Le coût dépend du contexte, pas du noyau

| contexte donné au vérificateur | temps par compilation |
|---|---|
| `import Mathlib` — candidat **valide**, cold | **207 s** |
| `import Mathlib` — candidat valide, warm | **187 s** |
| `import Mathlib` — candidat **invalide** | **220 s** |
| `Mathlib.Data.Nat.Basic` | **3.8 s** |
| core Lean seul (`omega`) | **6.8 s** |
| `Mathlib.Tactic.Linarith` | **7.3 s** |
| `Mathlib.Tactic.Ring` | **9.0 s** |

**Facteur 20 à 50** entre un import ciblé et l'import global. Le coût de
vérification n'est pas une propriété du noyau : c'est une propriété de la
**taille du contexte** qu'on lui donne à charger.

Erreur de conception de ma part, corrigée par la mesure : `lean_cost.py` écrivait
`import Mathlib`, soit le pire cas possible. À 200 s par candidat, 8 candidats sur
20 énoncés coûtaient 20 heures. Avec imports ciblés : ~20 minutes.

### Deux faits structurels

1. **Rejeter coûte autant qu'accepter** (220 s contre 207 s ; l'invalide est même
   plus cher). Le noyau doit charger tout le contexte avant de pouvoir dire non.
   Donc, en régime vérifiable, **le coût est proportionnel au nombre de candidats
   testés, pas au nombre retenus**. La politique « je réponds si un tirage passe »,
   gratuite à l'étape 11, coûte ici N × le prix unitaire.
2. **Pas d'amortissement entre invocations** (187 s contre 207 s). Les `.olean`
   sont rechargés à chaque fois. Un serveur Lean persistant changerait cela ; ce
   n'est pas le comportement par défaut, donc c'est le prix qu'un système naïf
   paierait.

### Échelle des trois régimes vérifiables mesurés

| régime | coût par vérification |
|---|---|
| arithmétique (étape 11) | < 0.001 s |
| Lean, imports ciblés | 4 - 9 s |
| Lean, import global | 187 - 220 s |

Environ **1 000×** entre l'arithmétique et Lean ciblé, **20 à 50×** entre Lean
ciblé et Lean global.

### Ce que ça dit du recadrage vers l'ingénierie

Le régime vérifiable est viable côté ingénierie logicielle non pas parce que ses
vérificateurs seraient meilleurs, mais parce que **le contexte y est déjà
découpé** : `tsc` type-check un fichier avec ses imports, `pytest` exécute une
suite ciblée. C'est le même geste que `import Mathlib.Tactic.Ring` plutôt que
`import Mathlib` — borner ce que le vérificateur doit charger. Découper le
contexte est le geste central, dans les deux domaines.

### Ce qui n'est PAS encore mesuré

**La couverture** : le taux de candidats produits par le modèle qui compilent
réellement. Le premier run a été interrompu par le coût de l'import global. Sans
ce chiffre on connaît le prix du régime, pas ce qu'il rapporte. Mesure lancée
juste après, avec imports ciblés.

---

## 2026-08-20 — DÉCLARATION DE PROTOCOLE (avant exécution) : chantier 1, code réel

Plan approuvé (`~/.claude/plans/luminous-greeting-chipmunk.md`). Transfert du
régime vérifiable vers l'ingénierie logicielle.

### Protocole

Corpus **MBPP sanitized** (427 problèmes, `data/sanitized-mbpp.json`), 60 premiers
retenus. Modèle Qwen2.5-1.5B-Instruct, N = 10 candidats, T = 0.7, seed 42 —
paramètres alignés sur les étapes 10-11 pour comparabilité.

**Vérificateur indépendant** : les tests viennent des auteurs du benchmark, pas du
modèle. Trois forces mesurées sur les mêmes candidats :
G4 syntaxe (`compile`) · G3 exécution sans exception · G2 tests fournis.

**Choix de protocole déclaré** : le premier test est donné au modèle comme
spécification (il fournit la signature de la fonction) ; les trois tests servent à
la vérification. C'est le protocole MBPP standard. Le test donné n'est pas écrit
par le modèle, l'indépendance du vérificateur est préservée.

**Isolation** (validée par Lamar) : sous-processus séparé, timeout 5 s, dossier
temporaire hors du dépôt, jamais d'`exec` en processus principal.

### Contrôles passés avant le run

- **60/60 solutions de référence passent leurs propres tests** → l'exécuteur est
  correct ; tout échec sera imputable au modèle.
- boucle infinie coupée par le timeout : oui (3.0 s)
- syntaxe invalide rejetée : oui · exception détectée : oui
- coût mesuré : **~40 ms par vérification** (2.4 s pour 60)

### Prédictions déposées

- La couverture G2 devrait dépasser le taux de tirage unique, comme aux étapes
  10-11 — c'est l'effet « le modèle a la réponse mais ne sait pas laquelle ».
- L'identité `couverture = 1 − part systématique` doit se retrouver ; si elle ne
  se retrouve pas, c'est que la partition ou la politique diffère de l'étape 11 et
  il faudra dire pourquoi.
- La couverture doit décroître avec la force : G4 ≥ G3 ≥ G2 par construction.
  Toute violation signale un bug.

### Nouveau degré de liberté

Le corpus est constitué des 60 **premiers** problèmes MBPP, pas d'un tirage
aléatoire — choix figé avant le run pour éviter toute sélection post-hoc. À
ajouter à `docs/DEGRES-DE-LIBERTE.md`.

---

## 2026-08-20 — Étape 12 (suite) : couverture du régime formel. 20 %.

Run terminé avec imports ciblés. Contrôle : **20/20 preuves canoniques
compilent** (1.7 s à 12.7 s selon le contexte), l'environnement est donc hors de
cause.

| | valeur |
|---|---|
| candidats qui compilent | **4/160 = 2.5 %** |
| énoncés couverts (≥ 1 candidat valide) | **4/20 = 20.0 %** |
| coût par candidat | **14.0 s** |
| coût par énoncé (8 candidats) | **112.3 s** |
| preuve canonique, pour mémoire | 6.0 s |

### Correction d'une affirmation de l'étape 12

J'écrivais « rejeter coûte autant qu'accepter » (220 s contre 207 s sur
`import Mathlib`). Avec imports ciblés, l'écart se creuse dans l'autre sens :
**14.0 s pour un candidat du modèle contre 6.0 s pour une preuve canonique**, soit
2,3×. Les tactiques invalides déclenchent des recherches longues (`simp`, `exact?`,
saturation) avant d'échouer. **Rejeter coûte davantage qu'accepter**, et le surcoût
augmente quand le taux d'échec augmente — exactement le mauvais couplage.

Coût effectif par énoncé **réellement couvert** : 112.3 / 0.20 ≈ **560 s**.

### Ce que ça établit, et ce que ça n'établit pas

**Établi** : avec un modèle généraliste de 1,5 B, le régime vérifiable formel est
une garantie parfaite et presque vide — 100 % de précision sur 20 % des énoncés,
à 560 s par énoncé couvert.

**Non établi** : que ce soit une propriété du *régime*. C'est une propriété du
**modèle**. Qwen2.5-1.5B-Instruct n'est pas un prouveur ; les systèmes spécialisés
(DeepSeek-Prover, AlphaProof, AlphaVerus) ne sont pas comparables. Le chiffre à
retenir n'est pas « le régime formel couvre 20 % » mais « le coût d'entrée du
régime formel inclut un modèle spécialisé, et un généraliste ne suffit pas ».

### Ce que ça dit du recadrage vers l'ingénierie

Le contraste est désormais mesuré des deux côtés du coût :

| | coût par vérification |
|---|---|
| exécution de tests (MBPP) | **~40 ms** |
| Lean, imports ciblés | **14 s** (candidat modèle) |
| Lean, import global | 187-220 s |

Facteur **350** entre l'exécution de tests et Lean ciblé. Le régime vérifiable est
viable en ingénierie parce que le vérificateur y est presque gratuit **et** parce
que le modèle y produit des candidats valides bien plus souvent. Les deux
conditions manquent en mathématiques formelles avec un modèle généraliste.

La ligne « code » de la table est en cours de mesure.

---

## 2026-08-20 — Chantier 1 : le régime vérifiable sur du code réel (MBPP)

60 tâches MBPP sanitized, Qwen2.5-1.5B-Instruct, N = 10 candidats, T = 0.7,
seed 42. Vérificateur indépendant (tests des auteurs du benchmark). Contrôle
préalable : 60/60 solutions de référence passent leurs propres tests.

### Partition

| catégorie | tâches |
|---|---|
| TOUJOURS-CORRECT | 17/60 = 28.3 % |
| BIFURQUANT | 33/60 = 55.0 % |
| TOUJOURS-FAUX | 10/60 = 16.7 % |

Sur les 43 tâches échouées au moins une fois : **76.7 % stochastique,
23.3 % systématique**.

### Couverture par force de vérification

| niveau | couverture | coût par vérification |
|---|---|---|
| G4 syntaxe (`compile`) | 100.0 % | 5.3 ms |
| G3 exécution sans exception | 100.0 % | 152.0 ms |
| G2 tests fournis | **83.3 %** | 37.0 ms |
| tirage unique, pour mémoire | 59.2 % | — |

### Les trois contrôles déclarés avant le run passent

1. **couverture G2 > tirage unique** : 83.3 % contre 59.2 %. L'effet « le modèle
   a la réponse mais ne sait pas laquelle » se reproduit sur un troisième domaine.
2. **identité `couverture = 1 − part systématique`** : part systématique
   = 10/60 = 16.667 %, couverture G2 = 83.333 %. **Égalité exacte au flottant
   près**, sans aucun ajustement.
3. **décroissance G4 ≥ G3 ≥ G2** : 100 % ≥ 100 % ≥ 83.3 %. Aucun bug signalé.

L'identité de l'étape 11 tient donc sur trois domaines indépendants
(arithmétique, code, et par construction). Ce n'est plus une observation, c'est
une régularité.

### Une anomalie apparente, expliquée

G3 (exécution) coûte 152 ms alors que G2 (tests, donc code **plus** long) coûte
37 ms. Cause : **18 candidats parsent mais n'exécutent pas**, dont des boucles
infinies coupées par le timeout à 5 000 ms. Ces timeouts gonflent la moyenne G3 ;
G2 ne les voit jamais, puisqu'un candidat n'atteint G2 que s'il a passé G3.

C'est le même motif qu'en Lean (14 s pour un candidat du modèle contre 6 s pour
une preuve canonique) : **détecter l'échec coûte plus cher que confirmer le
succès**, et le surcoût croît avec le taux d'échec. Ce couplage vaut donc dans les
deux domaines, avec deux vérificateurs sans rapport. À traiter comme une
contrainte de conception, pas comme un accident : toute politique de filtrage paie
le plus cher sur ce qu'elle rejette.

### Comparaison des deux domaines vérifiables

| | code MBPP | Lean + Mathlib |
|---|---|---|
| couverture | **83.3 %** | 20.0 % |
| coût par vérification | **37 ms** | 14 s |
| part systématique | 23.3 % | 80 % |

Facteur **380** sur le coût, facteur **4** sur la couverture, dans le même sens.
Le régime vérifiable est viable en ingénierie logicielle et hors de portée en
mathématiques formelles **avec ce modèle** — les deux conditions manquent
simultanément côté Lean, et c'est ce que le recadrage vers l'ingénierie avait
anticipé.

### Réserve maintenue

« Précision 100 % » signifie **conforme à la spécification exécutable fournie**.
Les tests MBPP sont peu nombreux (trois par tâche) ; un code qui les passe n'est
pas correct au sens d'un noyau. C'est exactement l'écart entre la ligne 5 et la
ligne 6 de `docs/TABLE-DECISION.md`, et c'est ce que le chantier 2 doit chiffrer
dans sa version dégradée (vérificateur circulaire).

---

## 2026-08-21 — DÉCLARATION DE PROTOCOLE (avant exécution) : chantier 2, indépendance du vérificateur

Les sept lignes de `docs/TABLE-DECISION.md` supposent un vérificateur indépendant
du générateur. Le terrain rapporte que les tests écrits par un LLM « renforcent le
comportement existant » — vérification circulaire. Aucune publication trouvée ne
chiffre ce que cela coûte.

### Trois degrés d'indépendance, au lieu des deux prévus au plan

| condition | qui écrit les tests | sur quoi |
|---|---|---|
| **A** | les auteurs de MBPP | l'énoncé (référence) |
| **B1** | le modèle | l'**énoncé** seul, sans voir le code |
| **B2** | le modèle | **son propre code** |

B1 n'était pas au plan. Il correspond à une pratique réelle — générer des tests
depuis la spécification — et il sépare deux effets qui seraient confondus : « les
tests d'un LLM sont faibles » et « les tests écrits en regardant le code sont
circulaires ».

### Métrique

Sur les candidats qui **passent** le vérificateur B :

**taux de faux vérifié** = fraction qui échoue aux tests de référence A.

C'est le chiffre qui manque : la probabilité qu'un système annonce « vérifié »
alors que le code est faux. Métrique secondaire : le **taux de vrai rejeté**
(passe A, échoue B), qui mesure la sévérité excessive.

### Prédictions déposées

- **B2 > B1** en taux de faux vérifié. Écrire les tests en regardant le code
  encode le comportement produit, pas la spécification voulue.
- **B2 sera élevé** — le terrain le décrit comme une garantie nulle ; si le
  chiffre est bas, c'est le terrain qui a tort et il faudra le dire.
- **B1 ne sera pas nul non plus** : un test généré depuis l'énoncé par le même
  modèle partage ses angles morts sur la spécification.

### Contrôle préalable obligatoire

Les tests B2 doivent passer sur le code qui les a engendrés dans la quasi-totalité
des cas. Si ce n'est pas le cas, le modèle produit des tests incohérents avec son
propre code — ce serait un résultat différent de celui visé, et il faudrait
l'analyser avant d'interpréter quoi que ce soit.

### Paramètres

40 tâches MBPP (les 40 premières, sous-ensemble strict du chantier 1), 4 candidats
de code par tâche, seed 42, T = 0.7. B1 généré une fois par tâche (l'énoncé ne
varie pas), B2 généré une fois par candidat. Isolation inchangée : sous-processus,
timeout 5 s, dossier temporaire hors dépôt.
