#!/usr/bin/env python3
"""Conceptual (non-data) figures for the Chinese draft.

These are explanatory schematics, NOT data plots: they contain no measured
values, only protocol structure already stated in the manuscript. Drawn with
matplotlib so every label is exact, editable and vector-exportable (a generative
image model would garble the Chinese labels and symbols).

  fig1_workflow_v2  -> 图 1  numbered role / evidence flow + privacy boundary
  fig_binding       -> 图 2  one secret, three derivations; context binds bytes
  fig_collusion     -> 图 3  shared deterministic join key vs hidden context

Palette Okabe-Ito; Times New Roman + Songti SC fallback; PDF(Type42) + 400dpi PNG.
"""
from pathlib import Path
import json
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch

HERE = Path(__file__).resolve().parent
MM = 1 / 25.4
W = 180 * MM
DPI = 400

BLUE = "#0072B2"
GREEN = "#009E73"
ORANGE = "#E69F00"
PURPLE = "#CC79A7"
SKY = "#56B4E9"
VERM = "#D55E00"
INK = "#1A1A1A"
GREY = "#6E6E6E"
LIGHT = "#F4F6F8"

plt.rcParams.update({
    "font.family": ["Times New Roman", "Songti SC"],
    "mathtext.fontset": "stix",
    "font.size": 9,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
    "axes.unicode_minus": False,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
    "text.color": INK,
})

MANIFEST = {}


def export(fig, stem, caption, notes):
    fig.savefig(HERE / f"{stem}.pdf", bbox_inches=None)
    fig.savefig(HERE / f"{stem}.png", dpi=DPI, bbox_inches=None)
    plt.close(fig)
    MANIFEST[stem] = dict(caption_zh=caption, kind="conceptual schematic (no measured data)",
                          encoding_notes=notes, palette="Okabe-Ito",
                          fonts="Times New Roman + Songti SC", width_mm=180,
                          png_dpi=DPI, pdf_fonttype=42,
                          publisher_requirements="PENDING — journal not chosen")
    print("  ", stem)


def newfig(h_mm):
    fig = plt.figure(figsize=(W, h_mm * MM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10 * h_mm / 180.0)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, title, sub, color, fs=9.5, sfs=7.6):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0.02,rounding_size=0.10",
                                linewidth=1.3, edgecolor=color, facecolor="white",
                                zorder=2))
    ax.add_patch(FancyBboxPatch((x, y), 0.09, h,
                                boxstyle="round,pad=0.0,rounding_size=0.02",
                                linewidth=0, facecolor=color, zorder=3))
    if sub:
        ax.text(x + w / 2 + 0.05, y + h * 0.66, title, ha="center", va="center",
                fontsize=fs, fontweight="bold", color=color, zorder=4)
        ax.text(x + w / 2 + 0.05, y + h * 0.30, sub, ha="center", va="center",
                fontsize=sfs, color="#333333", zorder=4)
    else:
        ax.text(x + w / 2 + 0.05, y + h / 2, title, ha="center", va="center",
                fontsize=fs, fontweight="bold", color=color, zorder=4)


def arrow(ax, a, b, color="#455A64", lw=1.2, style="-|>", rad=0.0):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle=style, mutation_scale=11,
                                 linewidth=lw, color=color, zorder=1,
                                 connectionstyle=f"arc3,rad={rad}",
                                 shrinkA=2, shrinkB=2))


def badge(ax, x, y, n, color=INK):
    ax.add_patch(Circle((x, y), 0.17, facecolor=color, edgecolor="white",
                        linewidth=0.8, zorder=5))
    ax.text(x, y, str(n), ha="center", va="center", color="white",
            fontsize=7.6, fontweight="bold", zorder=6)


def alabel(ax, x, y, text, fs=7.8, color=INK, ha="center"):
    ax.text(x, y, text, ha=ha, va="center", fontsize=fs, color=color, zorder=4,
            bbox=dict(boxstyle="round,pad=0.16", facecolor="white",
                      edgecolor="none", alpha=0.92))


