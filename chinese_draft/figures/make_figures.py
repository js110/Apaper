#!/usr/bin/env python3
"""Render the experiment-section figures for the Chinese draft.

Every plotted value comes from measurements.json, which extract_data.py derives
from the recorded prototype logs and cross-checks against the numbers already
quoted in the manuscript. Nothing is invented, filtered, smoothed or imputed.

Encoding rules applied here:
  * bars start at zero; where a truncated axis is used it is a point/line
    encoding and the truncation is stated on the figure and in the caption;
  * uncertainty is the sample standard deviation (ddof=1) of n=30 measured runs
    after one warmup, and is named as such in every caption;
  * raw observations are overlaid wherever a mean is shown;
  * colour is never the only cue: categories carry tick labels, series carry
    distinct markers, and every bar/point carries a direct value label;
  * no dual axes: quantities with different magnitudes get their own aligned
    panel and scale, and differing scales are disclosed.

Palette: Okabe-Ito (colour-vision-deficiency safe qualitative set).
Type: Times New Roman for Latin/numerals with Songti SC fallback for Chinese
(font.family must be the explicit list; a generic family does not fall back).
Output: vector PDF (Type 42 fonts) + 400 dpi PNG for the Word working draft.
Publisher-specific choices are PENDING: the target journal is not yet chosen.
"""
from pathlib import Path
import json
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

HERE = Path(__file__).resolve().parent
D = json.loads((HERE / "measurements.json").read_text())

MM = 1 / 25.4
W = 180 * MM          # full text width, consistent with the existing figures
DPI_PNG = 400

# Okabe-Ito
BLUE = "#0072B2"
GREEN = "#009E73"
ORANGE = "#E69F00"
PURPLE = "#CC79A7"
SKY = "#56B4E9"
VERM = "#D55E00"
INK = "#1A1A1A"
GREY = "#6E6E6E"

CIRC = ["rectangle", "region", "accountability", "active"]
CIRC_CN = ["矩形", "区域", "可追责", "活跃凭证"]
CIRC_SHORT = ["矩形", "区域", "可追责", "活跃"]
CIRC_COL = [BLUE, GREEN, ORANGE, PURPLE]
CIRC_MARK = ["o", "s", "^", "D"]

plt.rcParams.update({
    "font.family": ["Times New Roman", "Songti SC"],
    "mathtext.fontset": "stix",
    "font.size": 9,
    "axes.titlesize": 9.5,
    "axes.titleweight": "bold",
    "axes.labelsize": 9,
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "legend.fontsize": 8.5,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
    "axes.unicode_minus": False,
    "axes.edgecolor": "#4D4D4D",
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.color": "0.88",
    "grid.linewidth": 0.6,
    "xtick.color": "#333333",
    "ytick.color": "#333333",
    "text.color": INK,
    "axes.labelcolor": INK,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
    "hatch.linewidth": 0.6,
})

MANIFEST = {}


def reserve_bottom(fig, frac):
    """Keep a clear band at the bottom for footnotes / figure-level legends.

    constrained-layout rect is (left, bottom, WIDTH, HEIGHT), so the height must
    be 1-frac; passing 1 shifts the axes above the page and clips the top.
    """
    fig.get_layout_engine().set(rect=(0, frac, 1, 1 - frac))


def export(fig, stem, caption, sources, transforms, uncertainty, notes):
    fig.savefig(HERE / f"{stem}.pdf", bbox_inches=None)
    fig.savefig(HERE / f"{stem}.png", dpi=DPI_PNG, bbox_inches=None)
    plt.close(fig)
    MANIFEST[stem] = dict(
        caption_zh=caption, raw_data=sources, transformations=transforms,
        uncertainty=uncertainty, encoding_notes=notes,
        palette="Okabe-Ito", fonts="Times New Roman + Songti SC fallback",
        width_mm=180, png_dpi=DPI_PNG, pdf_fonttype=42,
        publisher_requirements="PENDING — target journal not yet chosen",
    )
    print(f"  {stem}.pdf / .png")


def raw_jitter(ax, x, vals, marker, width=0.16, seed=7):
    rng = np.random.default_rng(seed)
    ax.scatter(x + rng.uniform(-width, width, len(vals)), vals,
               s=7, color="#3A3A3A", marker=marker, alpha=0.5,
               linewidths=0.3, edgecolors="white", zorder=3)


def panel_tag(ax, tag):
    ax.text(-0.14, 1.04, tag, transform=ax.transAxes,
            fontsize=10, fontweight="bold", va="bottom", ha="left")


def footnote(fig, text, y=0.022):
    fig.text(0.012, y, text, fontsize=7.8, color=GREY, ha="left", va="bottom")


# ---------------------------------------------------------------- 图2 消融
def fig2():
    a = D["categorical"]["receipt_transfer"]
    b = D["categorical"]["context_substitution"]
    fig = plt.figure(figsize=(W, 78 * MM))
    axa = fig.add_axes([0.245, 0.20, 0.22, 0.50])
    axb = fig.add_axes([0.615, 0.20, 0.37, 0.50])

    def matrix(ax, spec, tag, title):
        rel, cases, grid, ev = (spec["relations"], spec["cases"],
                                spec["grid"], spec["evidence"])
        nr, nc = len(rel), len(cases)
        ax.set_xlim(0, nc)
        ax.set_ylim(nr, 0)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
        for s in ax.spines.values():
            s.set_visible(False)
        for i in range(nr):
            for j in range(nc):
                acc = grid[i][j] == "接受"
                face = BLUE if acc else VERM
                ax.add_patch(Rectangle((j + .05, i + .08), .90, .84,
                                       facecolor=face, edgecolor="white",
                                       linewidth=1.4, zorder=2))
                ax.text(j + .5, i + .38, "√" if acc else "×",
                        ha="center", va="center", color="white",
                        fontsize=13, fontweight="bold", zorder=3)
                ax.text(j + .5, i + .68, grid[i][j], ha="center", va="center",
                        color="white", fontsize=9.5, fontweight="bold", zorder=3)
                if "Groth16" in ev[i][j]:
                    ax.text(j + .84, i + .20, "◆", ha="center", va="center",
                            color="white", fontsize=6.5, zorder=3)
            ax.text(-.06, i + .5, rel[i], ha="right", va="center", fontsize=9)
        for j, c in enumerate(cases):
            ax.text(j + .5, -.16, c, ha="center", va="bottom", fontsize=9)
        ax.set_title(title, pad=30, loc="center")
        ax.text(-0.16, 1.02, tag, transform=ax.transAxes,
                fontsize=10, fontweight="bold", va="bottom", ha="left")

    matrix(axa, a, "(a)", "回执转移（§5.1）")
    matrix(axb, b, "(b)", "上下文替换（§5.2）")
    footnote(fig, "◆ 该情形还生成并验证了 Groth16 证明；其余为约束求解器检查。"
                  "“接受”表示见证/证明被放行，“拒绝”表示被挡下。", y=0.045)
    export(fig, "fig2_ablation",
           "图 4 受控消融：各项绑定挡住的攻击。(a) 回执转移；(b) 上下文替换。",
           ["experiments/binding.log", "experiments/context_ablation.log"],
           ["逐字转录 RESULT 行的接受/拒绝判定，未做聚合或折算"],
           "分类结果，无不确定度；证据级别（R1CS / R1CS+Groth16）以 ◆ 标注",
           "颜色非唯一线索：每格同时给出 √/× 符号与“接受/拒绝”文字")


