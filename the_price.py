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
    """Time each verifier over the same work, once.

    Returns (name, acceptance, precision, seconds). Acceptance is the share the
    verifier lets through. Precision is the share of those that are actually
    correct, which is the only sense in which a verifier is strong. A verifier
    that accepts everything has acceptance 1 and precision equal to the raw rate.
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
    dt = (time.perf_counter() - t0) / 100
    rows.append(("dispersion across samples", 1.0, None, dt))

    t0 = time.perf_counter()
    hits = [v_arithmetic(e, x) for e, x in ARITHMETIC]
    dt = (time.perf_counter() - t0) / len(ARITHMETIC)
    rows.append(("arithmetic, substitution", 1.0, sum(hits) / len(hits), dt))

    t0 = time.perf_counter()
    verdicts = [(v_syntax(c, t), truth) for c, t, truth in CODE]
    dt = (time.perf_counter() - t0) / len(CODE)
    rows.append(("code, syntax", *score(verdicts), dt))

    t0 = time.perf_counter()
    verdicts = [(v_execution(c, t), truth) for c, t, truth in CODE]
    dt = (time.perf_counter() - t0) / len(CODE)
    rows.append(("code, supplied tests", *score(verdicts), dt))

    return rows


def score(verdicts):
    """(acceptance, precision) from (accepted, actually_correct) pairs."""
    accepted = [truth for ok, truth in verdicts if ok]
    acceptance = len(accepted) / len(verdicts)
    precision = (sum(accepted) / len(accepted)) if accepted else None
    return acceptance, precision


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
    print(f"   {'verifier':<28}{'accepts':>10}{'precision':>11}{'cost':>12}")
    for name, cov, prec, dt in rows:
        p = f"{prec:.0%}" if prec is not None else "n/a"
        unit = f"{dt * 1e3:.2f} ms" if dt < 1 else f"{dt:.2f} s"
        print(f"   {name:<28}{cov:>9.0%}{p:>11}{unit:>12}")

    # Only rows that certify. Dispersion returns no precision, and dividing by
    # its near-zero cost would inflate the ratio without meaning anything.
    certifying = [r for r in rows if r[2] is not None]
    span = max(r[3] for r in certifying) / min(r[3] for r in certifying)
    print(f"\nC. Among verifiers that certify, cost spans a factor of {span:,.0f}.")
    print("   Strength and price move together. Choosing a verifier is a budget")
    print(f"   decision, and {systematic:.1%} of the work stays out of reach at any budget.\n")


if __name__ == "__main__":
    main()
