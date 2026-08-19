# Protocole cible — sortir du dataset confondu

Écrit le 19/08/2026, après l'échec du contrôle C1 (le comptage de mots égale le
pipeline complet : 0.939). Toute suite du projet passe par un protocole où les
deux classes **ne peuvent pas** différer en surface.

## Option A — Same-prompt bifurcation (Akarlar, arXiv 2604.15400)

Les deux classes proviennent du **même prompt**. Le confond de surface est
impossible par construction : la question porteuse est identique, seule la
complétion échantillonnée diffère.

Paramètres publiés :

| Élément | Valeur |
|---|---|
| Complétions par prompt | N = 20, température τ = 0.7 |
| Classification | Correct / Hallucination / Other, par *substring matching* |
| Critère de bifurcation | ≥ 2 Correct **et** ≥ 2 Hallucination sur les N |
| Trajectoires conservées | K = 6 runs par classe, residual stream complet à chaque (couche, step) |
| Modèle de référence | Qwen2.5-1.5B |
| Rendement observé | 27 prompts bifurquent sur 61 (44.3 %) |
| Divergence | dès le **premier token généré** |

Code : github.com/akarlaraytu/trajectory-commitment

**Réserve sur GPT-2 small.** Le protocole suppose un modèle capable de produire
des complétions correctes en quantité suffisante. GPT-2 small (124M) est bien plus
faible que Qwen2.5-1.5B : le taux de bifurcation sera plus bas, peut-être trop
pour constituer un échantillon. À mesurer avant d'investir — et si le rendement
est insuffisant, monter à `gpt2-large` ou passer à Qwen2.5-0.5B/1.5B, qui tournent
sur CPU.

**Ce que ce protocole change pour le projet** : la question devient « la
trajectoire du prompt prédit-elle *quelle branche* le modèle va prendre ? ».
C'est la question que ProbatioH1 pose depuis le début, et c'est la première fois
qu'elle serait réellement mesurée.

## Option B — Datasets appariés existants

TruthfulQA et HaluEval sont construits en **paires** : une même question porteuse,
une réponse correcte et une réponse incorrecte. L'appariement est au niveau de la
question, pas de la réponse.

⚠️ **L'appariement de la question ne garantit pas l'absence de confond dans la
réponse.** Les réponses correctes et incorrectes peuvent encore différer en
longueur ou en registre.

→ **Règle dure : exécuter `src/c1_surface_confound.py` sur tout nouveau dataset
avant de l'utiliser.** C1 devient une condition d'entrée, pas un contrôle
a posteriori.

## La barre à battre est haute

Une **sonde linéaire sur une seule couche médiane** atteint **0.904-1.000 AUROC**
sur TruthfulQA, HaluEval-QA et FEVER (Llama-3.1-8B, Mistral-7B, Qwen2.5-7B) —
arXiv 2606.02628. Bandes de couches optimales : blocs 13-18 sur 32 (Llama,
Mistral), 19-25 sur 28 (Qwen).

Et surtout : *« le signal de véracité est approximativement linéaire — les sondes
MLP dépassent rarement les sondes linéaires de plus de 0.01 AUROC »*.

**Conséquence directe pour ProbatioH1** : si une régression logistique sur les
activations d'une couche atteint 0.90+, une machinerie de courbure, de dwell time
et de certificats doit démontrer qu'elle apporte quelque chose que la sonde
linéaire n'a pas. Ce quelque chose ne peut plus être l'AUC. Les candidats
restants sont la **précocité** (détecter plus tôt dans la génération) et
l'**actionnabilité** (dire quoi faire, pas seulement détecter) — ce qui est
précisément la promesse de G0-G6, et ce qui devient donc le seul terrain où le
programme peut se distinguer.

## Voisins directs à lire avant tout écrit

- **arXiv 2606.02628** — sonde linéaire mid-layer, 0.904-1.000 AUROC. La barre.
- **arXiv 2605.13772** — « Where Does Reasoning Break? Step-Level Hallucination
  Detection via Hidden-State Transport Geometry ». Géométrie du transport des
  états cachés : le voisin le plus proche du projet.
- **arXiv 2510.04933** — « The Geometry of Truth: Layer-wise Semantic Dynamics »
  (le « LSD » cité dans le récapitulatif — existe bien).
- **arXiv 2606.12476** — détection séquentielle CUSUM avec bornes de délai.
- **arXiv 2606.06959** — OpenHalDet, benchmark unifié.
- **arXiv 2605.24919** — MultiHaluDet, probing multilingue.

## Séquence

1. Mesurer le taux de bifurcation de GPT-2 small sur ~60 prompts factuels
   (N = 20, τ = 0.7). **Décide si le protocole A est praticable à cette taille.**
2. Si oui : extraire K = 6 trajectoires par classe, refaire tourner les features.
   Si non : monter en taille de modèle, ou basculer sur option B avec C1 en garde.
3. Comparer d'abord à la **sonde linéaire**, pas à CoE. C'est elle la barre.
4. Seulement ensuite : progressivité couche par couche, et test causal
   d'intervention pour D2.
