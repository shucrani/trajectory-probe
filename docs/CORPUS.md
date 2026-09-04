# Corpus: what the field holds, and where this repository still stands

Nineteen papers downloaded on 2026-09-04, listed by arXiv id. The PDFs and their
text extractions stay out of the repository. What follows is measured over the
extracted text rather than recalled, and the counts are reproducible with grep.

## What the corpus establishes about the field

Ceilings are heavily worked. The word family around irreducible, ceiling,
saturation, plateau and upper bound appears 36 times in one paper alone, 20 in
another, 17 in a third. Any claim that a sampling ceiling is a new idea would be
false.

Cost is barely present. The vocabulary of GPU hours, FLOPs, inference cost,
compute budget, overhead, throughput, wall-clock and latency peaks at 7
occurrences and sits at 0 in eleven of the eighteen extracted papers.

The class of tasks where no sample is ever correct is named nowhere. The patterns
"never correct", "all samples wrong", "pass@k stays 0" and "no sample" return
zero across all eighteen. The field bounds what verification can recover. It does
not characterise the subset that generation never produces.

One extraction failed: `2604.04743` yields no text, so it is excluded from every
count above and needs a different route.

## The three papers that bear directly on this work

### 2607.13918, Han, Partially Correlated Verifier Cascades

Models serial verification gates with a per-instance false-accept rate as a
latent variable. A blind-spot atom of mass 1 − π at α = 1 caps total extractable
evidence at −ln(1 − π) nats, so reliability saturates strictly below 1. The lever
it isolates is decorrelation rather than adding gates.

This is a ceiling on the verifier side: errors a verifier accepts every time. The
systematic share measured here is a ceiling on the generator side: tasks where no
sample is correct. They are different quantities and they compose. Nobody has
composed them.

The paper validates on synthetic recovery experiments. This repository holds the
rule that `figures/synthetic/` validates nothing real, and a triple synthetic
guard that caught seven errors. Measuring Han's ceiling on real runs is an open
and well-defined piece of work.

### 2606.02628, Aiersilan, Hallucination Is Linearly Decodable from Mid-Layer Hidden States

Reports 0.904 to 1.000 AUROC for a linear probe on one mid-network layer, across
three 7B to 8B instruction-tuned models on four benchmarks, against 0.541 for
sampling-based detectors.

No surface-confound control appears in the abstract or the protocol. The C1
control in this repository found that counting characters reaches AUC 0.942 on a
hand-written hallucination corpus, against 0.939 for a full pipeline over hidden
states. Running C1 against their setup is cheap, and either it clears their
numbers or it moves them.

Their layer band also sits against a measurement made here: on GPT-2 the
embedding layer alone reaches 0.84 and the best layer 0.89, so the twelve blocks
add 0.05. Their peak bands are blocks 13 to 18 of 32, and 19 to 25 of 28. Whether
their signal survives a lexical control is untested by them.

### 2605.25133, Sedoc, Zhang and Foster, Trust but Verify

Prover-verifier deliberation for selective prediction, characterised through its
coverage-precision behaviour, reaching 84.2 % precision at 77 % coverage for
roughly three LLM calls.

Closest thing in the corpus to a price axis, and it counts calls. The decision
table here counts seconds and milliseconds, separates the cost of accepting from
the cost of rejecting, and traces the factor of 20 to 50 back to loaded context.
Counting calls hides all three.

## The rest, and what each is good for

`2509.20837` Verification Limits Code LLM Training, and `2606.20740` VeriBound,
carry the published ceilings this repository has to replicate against rather than
rediscover. `2502.00271` Scaling Flaws of Verifier-Guided Search and `2607.05391`
LLM-as-a-Verifier hold the current framing of verification as a scaling axis.
`2606.09376` Precision Is Not Faithfulness and `2506.11021` Functional Clustering
occupy the abstention question, which is the only level of the old programme that
survived here. `2602.21189` bears on pass@k optimisation.

`2604.15400` Akarlar is the paper the attractor inversion contradicts, and it
stays in the corpus for that reason. `2604.22601` NL2VC-60 reports 0 % to 81.82 %
through iterative verifier feedback, which is the untested loop that would stop
`coverage = 1 − systematic share` from being a bound.

`2604.16347` Lean Atlas, `2509.19632` Harder-Narasimhan and `2507.05327` Divided
Powers are the format target: a short arXiv note accompanying a formalization,
with no affiliation and no committee. `2604.14584` covers Bernstein-Sato in
positive characteristic and confirms the topic is mathematically live while
remaining unformalized.

## What holds and what does not

Consolidated: the price axis, absent from the corpus by measurement rather than
by assumption. Consolidated: the characterisation of the systematic class, named
nowhere. Consolidated: the surface-confound control, which one recent paper
reporting near-perfect AUROC does not run.

Not new: the existence of a ceiling. Occupied: abstention, worked by at least
four papers in this corpus, so any claim there is positioned against them rather
than first.

Reproduce the counts with:

    pdftotext each PDF, then grep -cioE over the patterns named above

## Second pass, 2026-09-04: one axis falls

Five more papers, corpus now at 24.

`2606.22864`, When AUC 0.998 Is Not Enough (Northeastern, UIUC, SMU, 22 June
2026), already performs the C1 move: a paired-construction scalar baseline over
text-side surfaces, on the same train/val/test split, showing that a near-perfect
headline AUC does not license the reading placed on it. Twenty-three occurrences
of surface-shortcut vocabulary.

`2508.08285` The Illusion of Progress and `2605.17028` PARALLAX work the same
seam: benchmark construction artefacts, and length-based baselines matching
complex probes.

C1 therefore stops being a contribution here. It becomes an instrument confirmed
by independent convergence, arrived at without knowledge of these papers. Running
it against `2606.02628` stays a useful replication and stops being a new result.

`2507.16488` ICR Probe exists, ACL 2025. An earlier note in this project recorded
it as untraceable, which was wrong.

The two remaining axes survive the pass. No paper in the corpus composes the
generator-side and verifier-side ceilings, and none takes price as a first-class
axis.
