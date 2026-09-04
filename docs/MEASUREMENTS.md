# What was measured, and what each measurement does not establish

Seven measurements sit in `results/` and were cited by nothing: not the README,
not `the_price.py`, not the other documents. This file states them, each with
the control that was run and the reservation that limits it.

A measurement nobody states is not a result. It is a file.

---

## The four patching steps (GPT-2 124M)

These four steps ask one question in sequence: does the internal state carry the
outcome, or only accompany it? They are not a replication attempt. Akarlar
reports on Qwen2.5-1.5B with 28 layers; every number below is GPT-2 124M with 12
layers. Different model, different depth. Where the numbers diverge from
Akarlar, that divergence is not evidence against Akarlar. It is a measurement on
another system, and the reference is quoted only to say what shape was expected.

### Step 4 — single-point patching · `causal_patching_20260820_0009`

Patch one activation at one step and one layer, then decode greedily so that
sampling noise is out of the measurement.

Control: self-patching changes 0 of 1080 generations. Patching a state with its
own activation must be a no-op, and is. The mechanism is sound.

| | rate | against random patch | |
|---|---|---|---|
| corruption, correct ← hallucination | 6.7 % (36/540) | 6.5 % (70/1080) | z = +0.14 |
| correction, hallucination ← correct | 4.4 % (24/540) | 6.5 % (70/1080) | z = −1.65 |

The rates are read from the run. The two z values are not: the run reported the
three rates side by side without testing them against each other, and they are
computed here as two-proportion tests. That absence is why the step could read
as a result for as long as it did.

**This step establishes nothing.** Both effects are indistinguishable from a
random patch, and correction sits below it. Akarlar's shape, corruption 87.5 %
and correction 33.3 %, does not appear at this scale on this model. The step is
reported here because a null result obtained under a passing control is worth
more than a null result nobody ran.

### Step 5 — window patching · `window_patching_20260820_0032`

Impose the donor trajectory over a window of 1 to 4 steps, and compare
cross-class against same-class at equal window, so that both carry the same
context shift and only the content of the state differs.

| window | corruption vs same-class | correction vs same-class |
|---|---|---|
| 1 | z = 1.05 | z = 0.00 |
| 2 | z = 2.54 | z = 1.45 |
| 3 | z = 2.96 | z = 1.22 |
| 4 | z = 2.11 | z = 2.28 |

Corruption separates from same-class from window 2 onward. Correction only at
window 4. The ordering is consistent with the reference expectation, corruption
in one shot and correction requiring sustained intervention, at roughly a fifth
of the reported magnitude.

Reservation: the self-patch control is defined only at window 1, where it passes
at 0/360. Beyond one step the context diverges and no no-op exists, so windows 2
to 4 rest on the cross-versus-same comparison alone.

### Step 6 — norm-matched patching · `normmatched_20260820_0059`

The decisive control. The patch is placed at the same L2 distance from the
recipient state as the donor state, but in a random direction: same amplitude,
none of the other class's content.

| | cross-class | norm-matched | |
|---|---|---|---|
| corruption | 9.2 % | 0.8 % | z = 5.13 (n=357) |
| correction | 14.6 % | 6.4 % | z = 3.54 (n=357) |

**This is where the causal effect is established.** The content of the state
matters beyond its amplitude. Step 4 did not show this because it compared
against a random patch rather than against an amplitude-matched one.

The asymmetry runs the other way from the reference: correction 14.6 % against
corruption 9.2 %. On this model, at this budget, the attractor sits on the
correct side. Stated as measured, not as a claim about larger models.

### Step 7 — is the repairing direction shared? · `repair_direction_20260820_0045`

If a direction computed on other prompts repairs a prompt it never saw, it is a
steering vector and it is usable. All conditions at equal norm:

| | repair rate | |
|---|---|---|
| oracle-pair (step 6) | 12.1 % (16/132) | |
| oracle-prompt (ceiling) | 8.3 % (11/132) | |
| transfer, other prompts | 0.8 % (1/132) | z = −1.01 against random |
| random (floor) | 2.3 % (3/132) | |