# ---------------------------------------------------------------- 图1 流程
def fig1():
    fig, ax = newfig(96)
    box(ax, 3.55, 4.45, 2.9, 0.60, "注册机构", "登记参与者 · 授权签发者", BLUE, fs=9.0, sfs=7.0)
    box(ax, 0.25, 2.43, 2.5, 0.62, "事件签发者", "观察事件 · 签回执", ORANGE, fs=9.0, sfs=7.0)
    box(ax, 3.75, 2.43, 2.5, 0.62, "参与者（车辆）", "加密报告 · 构造证明", GREEN, fs=9.0, sfs=7.0)
    box(ax, 7.25, 2.43, 2.5, 0.62, "验证网关", "重构 c · 验证 π · 查重 N", PURPLE, fs=9.0, sfs=7.0)
    box(ax, 6.95, 0.61, 2.8, 0.56, "报告接收方", "认证并解密 → 明文 μ", SKY, fs=9.0, sfs=7.0)

    arrow(ax, (4.1, 4.45), (1.5, 3.05))
    badge(ax, 2.62, 3.78, 1, ORANGE)
    alabel(ax, 2.30, 4.10, "授权证书 σ_W")
    arrow(ax, (5.0, 4.45), (5.0, 3.05))
    badge(ax, 5.0, 3.78, 2, GREEN)
    alabel(ax, 5.30, 3.78, "凭证 σ_A", ha="left")
    arrow(ax, (7.25, 2.85), (6.25, 2.85))
    badge(ax, 6.75, 2.85, 3, PURPLE)
    alabel(ax, 6.75, 3.14, "挑战 q")
    arrow(ax, (3.75, 2.85), (2.75, 2.85))
    badge(ax, 3.25, 2.85, 4, ORANGE)
    alabel(ax, 3.25, 3.14, "回执请求 (c, h, z)")
    arrow(ax, (2.75, 2.61), (3.75, 2.61))
    badge(ax, 3.25, 2.61, 5, ORANGE)
    alabel(ax, 3.25, 2.30, "事件回执 σ_E")
    arrow(ax, (6.25, 2.61), (7.25, 2.61))
    badge(ax, 6.75, 2.61, 6, PURPLE)
    alabel(ax, 6.75, 2.30, "提交 (N, π, R, n)")
    arrow(ax, (8.5, 2.43), (8.5, 1.17))
    badge(ax, 8.5, 1.81, 7, SKY)
    alabel(ax, 8.72, 1.81, "已验证信封 R", ha="left")

    ax.add_patch(FancyBboxPatch((3.35, 1.30), 3.3, 0.78,
                                boxstyle="round,pad=0.02,rounding_size=0.10",
                                linewidth=1.0, edgecolor=GREEN, linestyle="--",
                                facecolor="#EAF6F1", zorder=1))
    ax.text(5.0, 1.86, "零知识证明的私有见证", ha="center", va="center",
            fontsize=8.4, fontweight="bold", color=GREEN)
    ax.text(5.0, 1.52, "s, σ_A, W, σ_W, σ_E, x, y, t 不出证明", ha="center",
            va="center", fontsize=7.8, color="#22553F")
    arrow(ax, (5.0, 2.43), (5.0, 2.08), color=GREEN, lw=1.0, style="-")

    fig.text(0.02, 0.035,
             "编号为消息顺序。所测网关中网关与接收方同置，且认证先于受理；"
             "上下文隐藏构造（§4.7）中步骤 4 只发送 (h, z)，不发送 c。",
             fontsize=7.8, color=GREY, ha="left", va="bottom")
    export(fig, "fig1_workflow_v2",
           "图 1 报告绑定时空验证的角色与证据流（编号为消息顺序）。",
           "概念示意图；私有见证以虚线框标出；同置与认证先于受理在图注说明")