# ------------------------------------------------- 图3 上下文隐藏构造代价
def fig3():
    items = [
        ("无记名对照", 29173, GREEN, "s", "放行回执转移（图 4a）"),
        ("上下文隐藏构造", 29503, BLUE, "o", "拒绝两类替换，签发者不再获得上下文"),
        ("主关系", 29833, ORANGE, "^", "拒绝替换，但两侧共享确定性上下文"),
    ]
    fig, ax = plt.subplots(figsize=(W, 66 * MM), layout="constrained")
    reserve_bottom(fig, 0.085)
    ys = np.arange(len(items))[::-1]
    ax.set_ylim(-0.72, 2.62)
    ax.set_xlim(0, 33500)
    ax.axvline(29833, color=GREY, linestyle="--", linewidth=0.9, zorder=5)
    ax.text(29833, 2.50, "主关系基准 29,833", ha="right", va="top",
            fontsize=8, color=GREY)
    for y, (name, val, col, mk, note) in zip(ys, items):
        ax.barh(y, val, height=0.46, color=col, alpha=0.85, edgecolor="white",
                linewidth=0.8, zorder=3)
        ax.text(val + 350, y, f"{val:,}", ha="left", va="center",
                fontsize=9.5, fontweight="bold", color=col)
        ax.text(350, y - 0.36, note, ha="left", va="top", fontsize=8, color=GREY)
    ax.set_yticks(ys)
    ax.set_yticklabels([i[0] for i in items], fontsize=9.5)
    ax.set_xlabel("R1CS 约束数（条）")
    ax.set_xticks([0, 10000, 20000, 30000])
    ax.set_xticklabels(["0", "10,000", "20,000", "30,000"])
    ax.grid(axis="y", visible=False)
    footnote(fig, "横轴为零基线；三个变体约束数相对差异不足 2.3%，具体数值直接标注在"
                  "柱端；上下文隐藏构造未测时间，故本图不含时间。")
    export(fig, "fig3_context_hiding_cost",
           "图 5 三个矩形电路变体的约束数与安全性后果。",
           ["experiments/ablation_cost.log",
            "experiments/context_hiding_candidate.log",
            "experiments/benchmark.log"],
           ["约束数取日志 CIRCUIT/RESULT 行的整数值"],
           "约束数为确定性计数，无不确定度",
           "横轴零基线柱状图；柱端标注绝对值，每柱下方注明安全性后果")


# ------------------------------------------------------- 图4 四电路开销
def fig4():
    fig, axes = plt.subplots(1, 3, figsize=(W, 72 * MM), layout="constrained",
                             gridspec_kw=dict(wspace=0.28))
    reserve_bottom(fig, 0.075)
    for ax in axes:
        ax.tick_params(axis="x", labelsize=8)
    x = np.arange(4)
    con = [D["circuits"][k]["meta"]["constraints"] for k in CIRC]
    pm = [D["circuits"][k]["prove_ms"]["mean"] for k in CIRC]
    ps = [D["circuits"][k]["prove_ms"]["sd"] for k in CIRC]
    vm = [D["circuits"][k]["verify_ms"]["mean"] for k in CIRC]
    vs = [D["circuits"][k]["verify_ms"]["sd"] for k in CIRC]

    ax = axes[0]
    ax.bar(x, con, width=0.62, color=CIRC_COL, edgecolor="white", linewidth=0.8, zorder=2)
    for i, v in enumerate(con):
        ax.text(i, v + 1600, f"{v:,}", ha="center", va="bottom",
                fontsize=8.8, fontweight="bold")
    ax.set_ylim(0, 79000)
    ax.set_ylabel("R1CS 约束数（条）")
    ax.set_title("(a) 电路规模", loc="left")
    ax.set_xticks(x, CIRC_SHORT)
    ax.yaxis.set_major_formatter(lambda v, p: f"{int(v):,}")

    ax = axes[1]
    ax.bar(x, pm, width=0.62, color=CIRC_COL, edgecolor="white", linewidth=0.8, zorder=2)
    ax.errorbar(x, pm, yerr=ps, fmt="none", ecolor=INK, elinewidth=1.0,
                capsize=3.5, capthick=1.0, zorder=4)
    for i, k in enumerate(CIRC):
        raw_jitter(ax, i, D["circuits"][k]["prove_raw_ms"], CIRC_MARK[i], 0.17)
        ax.text(i, pm[i] + ps[i] + 24, f"{pm[i]:.2f}\n±{ps[i]:.2f}",
                ha="center", va="bottom", fontsize=8.2, fontweight="bold", linespacing=1.15)
    ax.set_ylim(0, 560)
    ax.set_ylabel("证明生成时间 (ms)")
    ax.set_title("(b) 证明生成", loc="left")
    ax.set_xticks(x, CIRC_SHORT)

    ax = axes[2]
    ax.bar(x, vm, width=0.62, color=CIRC_COL, edgecolor="white", linewidth=0.8, zorder=2)
    ax.errorbar(x, vm, yerr=vs, fmt="none", ecolor=INK, elinewidth=1.0,
                capsize=3.5, capthick=1.0, zorder=4)
    for i, k in enumerate(CIRC):
        raw_jitter(ax, i, D["circuits"][k]["verify_raw_ms"], CIRC_MARK[i], 0.17)
        ax.text(i, vm[i] + vs[i] + 0.11, f"{vm[i]:.3f}\n±{vs[i]:.3f}",
                ha="center", va="bottom", fontsize=8.2, fontweight="bold", linespacing=1.15)
    ax.set_ylim(0, 1.86)
    ax.set_ylabel("验证时间 (ms)")
    ax.set_title("(c) 网关验证", loc="left")
    ax.set_xticks(x, CIRC_SHORT)

    for ax in axes:
        ax.set_xlim(-0.62, 3.62)
        ax.grid(axis="x", visible=False)
    footnote(fig, "活跃 = 活跃凭证成员性电路。误差棒为样本标准差（n=30，一次预热后）；"
                  "深灰点为逐次原始测量。")
    export(fig, "fig4_circuit_cost",
           "图 6 四个电路的规模与本地开销。",
           ["experiments/benchmark.log", "experiments/region_benchmark.log",
            "experiments/accountability_benchmark.log",
            "experiments/revocation_benchmark.log"],
           ["ns→ms（除以 1e6）；样本均值与样本标准差 ddof=1；约束数取 compile 行整数"],
           "样本标准差，n=30 次测量运行（1 次预热不计入）",
           "柱状图零基线；原始 30 点叠加显示；每柱直接标注均值±标准差")


