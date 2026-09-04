# trajectory-probe

How much hallucination can be removed from a language model without giving it any
outside knowledge, and at what price?

This repository answers by measurement. Thirteen steps, every protocol declared
before it ran, every control recorded whether it passed or failed.

## Start here

    python3 the_price.py

One file, standard library only, no GPU and no model download. It reads real
runs recorded on 2026-08-20 and 2026-09-04, prints the coverage reached at the
sampled budget and its exact identity, then times four verifiers of rising
strength on your machine. Timings are measured on your hardware and will differ
from any number quoted below. Everything below
is detail.

## Main result: the decision table

For a given budget, which strength of guarantee is reachable, and over what
fraction of the work. Detail and sources in
[`docs/TABLE-DECISION.md`](docs/TABLE-DECISION.md).

| domain and verifier | coverage | precision | cost per check |
|---|---|---|---|
| empirical, spread across samples | 57.6 % | 70.6 % | ~0 |
| arithmetic, substitution and modulo | 95.2 % | 100 % | < 1 ms |
| code, syntax (`compile`) | 100 % | n/a | 5.3 ms |
| code, runs without exception | 100 % | n/a | 152 ms |
| code, supplied tests | 83.0 % | 100 %\* | 25 ms |
| Lean and Mathlib, targeted imports | 20.0 % | 100 % | 14 s |
| Lean and Mathlib, `import Mathlib` | not measured | 100 % | 187-220 s |

\* meets the executable specification supplied, which is weaker than correctness
in the sense of a proof kernel.

A row reads: with integration tests, 83 % of tasks get an answer carrying a total
guarantee relative to those tests, for 25 ms of checking. Coverage is measured at
ten samples per task, on 100 tasks, and is not a ceiling: see below.

## The twin repository: why the first line tops out

The row "empirical, spread across samples" is the only one that judges the model
by itself. It tops out at 70.6 % precision. Every row above it calls an outside
verifier, of rising strength and rising price.