**Transfer fails.** It does not beat the random floor, while oracle-prompt does
repair (z = −2.95 between them). The direction exists and is specific to each
case: observable, unusable. Building the vector that leads to the answer
requires already knowing the answer.

This closes a door. Any plan resting on a transferable steering direction, on
this model at this scale, starts from a measured negative.

---

## Two cost measurements

### Step 12 — what a proof-checked regime actually costs · `lean_cost_...20260820_1001`

Qwen2.5-1.5B, N=8 candidates per statement, Lean 4 with Mathlib.

- candidates that compile: 4/160 = **2.5 %**
- statements covered by at least one valid candidate: 4/20 = **20 %**
- 112.3 s per statement, against under a millisecond for the arithmetic regime

Precision is 100 % by construction, since the kernel admits nothing false. What
changes between verifiable regimes is coverage and cost. A collapsing coverage
means a guarantee that is perfect and empty: right, about almost nothing.

### Chantier 2 — is the verifier independent? · `verifier_independence_20260821_1352`

Qwen2.5-1.5B, 40 tasks, 4 candidates each, 156 executable candidates. Two
generated verifiers are scored against the MBPP reference tests.

| | falsely verified | truly rejected | agreement with reference |
|---|---|---|---|
| B1, tests written from the statement | 13.2 % | 48.0 % | 61.4 % |
| B2, tests written from the code | 20.8 % | 43.7 % | 64.1 % |

"Falsely verified" is the probability that a system announces VERIFIED on code
the reference rejects. A verifier with a high rate there does not deliver a weak
guarantee. It delivers none, while producing the appearance of verification.

**Control failed.** B2's tests pass on the code that generated them only 53/156
= 34 % of the time, where near-total was expected. B2 is disqualified by its own
control: the model writes tests inconsistent with its own code, which is a
separate finding and not the one sought. B1 does not depend on that control and
its 13.2 % stands, conditional on the MBPP reference itself being sound, which
this measurement does not test.

The commit that recorded this run called the chantier inconclusive. That verdict
holds for the chantier. It does not erase B1.

---

## Step 1 — the bifurcation rates · `bifurcation_gpt2_typed_20260820_0056`

87 prompts, N=40 completions, T=0.7, GPT-2, classes matched by type.

This is not the input to part A of `the_price.py`. Part A reads step 10,
`reduction_bound_20260820_0115`, which covers the same 87 prompts at N=20. Step
1 is the same population sampled twice as deeply, and nothing reads it.

That made it the one place where the sampling-budget question could be asked on
data already in hand. Part A calls a prompt unsolved when none of 20 samples is
correct; step 1 drew 40 of them, on the same prompts, same model, same
temperature, same completion length. The comparison was run on 2026-09-04.

Control first, since the two correctness criteria come from different scripts:
mean correct rate 10.9 % at N=20 against 11.1 % at N=40, per-prompt correlation
0.951. The criteria agree, so the comparison is legitimate.

**Eight of the seventeen prompts counted unsolved at 20 draws produce a correct
completion at 40.** Those completions were observed. For those eight, the
probability of a correct sample is not zero, and no test is needed to say so.
Nearly half of what part A called unsolved was a limit of the budget rather than
a limit of the model.

Three prompts move the other way, which two independent runs will do. On the
aggregate the claim is weaker and is reported as such: coverage 71.2 % at K=20
against 79.7 % at K=40 on the 59 asserting prompts, McNemar exact on the 11
discordant prompts p = 0.23. Not established. The certain part is the eight
observed completions; the aggregate needs K raised on one population rather than
two runs compared.

Both files also record that 28 of 87 prompts are silent, 32 %, the model
asserting nothing at all. Silence is not error and is excluded from the coverage
figure. Whether it should be is a question about what the measurement is for,
and it has been argued nowhere.
