# Ordres invisibles — degrés de liberté du protocole

Écrit le 20/08/2026, après sept étapes de mesure.

Chaque résultat de ce dépôt repose sur des choix qui n'ont jamais été énoncés
comme tels : des seuils, des définitions, des bornes. Tant qu'ils restent
implicites, ils sont ajustables après coup — et un protocole ajustable après coup
produit le résultat qu'on attendait. Ce document les nomme et les fige.

**Règle : tout changement à une valeur de ce document est un changement de
protocole. Il se déclare dans `log.md`, avec sa raison, avant le run — jamais
après avoir vu le résultat.**

---

## 1. Constitution du corpus

| Choix | Valeur figée | S'il changeait |
|---|---|---|
| Nombre de prompts candidats | 30 | Plus de prompts = plus de bifurcations exploitables ; ne change aucune conclusion, augmente la puissance. |
| Forme syntaxique | tous « The X of Y is… » | **Critique.** La composante partagée mesurée à l'étape 7 (cos 0.36) est celle d'une famille syntaxique unique. Une forme variée la ferait probablement baisser. |
| Langue | anglais uniquement | Non testé ailleurs. |
| Réponses acceptées | listes d'alias écrites à la main | « longest river » accepte `nile` **et** `amazon`. Un choix plus strict réduirait le taux de Correct. |
| Domaine | faits encyclopédiques courts | Aucun raisonnement, aucune génération longue. |

## 2. Génération

| Choix | Valeur figée | Portée |
|---|---|---|
| Modèle | `gpt2` (124M, 12 blocs) | **La contrainte dominante.** Non instruction-tuned. |
| Température | 0.7 | Fixée d'après Akarlar. Plus haute = plus de bifurcations, plus de bruit. |
| Échantillonnage | `top_k=0`, `top_p=1.0` (pur) | Toute troncature changerait la distribution des issues. |
| `max_new_tokens` | 8 | **Coupe les phrases.** Les trajectoires ne couvrent que le début de la réponse. |
| Budget par prompt | 200 tirages max | Un prompt qui n'atteint pas le quota est écarté — sélection silencieuse en faveur des prompts qui bifurquent facilement. |
| Seed | 42 partout | Un seul seed. Aucune conclusion n'a été répliquée sur un autre. |

## 3. Classification — le choix le plus lourd

| Classe | Règle figée |
|---|---|
| `Correct` | une forme attendue apparaît, **à frontière de mot** |
| `Hallucination` | pas de forme attendue, mais une **entité** assertée : `[A-Z][a-zA-Z]{2,}` ou un nombre, absente du prompt |
| `NoAnswer` | continuation sans entité |
| `Other` | vide ou dégénérée |

**Asymétrie de largeur, non résolue.** `Correct` exige une chaîne précise ;
`Hallucination` accepte n'importe quelle entité. Une classe étroite est plus
difficile à atteindre par hasard qu'une classe large, indépendamment de toute
géométrie. Cette asymétrie de *mesure* peut expliquer une partie de l'asymétrie
de *résultat* observée à l'étape 6 (correction 0 % sous bruit apparié).

C'est le degré de liberté le plus susceptible de renverser une conclusion.
Le test qui le lèverait : imposer à `Hallucination` de nommer une entité du même
type que la réponse attendue (une ville pour une capitale). **Non fait.**

## 4. Extraction des trajectoires

| Choix | Valeur figée | Effet |
|---|---|---|
| Position lue | dernier token uniquement | Le reste de la séquence est ignoré. |
| Indexation des couches | `hidden_states` de transformers : 13 = 1 embedding + 12 blocs | La couche 0 est `wte + wpe` — d'où le constat « la séparation est lexicale ». |
| Couche 12 | **exclue du patching** | Elle est prise après `ln_f` ; un hook sur un bloc ne peut pas la reproduire. |
| K par classe | 6 | Fixé d'après Akarlar. Plafonne la fiabilité des directions (split-half 0.47). |
| Seuil de bifurcation | ≥ 2 par classe sur N | Plus strict = moins de prompts, classes plus franches. |

## 5. Analyse statistique

| Choix | Valeur figée |
|---|---|
| Sonde | `LogisticRegression(C=0.01)` + `StandardScaler`, fold-safe |
| Validation | leave-one-prompt-out, AUC moyennée par pli |
| Permutation | 200 tirages, **contrainte à l'intérieur de chaque prompt** |
| Cellule testée | dernier step, dernière couche — **pré-spécifiée avant de voir la carte** |
| Correction multiple | Bonferroni annoncée quand plusieurs cellules sont comparées |

La carte complète (104 cellules) est **descriptive**. Son maximum n'est jamais
rapporté comme un résultat.

## 6. Patching — la limite structurelle à connaître

| Choix | Valeur figée | Conséquence |
|---|---|---|
| Décodage après patch | greedy | Retire le hasard d'échantillonnage de la mesure causale. |
| Cible du patch | sortie du bloc, dernier token | |
| **Cache KV** | **absent — recalcul complet à chaque step** | **Un patch n'influence la suite que par le token qu'il fait produire.** Il ne persiste pas dans un état mémorisé. Un window patching avec cache mesurerait autre chose, probablement plus proche d'Akarlar. |
| Steps patchés | 1 à 3 (ponctuel), fenêtres 1-4 depuis le step 1 | |
| Couches patchées | 4, 8, 11 (≈ tiers, deux tiers, fin) | Akarlar patche à 71 % et 86 % de la profondeur, soit ≈ 8.5 et 10.3 ici. Zone couverte. |
| Contrôle à w = 1 | self-patch, doit être 0 % | Validé : 0/1080. |
| Contrôle à w > 1 | same-class patch | Le self-patch **ne peut pas** être un no-op au-delà de w = 1 : le contexte a divergé. |
| Comparaison de référence | **à norme égale** | Sans cela on ne mesure que l'amplitude du déplacement — erreur commise à l'étape 5, corrigée à l'étape 6. |

## 7. Ce qui pourrait renverser quoi

Classé par risque décroissant.

1. **L'asymétrie de largeur des classes** (§ 3) peut expliquer une partie du
   résultat central de l'étape 6. → imposer un type d'entité à `Hallucination`.
2. **L'absence de cache KV** (§ 6) borne ce que le window patching peut montrer.
   → réimplémenter avec cache, seule façon de comparer vraiment à Akarlar.
3. **Le modèle** (§ 2). 124M non instruction-tuned. L'absence de transfert de la
   direction de réparation (étape 7) est peut-être un fait sur GPT-2 small, pas
   sur les transformers. → répliquer sur Qwen2.5-0.5B-Instruct.
4. **La forme syntaxique unique** (§ 1) surestime probablement la composante
   partagée entre prompts — ce qui rend l'absence de transfert plus forte, pas
   plus faible.
5. **Le seed unique** (§ 2). Aucune conclusion n'a été répliquée sur un autre.

## 8. Ce qui ne bougera pas

Deux résultats ne dépendent d'aucune valeur de ce document.

- **Step 0 → AUC = 0.500 exactement.** Les deux classes partagent le même état de
  prompt : c'est une identité, pas une mesure. Rien ne peut la déplacer.
- **C1 : le comptage de caractères atteint 0.942 sur le dataset artisanal**, contre
  0.939 pour le pipeline complet. Aucun réglage de sonde ou de couche ne rattrape
  un dataset dont les classes diffèrent par la longueur.