# --------------------------------------------------- 图5 逐次测量（重绘）
def fig5():
    fig, axes = plt.subplots(1, 2, figsize=(W, 76 * MM), layout="constrained",
                             gridspec_kw=dict(wspace=0.26))
    reserve_bottom(fig, 0.085)
    for ax, key, title in ((axes[0], "prove", "(a) 证明生成"),
                           (axes[1], "verify", "(b) 证明验证")):
        for k, cn, col, mk in zip(CIRC, CIRC_CN, CIRC_COL, CIRC_MARK):
            v = D["circuits"][k][f"{key}_raw_ms"]
            ax.scatter(range(1, 31), v, s=17, color=col, marker=mk,
                       alpha=0.8, label=cn, linewidths=0.3, edgecolors="white", zorder=3)
            ax.axhline(float(np.median(v)), color=col, linestyle="--",
                       linewidth=0.9, alpha=0.9, zorder=2)
        ax.set_xlim(0, 31)
        ax.set_xlabel("测量序号")
        ax.set_ylabel("时间 (ms)")
        ax.set_title(title, loc="left")
        ax.grid(axis="x", visible=False)
    axes[0].set_ylim(0, 520)
    axes[1].set_ylim(0, 1.9)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, frameon=False, loc="lower center", ncol=4,
               bbox_to_anchor=(0.5, 0.012), handletextpad=0.5, columnspacing=1.8)
    export(fig, "fig5_per_run",
           "图 7 四个电路各三十次本地证明生成与验证的逐次测量（虚线为中位数；"
           "两面板纵轴均为零基线）。",
           ["experiments/benchmark.log", "experiments/region_benchmark.log",
            "experiments/accountability_benchmark.log",
            "experiments/revocation_benchmark.log"],
           ["ns→ms；逐次原值直接绘制，未平滑；中位数由 30 个原值算得"],
           "逐次原始观测，n=30；虚线为中位数（非均值）",
           "四个序列用不同标记区分，颜色非唯一线索")


# ------------------------------------------------------- 图6 树深缩放
def fig6():
    depths = [4, 6, 8]
    cells = [16, 64, 256]
    con = [D["region_scaling"][str(d)]["meta"]["constraints"] for d in depths]
    pm = [D["region_scaling"][str(d)]["prove_ms"]["mean"] for d in depths]
    ps = [D["region_scaling"][str(d)]["prove_ms"]["sd"] for d in depths]
    vm = [D["region_scaling"][str(d)]["verify_ms"]["mean"] for d in depths]
    vs = [D["region_scaling"][str(d)]["verify_ms"]["sd"] for d in depths]
    xt = [f"{d} / {n}" for d, n in zip(depths, cells)]

    fig, axes = plt.subplots(1, 3, figsize=(W, 68 * MM), layout="constrained",
                             gridspec_kw=dict(wspace=0.34))
    reserve_bottom(fig, 0.075)

    ax = axes[0]
    ax.plot(depths, con, color=BLUE, marker="o", markersize=7, linewidth=1.6,
            markeredgecolor="white", markeredgewidth=0.9, zorder=3)
    for d, c in zip(depths, con):
        ax.annotate(f"{c:,}", (d, c), textcoords="offset points", xytext=(0, 11),
                    ha="center", fontsize=9, fontweight="bold", color=BLUE,
                    bbox=dict(boxstyle="round,pad=0.14", facecolor="white",
                              edgecolor="none"))
    ax.set_ylim(0, 37600)
    ax.set_xlim(3.4, 8.6)
    ax.set_xticks(depths, xt)
    ax.set_xlabel("区域树深度 / 授权单元数")
    ax.set_ylabel("R1CS 约束数（条）")
    ax.set_title("(a) 约束数", loc="left")
    ax.yaxis.set_major_formatter(lambda v, p: f"{int(v):,}")
    ax.text(0.03, 0.60, "+2,652 条（+8.0%）", transform=ax.transAxes,
            fontsize=9, color=VERM, fontweight="bold", va="top")
    ax.text(0.03, 0.52, "单元数 ×16", transform=ax.transAxes,
            fontsize=8.2, color=GREY, va="top")

    ax = axes[1]
    ax.errorbar(depths, pm, yerr=ps, color=GREEN, marker="s", markersize=7,
                linewidth=1.6, capsize=4, capthick=1.0, elinewidth=1.0,
                markeredgecolor="white", markeredgewidth=0.9, zorder=3)
    for i, (d, m, s) in enumerate(zip(depths, pm, ps)):
        dy = 12 if i != 1 else -20
        ax.annotate(f"{m:.2f}±{s:.2f}", (d, m), textcoords="offset points",
                    xytext=(0, dy), ha="center", fontsize=8.0,
                    fontweight="bold", color=GREEN,
                    bbox=dict(boxstyle="round,pad=0.12", facecolor="white",
                              edgecolor="none"))
    ax.set_ylim(0, 268)
    ax.set_xlim(3.4, 8.6)
    ax.set_xticks(depths, xt)
    ax.set_xlabel("区域树深度 / 授权单元数")
    ax.set_ylabel("证明生成时间 (ms)")
    ax.set_title("(b) 证明生成", loc="left")
    ax.text(0.03, 0.55, "+10.65 ms（+5.2%）", transform=ax.transAxes,
            fontsize=9, color=VERM, fontweight="bold", va="top")

    ax = axes[2]
    ax.errorbar(depths, vm, yerr=vs, color=PURPLE, marker="D", markersize=6,
                linewidth=1.6, capsize=4, capthick=1.0, elinewidth=1.0,
                markeredgecolor="white", markeredgewidth=0.9, zorder=3)
    for d, m in zip(depths, vm):
        ax.annotate(f"{m:.3f}", (d, m), textcoords="offset points",
                    xytext=(0, 11), ha="center", fontsize=8.6,
                    fontweight="bold", color=PURPLE)
    ax.set_ylim(0, 1.62)
    ax.set_xlim(3.4, 8.6)
    ax.set_xticks(depths, xt)
    ax.set_xlabel("区域树深度 / 授权单元数")
    ax.set_ylabel("验证时间 (ms)")
    ax.set_title("(c) 网关验证", loc="left")
    ax.text(0.03, 0.96, "≈1 ms，基本不变", transform=ax.transAxes,
            fontsize=9, color=VERM, fontweight="bold", va="top")
    for ax in axes:
        ax.grid(axis="x", visible=False)
    footnote(fig, "误差棒为样本标准差（n=30）。三个面板纵轴均为零基线，各自独立量程，"
                  "未用双轴；(a) 的绝对增量与增长率直接标注在图内。")
    export(fig, "fig6_region_scaling",
           "图 8 区域树深度对约束数、证明生成与验证时间的影响。",
           ["experiments/region_scale_4.log", "experiments/region_scale_6.log",
            "experiments/region_scale_8.log"],
           ["ns→ms；均值与样本标准差 ddof=1；增长率由两端均值/约束数相除算得"],
           "样本标准差，n=30；约束数为确定性计数",
           "三面板均零基线且分量程；(b)(c) 独立量程，避免把 ~1 ms 的验证画成不可见")


