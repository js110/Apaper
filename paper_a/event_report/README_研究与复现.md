# 单报告车联网众包论文：文件与复现

目标期刊为 Springer 的 Telecommunication Systems，使用其 Springer Nature 双栏 LaTeX 模板。武汉大学图书馆公开目录列该刊为 SCIE、计算机科学四区；该页面所列 JCR 年份为 2024，正式投稿前应以单位认可的最新收录和分区数据库复核。该选择与期刊范围匹配，但录用与否取决于编辑和审稿。

本文的研究对象回到初稿的单任务、单报告时空合规认证。已有团队论文 TST-Audit 作为相关工作引用：它侧重覆盖状态审计，并已定义匿名凭证、网格／时间范围的微证明与限域去重接口；本文不将这些已有构件当作首次提出。

## 文件

- `manuscript.tex` 和 `manuscript.pdf`：Springer Nature 双栏模板的论文源稿与编译版本；第 6 节为 Discussion。
- `sn-jnl.cls`、`sn-mathphys-num.bst`、`references.bib`、`figure1_scientific.pdf`、`benchmark.pdf`：本地可编译所需模板、文献与图。
- `prototype/`：Go 电路与软件网关，包含矩形策略、离散区域、条件开启身份点、活跃凭证树、ML-KEM-768/AES-GCM 报告封装及受控消融。
- `experiments/`：四组原始计时日志、测试日志和绘图脚本。
- `../../research/`：文献、协议与安全审查记录；部分早期报告记录的是阶段性版本，以最终源码和日志为准。

## 方法和结果边界

证据签发者的物理观察及登记机构的管理规则是方法前提。身份开启原型恢复的是与凭证绑定的登记点，现实身份映射及开启授权依靠可信登记机构；活跃根更新的跨重启持久化和受认证分发需要外部服务。论文的性能数据是在同一 Apple M1 电脑上通过软件证明系统测得，实验输入是合成数据；四组证明开销实验各 30 次，另有 30 次同进程完整软件流程实验，区分一次性设置、单次证明、验证及软件流程的开销。证明计时不包括签发、构造密文、网络、身份开启或树更新；软件流程另行计入部分环节。

本目录的稿件供作者核对、完善投稿资料使用。投稿前需由作者核实作者贡献、基金、利益冲突、关联成果和目标期刊的收录与分区；本地测试或期刊分区均不保证录用。

## 重编译与测试

在本目录：

```bash
python3 experiments/plot_results.py
latexmk -pdf -interaction=nonstopmode -halt-on-error manuscript.tex
```

在 `prototype/` 目录，使用 Go 1.26.8 或兼容的 Go 工具链：

```bash
go test -count=1 -timeout=15m ./...
EVENT_BENCH_RUNS=30 go test -run '^TestBenchmarkExperiment$' -count=1 -v
EVENT_REGION_BENCH_RUNS=30 go test -run '^TestRegionBenchmarkExperiment$' -count=1 -v
EVENT_ACCOUNTABILITY_BENCH_RUNS=30 go test -run '^TestAccountabilityBenchmarkExperiment$' -count=1 -v
EVENT_REVOCATION_BENCH_RUNS=30 go test -run '^TestRevocationBenchmarkExperiment$' -count=1 -v
EVENT_END_TO_END_RUNS=30 go test -run '^TestEndToEndExperiment$' -count=1 -v
```

各组性能日志包含源文件 SHA-256、工具版本、硬件环境、逐次耗时和序列化字节数。测试用的本地 setup 不是多方可信设置方案。需要下载依赖时可根据网络环境配置 `GOPROXY`；实验程序不依赖原稿中未经验证的密码学替代后端。
