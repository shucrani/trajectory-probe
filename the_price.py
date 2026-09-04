"""What a guarantee costs.

One file, standard library only, one command:

    python3 the_price.py

Sampling a language model many times fixes some errors and, at the budgets used
here, leaves others untouched. That share is a floor at this budget and not a
floor in the limit: a task no sample solves in K draws may be out of reach for
this model, or merely rare, and finite sampling does not separate the two.
Crossing it requires a verifier, and every verifier has a price. This file
measures both halves at a stated budget and prints the table.

What it does not measure, and what would have to be measured to say ceiling:
how coverage moves when K rises on the tasks left uncovered, and how often a
candidate that passes the supplied tests is nonetheless wrong.

Part A reads real runs: 87 prompts, 20 samples each, GPT-2 at T=0.7, recorded
2026-08-20. Nothing is generated here, so no GPU and no model download.

Part B times four verifiers of rising strength on tasks carried in this file.
The timings are measured when you run it, on your machine.

Part C measures how strong those verifiers are, over 600 recorded samples from
a second system: Qwen2.5-1.5B-Instruct on 60 MBPP tasks, recorded 2026-08-20.

Part D composes the two limits of that second system. Part A is a separate
measurement, on another model and another corpus. It is not an input to the
composition and must not be read as one.

Everything else in this repository is detail. Read this and you have the result.
"""
import json
import math
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

RUNS = Path(__file__).parent / "results" / "reduction_bound_20260820_0115.json"
CODE_RUNS = (Path(__file__).parent / "results" /
             "code_bound_Qwen2.5-1.5B-Instruct_20260904_1045.json")
DEEP = (Path(__file__).parent / "results" /
        "bifurcation_gpt2_typed_20260820_0056.json")
BUDGET = (Path(__file__).parent / "results" /
          "budget_scaling_100_partiel_10sur17.json")


# ---------------------------------------------------------------- Part A

def partition():
    """Split real prompts by what 20 samples ever produced.

    always-right   every sample correct       nothing to fix
    bifurcating    some correct, some wrong   sampling can fix this
    always-wrong   no sample correct          sampling never fixes this
    silent         the model asserts nothing  outside the question
    """
    rows = json.loads(RUNS.read_text())["rows"]
    buckets = {"always-right": 0, "bifurcating": 0, "always-wrong": 0, "silent": 0}
    name = {"TOUJOURS-CORRECT": "always-right", "BIFURQUANT": "bifurcating",
            "TOUJOURS-FAUX": "always-wrong", "MUET": "silent"}
    for r in rows:
        buckets[name[r["categorie"]]] += 1
    return buckets, len(rows)


def budget():
    """The same 87 prompts drawn 20 times, and drawn 40 times, independently.

    Two separate runs, same model and temperature and completion length. The 40
    draws do not contain the 20, so this is two estimates of coverage and not
    one nested in the other.

    What it settles is narrow and certain. A prompt counted unsolved at 20 draws
    can produce a correct completion at 40. Those completions were observed, so
    for those prompts the probability of a correct sample is not zero, whatever
    the word ceiling suggests. What it does not settle is whether coverage rises
    in aggregate: some prompts go the other way, and the paired test on the
    discordant ones is reported here rather than hidden.
    """
    deep = {r["prompt"]: r for r in json.loads(DEEP.read_text())}
    shallow = {r["prompt"]: r for r in json.loads(RUNS.read_text())["rows"]}
    common = [q for q in shallow
              if shallow[q]["categorie"] != "MUET" and q in deep]
    unsolved = [q for q in common if shallow[q]["correct"] == 0]
    gained = sum(1 for q in unsolved if deep[q]["counts"]["Correct"] > 0)
    lost = sum(1 for q in common if shallow[q]["correct"] > 0
               and deep[q]["counts"]["Correct"] == 0)
    # McNemar, exact and two-sided, on the discordant prompts only.
    d = gained + lost
    tail = sum(math.comb(d, i) for i in range(gained, d + 1)) / 2 ** d
    return len(unsolved), gained, lost, min(1.0, 2 * tail)


