#!/usr/bin/env python3
"""Extract raw measurements from the recorded prototype logs and re-derive every
number quoted in the Chinese draft. Read-only with respect to the logs.

Sources (all under paper_a/event_report/experiments/):
  benchmark.log                 rectangle circuit, 30 runs
  region_benchmark.log          depth-8 region circuit, 30 runs
  accountability_benchmark.log  region + accountability circuit, 30 runs
  revocation_benchmark.log      full active-credential circuit, 30 runs
  ablation_cost.log             holder-bound vs bearer control, 30 runs each
  region_scale_4/6/8.log        region depth scaling, 30 runs each
  end_to_end.log                in-process acceptance path, 30 runs (+1 warmup)
  binding.log / context_ablation.log / context_hiding_candidate.log
                                categorical accept/reject outcomes
  context_linkability.log       synthetic shared-context join count

Uncertainty convention: sample mean +/- sample standard deviation (ddof=1),
n=30 measured runs after 1 warmup, matching the draft. No data is altered,
filtered, smoothed or imputed.
"""
from pathlib import Path
import json
import re
import statistics as st

EXP = Path("/Users/jiangsheng/Desktop/Apaper/paper_a/event_report/experiments")
OUT = Path(__file__).resolve().parent


def meta(name):
    txt = (EXP / name).read_text()
    d = {}
    for key in ("compile_ns", "setup_ns", "constraints",
                "public_variables_including_one", "secret_variables",
                "region_depth", "region_cells", "active_depth",
                "active_credentials", "runs", "warmup"):
        m = re.search(rf"\b{key}=(\d+)", txt)
        if m:
            d[key] = int(m.group(1))
    m = re.search(r'started_utc=(\S+)', txt)
    if m:
        d["started_utc"] = m.group(1)
    d["source_sha256"] = dict(re.findall(r"source_sha256 file=(\S+) digest=(\w+)", txt))
    return d


def samples(name):
    """Rows under the 'sample,prove_ns,verify_ns,proof_bytes,public_witness_bytes' header."""
    lines = (EXP / name).read_text().splitlines()
    h = lines.index("sample,prove_ns,verify_ns,proof_bytes,public_witness_bytes")
    rows = []
    for line in lines[h + 1:]:
        f = line.split(",")
        if len(f) == 5 and f[0].isdigit():
            rows.append([int(x) for x in f])
    assert len(rows) == 30, (name, len(rows))
    return rows


def ablation_samples(name):
    """'SAMPLE <label> <i> <prove_ns> <verify_ns>' rows, grouped by label."""
    groups = {}
    counts = {}
    for line in (EXP / name).read_text().splitlines():
        m = re.match(r"CIRCUIT (\w+) constraints=(\d+) warmup=(\d+) runs=(\d+)", line)
        if m:
            counts[m.group(1)] = dict(constraints=int(m.group(2)),
                                      warmup=int(m.group(3)), runs=int(m.group(4)))
        m = re.match(r"SAMPLE (\w+) (\d+) (\d+) (\d+)", line)
        if m:
            groups.setdefault(m.group(1), []).append(
                [int(m.group(2)), int(m.group(3)), int(m.group(4))])
    for k, v in groups.items():
        assert len(v) == counts[k]["runs"], (k, len(v))
    return groups, counts


def e2e_samples(name):
    lines = (EXP / name).read_text().splitlines()
    h = next(i for i, l in enumerate(lines) if l.startswith("sample,challenge_ns"))
    cols = lines[h].split(",")
    rows = []
    for line in lines[h + 1:]:
        f = line.split(",")
        if len(f) == len(cols) and f[0].isdigit():
            rows.append({c: int(v) for c, v in zip(cols, f)})
    assert len(rows) == 30, len(rows)
    return cols, rows


def ms(vals):
    return [v / 1e6 for v in vals]


