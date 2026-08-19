# Références — statut de vérification

Vérifié le 19/08/2026 par recherche web. Trois catégories : **existe** (trouvé,
chiffres confirmés) · **non confirmé sous ce nom** · **non vérifié**.

## Existe — vérifié

**Akarlar, « Hallucination as Trajectory Commitment: Causal Evidence for
Asymmetric Attractor Dynamics in Transformer Generation »**, arXiv 2604.15400,
avril 2026. Code : github.com/akarlaraytu/trajectory-commitment
- Activation patching sur 28 couches. Corruption (correct → halluciné) : **87.5 %
  à la couche 20**. Correction inverse : **33.3 % à la couche 24**. Chiffres du
  rapport v2 confirmés.
- Window patching : la correction exige une intervention soutenue multi-étapes ;
  la corruption ne demande qu'une seule perturbation.
- **Point décisif pour nous** : le protocole est la *same-prompt bifurcation* —
  un même prompt est échantillonné de façon répétée pour observer la divergence
  spontanée, explicitement afin d'**isoler la dynamique de trajectoire des
  confonds de niveau prompt**. C'est la solution publiée au confond décrit dans
  le README § 3.

**« Hallucination Basins: A Dynamic Framework for Understanding and Controlling
LLM Hallucinations »**, arXiv 2604.04743, avril 2026.
- Bassins attracteurs dans les espaces latents couche par couche, utilisés comme
  mécanisme de steering. C'est le voisin direct de G3/D1.

**Wang et al., Chain-of-Embedding**, ICLR 2025 — déjà répliquée ici (AUC 0.873).

**FactCheckmate**, Alnuhait et al., EMNLP Findings 2025 — +34.4 % de facticité
par intervention précoce. Chiffre confirmé indépendamment (récapitulatif § 2.3).

## Voisins découverts pendant la vérification — à lire avant tout écrit

- **« Quickest Detection of Hallucination Onset: Delay Bounds and Learned CUSUM
  Statistics »**, arXiv 2606.12476, juin 2026. **Traite exactement le problème du
  test irréductible (§ IX) — détection précoce avec bornes de délai prouvées —
  par la détection séquentielle classique (CUSUM).** Antériorité la plus directe
  sur la partie « certification précoce ».
- **« Reasoning as Attractor Dynamics »**, arXiv 2606.24543, juin 2026 — bassins
  larges pour le raisonnement correct, minima instables pour l'hallucination.
- **« Attention Sinks as Internal Signals for Hallucination Detection »**,
  arXiv 2604.10697.
- **ICLR 2026** — interventions sur attracteurs, sans entraînement.
- **MultiHaluDet**, arXiv 2605.24919 — probing des états cachés, multilingue.

## Non confirmé sous ce nom

**« ICR Probe » (ACL 2025)** — pas retrouvé sous ce titre. Travaux voisins
existants à ACL 2025 : **PRISM** (« Prompt-Guided Internal States for
Hallucination Detection », aclanthology 2025.acl-long.1058) et
**ReDeEP** (ICLR 2025). Le pic de détection en couches moyennes attribué à
« ICR Probe » doit être re-sourcé avant toute citation.

Incohérence interne à signaler : le rapport v2 situe ce pic aux **couches 10-15
sur 28** ; la figure `probatioh1_v2_stability.png` le dessine à la **couche 4
sur 8**. Les deux ne peuvent pas décrire la même mesure.

## Non vérifié — à faire avant citation

- **ARS (2026), « Answer-Agreement Representation Shaping »**
- **H-Neurons (Emergent Mind 2026)** — « AUROC 0.80-0.95 sur 6 familles »
- **Global Evolutionary Steering (2026)** — « saturation k ≈ 22-26 sur 28 »
- **Heimersheim & Turner 2023** (fondement de P1, croissance exponentielle des
  normes du residual stream) — plausible et probablement correct, mais non
  re-vérifié ici.

## Conséquence sur le claim d'interstice

« L'interstice est vierge » n'est pas soutenable. Entre avril et juin 2026 le
champ a produit : les bassins d'hallucination, l'asymétrie causale
corruption/correction, les interventions sur attracteurs, et la détection
séquentielle avec bornes de délai. C'est un sujet chaud, pas une case vide.
Ce qui reste éventuellement libre est plus étroit : le **protocole de validation**
(garde-fou triple) et la **gradation de récupérabilité** — à condition qu'ils
soient testés.

---

## Cadre incertitude / confabulation (recherche du 20/08/2026)

Le recadrage sur la **réduction** place le projet dans une littérature différente
de celle de la géométrie latente. Vérifié inline, sources primaires.

**Farquhar et al., « Detecting hallucinations in large language models using
semantic entropy », Nature 630, 625-630 (2024).**
Entropie calculée au niveau du **sens** et non des tokens : les réponses sont
regroupées par implication bidirectionnelle (A entraîne B et B entraîne A), puis
l'entropie est calculée sur les grappes. Une seule grappe = modèle confiant ;
beaucoup de petites grappes = confabulation. Ne demande aucune vérité terrain.
→ C'est notre catégorie **BIFURQUANT**, avec une mesure plus fine que notre
simple accord d'entités (0.666 d'AUC chez nous — l'entropie sémantique ferait
mieux).
→ Les auteurs précisent qu'ils **ne distinguent pas** incertitude aléatoire et
épistémique.

**Définition de la confabulation** : une affirmation à la fois fausse et
**arbitraire** — sensible au seed. Explicitement distinguée des cas où le modèle
est *systématiquement* faux pour cause de données d'entraînement erronées, ou par
échec de raisonnement. C'est exactement notre partition BIFURQUANT / TOUJOURS-FAUX.

**« Delusions of Large Language Models », arXiv 2503.06709.**
Les *delusions* sont des hallucinations à **haute croyance** : contrairement aux
hallucinations ordinaires qui s'accompagnent d'incertitude, elles présentent une
**faible** incertitude, ce qui les rend difficiles à détecter et à corriger.
→ Notre TOUJOURS-FAUX, et l'explication de notre AUC d'abstention plafonnée.

**« HACK: Hallucinations Along Certainty and Knowledge Axes », arXiv 2510.24222**
(Technion, Google Research, Oxford, Hebrew University, Harvard).
Deux axes : la connaissance est-elle présente dans les paramètres, et le modèle
est-il certain. Le sous-ensemble critique identifié : **halluciner avec certitude
alors que la connaissance correcte est présente**. Les méthodes de mitigation
« bonnes en moyenne » échouent de façon **disproportionnée** sur ce sous-ensemble.
→ Confirme que la moyenne masque le cas dangereux, et justifie de rapporter la
partition plutôt qu'un taux global.

**« Representation-based Broad Hallucination Detectors Fail to Generalize Out of
Distribution », arXiv 2509.19372.**
→ Converge avec notre étape 7 : la direction de réparation ne se transfère pas
d'un prompt à l'autre (0.8 % contre 8.3 %).

### Le trou

La recherche ne retourne **aucune quantification de la proportion**
confabulation / erreur systématique. Le cadre conceptuel est posé et bien cité ;
le ratio, non — et c'est lui qui borne le rendement de toute méthode fondée sur
l'incertitude.

C'est ce que mesure l'étape 10 : **56 % stochastique / 44 % systématique** sur
GPT-2 small, et la mesure est en cours sur Qwen2.5-1.5B-Instruct. Si le chiffre
se déplace fortement avec la taille et l'instruction-tuning, c'est une donnée
utile au champ ; s'il est stable, c'est une borne.
