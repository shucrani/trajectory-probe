# CLAUDE.md — trajectory-probe

Projet de recherche, couche 2 (objectif de vie), distinct de Sprinkling Act.
Le CLAUDE.md global (~/CLAUDE.md) s'applique ; ce fichier ajoute les règles
propres à un travail empirique.

## Nature du projet
Interprétabilité : géométrie des trajectoires inter-couches d'un Transformer
comme signal d'hallucination. Deux lignes cohabitent et ne doivent pas être
confondues :
- **ligne empirique** — le notebook GPT-2, seul endroit où quelque chose est mesuré
- **ligne axiomatique** — ProbatioH1 (12 axiomes, modèle jouet), aucune mesure

## Règles dures

1. **Étiqueter la provenance de tout nombre et de toute figure** : mesuré sur un
   modèle réel, ou produit par un simulateur. Jamais dans la même figure sans
   légende explicite. Le doute par défaut = synthétique.
2. **Pas de machinerie avant le fait.** Aucun nouvel axiome, score composite,
   certificat ou carte tant que la mesure qu'il prétend organiser n'existe pas.
   C'est l'erreur qui a coûté CARRT (formalisme élégant sur substrat non testé).
3. **Le résultat négatif est un livrable.** Une hypothèse réfutée proprement se
   garde, se date et s'écrit. On ne la recycle pas en la renommant.
4. **Baseline avant claim.** Toute feature proposée se compare à la métrique
   publiée la plus proche (ici Chain-of-Embedding, Wang et al. ICLR 2025) sur le
   même dataset et le même protocole, avant tout écrit.
5. **Pas de re-tuning sur les mêmes points.** Chaque itération de feature vue sur
   le même dataset gonfle le p-value réel. Si on itère, on le note dans `log.md`
   et on garde un jeu de validation jamais regardé.
6. **Fold-safe, toujours.** PCA, centroïdes, normalisation et statistiques de
   population se calculent sur le train set du pli, jamais sur train+test.
7. **Archiver la sortie brute** de chaque run réel dans `results/`, datée, avec
   le hash du notebook. Une figure sans sa sortie brute n'est pas un résultat.
8. **Écrire dans `log.md`** à chaque run et à chaque décision — ce qui a été
   testé, le nombre obtenu, la conclusion. Datée, jamais réécrite.

## Registre
Sobre, incrémental, insider. « we define / we measure / we compare ». Pas de
vocabulaire grandiose, pas de « framework révolutionnaire », pas de nom latin sur
un modèle jouet. Ce qui n'est pas mesuré se dit « non mesuré ».

## Ce que ce projet n'est pas
Pas de dérive vers la recherche ML généraliste ou la course au SOTA. La question
est étroite et le reste : *ce signal géométrique existe-t-il, et bat-il ce qui est
déjà publié ?*