def summary(vals):
    return dict(n=len(vals), mean=st.mean(vals), sd=st.stdev(vals),
                median=st.median(vals), min=min(vals), max=max(vals))


def fmt(s, nd=2):
    return f"{s['mean']:.{nd}f}±{s['sd']:.{nd}f}"


data = {"provenance": {}, "circuits": {}, "ablation_cost": {},
        "region_scaling": {}, "end_to_end": {}, "categorical": {}}

CIRCUITS = [("rectangle", "benchmark.log"), ("region", "region_benchmark.log"),
            ("accountability", "accountability_benchmark.log"),
            ("active", "revocation_benchmark.log")]
for key, name in CIRCUITS:
    m = meta(name)
    rows = samples(name)
    prove = summary(ms([r[1] for r in rows]))
    verify = summary(ms([r[2] for r in rows]))
    data["circuits"][key] = dict(
        log=name, meta=m, prove_ms=prove, verify_ms=verify,
        prove_raw_ms=ms([r[1] for r in rows]),
        verify_raw_ms=ms([r[2] for r in rows]),
        proof_bytes=sorted({r[3] for r in rows}),
        public_witness_bytes=sorted({r[4] for r in rows}))
    data["provenance"][name] = m["source_sha256"]

groups, counts = ablation_samples("ablation_cost.log")
for key, rows in groups.items():
    data["ablation_cost"][key] = dict(
        constraints=counts[key]["constraints"], runs=counts[key]["runs"],
        prove_ms=summary(ms([r[1] for r in rows])),
        verify_ms=summary(ms([r[2] for r in rows])),
        prove_raw_ms=ms([r[1] for r in rows]),
        verify_raw_ms=ms([r[2] for r in rows]))

for d in (4, 6, 8):
    name = f"region_scale_{d}.log"
    m = meta(name)
    rows = samples(name)
    data["region_scaling"][str(d)] = dict(
        log=name, meta=m,
        prove_ms=summary(ms([r[1] for r in rows])),
        verify_ms=summary(ms([r[2] for r in rows])),
        prove_raw_ms=ms([r[1] for r in rows]),
        verify_raw_ms=ms([r[2] for r in rows]))

cols, rows = e2e_samples("end_to_end.log")
e2e = {"log": "end_to_end.log", "meta": meta("end_to_end.log"), "columns": cols}
for c in cols[1:]:
    vals = [r[c] for r in rows]
    if c.endswith("_ns"):
        # store timings in ms so they are directly comparable with the draft
        e2e[c] = summary(ms(vals))
        e2e[c + "_raw_ms"] = ms(vals)
    else:
        e2e[c] = sorted(set(vals))
e2e["raw"] = rows
data["end_to_end"] = e2e

# categorical outcomes, transcribed verbatim from the RESULT lines
data["categorical"]["receipt_transfer"] = {
    "source": "binding.log",
    "relations": ["持有人绑定（主关系）", "无记名对照"],
    "cases": ["自己的回执", "复制的回执"],
    "grid": [["接受", "拒绝"], ["接受", "接受"]],
    "evidence": [["R1CS", "R1CS"], ["R1CS", "R1CS+Groth16"]],
}
data["categorical"]["context_substitution"] = {
    "source": "context_ablation.log",
    "relations": ["完整关系", "无上下文绑定"],
    "cases": ["原始上下文", "替换报告", "替换挑战", "替换任务"],
    "grid": [["接受", "拒绝", "拒绝", "拒绝"], ["接受", "接受", "接受", "接受"]],
    "evidence": [["R1CS"] * 4, ["R1CS+Groth16"] * 4],
}
data["categorical"]["context_hiding"] = {
    "source": "context_hiding_candidate.log",
    "constraints": 29503,
    "candidate_valid": "Groth16_verified",
    "substituted_context": "R1CS_rejected",
    "substituted_holder": "R1CS_rejected",
    "timing_measured": False,
}
data["categorical"]["linkability"] = {
    "source": "context_linkability.log", "joined": 2, "total": 2}