def law(buckets):
    """coverage = 1 - unsolved share, over prompts where the model asserts.

    Unsolved means every one of the 20 samples is wrong. A verifier picks a
    correct sample when one is present, so what it can reach is exactly the
    complement of that share, at this budget and no further.
    """
    asserting = buckets["always-right"] + buckets["bifurcating"] + buckets["always-wrong"]
    unsolved = buckets["always-wrong"] / asserting
    coverage = (buckets["always-right"] + buckets["bifurcating"]) / asserting
    assert abs(coverage - (1 - unsolved)) < 1e-12, "the identity failed"
    return asserting, unsolved, coverage


# ---------------------------------------------------------------- Part B

ARITHMETIC = [("17 * 23", "391"), ("2 ** 10", "1024"), ("144 // 12", "12")]

# (source, tests, is_actually_correct). The third field is the ground truth a
# verifier does not see. Precision is measured against it.
CODE = [
    ("def f(n): return n * 2", "assert f(3) == 6", True),
    ("def f(n): return n + 2", "assert f(3) == 6", False),   # wrong, tests catch it
    ("def f(n): return n *", "assert f(3) == 6", False),     # broken, syntax catches it
]


def timed(fn, *a):
    t0 = time.perf_counter()
    out = fn(*a)
    return out, time.perf_counter() - t0


def v_dispersion(samples):
    """Weakest: agree with yourself. Reads no ground truth, so it cannot certify."""
    top = statistics.mode(samples)
    return sum(s == top for s in samples) / len(samples) > 0.5


def v_arithmetic(expr, expected):
    """Substitution. Total precision, and only where an expression exists."""
    try:
        return str(eval(expr, {"__builtins__": {}})) == expected
    except Exception:
        return False


def v_syntax(code, _tests):
    """The code parses. compile does not run it, so this is safe in-process."""
    try:
        compile(code, "<candidate>", "exec")
        return True
    except SyntaxError:
        return False


def v_execution(code, tests):
    """The supplied tests pass. Strongest here, and the slowest.

    Runs in a subprocess with a timeout, in a temp directory outside the repo.
    Never exec in this process.
    """
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "candidate.py"
        f.write_text(code + "\n" + tests + "\n")
        try:
            r = subprocess.run([sys.executable, str(f)], cwd=d,
                               capture_output=True, timeout=5)
            return r.returncode == 0
        except subprocess.TimeoutExpired:
            return False


def price():
    """Time each verifier over the same work, once. Returns (name, seconds).

    Price only. How strong each verifier is gets measured in part C, on recorded
    runs, because strength read off three hand-written candidates would say more
    about the candidates than about the verifier.
    """
    rows = []

    # Warm-up. The first call pays import and allocation costs that belong to
    # neither the verifier nor the machine, and it inflated the weakest row.
    v_dispersion(["a", "a", "b"])
    v_arithmetic("1 + 1", "2")
    v_syntax("x = 1", "")
    v_execution("x = 1", "assert x == 1")

    samples = ["391", "391", "390", "391", "17"]
    t0 = time.perf_counter()
    for _ in range(100):
        v_dispersion(samples)
    rows.append(("dispersion across samples", (time.perf_counter() - t0) / 100))

    t0 = time.perf_counter()
    for e, x in ARITHMETIC:
        v_arithmetic(e, x)
    rows.append(("arithmetic, substitution", (time.perf_counter() - t0) / len(ARITHMETIC)))

    t0 = time.perf_counter()
    for c, t, _ in CODE:
        v_syntax(c, t)
    rows.append(("code, syntax", (time.perf_counter() - t0) / len(CODE)))

    t0 = time.perf_counter()
    for c, t, _ in CODE:
        v_execution(c, t)
    rows.append(("code, supplied tests", (time.perf_counter() - t0) / len(CODE)))

    return rows


# ---------------------------------------------------------------- Part C

