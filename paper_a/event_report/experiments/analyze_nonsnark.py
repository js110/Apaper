#!/usr/bin/env python3
"""Statistics for nonsnark_baseline.log (four arms, one block per arm).

Usage: python3 experiments/analyze_nonsnark.py [log_path] [out_path]
Prints per-arm phase means/SDs/medians, submission byte totals, pairwise tests on
total_to_accept, and the qualitative RESULT/STRUCTURE lines. Pure standard
library.

Design note: this harness runs each arm as one consecutive block of iterations,
so iteration index is not a shared blocking factor across arms (unlike
interleaved_comparison.log). Comparisons are therefore unpaired.
"""
import math
import statistics
import sys

ARMS = ("hidden_active", "bbs_credential", "privacy_pass", "trusted_baseline")


def betacf(a, b, x):
    MAXIT, EPS, FPMIN = 300, 3.0e-12, 1.0e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < FPMIN:
        d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < EPS:
            break
    return h


def betai(a, b, x):
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    bt = math.exp(lbeta + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * betacf(a, b, x) / a
    return 1.0 - bt * betacf(b, a, 1.0 - x) / b


def t_two_sided_p(t, df):
    return betai(df / 2.0, 0.5, df / (df + t * t))


def welch(x, y):
    nx, ny = len(x), len(y)
    mx, my = statistics.mean(x), statistics.mean(y)
    vx, vy = statistics.variance(x), statistics.variance(y)
    se = math.sqrt(vx / nx + vy / ny)
    t = (mx - my) / se
    df = (vx / nx + vy / ny) ** 2 / ((vx / nx) ** 2 / (nx - 1) + (vy / ny) ** 2 / (ny - 1))
    return t, df, t_two_sided_p(t, df)


def ranks_with_ties(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        r = (i + j + 2) / 2.0
        for k in range(i, j + 1):
            ranks[order[k]] = r
        i = j + 1
    return ranks


def mann_whitney(x, y):
    nx, ny = len(x), len(y)
    allv = x + y
    rk = ranks_with_ties(allv)
    u1 = sum(rk[:nx]) - nx * (nx + 1) / 2.0
    mu = nx * ny / 2.0
    s = sorted(allv)
    sizes, run = [], 1
    for i in range(1, len(s)):
        if s[i] == s[i - 1]:
            run += 1
        else:
            sizes.append(run)
            run = 1
    sizes.append(run)
    tie = sum(t ** 3 - t for t in sizes if t > 1)
    sigma2 = nx * ny / 12.0 * ((nx + ny) + 1.0 - tie / (nx + ny) / (nx + ny - 1.0))
    z = (u1 - mu) / math.sqrt(sigma2)
    p = math.erfc(abs(z) / math.sqrt(2.0))
    return u1, z, p


def load(path):
    header, arms = {}, {}
    cur = None
    cols = None
    with open(path) as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if line.startswith(("experiment=", "started_utc=", "completed_utc=", "go=", "cpu=",
                                "modules=", "backend=", "model=", "round_trips=", "SCOPE")):
                if line.startswith("SCOPE"):
                    header["scope"] = line
                else:
                    k, _, v = line.partition("=")
                    header[k] = v
                continue
            if line.startswith("ARM "):
                p = line.split()
                cur = p[1]
                arms[cur] = {"meta": " ".join(p[2:]), "rows": []}
                cols = None
                continue
            if line.startswith("RESULT ") or line.startswith("STRUCTURE "):
                arms[cur].setdefault("notes", []).append(line)
                continue
            if line.startswith("sample,"):
                cols = line.split(",")
                continue
            if line.startswith("STAT "):
                k, _, v = line.partition(" median_total_to_accept_ns=")
                arms[k.split("arm=")[1]]["median_stat"] = v
                continue
            if cols and cur:
                p = line.split(",")
                if p[0] == "warmup" or p[0].isdigit():
                    arms[cur]["rows"].append(dict(zip(cols, p)))
    return header, arms


def num(row, key):
    return int(row[key])


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "experiments/nonsnark_baseline.log"
    out = sys.argv[2] if len(sys.argv) > 2 else None
    header, arms = load(path)

    lines = []
    w = lines.append
    w(f"file={path}")
    w(f"started_utc={header.get('started_utc', '?')} completed_utc={header.get('completed_utc', '?')}")
    w(f"go={header.get('go', '?')} modules={header.get('modules', '?')}")
    w(f"backend={header.get('backend', '?')}")
    w(f"round_trips={header.get('round_trips', '?')}")
    w(f"model={header.get('model', '?')}")
    w("")

    totals = {}
    for arm in ARMS:
        rows = [r for r in arms[arm]["rows"] if r["sample"] != "warmup"]
        if not rows:
            continue
        totals[arm] = [num(r, "total_to_accept_ns") for r in rows]
        w(f"== arm={arm} n={len(rows)} {arms[arm]['meta']}")
        phase_cols = [c for c in rows[0] if c.endswith("_ns") and c != "total_to_accept_ns"]
        for col in ["total_to_accept_ns"] + phase_cols:
            v = [num(r, col) / 1e6 for r in rows]
            mean = statistics.mean(v)
            sd = statistics.stdev(v) if len(v) > 1 else 0.0
            md = statistics.median(v)
            lo = min(v)
            hi = max(v)
            w(f"  {col:38s} mean={mean:10.3f} sd={sd:8.3f} median={md:10.3f} min={lo:10.3f} max={hi:10.3f} ms")
        byte_cols = [c for c in rows[0] if c.endswith("_bytes")]
        for col in byte_cols:
            vals = {num(r, col) for r in rows}
            w(f"  {col:38s} {'constant=' + str(vals.pop()) if len(vals) == 1 else 'values=' + str(sorted(vals))}")
        for note in arms[arm].get("notes", []):
            w("  " + note)
        w("")

    w("== pairwise total_to_accept (unpaired, ms)")
    for i, a in enumerate(ARMS):
        for b in ARMS[i + 1:]:
            if a not in totals or b not in totals:
                continue
            x, y = [v / 1e6 for v in totals[a]], [v / 1e6 for v in totals[b]]
            t, df, p = welch(x, y)
            u, z, mp = mann_whitney(x, y)
            ratio = statistics.mean(x) / statistics.mean(y)
            w(f"  {a} vs {b}: mean {statistics.mean(x):.3f} vs {statistics.mean(y):.3f} "
              f"ratio={ratio:.1f}x Welch t={t:.2f} df={df:.1f} p={p:.2e}; MWU U={u:.0f} z={z:.2f} p={mp:.2e}")
    w("")

    # Sizes that a verifier actually receives per submission.
    w("== per-submission payload on the wire (bytes, component sum)")
    for arm in ARMS:
        rows = [r for r in arms[arm]["rows"] if r["sample"] != "warmup"]
        if not rows:
            continue
        w(f"  {arm:16s} component_sum={rows[0]['component_sum_bytes']:>6s} "
          f"plaintext={rows[0]['plaintext_bytes']:>4s} detail=" +
          ", ".join(f"{c[:-6]}={rows[0][c]}" for c in rows[0]
                    if c.endswith("_bytes") and c not in ("plaintext_bytes", "component_sum_bytes")))
    w("")
    w(f"scope={header.get('scope', '?')}")

    text = "\n".join(lines)
    print(text)
    if out:
        with open(out, "w") as f:
            f.write(text + "\n")


if __name__ == "__main__":
    main()