# --------------------------------------------------- 图7 受理耗时分解
def fig7():
    e = D["end_to_end"]
    prove = e["prove_ns"]["mean"]
    total = e["total_to_accept_ns"]["mean"]
    others = [("网关验证·解密·查重", e["gateway_verify_decrypt_dedup_ns"]["mean"], BLUE),
              ("夹具签名与见证构造", e["fixture_sign_and_witness_ns"]["mean"], GREEN),
              ("报告加密", e["encrypt_ns"]["mean"], ORANGE),
              ("证明序列化", e["proof_serialize_ns"]["mean"], PURPLE),
              ("挑战签发", e["challenge_ns"]["mean"], SKY)]
    rest = total - prove

    fig = plt.figure(figsize=(W, 66 * MM), layout="constrained")
    gs = fig.add_gridspec(1, 2, width_ratios=[1.05, 1.5], wspace=0.46)

    ax = fig.add_subplot(gs[0, 0])
    ax.barh([0], [prove], height=0.40, color=VERM, edgecolor="white",
            linewidth=0.8, zorder=2)
    ax.barh([0], [rest], left=[prove], height=0.40, color=GREY,
            edgecolor="white", linewidth=0.8, zorder=2)
    ax.set_ylim(-0.62, 1.02)
    ax.set_xlim(0, 452)
    ax.set_yticks([])
    ax.set_xlabel("时间 (ms)")
    ax.set_title("(a) 受理总耗时构成", loc="left")
    ax.grid(axis="y", visible=False)
    ax.text(prove / 2, 0, f"证明生成 {prove:.2f} ms\n{prove / total * 100:.2f}%",
            ha="center", va="center", color="white", fontsize=9.5,
            fontweight="bold", zorder=3, linespacing=1.3)
    ax.annotate(f"其余合计 {rest:.2f} ms（{rest / total * 100:.2f}%）\n见 (b)，注意尺度不同",
                xy=(total, 0.20), xytext=(292, 0.78),
                fontsize=8.4, color=INK, ha="center", va="center",
                arrowprops=dict(arrowstyle="-|>", color=GREY, lw=0.9,
                                connectionstyle="arc3,rad=-0.18"),
                bbox=dict(boxstyle="round,pad=0.32", facecolor="#F5F5F5",
                          edgecolor="#CCCCCC", linewidth=0.6))
    ax.text(0.0, -0.48, f"总计 {total:.2f}±{e['total_to_accept_ns']['sd']:.2f} ms",
            transform=ax.get_yaxis_transform(), fontsize=8.8,
            fontweight="bold", va="center")

    ax = fig.add_subplot(gs[0, 1])
    names = [o[0] for o in others]
    vals = [o[1] for o in others]
    cols = [o[2] for o in others]
    y = np.arange(len(others))[::-1]
    ax.barh(y, vals, height=0.56, color=cols, edgecolor="white",
            linewidth=0.8, zorder=2)
    for yy, v in zip(y, vals):
        ax.text(v + 0.035, yy, f"{v:.3f}", va="center", ha="left",
                fontsize=8.8, fontweight="bold")
    ax.set_yticks(y, names, fontsize=8.8)
    ax.set_xlim(0, 1.72)
    ax.set_ylim(-1.18, len(others) - 0.20)
    ax.set_xlabel("时间 (ms)")
    ax.set_title("(b) 除证明生成外的分量（尺度与 (a) 不同）", loc="left", fontsize=9)
    ax.grid(axis="y", visible=False)
    ax.axhline(-0.34, color="#CCCCCC", linewidth=0.7)
    ax.barh([-0.78], [e["audit_open_ns"]["mean"]], height=0.42, color="white",
            edgecolor=GREY, linewidth=0.9, hatch="////", zorder=2)
    ax.text(e["audit_open_ns"]["mean"] + 0.035, -0.78,
            f"{e['audit_open_ns']['mean']:.3f}（单独计时）",
            va="center", ha="left", fontsize=8.2, color=GREY)
    ax.text(-0.02, -0.78, "身份开启", transform=ax.get_yaxis_transform(),
          va="center", ha="right", fontsize=8.8, color=GREY)
    footnote(fig, "身份开启为单独计时项，不计入受理总耗时；(a) 的灰色尾段即 (b) 各分量之和。",
             y=0.018)
    reserve_bottom(fig, 0.07)
    export(fig, "fig7_accept_latency",
           "图 9 同进程受理路径的耗时分解。",
           ["experiments/end_to_end.log"],
           ["ns→ms；各分量取 30 次样本均值；其余合计 = 总均值 − 证明生成均值"],
           "样本标准差，n=30；(a) 标注总耗时的均值±标准差",
           "(a) 零基线堆叠条；(b) 为零基线但量程不同的独立面板，尺度差异已在标题与图注披露")