# ---------------------------------------------------------------- 图2 绑定
def fig_binding():
    fig, ax = newfig(80)
    box(ax, 0.30, 1.85, 1.55, 0.60, "秘密 s", None, GREEN, fs=10)
    box(ax, 3.05, 3.30, 2.55, 0.55, "H101(s) 凭证承诺", "机构签名验证 · 式(4)", BLUE, fs=8.4, sfs=6.8)
    box(ax, 3.05, 1.85, 2.55, 0.60, "h = H103(s, c)", "持有人值 · 认人", GREEN, fs=8.6, sfs=6.8)
    box(ax, 3.05, 0.45, 2.55, 0.55, "N = H105(s, tid)", "任务标签 · 查重 · 式(7)", PURPLE, fs=8.4, sfs=6.8)
    box(ax, 6.55, 3.30, 3.15, 0.55, "信封 R + 任务 T + 挑战 q", "网关用自身配置与实际收到字节同算", GREY, fs=8.2, sfs=6.6)
    box(ax, 6.55, 2.35, 3.15, 0.55, "c = ContextField(T, q, R)", "报告上下文 · 式(2)", BLUE, fs=8.4, sfs=6.8)
    box(ax, 6.55, 1.05, 3.15, 0.60, "m = H104(c, h, x, y, t)", "被签消息 · 式(3)/(6)", ORANGE, fs=8.4, sfs=6.8)

    arrow(ax, (1.85, 2.25), (3.05, 3.50), color=BLUE)
    arrow(ax, (1.85, 2.15), (3.05, 2.15), color=GREEN)
    arrow(ax, (1.85, 2.05), (3.05, 0.75), color=PURPLE)
    arrow(ax, (8.1, 3.30), (8.1, 2.90), color=BLUE)
    arrow(ax, (6.55, 2.55), (5.60, 2.30), color=BLUE)
    arrow(ax, (6.55, 2.45), (7.6, 1.65), color=BLUE, rad=-0.12)
    arrow(ax, (5.60, 2.00), (6.55, 1.40), color=GREEN)
    alabel(ax, 2.42, 3.05, "H101", fs=7.2, color=BLUE)
    alabel(ax, 2.42, 2.32, "H103", fs=7.2, color=GREEN)
    alabel(ax, 2.42, 1.30, "H105", fs=7.2, color=PURPLE)
    alabel(ax, 6.05, 2.52, "c", fs=7.4, color=BLUE)
    alabel(ax, 6.05, 1.62, "h", fs=7.4, color=GREEN)

    fig.text(0.02, 0.035,
             "式(4)—式(7) 共用同一个秘密 s；上下文 c 由网关从实际收到的信封字节重构，"
             "故式(6) 的回执验证把绑定延伸到本次提交的内容。",
             fontsize=7.8, color=GREY, ha="left", va="bottom")
    export(fig, "fig_binding",
           "图 2 同一个秘密支撑凭证、持有人值与任务标签，上下文把绑定延伸到收到的报告字节。",
           "概念示意图；节点标注对应式号；无实验数据")