def coverage_and_precision():
    """Coverage at a fixed budget, and what the verifier does with it.

    100 MBPP tasks, 10 samples each, Qwen2.5-1.5B-Instruct, recorded 2026-09-04.
    The first 60 reproduce the 2026-08-20 run exactly, task for task, so the
    pipeline is deterministic and none of the width below is sampling noise.
    Every sample carries the verdict of three verifiers of rising strength:
    syntax, runs without exception, supplied tests.

    Tests stand in for ground truth here. They are the strongest verifier on
    hand, not truth, and a candidate that passes the supplied tests can still be
    wrong. Every number below inherits that limit.
    """
    rows = json.loads(CODE_RUNS.read_text())["rows"]
    samples = [s for r in rows for s in r["results"]]

    # Ceiling one, on the generator. Tasks where no sample ever passes.
    never = sum(1 for r in rows if r["n_ok"] == 0)
    single = sum(r["n_ok"] / r["n"] for r in rows) / len(rows)

    # Ceiling two, on the verifier. Over the samples the strongest verifier
    # rejects, the share a weaker one waves through. These are the errors it
    # cannot see, at any number of calls, because its verdict is a function of
    # the candidate and does not vary between calls.
    wrong = [s for s in samples if not s["tests"]]
    stats = {}
    for weak in ("syntax", "runs"):
        accepted = [s for s in samples if s[weak]]
        stats[weak] = {
            "blind": sum(s[weak] for s in wrong) / len(wrong),
            "accepts": len(accepted) / len(samples),
            "precision": sum(s["tests"] for s in accepted) / len(accepted),
        }

    # Two different verifiers in series. Stacking one verifier k times changes
    # nothing, so the only lever is a second verifier that fails differently.
    both = [s for s in samples if s["syntax"] and s["runs"]]
    stats["syntax AND runs"] = {
        "blind": sum(s["syntax"] and s["runs"] for s in wrong) / len(wrong),
        "accepts": len(both) / len(samples),
        "precision": sum(s["tests"] for s in both) / len(both),
    }

    # The two do not multiply as they stand. Verifier precision is 0 on tasks
    # where no sample is good and 72 percent where one is, so the marginal
    # precision already carries that loss and multiplying it by coverage counts
    # the loss twice. The composition needs the precision conditioned on the
    # tasks coverage lets through.
    reachable = [s for r in rows if r["n_ok"] > 0 for s in r["results"]]
    accepted = [s for s in reachable if s["runs"]]
    conditional = sum(s["tests"] for s in accepted) / len(accepted)

    return len(rows), len(samples), never, stats, conditional, single


def wilson(k, n, z=1.96):
    """95 percent Wilson interval. A rate quoted on 60 tasks without one misleads."""
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - h) / d, (c + h) / d


# --------------------------------------------------------------- Output