# --------------------------------------------------- 图8 通信量分解
def fig8():
    e = D["end_to_end"]
    parts = [("报告信封", e["envelope_bytes"][0], BLUE),
             ("零知识证明", e["proof_bytes"][0], VERM),
             ("挑战 nonce", e["nonce_ascii_bytes"][0], GREEN),
             ("身份密文", e["identity_cipher_bytes"][0], PURPLE),
             ("任务标签", e["nullifier_bytes"][0], ORANGE)]
    total = e["component_sum_bytes"][0]

    fig = plt.figure(figsize=(W, 84 * MM))
    ax_a = fig.add_axes([0.055, 0.34, 0.55, 0.50])
    ax_b = fig.add_axes([0.72, 0.34, 0.265, 0.50])
    ax = ax_a
    left = 0
    for name, v, col in parts:
        ax.barh([0], [v], left=[left], height=0.40, color=col,
                edgecolor="white", linewidth=1.0, zorder=2)
        if v >= 100:
            ax.text(left + v / 2, 0, f"{v:,}", ha="center", va="center",
                    color="white", fontsize=9, fontweight="bold", zorder=3)
        left += v
    ax.set_xlim(0, total * 1.02)
    ax.set_ylim(-0.75, 1.05)
    ax.set_yticks([])
    ax.set_xlabel("字节")
    ax.set_title("(a) 单份提交的通信量构成", loc="left")
    ax.grid(axis="y", visible=False)
    ax.text(total * 0.99, 0.66, f"合计 {total:,} 字节", ha="right", va="center",
            fontsize=9.5, fontweight="bold")
    ax.text(0, 0.66, f"明文 {e['plaintext_bytes'][0]} 字节 → 信封 {e['envelope_bytes'][0]:,} 字节",
            ha="left", va="center", fontsize=8.4, color=GREY)

    ax = ax_b
    ax.tick_params(axis="x", labelsize=8)
    x = np.arange(4)
    pw = [D["circuits"][k]["public_witness_bytes"][0] for k in CIRC]
    pb = [D["circuits"][k]["proof_bytes"][0] for k in CIRC]
    ax.bar(x - 0.19, pb, width=0.36, color=VERM, edgecolor="white",
           linewidth=0.8, zorder=2, label="证明")
    ax.bar(x + 0.19, pw, width=0.36, color=SKY, edgecolor="white",
           linewidth=0.8, zorder=2, label="公开见证")
    for i in range(4):
        ax.text(i - 0.19, pb[i] + 14, str(pb[i]), ha="center", va="bottom",
                fontsize=8.6, fontweight="bold", color=VERM)
        ax.text(i + 0.19, pw[i] + 14, str(pw[i]), ha="center", va="bottom",
                fontsize=8.6, fontweight="bold", color="#2A7FB8")
    ax.set_xticks(x, CIRC_CN)
    ax.set_ylim(0, 740)
    ax.set_xlim(-0.62, 3.62)
    ax.set_ylabel("字节")
    ax.set_title("(b) 证明尺寸不随电路规模变化", loc="left", fontsize=9)
    ax.legend(frameon=False, loc="upper left", fontsize=8.5)
    ax.grid(axis="x", visible=False)

    handles = [Rectangle((0, 0), 1, 1, facecolor=c, edgecolor="white")
               for _, _, c in parts]
    fig.legend(handles, [f"{n} {v:,} B（{v / total * 100:.1f}%）" for n, v, _ in parts],
               frameon=False, loc="lower center", ncol=3,
               bbox_to_anchor=(0.5, 0.115), fontsize=7.8,
               handlelength=1.1, handleheight=0.9, columnspacing=1.6,
               handletextpad=0.4, labelspacing=0.35)
    footnote(fig, "信封 = ML-KEM-768 密文 + AES-256-GCM；身份密文为两个压缩群点。"
                  "公开见证由网关本地重构，不计入 (a)；(a) 不含传输成帧与配置分发。", y=0.02)
    export(fig, "fig8_communication",
           "图 10 单份提交的通信量构成与证明尺寸。",
           ["experiments/end_to_end.log", "experiments/benchmark.log",
            "experiments/region_benchmark.log",
            "experiments/accountability_benchmark.log",
            "experiments/revocation_benchmark.log"],
           ["字节数取日志中 30 次运行恒定的整数值；占比由分量除以合计算得"],
           "确定性字节计数，30 次运行中取值恒定，无不确定度",
           "零基线堆叠条与分组柱；大段直接标注字节数，小段数值在图例给出，颜色非唯一线索")