def variant_sections(name, section_prefix):
    """Parse 'VARIANT x k=v...' / 'ARM x k=v...' sections followed by CSV blocks."""
    lines = (EXP / name).read_text().splitlines()
    out = {}
    current = None
    cols = None
    rows = []
    results = []
    for line in lines:
        m = re.match(rf"{section_prefix} (\w+) (.*)", line)
        if m:
            if current is not None and cols is not None:
                out[current]["columns"] = cols
                out[current]["rows"] = rows
            current = m.group(1)
            out[current] = {k: int(v) for k, v in re.findall(r"(\w+)=(\d+)", m.group(2))}
            cols, rows = None, []
            continue
        if line.startswith("sample,"):
            if current is not None and cols is not None:
                out[current]["columns"] = cols
                out[current]["rows"] = rows
            cols = line.split(",")
            rows = []
            continue
        if line.startswith("RESULT "):
            results.append(line)
            continue
        if cols is not None and current is not None:
            f = line.split(",")
            if len(f) == len(cols) and (f[0].isdigit() or f[0] == "warmup"):
                if f[0].isdigit():
                    rows.append({c: int(v) for c, v in zip(cols, f)})
    if current is not None and cols is not None:
        out[current]["columns"] = cols
        out[current]["rows"] = rows
    for k, v in out.items():
        assert len(v["rows"]) == 30, (name, k, len(v["rows"]))
        for c in v["columns"][1:]:
            vals = [r[c] for r in v["rows"]]
            if c.endswith("_ns"):
                v[c] = summary(ms(vals))
                v[c + "_raw_ms"] = ms(vals)
            else:
                v[c] = sorted(set(vals))
    return out, results


hidden, hidden_results = variant_sections("context_hiding_extensions.log", "VARIANT")
data["hidden_extensions"] = hidden
data["hidden_extensions_results"] = hidden_results
data["provenance"]["context_hiding_extensions.log"] = meta("context_hiding_extensions.log")["source_sha256"]

comparison, comparison_results = variant_sections("protocol_comparison.log", "ARM")
data["protocol_comparison"] = comparison
data["protocol_comparison_results"] = comparison_results
data["protocol_comparison_structure"] = {
    k: int(v) for k, v in re.findall(
        r"STRUCTURE arm=(\w+) issuer_input_bytes=(\d+)",
        (EXP / "protocol_comparison.log").read_text())}
data["provenance"]["protocol_comparison.log"] = meta("protocol_comparison.log")["source_sha256"]

nonsnark, nonsnark_results = variant_sections("nonsnark_baseline.log", "ARM")
data["nonsnark_baseline"] = nonsnark
data["nonsnark_baseline_results"] = nonsnark_results
_ns_txt = (EXP / "nonsnark_baseline.log").read_text()
data["nonsnark_baseline_structure"] = {
    m.group(1): m.group(2).strip()
    for m in re.finditer(r"STRUCTURE arm=(\w+) (.*)", _ns_txt)}
data["nonsnark_baseline_round_trips"] = re.search(r"round_trips=(.*)", _ns_txt).group(1).strip()
data["provenance"]["nonsnark_baseline.log"] = meta("nonsnark_baseline.log")["source_sha256"]

(OUT / "measurements.json").write_text(
    json.dumps(data, ensure_ascii=False, indent=1))

