#!/usr/bin/env python3
"""Statistics for interleaved_comparison.log (randomized per-round order).

Usage: python3 experiments/analyze_interleaved.py [log_path]
Prints per-arm means/SDs, paired and unpaired tests on total_to_accept and
prove times, and an order-effect check. Pure standard library.
"""
import math
import statistics
import sys

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

def paired_t(d):
    n = len(d)
    md = statistics.mean(d)
    sd = statistics.stdev(d)
    t = md / (sd / math.sqrt(n))
    return t, n - 1, t_two_sided_p(t, n - 1), md, sd

def ranks_with_ties(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        r = (i + j + 2) / 2.0  # average of 1-based ranks i+1..j+1
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
    tie = sum(t ** 3 - t for t in _tie_sizes(allv))
    sigma2 = nx * ny / 12.0 * ((all_n := nx + ny) + 1.0 - tie / (nx + ny) / (nx + ny - 1.0))
    z = (u1 - mu) / math.sqrt(sigma2)
    p = math.erfc(abs(z) / math.sqrt(2.0))
    return u1, z, p

def _tie_sizes(values):
    s = sorted(values)
    sizes, run = [], 1
    for i in range(1, len(s)):
        if s[i] == s[i - 1]:
            run += 1
        else:
            sizes.append(run)
            run = 1
    sizes.append(run)
    return [t for t in sizes if t > 1]

def wilcoxon(d):
    nz = [x for x in d if x != 0]
    n = len(nz)
    rk = ranks_with_ties([abs(x) for x in nz])
    wp = sum(r for r, x in zip(rk, nz) if x > 0)
    wn = sum(r for r, x in zip(rk, nz) if x < 0)
    w = min(wp, wn)
    mu = n * (n + 1) / 4.0
    tie = sum(t ** 3 - t for t in _tie_sizes([abs(x) for x in nz]))
    sigma2 = n * (n + 1) * (2 * n + 1) / 24.0 - tie / 48.0
    z = (w - mu) / math.sqrt(sigma2)
    p = math.erfc(abs(z) / math.sqrt(2.0))
    return w, z, p

def ms(ns_list):
    return [v / 1e6 for v in ns_list]

def describe(name, vals):
    m = statistics.mean(vals)
    sd = statistics.stdev(vals)
    md = statistics.median(vals)
    print(f"{name}: n={len(vals)} mean={m:.2f} sd={sd:.2f} median={md:.2f} (ms)")

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "experiments/interleaved_comparison.log"
    shared, hidden = {}, {}  # round -> (prove_ns, total_ns)
    first_shared_rounds = []
    with open(path) as f:
        for line in f:
            p = line.strip().split(",")
            if len(p) == 6 and p[0].isdigit():
                rnd, arm, slot, first, prove_ns, total_ns = int(p[0]), p[1], int(p[2]), p[3], int(p[4]), int(p[5])
                (shared if arm == "shared_active" else hidden)[rnd] = (prove_ns, total_ns)
                if slot == 0:
                    first_shared_rounds.append(first == "shared")
    rounds = sorted(set(shared) & set(hidden))
    assert len(rounds) == len(shared) == len(hidden), "incomplete pairs"
    s_tot = [shared[r][1] for r in rounds]
    h_tot = [hidden[r][1] for r in rounds]
    s_prv = [shared[r][0] for r in rounds]
    h_prv = [hidden[r][0] for r in rounds]
    print(f"file={path} rounds={len(rounds)} order_first_shared={sum(first_shared_rounds)}/{len(first_shared_rounds)}")
    describe("total_to_accept shared_active", ms(s_tot))
    describe("total_to_accept hidden_active", ms(h_tot))
    describe("prove         shared_active", ms(s_prv))
    describe("prove         hidden_active", ms(h_prv))
    for label, a, b in (("total_to_accept", s_tot, h_tot), ("prove", s_prv, h_prv)):
        d = [x - y for x, y in zip(a, b)]
        t, df, p, md, sd = paired_t(d)
        w, wz, wp = wilcoxon(d)
        ut, udf, up = welch(a, b)
        u, z, mp = mann_whitney(a, b)
        se = sd / math.sqrt(len(d))
        lo, hi = md - 2.0 * se, md + 2.0 * se
        print(f"[{label}] diff(shared-hidden): mean={md/1e6:+.2f} ms 95%CI~[{lo/1e6:+.2f},{hi/1e6:+.2f}] median={statistics.median(ms(d)):+.2f}")
        print(f"[{label}] paired t={t:.2f} df={df} p={p:.4f}; Wilcoxon W={w:.0f} z={wz:.2f} p={wp:.4f}")
        print(f"[{label}] Welch t={ut:.2f} df={udf:.1f} p={up:.4f}; Mann-Whitney U={u:.0f} z={z:.2f} p={mp:.4f}")
    # order effect: shared-first rounds vs hidden-first rounds, per arm
    for label, store in (("shared_active", shared), ("hidden_active", hidden)):
        a = [store[r][1] / 1e6 for r in rounds if first_shared_rounds[r - 1]]
        b = [store[r][1] / 1e6 for r in rounds if not first_shared_rounds[r - 1]]
        if a and b:
            ut, udf, up = welch(a, b)
            print(f"order_effect {label}: first={statistics.mean(a):.2f}({len(a)}) second={statistics.mean(b):.2f}({len(b)}) Welch p={up:.4f}")

if __name__ == "__main__":
    main()