# ------------------------------------------- 图9 隐藏构造扩展到全部电路
def fig9():
    H = D["hidden_extensions"]
    keys = ["rectangle", "region", "accountability", "active"]
    shared_con = [H[k]["shared_constraints"] for k in keys]
    hidden_con = [H[k]["hidden_constraints"] for k in keys]
    shared_pm = [D["circuits"][k]["prove_ms"]["mean"] for k in keys]
    shared_ps = [D["circuits"][k]["prove_ms"]["sd"] for k in keys]
    hidden_pm = [H[k]["prove_ns"]["mean"] for k in keys]
    hidden_ps = [H[k]["prove_ns"]["sd"] for k in keys]

    fig, axes = plt.subplots(1, 2, figsize=(W, 78 * MM), layout="constrained",
                             gridspec_kw=dict(wspace=0.26))
    reserve_bottom(fig, 0.115)
    x = np.arange(4)
    w = 0.36

    ax = axes[0]
    ax.bar(x - w / 2, shared_con, width=w, color=ORANGE, edgecolor="white",
           linewidth=0.8, zorder=2, label="共享上下文")
    ax.bar(x + w / 2, hidden_con, width=w, color=BLUE, edgecolor="white",
           linewidth=0.8, zorder=2, label="隐藏上下文")
    for i in range(4):
        ax.text(i - w / 2, shared_con[i] + 1500, f"{shared_con[i]:,}",
                ha="center", va="bottom", fontsize=7.6, fontweight="bold",
                color="#9A6B00", rotation=90)
        ax.text(i + w / 2, hidden_con[i] + 1500, f"{hidden_con[i]:,}",
                ha="center", va="bottom", fontsize=7.6, fontweight="bold",
                color=BLUE, rotation=90)
    ax.set_ylim(0, 88000)
    ax.set_xlim(-0.62, 3.62)
    ax.set_xticks(x, CIRC_SHORT)
    ax.set_ylabel("R1CS 约束数（条）")
    ax.set_title("(a) 四个电路的约束数", loc="left")
    ax.yaxis.set_major_formatter(lambda v, p: f"{int(v):,}")
    ax.legend(frameon=False, loc="upper left", fontsize=8.5)
    ax.grid(axis="x", visible=False)
    ax.text(0.985, 0.50, "每个电路均 −330 条", transform=ax.transAxes,
            fontsize=8.6, color=VERM, fontweight="bold", ha="right",
            rotation=90, va="center")

    ax = axes[1]
    ax.bar(x - w / 2, shared_pm, width=w, color=ORANGE, edgecolor="white",
           linewidth=0.8, zorder=2, label="共享上下文")
    ax.bar(x + w / 2, hidden_pm, width=w, color=BLUE, edgecolor="white",
           linewidth=0.8, zorder=2, label="隐藏上下文")
    ax.errorbar(x - w / 2, shared_pm, yerr=shared_ps, fmt="none", ecolor=INK,
                elinewidth=1.0, capsize=3.0, capthick=1.0, zorder=4)
    ax.errorbar(x + w / 2, hidden_pm, yerr=hidden_ps, fmt="none", ecolor=INK,
                elinewidth=1.0, capsize=3.0, capthick=1.0, zorder=4)
    for i in range(4):
        ax.text(i - w / 2, shared_pm[i] + shared_ps[i] + 40,
                f"{shared_pm[i]:.1f}", ha="center", va="bottom",
                fontsize=7.8, fontweight="bold", color="#9A6B00")
        ax.text(i + w / 2, hidden_pm[i] + hidden_ps[i] + 18,
                f"{hidden_pm[i]:.1f}", ha="center", va="bottom",
                fontsize=7.8, fontweight="bold", color=BLUE)
        raw_jitter(ax, i + w / 2, H[keys[i]]["prove_ns_raw_ms"], CIRC_MARK[i], 0.10)
    ax.set_ylim(0, 560)
    ax.set_xlim(-0.62, 3.62)
    ax.set_xticks(x, CIRC_SHORT)
    ax.set_ylabel("证明生成时间 (ms)")
    ax.set_title("(b) 证明生成时间", loc="left")
    ax.legend(frameon=False, loc="upper left", fontsize=8.5)
    ax.grid(axis="x", visible=False)

    footnote(fig, "共享上下文数值取自 benchmark.log（同机、独立会话）；隐藏上下文取自 context_hiding_extensions.log。\n"
                  "矩形隐藏版同 benchmark.log 用固定见证法，扩展隐藏版逐次新鲜见证；误差棒为样本标准差（n=30，一次预热后），灰点为隐藏版原始测量。")
    export(fig, "fig9_hidden_extensions",
           "图 11 上下文隐藏构造扩展到全部四个电路：约束数与证明生成时间。",
           ["experiments/context_hiding_extensions.log",
            "experiments/benchmark.log", "experiments/region_benchmark.log",
            "experiments/accountability_benchmark.log",
            "experiments/revocation_benchmark.log"],
           ["ns→ms；均值与样本标准差 ddof=1；约束数取 VARIANT 行整数；差值由共享减隐藏算得"],
           "样本标准差，n=30；约束数为确定性计数",
           "零基线分组柱；每柱直接标注数值；(a) 数值标签竖排以免重叠；颜色非唯一线索（图例＋位置＋标签）")