# ---- cross-check against every number quoted in the draft ----
print("=== 表4 / §5.4 四电路（均值±样本标准差, n=30）===")
expect = {
    "rectangle":      (29833, 103.84, 2.596, "146.74±10.53", "1.027±0.088", 364),
    "region":         (35798,  50.35, 2.182, "214.28±8.76",  "0.995±0.058", 396),
    "accountability": (62627,  71.96, 3.204, "303.93±12.02", "1.056±0.257", 588),
    "active":         (68592,  76.22, 4.424, "422.47±23.72", "1.016±0.038", 620),
}
ok = True
for k, (con, comp, setup, pv, vv, pw) in expect.items():
    c = data["circuits"][k]
    got = (c["meta"]["constraints"], round(c["meta"]["compile_ns"] / 1e6, 2),
           round(c["meta"]["setup_ns"] / 1e9, 3), fmt(c["prove_ms"]),
           fmt(c["verify_ms"], 3), c["public_witness_bytes"])
    exp = (con, comp, setup, pv, vv, [pw])
    match = got == exp
    ok &= match
    print(f"  {k:15s} {'OK ' if match else 'DIFF'} got={got}")
    if not match:
        print(f"  {'':15s}      exp={exp}")
    print(f"  {'':15s}      proof_bytes={c['proof_bytes']}")

print("\n=== 表5 / §5.5 树深缩放 ===")
for d, (con, pv, vv) in {"4": (33146, "206.64±8.31", "1.004±0.023"),
                         "6": (34472, "210.75±8.53", "1.008±0.060"),
                         "8": (35798, "217.29±8.88", "1.017±0.061")}.items():
    r = data["region_scaling"][d]
    got = (r["meta"]["constraints"], fmt(r["prove_ms"]), fmt(r["verify_ms"], 3))
    exp = (con, pv, vv)
    ok &= got == exp
    print(f"  depth {d} {'OK ' if got == exp else 'DIFF'} got={got} exp={exp}")
print(f"  约束增量 4→8 = {data['region_scaling']['8']['meta']['constraints'] - data['region_scaling']['4']['meta']['constraints']} (稿中 2,652)")

print("\n=== §5.2 持有人绑定 / 无记名对照 ===")
for k, (con, pv, vv) in {"bound": (29833, "142.67±5.48", "1.012±0.099"),
                         "bearer": (29173, "138.35±6.65", "0.981±0.065")}.items():
    a = data["ablation_cost"][k]
    got = (a["constraints"], fmt(a["prove_ms"]), fmt(a["verify_ms"], 3))
    exp = (con, pv, vv)
    ok &= got == exp
    print(f"  {k:8s} {'OK ' if got == exp else 'DIFF'} got={got} exp={exp}")
b = data["ablation_cost"]["bound"]["prove_ms"]["mean"]
r = data["ablation_cost"]["bearer"]["prove_ms"]["mean"]
print(f"  约束差 = {data['ablation_cost']['bound']['constraints'] - data['ablation_cost']['bearer']['constraints']} (稿中 660)")
print(f"  生成时间差 = {b - r:.2f} ms (稿中 约4.3)")
print(f"  上下文隐藏约束 = {data['categorical']['context_hiding']['constraints']} (稿中 29,503); 差 = {29833 - 29503} (稿中 330)")

print("\n=== §5.6 同进程受理路径（ns→ms, n=30）===")
e = data["end_to_end"]
for c, nd, exp in [("total_to_accept_ns", 2, "410.47±17.90"),
                   ("prove_ns", 2, "408.09"),
                   ("encrypt_ns", 3, "0.036"),
                   ("fixture_sign_and_witness_ns", 3, "0.952"),
                   ("gateway_verify_decrypt_dedup_ns", 3, "1.368"),
                   ("audit_open_ns", 3, "0.336")]:
    s = e[c]
    got = fmt(s, nd) if "±" in exp else f"{s['mean']:.{nd}f}"
    ok &= got == exp
    print(f"  {c:34s} {'OK ' if got == exp else 'DIFF'} got={got} exp={exp}")
for c, exp in [("plaintext_bytes", 40), ("envelope_bytes", 1158), ("proof_bytes", 164),
               ("nonce_ascii_bytes", 64), ("nullifier_bytes", 32),
               ("identity_cipher_bytes", 64), ("component_sum_bytes", 1482),
               ("public_witness_bytes", 620)]:
    got = e[c]
    ok &= got == [exp]
    print(f"  {c:34s} {'OK ' if got == [exp] else 'DIFF'} got={got} exp=[{exp}]")