# ---------------------------------------------------------------- 图3 共谋
def fig_collusion():
    fig, ax = newfig(86)
    ymax = 10 * 86 / 180.0

    ISS = ["$c_i$", "$h_i$", "$z_i=(x,y,t)$", "$\\sigma_{E,i},\\ \\tau^{I}_i$", "$W$"]
    ISS_HIDDEN = ["$h_i$", "$z_i=(x,y,t)$", "$\\sigma_{E,i},\\ \\tau^{I}_i$", "$W$"]
    GW = ["$c_j$", "$\\mathrm{tid}_j,\\ N_j$", "$P_j,\\ \\pi_j,\\ R_j$",
          "$q_j,\\ \\tau^{G}_j,\\ \\mu_j$", "$A$"]

    def records(x0, issuer_fields, hl_c, panel_title, tag):
        ax.text(x0 + 2.15, ymax - 0.28, panel_title, ha="center", va="center",
                fontsize=9.5, fontweight="bold")
        ax.text(x0 - 0.05, ymax - 0.28, tag, ha="left", va="center",
                fontsize=10, fontweight="bold")
        ax.add_patch(FancyBboxPatch((x0, 1.55), 1.8, 2.55,
                                    boxstyle="round,pad=0.02,rounding_size=0.08",
                                    linewidth=1.2, edgecolor=ORANGE, facecolor="white"))
        ax.text(x0 + 0.9, 3.85, "签发者记录", ha="center", va="center",
                fontsize=8.8, fontweight="bold", color=ORANGE)
        for k, f in enumerate(issuer_fields):
            hl = hl_c and k == 0
            ax.text(x0 + 0.15, 3.45 - k * 0.42, f, ha="left", va="center",
                    fontsize=8.0, color=VERM if hl else "#333333")
        gx = x0 + 2.5
        ax.add_patch(FancyBboxPatch((gx, 1.55), 1.8, 2.55,
                                    boxstyle="round,pad=0.02,rounding_size=0.08",
                                    linewidth=1.2, edgecolor=PURPLE, facecolor="white"))
        ax.text(gx + 0.9, 3.85, "网关记录", ha="center", va="center",
                fontsize=8.8, fontweight="bold", color=PURPLE)
        for k, f in enumerate(GW):
            hl = hl_c and k == 0
            ax.text(gx + 0.15, 3.45 - k * 0.42, f, ha="left", va="center",
                    fontsize=8.0, color=VERM if hl else "#333333")
        return x0 + 1.8, gx

    ia, ga = records(0.30, ISS, True, "主关系：两侧共享确定性上下文", "(a)")
    ax.plot([ia, ga], [2.85, 2.85], color=VERM, lw=2.4, solid_capstyle="round")
    ax.plot([ia, ia + 0.12], [2.97, 2.85], color=VERM, lw=2.0)
    ax.plot([ia, ia + 0.12], [2.73, 2.85], color=VERM, lw=2.0)
    ax.plot([ga, ga - 0.12], [2.97, 2.85], color=VERM, lw=2.0)
    ax.plot([ga, ga - 0.12], [2.73, 2.85], color=VERM, lw=2.0)
    ax.text(2.45, 1.15, "c 为等值连接键：合并记录即还原坐标", ha="center",
            va="center", fontsize=8.2, color=VERM, fontweight="bold")
    ax.text(2.45, 0.60, "h_i = H103(s_i, c_j)，c 双方皆知", ha="center",
            va="center", fontsize=7.8, color=GREY)

    ib, gb = records(5.30, ISS_HIDDEN, False, "上下文隐藏：签发者不见 c", "(b)")
    ax.plot([ib, gb], [2.85, 2.85], color="#BBBBBB", lw=1.2)
    mx = (ib + gb) / 2
    ax.plot([mx - 0.11, mx + 0.11], [2.97, 2.73], color=VERM, lw=1.8)
    ax.plot([mx - 0.11, mx + 0.11], [2.73, 2.97], color=VERM, lw=1.8)
    ax.text(7.45, 1.15, "无确定性连接键：s 未知，h 等价随机", ha="center",
            va="center", fontsize=8.2, color=GREY, fontweight="bold")
    ax.text(7.45, 0.60, "残留：时空邻近 z_i∈P_j 且 |τG_j−τI_i|≤Δ",
            ha="center", va="center", fontsize=7.8, color=GREY)

    fig.text(0.02, 0.020,
             "红色为两侧共有的确定性字段。(a) 中 c 可由双方记录等值连接；(b) 中签发者记录不含 c，\n"
             "唯一跨集合关系 h_i=H103(s_i,c_j) 的密钥 s 对双方未知，故无可高效计算的连接键。",
             fontsize=7.8, color=GREY, ha="left", va="bottom", linespacing=1.5)
    export(fig, "fig_collusion",
           "图 3 合谋双方记录之间的连接键：主关系共享确定性上下文，上下文隐藏构造将其消除。",
           "概念示意图；字段集合与 §4.7 共谋视图一致；残留时空邻近通道单独标注")


if __name__ == "__main__":
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        print("rendering conceptual figures:")
        fig1(); fig_binding(); fig_collusion()
        g = [str(x.message) for x in w if "missing from" in str(x.message).lower()]
        print("glyph warnings:", len(g))
        for x in g[:10]:
            print("  ", x)
    (HERE / "concept_manifest.json").write_text(json.dumps(MANIFEST, ensure_ascii=False, indent=1))
    print("wrote concept_manifest.json")