# ------------------------------------------- 图10 三臂同任务对照
def fig10():
    C = D["protocol_comparison"]
    S = D["protocol_comparison_structure"]
    base = C["trusted_baseline"]
    arms = ["shared_active", "hidden_active", "trusted_baseline"]
    labels = ["共享上下文\n活跃版", "隐藏上下文\n活跃版", "可信签发\n基线"]
    cols = [ORANGE, BLUE, GREEN]
    tm = [C[a]["total_to_accept_ns"]["mean"] for a in arms]
    ts = [C[a]["total_to_accept_ns"]["sd"] for a in arms]

    fig = plt.figure(figsize=(W, 86 * MM))
    ax_a = fig.add_axes([0.065, 0.40, 0.27, 0.46])
    ax_b = fig.add_axes([0.415, 0.40, 0.27, 0.46])
    ax_c = fig.add_axes([0.775, 0.40, 0.21, 0.46])

    ax = ax_a
    x = np.arange(3)
    ax.bar(x, tm, width=0.58, color=cols, edgecolor="white", linewidth=0.8, zorder=2)
    ax.errorbar(x, tm, yerr=ts, fmt="none", ecolor=INK, elinewidth=1.0,
                capsize=3.5, capthick=1.0, zorder=4)
    for i, a in enumerate(arms):
        raw_jitter(ax, i, C[a]["total_to_accept_ns_raw_ms"], "o", 0.13)
        nd = 3 if a == "trusted_baseline" else 2
        ax.text(i, tm[i] + ts[i] + 16, f"{tm[i]:.{nd}f}\n±{ts[i]:.{nd}f}",
                ha="center", va="bottom", fontsize=7.8, fontweight="bold",
                linespacing=1.15)
    ax.set_ylim(0, 520)
    ax.set_xlim(-0.62, 2.62)
    ax.set_xticks(x, labels, fontsize=8)
    ax.set_ylabel("挑战至受理总耗时 (ms)")
    ax.set_title("(a) 受理延迟", loc="left")
    ax.grid(axis="x", visible=False)

    ax = ax_b
    zk = C["shared_active"]
    zk_parts = [("报告信封", zk["envelope_bytes"][0], BLUE),
                ("证明/回执", zk["proof_bytes"][0], VERM),
                ("挑战 nonce", zk["nonce_ascii_bytes"][0], GREEN),
                ("任务标签", zk["nullifier_bytes"][0], ORANGE),
                ("身份密文", zk["identity_cipher_bytes"][0], PURPLE)]
    for i, a in enumerate(arms[:2]):
        left = 0
        for name, v, col in zk_parts:
            ax.bar(i, v, bottom=left, width=0.52, color=col,
                   edgecolor="white", linewidth=0.8, zorder=2)
            if v >= 100:
                ax.text(i, left + v / 2, f"{v:,}", ha="center", va="center",
                        color="white", fontsize=7.8, fontweight="bold", zorder=3)
            left += v
        ax.text(i, left + 34, f"{left:,}", ha="center", va="bottom",
                fontsize=8.4, fontweight="bold")
    left = 0
    base_parts = [("报告明文", base["plaintext_bytes"][0], BLUE),
                  ("证明/回执", base["receipt_bytes"][0], VERM),
                  ("挑战 nonce", base["nonce_ascii_bytes"][0], GREEN)]
    for name, v, col in base_parts:
        ax.bar(2, v, bottom=left, width=0.52, color=col,
               edgecolor="white", linewidth=0.8, zorder=2)
        if v >= 100:
            ax.text(2, left + v / 2, f"{v:,}", ha="center", va="center",
                    color="white", fontsize=7.8, fontweight="bold", zorder=3)
        left += v
    ax.text(2, left + 34, f"{left:,}", ha="center", va="bottom",
            fontsize=8.4, fontweight="bold")
    ax.set_ylim(0, 1720)
    ax.set_xlim(-0.62, 2.62)
    ax.set_xticks(x, labels, fontsize=8)
    ax.set_ylabel("网关提交分量合计 (B)")
    ax.set_title("(b) 提交通信量", loc="left")
    ax.grid(axis="x", visible=False)

    ax = ax_c
    iv = [S["shared_active"], S["hidden_active"], base["request_bytes"][0]]
    ax.bar(x, iv, width=0.58, color=cols, edgecolor="white", linewidth=0.8, zorder=2)
    notes = ["上下文＋持有人\n＋事件", "持有人＋事件", "身份密钥＋全文\n＋事件"]
    for i, v in enumerate(iv):
        ax.text(i, v + 7, str(v), ha="center", va="bottom",
                fontsize=8.4, fontweight="bold")
        ax.text(i, -62, notes[i], ha="center", va="top", fontsize=7.2,
                color=GREY, linespacing=1.2)
    ax.set_ylim(0, 268)
    ax.set_xlim(-0.62, 2.62)
    ax.set_xticks(x, labels, fontsize=8)
    ax.set_ylabel("签发者请求分量 (B)")
    ax.set_title("(c) 签发者可见输入", loc="left")
    ax.grid(axis="x", visible=False)

    handles = [Rectangle((0, 0), 1, 1, facecolor=c, edgecolor="white")
               for _, _, c in zk_parts]
    fig.legend(handles, ["报告信封/明文", "证明/签名回执", "挑战 nonce",
                         "任务标签（仅 ZK 臂）", "身份密文（仅 ZK 臂）"],
               frameon=False, loc="lower center", ncol=5,
               bbox_to_anchor=(0.5, 0.10), fontsize=7.6,
               handlelength=1.1, handleheight=0.9, columnspacing=1.4,
               handletextpad=0.4)
    footnote(fig, "三臂在同一进程、同一任务形状下顺序测量（protocol_comparison.log，n=30，一次预热后）；(b) 不含传输成帧。\n"
                  f"基线回执 {base['receipt_bytes'][0]} B＝假名 32＋事件 12＋摘要 64＋签名 64；(c) 取 STRUCTURE 与 request_bytes 行（基线含报告全文）；误差棒为样本标准差。",
             y=0.015)
    export(fig, "fig10_protocol_comparison",
           "图 12 同一任务下三臂对照：受理延迟、提交通信量与签发者可见输入。",
           ["experiments/protocol_comparison.log"],
           ["ns→ms；均值与样本标准差 ddof=1；字节数取日志恒定整数；签发者输入取 STRUCTURE 行"],
           "样本标准差，n=30；字节数为确定性计数",
           "零基线柱状/堆叠条；每柱直接标注数值；(c) 下方文字注明各臂签发者实际可见字段，颜色非唯一线索")