comp = ["challenge_ns", "encrypt_ns", "fixture_sign_and_witness_ns", "prove_ns",
        "proof_serialize_ns", "gateway_verify_decrypt_dedup_ns"]
tot = sum(e[c]["mean"] for c in comp)
print(f"  分量之和 = {tot:.3f} ms vs total_to_accept = {e['total_to_accept_ns']['mean']:.3f} ms")
print(f"  证明生成占比 = {e['prove_ns']['mean'] / e['total_to_accept_ns']['mean'] * 100:.2f}%")
print(f"  非证明分量合计 = {tot - e['prove_ns']['mean']:.3f} ms")

print("\n=== 派生量（用于图注，均由实测值算得）===")
c4 = data["region_scaling"]["4"]; c8 = data["region_scaling"]["8"]
print(f"  单元数 16→256 = {256 / 16:.0f} 倍")
print(f"  约束增长 = {(c8['meta']['constraints'] - c4['meta']['constraints']) / c4['meta']['constraints'] * 100:.2f}%")
print(f"  生成时间增长 = {(c8['prove_ms']['mean'] - c4['prove_ms']['mean']) / c4['prove_ms']['mean'] * 100:.2f}%")
print(f"  证明占通信量 = {164 / 1482 * 100:.2f}%")
print(f"  信封占通信量 = {1158 / 1482 * 100:.2f}%")

print("\n=== §5.7 隐藏上下文扩展（context_hiding_extensions.log, n=30）===")
for k in ("rectangle", "region", "accountability", "active"):
    h = data["hidden_extensions"][k]
    print(f"  {k:15s} shared={h['shared_constraints']:,} hidden={h['hidden_constraints']:,} "
          f"delta={h['shared_constraints'] - h['hidden_constraints']}")
    if "prove_ns" in h:
        print(f"  {'':15s} prove={fmt(h['prove_ns'])} ms", end="")
        if "verify_ns" in h:
            print(f" verify={fmt(h['verify_ns'], 3)} ms", end="")
        if "total_to_accept_ns" in h:
            print(f" total_to_accept={fmt(h['total_to_accept_ns'])} ms", end="")
        print()
for line in data["hidden_extensions_results"]:
    print(" ", line)

print("\n=== §5.8 三臂对照（protocol_comparison.log, n=30, 同一会话）===")
for k in ("shared_active", "hidden_active", "trusted_baseline"):
    c = data["protocol_comparison"][k]
    print(f"  {k:16s} constraints={c['constraints']:,} total_to_accept={fmt(c['total_to_accept_ns'])} ms "
          f"component_sum={c['component_sum_bytes']} B")
    if "prove_ns" in c:
        print(f"  {'':16s} prove={fmt(c['prove_ns'])} ms gateway={fmt(c['gateway_verify_decrypt_dedup_ns'], 3)} ms")
    else:
        print(f"  {'':16s} issuer_verify_and_sign={fmt(c['issuer_verify_and_sign_ns'], 3)} ms "
              f"gateway_verify_dedup={fmt(c['gateway_verify_dedup_ns'], 3)} ms request_bytes={c['request_bytes']}")
for line in data["protocol_comparison_results"]:
    print(" ", line)

print("\n=== §5.9 非 SNARK 匿名基线（nonsnark_baseline.log, n=30, 同一会话）===")
for k in ("hidden_active", "bbs_credential", "privacy_pass", "trusted_baseline"):
    c = data["nonsnark_baseline"][k]
    print(f"  {k:16s} total_to_accept={fmt(c['total_to_accept_ns'])} ms "
          f"component_sum={c['component_sum_bytes']} B")
    for col in [x for x in c["columns"][1:] if x.endswith("_ns") and x != "total_to_accept_ns"]:
        print(f"  {'':16s} {col:34s} {fmt(c[col], 3)} ms")