That shape has a proved counterpart, formalized in a separate repository.
[`lean-lab`](https://github.com/shucrani/lean-lab) follows the diagonal thread:
Cantor, then Lawvere's fixed-point theorem which abstracts it, then halting and
Tarski. The four statements say one thing in four costumes, that a system does
not decide its own truth from the inside. Every file there is kernel-checked with
no `sorry`, and `check_axioms.lean` attests it.

What the link is. The no-go results give the shape of the table: why a precision
column does not reach 100 % without stepping outside the system, and why every
step outside is paid for.

What the link is not. Lawvere does not imply 70.6 %. No theorem predicts a number
measured on GPT-2. The agreement between the two repositories is a coherence, and
it is not a deduction. Confusing them would be the machinery-before-the-fact this
project rules out.

## Two measured regularities

### `coverage = 1 − unsolved share`

Once at least one sample is correct, a verifier finds it. Checked on three
independent domains, once to exact equality: the unsolved share on MBPP is
17/100 = 17.0 %, measured coverage 83.0 %, over 100 tasks at ten samples each.
The 95 % interval on that coverage is [74.5 %, 89.1 %], and the first 60 tasks
reproduce the 2026-08-20 run exactly, so none of that width is sampling noise.

Unsolved is not unsolvable. On the factual corpus, where the same 87 prompts
were drawn 20 times and 40 times independently, 8 of the 17 prompts unsolved at
20 draws produce a correct completion at 40. Half of what a fixed budget calls
a limit of the model is a limit of the budget.

Aggregation captures only part of the stochastic share: 95.2 % against 76.2 % for
majority voting on the same corpus. Verifying and grading part company here.

### Aggregation pays in proportion to the stochastic share

| model, corpus | stochastic share | error reduction by vote |
|---|---|---|
| GPT-2 small, factual | 56 % | 25.3 % |
| Qwen2.5-1.5B, MBPP code | 76.7 % | n/a |
| Qwen2.5-1.5B, factual | 100 %† | 70.2 % |

† corpus ceiling: the questions were written for GPT-2 and no longer carry
difficulty for this model.

## The levers, with numbers

| lever | gain | price |
|---|---|---|
| take the mode (vote or greedy) | 25 % to 70 % fewer errors | none |
| abstain on disagreement across samples | 60 % fewer errors | 42 % of coverage |
| verify by running tests | 100 % precision over 83.0 % | 25 ms |
| verify by proof kernel | 100 % over 20 % | 14 s |

And a bound: 23 % to 44 % of errors are unsolved at the sampled budget depending
on the model and corpus pair, meaning the model got it wrong on every sample
drawn. No aggregation, no
decoding scheme and no perturbation corrects them. They require an outside
source.

Check cost tracks the loaded context rather than the verifier: a factor of 20 to
50 between a targeted Lean import and the global one. Rejecting also costs more
than accepting, 14 s against 6 s in Lean and timeouts at 5 s in Python, a
coupling seen on two unrelated verifiers.

## Negative results, which are results

A signal can be carried entirely by sentence length. On a hand-written
hallucination dataset, counting characters reaches AUC 0.942 where a full
pipeline over hidden states reaches 0.939. Any work on this kind of corpus has to
clear that control before being read.

Nothing in the prompt predicts the outcome. Under same-prompt bifurcation both
classes share the prompt state, and AUC comes out at 0.500 exactly, to the float.
This is an identity, and it closes certification prior to generation.

Cross-layer separation is lexical. The embedding layer reaches 0.84 and the best
layer 0.89, so the twelve transformer blocks add 0.05.

The attractor sits on the correct side. Noise of matched amplitude repairs a
hallucinated trajectory in 6.4 % of cases and corrupts a correct one in 0.8 %.
This contradicts the asymmetry reported on a larger model
([arXiv 2604.15400](https://arxiv.org/abs/2604.15400)), with the scale caveat
assumed.

The repairing direction does not transfer. Cosine similarity across prompts is
0.36, yet transfer repairs 0.8 % against 8.3 % for the prompt's own direction.
Repair works by injecting the answer, which closes autonomous corrective
steering.

## Method

Every measurement is preceded by a control able to invalidate it, and the
protocol goes into [`log.md`](log.md) before the run, with its prediction and its
refutation criterion. Degrees of freedom are frozen in
[`docs/DEGRES-DE-LIBERTE.md`](docs/DEGRES-DE-LIBERTE.md).

Seven controls caught seven real errors, each of which had produced a plausible
and false number:

- `"0"` matched as a substring of `"110"`, giving 15 false positives
- non-answers counted as hallucinations, making the bifurcation rate right by accident
- text and activations drawn from different runs, putting self-patch at 18 % instead of 0 %
- an amplitude effect read as a content effect, reducing a z of 2.96 to nothing
- aggregation per sample instead of per task, turning a vote of +6.8 % into −10.4 %
- agreement approximated instead of exact, turning an AUC of 0.666 into 0.436
- generated tests inconsistent with their own code, which made chantier 2 inconclusive

The last one shows the principle. Without that control, the sentence "circular
verification produces 20.8 % false verified" would have entered the log: citable,
plausible and false.

## What is not measured

- Verifier circularity. Chantier 2 is inconclusive: the model used does not write
  tests consistent with its own code (34 % where near-total was expected). The
  number is absent from this repository and from the literature.
- The repair loop. [NL2VC-60](https://arxiv.org/html/2604.22601v1) reports 0 % to
  81.82 % through iterative verifier feedback. Were that to reproduce here,
  `coverage = 1 − unsolved share` would stop being a bound. Untested.
- Scale. Everything is measured on GPT-2 small (124 M) and Qwen2.5-1.5B-Instruct,
  on a single machine. The partition depends on the model and corpus pair. It is
  measured per model and does not travel.

## Reproducing

```bash
uv venv --python 3.12 .venv && VIRTUAL_ENV=.venv uv pip install torch transformers scikit-learn numpy matplotlib
.venv/bin/python src/c1_surface_confound.py      # surface confound control
.venv/bin/python src/reduction_bound.py          # partition and knowledge-free strategies
.venv/bin/python src/verifiable_bound.py         # verifiable regime, arithmetic
.venv/bin/python src/code_bound.py               # verifiable regime, code (MBPP)
```

For Lean, see [`docs/PROTOCOLE-CIBLE.md`](docs/PROTOCOLE-CIBLE.md). Generated code
runs in an isolated subprocess, with a timeout, outside the repository.

## Layout

```
src/        measurement scripts, one per step
results/    raw timestamped outputs, never the figures alone
docs/       decision table, degrees of freedom, checked references
log.md      dated journal: protocols, predictions, controls, failures
figures/    gpt2/ = measured · synthetic/ = simulated, validates nothing real
```

## Origin

The repository grows out of an earlier programme, ProbatioH1, which set out to
certify latent trajectories. The measurements closed that route and opened
another one, the verifiable regime. The audit of that programme, its axioms and
their status after measurement stay in [`docs/`](docs/). Correcting an archive
would falsify the trace.