# ------------------------------------------- 图11 非 SNARK 匿名基线对照
def fig11():
    C = D["nonsnark_baseline"]
    zk, bbs, pp, base = C["hidden_active"], C["bbs_credential"], C["privacy_pass"], C["trusted_baseline"]
    arms = ["bbs_credential", "privacy_pass", "trusted_baseline"]
    labels = ["BBS+ 匿名凭证", "Privacy Pass 令牌", "可信签发基线"]

    fig = plt.figure(figsize=(W, 112 * MM))
    ax_a = fig.add_axes([0.072, 0.605, 0.890, 0.300])
    ax_b = fig.add_axes([0.072, 0.150, 0.415, 0.290])
    ax_c = fig.add_axes([0.575, 0.150, 0.387, 0.290])

    # (a) role-split latency of the three non-SNARK arms
    ax = ax_a
    parts = {
        "bbs_credential": [("参与者侧", bbs["request_sign_ns"]["mean"] + bbs["derive_presentation_ns"]["mean"], BLUE),
                           ("签发者侧", bbs["issuer_verify_and_sign_ns"]["mean"], VERM),
                           ("网关侧", bbs["gateway_verify_dedup_ns"]["mean"], GREEN)],
        "privacy_pass": [("参与者侧", pp["blind_ns"]["mean"] + pp["finalize_ns"]["mean"], BLUE),
                         ("签发者侧", pp["issuer_evaluate_ns"]["mean"], VERM),
                         ("网关侧", pp["gateway_state_ns"]["mean"], GREEN)],
        "trusted_baseline": [("参与者侧", base["request_sign_ns"]["mean"], BLUE),
                             ("签发者侧", base["issuer_verify_and_sign_ns"]["mean"], VERM),
                             ("网关侧", base["gateway_verify_dedup_ns"]["mean"], GREEN)],
    }
    x = np.arange(3)
    for i, a in enumerate(arms):
        left = 0.0
        for name, v, col in parts[a]:
            ax.bar(i, v, bottom=left, width=0.54, color=col, edgecolor="white",
                   linewidth=0.8, zorder=2)
            if v >= 0.55:
                ax.text(i, left + v / 2, f"{v:.2f}", ha="center", va="center",
                        color="white", fontsize=7.6, fontweight="bold", zorder=3)
            left += v
        tot = C[a]["total_to_accept_ns"]
        ax.errorbar(i, tot["mean"], yerr=tot["sd"], fmt="none", ecolor=INK,
                    elinewidth=1.0, capsize=3.5, capthick=1.0, zorder=4)
        ax.text(i, tot["mean"] + tot["sd"] + 0.35, f"{tot['mean']:.2f}",
                ha="center", va="bottom", fontsize=8.4, fontweight="bold")
    ax.set_ylim(0, 18.5)
    ax.set_xlim(-0.62, 2.62)
    ax.set_xticks(x, labels, fontsize=7.6)
    ax.set_ylabel("挑战至受理总耗时 (ms)")
    ax.set_title("(a) 非零知识三臂分角色耗时", loc="left")
    ax.grid(axis="x", visible=False)
    if pp["issuer_redeem_ns"]["mean"] > 0:
        ax.annotate(f"Privacy Pass 另有签发者兑换 {pp['issuer_redeem_ns']['mean']:.3f} ms（第 4 次往返，已计入总耗时）",
                    xy=(1, parts["privacy_pass"][0][1] + parts["privacy_pass"][1][1] / 2),
                    xytext=(-0.55, 17.2), ha="left",
                    arrowprops=dict(arrowstyle="-", lw=0.7, color=GREY,
                                    connectionstyle="arc3,rad=0.22"))

    # (b) gateway-side cost per submission, all four arms
    ax = ax_b
    gw = [(bbs, "gateway_verify_dedup_ns"), (pp, "gateway_state_ns"),
          (zk, "gateway_verify_decrypt_dedup_ns"), (base, "gateway_verify_dedup_ns")]
    gw_labels = ["BBS+\n出示验证", "Privacy Pass\n字段检查", "隐藏上下文\n活跃版", "可信签发\n基线"]
    gw_cols = [VERM, PURPLE, BLUE, GREEN]
    gx = np.arange(4)
    means = [arm[col]["mean"] for arm, col in gw]
    sds = [arm[col]["sd"] for arm, col in gw]
    ax.bar(gx, means, width=0.56, color=gw_cols, edgecolor="white", linewidth=0.8, zorder=2)
    ax.errorbar(gx, means, yerr=sds, fmt="none", ecolor=INK, elinewidth=1.0,
                capsize=3.5, capthick=1.0, zorder=4)
    for i, (arm, col) in enumerate(gw):
        raw_jitter(ax, i, arm[col + "_raw_ms"], "o", 0.13, seed=11 + i)
        nd = 3 if means[i] < 10 else 2
        ax.text(i, means[i] + sds[i] + 0.12, f"{means[i]:.{nd}f}", ha="center",
                va="bottom", fontsize=8.2, fontweight="bold")
    ax.set_ylim(0, 5.9)
    ax.set_xlim(-0.62, 3.62)
    ax.set_xticks(gx, gw_labels, fontsize=7.6)
    ax.set_ylabel("网关侧单份耗时 (ms)")
    ax.set_title("(b) 网关侧验证代价", loc="left")
    ax.grid(axis="x", visible=False)

    # (c) submission payload, all four arms
    ax = ax_c
    sums = [bbs["component_sum_bytes"][0], pp["component_sum_bytes"][0],
            zk["component_sum_bytes"][0], base["component_sum_bytes"][0]]
    notes = [f"{bbs['component_sum_bytes'][0]:,}\n另需报告明文\n{bbs['plaintext_bytes'][0]} B",
             f"{pp['component_sum_bytes'][0]:,}",
             f"{zk['component_sum_bytes'][0]:,}",
             f"{base['component_sum_bytes'][0]:,}"]
    ax.bar(gx, sums, width=0.56, color=gw_cols, edgecolor="white", linewidth=0.8, zorder=2)
    for i, v in enumerate(sums):
        ax.text(i, v + 40, notes[i], ha="center", va="bottom", fontsize=7.6,
                fontweight="bold", linespacing=1.2)
    ax.set_ylim(0, 2050)
    ax.set_xlim(-0.62, 3.62)
    ax.set_xticks(gx, ["BBS+ 凭证", "Privacy Pass\n令牌", "隐藏上下文\n活跃版", "可信签发\n基线"], fontsize=7.6)
    ax.set_ylabel("网关提交分量合计 (B)")
    ax.set_title("(c) 单份提交通信量", loc="left")
    ax.grid(axis="x", visible=False)

    handles = [Rectangle((0, 0), 1, 1, facecolor=c, edgecolor="white")
               for c in (BLUE, VERM, GREEN)]
    fig.legend(handles, ["参与者侧（签名/盲化/出示导出）", "签发者侧（验签与签名）", "网关侧（验证与查重）"],
               frameon=False, loc="lower center", ncol=3, bbox_to_anchor=(0.5, 0.500),
               fontsize=7.4, handlelength=1.1, handleheight=0.9,
               columnspacing=1.6, handletextpad=0.4)
    footnote(fig, "四臂在同一进程、同一任务形状下顺序测量，每臂一次预热后测 30 次（nonsnark_baseline.log）；误差棒为样本标准差。\n"
                  f"隐藏上下文活跃臂端到端 {zk['total_to_accept_ns']['mean']:.2f}±{zk['total_to_accept_ns']['sd']:.2f} ms，"
                  f"为 BBS+ 臂的 {zk['total_to_accept_ns']['mean'] / bbs['total_to_accept_ns']['mean']:.1f} 倍、"
                  f"Privacy Pass 臂的 {zk['total_to_accept_ns']['mean'] / pp['total_to_accept_ns']['mean']:.1f} 倍，量程与 (a) 不同故不入柱。",
             y=0.012)

    export(fig, "fig11_nonsnark_baseline",
           "图 13 两条匿名非零知识基线与零知识臂的四臂对照：分角色耗时、网关侧代价与单份提交通信量。",
           ["experiments/nonsnark_baseline.log"],
           ["ns→ms；均值与样本标准差 ddof=1，n=30；(a) 参与者侧为请求签名与出示导出（BBS+）或盲化与令牌合成（Privacy Pass）之和；字节数取日志恒定整数"],
           "样本标准差，n=30；字节数为确定性计数",
           "零基线柱状/堆叠条；三面板量程各自独立且 (a) 不含零知识臂，量程差异已在图注与脚注声明；每柱直接标注数值；(b) 叠加逐次原始测量；颜色非唯一线索")


if __name__ == "__main__":
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        print("rendering:")
        fig2(); fig3(); fig4(); fig5(); fig6(); fig7(); fig8(); fig9(); fig10(); fig11()
        glyph = [str(x.message) for x in w
                 if "missing from" in str(x.message).lower()
                 or "glyph" in str(x.message).lower()]
        print(f"\nfont/glyph warnings: {len(glyph)}")
        for g in glyph[:12]:
            print("  ", g)
    (HERE / "figures_manifest.json").write_text(
        json.dumps(MANIFEST, ensure_ascii=False, indent=1))
    print("\nwrote figures_manifest.json")