for line in data["nonsnark_baseline_results"]:
    print(" ", line)
for k, v in data["nonsnark_baseline_structure"].items():
    print(f"  STRUCTURE {k}: {v}")
print(f"  round_trips={data['nonsnark_baseline_round_trips']}")
_ns = data["nonsnark_baseline"]
_ratio = {"zk/bbs": _ns["hidden_active"]["total_to_accept_ns"]["mean"] / _ns["bbs_credential"]["total_to_accept_ns"]["mean"],
          "zk/pp": _ns["hidden_active"]["total_to_accept_ns"]["mean"] / _ns["privacy_pass"]["total_to_accept_ns"]["mean"],
          "zk/base": _ns["hidden_active"]["total_to_accept_ns"]["mean"] / _ns["trusted_baseline"]["total_to_accept_ns"]["mean"],
          "gw_bbs/gw_zk": _ns["bbs_credential"]["gateway_verify_dedup_ns"]["mean"] / _ns["hidden_active"]["gateway_verify_decrypt_dedup_ns"]["mean"]}
for k, v in _ratio.items():
    print(f"  ratio {k:12s} = {v:.1f}x")
for k, nd, exp in [("hidden_active", 2, "396.57±8.35"), ("bbs_credential", 2, "14.05±0.12"),
                   ("privacy_pass", 2, "6.58±0.02"), ("trusted_baseline", 3, "0.698±0.004")]:
    got = fmt(_ns[k]["total_to_accept_ns"], nd)
    ok &= got == exp
    print(f"  total_to_accept {k:16s} {'OK ' if got == exp else 'DIFF'} got={got} exp={exp}")
for k, exp in [("hidden_active", 1482), ("bbs_credential", 704),
               ("privacy_pass", 1496), ("trusted_baseline", 276)]:
    got = _ns[k]["component_sum_bytes"][0]
    ok &= got == exp
    print(f"  component_sum {k:16s} {'OK ' if got == exp else 'DIFF'} got={got} exp={exp}")
for k, col, nd, exp in [("hidden_active", "prove_ns", 2, "394.11±8.34"),
                        ("hidden_active", "gateway_verify_decrypt_dedup_ns", 3, "1.336±0.053"),
                        ("bbs_credential", "issuer_verify_and_sign_ns", 3, "2.938±0.034"),
                        ("bbs_credential", "derive_presentation_ns", 3, "6.183±0.057"),
                        ("bbs_credential", "gateway_verify_dedup_ns", 3, "4.787±0.040"),
                        ("bbs_credential", "request_sign_ns", 3, "0.109±0.003"),
                        ("privacy_pass", "blind_ns", 3, "0.624±0.006"),
                        ("privacy_pass", "issuer_evaluate_ns", 3, "2.200±0.016"),
                        ("privacy_pass", "finalize_ns", 3, "3.133±0.009"),
                        ("privacy_pass", "issuer_redeem_ns", 3, "0.619±0.010")]:
    got = fmt(_ns[k][col], nd)
    ok &= got == exp
    print(f"  phase {k}:{col:32s} {'OK ' if got == exp else 'DIFF'} got={got} exp={exp}")
_gw = _ns["bbs_credential"]["gateway_verify_dedup_ns"]["mean"] / _ns["hidden_active"]["gateway_verify_decrypt_dedup_ns"]["mean"]
print(f"  网关侧 BBS/ZK = {_gw:.1f}x (稿中 约3.6)")
ok &= round(_gw, 1) == 3.6
print(f"  与 §5.8 隐藏臂差 = "
      f"{abs(_ns['hidden_active']['total_to_accept_ns']['mean'] - data['protocol_comparison']['hidden_active']['total_to_accept_ns']['mean']):.2f} ms")
print("\nALL MATCH" if ok else "\n*** MISMATCH — 必须先查清再绘图 ***")
print("wrote", OUT / "measurements.json")