def main():
    buckets, total = partition()
    asserting, unsolved, coverage = law(buckets)

    print(f"\nA. What 20 samples produced, over {total} real prompts\n")
    for k, v in buckets.items():
        print(f"   {k:<16} {v:>4}   {v / total:6.1%}")

    print(f"\n   Over the {asserting} prompts where the model asserts something:")
    print(f"   unsolved at K=20  {unsolved:6.1%}   no sample among the 20 is correct")
    print(f"   coverage at K=20  {coverage:6.1%}   = 1 - unsolved, exactly")
    n_uns, gained, lost, pval = budget()
    print(f"\n   Coverage at a budget, not a ceiling. Drawn 40 times instead of 20,")
    print(f"   independently, {gained} of those {n_uns} unsolved prompts produce a correct")
    print(f"   completion. Those completions were observed, so the probability of a")
    print(f"   correct sample is not zero there. Half the unsolved share is not a")
    print(f"   limit of the model. It is a limit of the budget.")
    print(f"\n   The aggregate move is a separate claim and is not established:")
    print(f"   {lost} prompts go the other way, and McNemar on the {gained + lost} discordant")
    print(f"   prompts gives p = {pval:.2f}. Two runs of 59 prompts cannot settle it.")

    print("\nB. What each verifier costs, timed on this machine now\n")
    rows = price()
    print(f"   {'verifier':<28}{'cost per check':>16}")
    for name, dt in rows:
        unit = f"{dt * 1e3:.3f} ms" if dt < 1 else f"{dt:.2f} s"
        print(f"   {name:<28}{unit:>16}")

    # Dispersion reads no ground truth, so it certifies nothing, and dividing by
    # its near-zero cost would inflate the ratio without meaning anything.
    certifying = [r for r in rows if not r[0].startswith("dispersion")]
    span = max(r[1] for r in certifying) / min(r[1] for r in certifying)
    print(f"\n   Among verifiers that certify, cost spans a factor of {span:,.0f}.")

    n_tasks, n_samples, never, stats, conditional, single = coverage_and_precision()
    print(f"\nC. The verifier, over {n_samples} recorded samples on {n_tasks} tasks\n")
    print(f"   {'verifier':<20}{'accepts':>9}{'precision':>11}{'blind spot':>12}")
    for name, st in stats.items():
        print(f"   {name:<20}{st['accepts']:>8.0%}{st['precision']:>11.0%}{st['blind']:>12.0%}")
    print("\n   Blind spot is the share of genuinely wrong samples a verifier accepts.")
    print("   Calling the same verifier k times does not move it: the verdict is a")
    print("   function of the candidate. Only a verifier that fails differently does.")
    gained = stats["runs"]["blind"] - stats["syntax AND runs"]["blind"]
    print(f"\n   Chaining syntax and runs buys {gained:.1%} of blind spot back, because")
    print("   running without exception already implies parsing. Two gates that fail")
    print("   the same way are one gate, and the series costs twice.")

    good = n_tasks - never
    reach = good / n_tasks
    print(f"\nD. Composing the two\n")
    print(f"   coverage at K=10     {reach:6.1%}   tasks with at least one good sample")
    print(f"   verifier precision   {conditional:6.1%}   among those tasks only, once it accepts")
    print(f"   composed             {reach * conditional:6.1%}   what gets through and is correct")
    print(f"\n   The marginal precision, {stats['runs']['precision']:.1%}, must not be used here. It is 0 on")
    print("   tasks with no good sample and mixes that loss back in, so multiplying it")
    print("   by coverage counts the same loss twice.")
    print(f"\n   single draw          {single:6.1%}   one sample, expected")
    print(f"   headroom opened      {reach - single:6.1%}   what ten draws put within reach")
    print(f"   recovered            {reach * conditional - single:6.1%}   what the verifier turns into an answer")
    print(f"   recovery             {(reach * conditional - single) / (reach - single):6.1%}   the share of that headroom recovered")
    print(f"\n   Ten draws open {reach - single:.0%} of headroom and the verifier takes"
          f" {reach * conditional - single:.0%}.")
    print("   The candidates are there and nothing on hand tells them apart. That is")
    print("   the number to move, and more sampling does not move it.")

    lo, hi = wilson(good, n_tasks)
    print(f"\n   n = {n_tasks} tasks, so coverage carries a 95% interval of")
    print(f"   [{lo:.1%}, {hi:.1%}]. Every figure in C and D inherits that width.")
    print("   One limit sits on the generator and one on the verifier. They are")
    print("   different quantities, and they compose only once the second is")
    print("   conditioned on what the first lets through.")
    print("\n   Neither is a ceiling. The first is measured at K=10 and the second is")
    print("   read against the supplied tests, which stand in for truth and are not")
    print("   truth. Both bounds move if either assumption is tested.")

    b = json.loads(BUDGET.read_text())
    out = [r for r in b["rows"] if r["m"] > 0]
    print(f"\n   The first assumption was tested. Of the {b['taches_visees']} tasks with no good")
    print(f"   sample in ten draws, {b['taches_mesurees']} were drawn {b['total_tirages']} times: {len(out)} produced a correct")
    rates = ", ".join(f"{r['m']}%" for r in sorted(out, key=lambda r: -r["m"]))
    print(f"   one, at {rates}. Ten draws counted them out of reach and they")
    print(f"   were rare. The other {b['taches_mesurees'] - len(out)} are bounded under 3% by the rule of three,")
    print(f"   which is a bound and not a zero. {b['taches_visees'] - b['taches_mesurees']} tasks remain unmeasured.\n")


if __name__ == "__main__":
    main()
