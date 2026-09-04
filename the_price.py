"""What a guarantee costs.

One file, standard library only, one command:

    python3 the_price.py

Sampling a language model many times fixes some errors and never fixes others.
The share it never fixes is a floor no amount of sampling reaches. Crossing that
floor requires a verifier, and every verifier has a price. This file measures
both halves and prints the table.

Part A reads real runs: 87 prompts, 20 samples each, GPT-2 at T=0.7, recorded
2026-08-20. Nothing is generated here, so no GPU and no model download.

Part B times four verifiers of rising strength on tasks carried in this file.
The timings are measured when you run it, on your machine.

Part C composes the two.

Everything else in this repository is detail. Read this and you have the result.
"""
import json
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

RUNS = Path(__file__).parent / "results" / "reduction_bound_20260820_0115.json"
CODE_RUNS = (Path(__file__).parent / "results" /
             "code_bound_Qwen2.5-1.5B-Instruct_20260820_1259.json")


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


def law(buckets):
    """coverage = 1 - systematic share, over prompts where the model asserts.

    Systematic means every sample is wrong. A verifier picks a correct sample
    when one exists, so its ceiling is exactly the complement of that share.
    """
    asserting = buckets["always-right"] + buckets["bifurcating"] + buckets["always-wrong"]
    systematic = buckets["always-wrong"] / asserting
    coverage = (buckets["always-right"] + buckets["bifurcating"]) / asserting
    assert abs(coverage - (1 - systematic)) < 1e-12, "the identity failed"
    return asserting, systematic, coverage


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

    Price only. How strong each verifier is gets measured in part D, on recorded
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


def score(verdicts):
    """(acceptance, precision) from (accepted, actually_correct) pairs."""
    accepted = [truth for ok, truth in verdicts if ok]
    acceptance = len(accepted) / len(verdicts)
    precision = (sum(accepted) / len(accepted)) if accepted else None
    return acceptance, precision


# ---------------------------------------------------------------- Part D

def ceilings():
    """The two ceilings, measured on recorded runs.

    60 MBPP tasks, 10 samples each, Qwen2.5-1.5B-Instruct, recorded 2026-08-20.
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
    systematic = never / len(rows)

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

    return len(rows), len(samples), systematic, stats


# ---------------------------------------------------------------- Part C

def main():
    buckets, total = partition()
    asserting, systematic, coverage = law(buckets)

    print(f"\nA. What 20 samples ever produced, over {total} real prompts\n")
    for k, v in buckets.items():
        print(f"   {k:<16} {v:>4}   {v / total:6.1%}")

    print(f"\n   Over the {asserting} prompts where the model asserts something:")
    print(f"   systematic share  {systematic:6.1%}   no sample is ever correct")
    print(f"   verifier ceiling  {coverage:6.1%}   = 1 - systematic share, exactly")
    print("\n   No amount of sampling crosses that ceiling. Only outside knowledge does.")

    print("\nB. What each verifier costs, timed on this machine now\n")
    rows = price()
    print(f"   {'verifier':<28}{'cost per check':>16}")
    for name, dt in rows:
        unit = f"{dt * 1e3:.3f} ms" if dt < 1 else f"{dt:.2f} s"
        print(f"   {name:<28}{unit:>16}")

    # Only rows that certify. Dispersion returns no precision, and dividing by
    # its near-zero cost would inflate the ratio without meaning anything.
    # Dispersion reads no ground truth, so it certifies nothing and its near-zero
    # cost would inflate the ratio without meaning anything.
    certifying = [r for r in rows if not r[0].startswith("dispersion")]
    span = max(r[1] for r in certifying) / min(r[1] for r in certifying)

    n_tasks, n_samples, sys_code, stats = ceilings()
    print(f"\nD. The second ceiling, over {n_samples} recorded samples on {n_tasks} tasks\n")
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

    print(f"\nE. Composing the two\n")
    print(f"   generator ceiling    {1 - sys_code:6.1%}   tasks with at least one good sample")
    print(f"   best verifier here   {stats['syntax AND runs']['precision']:6.1%}   precision once it accepts")
    print(f"   composed             {(1 - sys_code) * stats['syntax AND runs']['precision']:6.1%}   what actually gets through, correct")
    print(f"\n   Among verifiers that certify, cost spans a factor of {span:,.0f}.")
    print("   One ceiling sits on the generator and one on the verifier. They are")
    print("   different quantities and they multiply.\n")


if __name__ == "__main__":
    main()
