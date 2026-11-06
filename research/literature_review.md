# 单报告车联网众包认证：针对性证据矩阵与引文清单

核查日期：2026-11-04。目标：为匿名、任务级时空合规与重复提交检测的单报告协议提供来源和查重边界。方法：按“众包/ZK/一次提交、时空/位置证明、多见证/采集时来源、可信传感数据、远程证明”进行定向网络检索，对优先文献查看作者全文、出版商页面或原始论文摘要；期刊元数据使用出版商或 Crossref 核对。此为有限检索，不是系统综述，不证明全球首创；文中“未发现”指所阅范围，不等同文献没有该机制。

## 对作者自有工作的实质对照

**He et al., TST-Audit, Ad Hoc Networks 192, 104345 (2026)**, [DOI](https://doi.org/10.1016/j.adhoc.2026.104345). 已逐页阅读用户提供全文，第 4 页 3.1–3.2 节规定：隐藏精确 `(ℓ,t)` 映射到**公开** `(g,τ)`，外部信任方车辆凭证，凭证秘密确定性派生网格—周期 nullifier，指定边缘及可选短期挑战绑定；空间证明/凭证是可插拔接口。第 1 页强调目标是覆盖状态而非感知内容真伪。覆盖记录 `r_i=(g_i,τ,σ_i,π_micro)` 本身没有明确列出特定传感载荷及其与见证的签名关系，不能据此推断接入的具体微证明不可能包含它。全文第 5、7、8–9 页区分完整设计和实测原型：主原型的微证明验证、去重和 MST 更新为电路外；小参数电路使用 MiMC 摘要检查占位，MiMC-5 仅用于性能剖析；车辆端真实证明开销没有测量。不可将公开的 `g,τ` 说成对所有角色隐藏，不能把“匿名、时空判定、限域 nullifier、edge challenge”作为本论文首次提出。

**初稿 PCVCS**（用户提供 PDF 第 1、6–8 页）：系统层面已把 RSU 时空令牌、Merkle 地区证明、时间范围证明、任务级可链接环签名以及 ML-KEM 传输组合；其 RSU 令牌为广播签名，声称位于覆盖区的车辆接收，车辆自做承诺。因此新论文若采用 bearer-bound token，应区别凭证重用、完整性和物理同地三种不同属性，不得仅凭论文没有写清就指责原系统已被攻击。完整源码和威胁模型须另审计。

## 优先阅读的原始文献

1. **Ni et al., SPOON, TMC 2020** — [作者接收版全文](https://uwaterloo.ca/scholar/sites/ca.scholar/files/sshen/files/93.pdf), DOI [10.1109/TMC.2019.2908638](https://doi.org/10.1109/TMC.2019.2908638). 实现隐私任务分配、匿名凭证、感知报告加密与重复报告识别；全文数据报告格式含任务编号、密文、时隙、报告标识和防双报标签，证明分析涉及双报。它是“匿名众包 + 时空任务 + 报告 + 防双报”的强近邻，不能声称这些功能的整体思路空白。该文重心为任务分配/信誉，不可仅据此断言其对硬件见证、采集真实性或所提统一电路的处理能力。
2. **Xu, Lin, Wu, Sensors 2021** — [论文](https://www.mdpi.com/1424-8220/21/9/3036), [PubMed 元数据和摘要](https://pubmed.ncbi.nlm.nih.gov/33925947/), DOI [10.3390/s21093036](https://doi.org/10.3390/s21093036). 用内积加密和知识证明处理隐私任务匹配；其摘要明确“一位合格工作者每任务只能提交一次”及跨任务不可链接。因此任务范围唯一标签/匿名限次不是新原语。
3. **Zhu et al., ACM Transactions on Internet of Things 2022** — [作者全文](https://www.cs.cityu.edu.hk/~weliang/papers/ZCGL22.pdf), DOI [10.1145/3549550](https://doi.org/10.1145/3549550). 场景为停车混合感知；§5 已涉及匿名、不可链接、重复停车报告/积分作弊及承诺和知识证明。§5.2.3 按停车位、时间和秘密构造标记。本文没有由此声称其支持我们指定的 RSU 见证/报告绑定；需按接口完整比较。
4. **Brito et al., Scientific Reports 2025** — [出版商全文](https://doi.org/10.1038/s41598-025-04566-4). 提出位置证明的见证区、见证者距离界定、时间一致性和聚合签名/共识模型。因此多见证者证明参与者时空存在也已有先例；具体网络隐私和可组合威胁模型仍需对照。
5. **Brito et al., “Decentralized Proof-of-Location for Content Provenance”, 2026** — [原始预印本](https://arxiv.org/abs/2603.27883), 标为预印本，非已确认同行评审。提出多个见证者对采集时物理情境的验证，场景包含 smart mobility，并分析数字记录在正确地点仍可能伪造或布置场景。它比抽象位置证明更接近“同事件报告内容+时空见证”；不能称内容/地点/时间联合认证或多模态见证本身首创。摘要/正文未作为本工作匿名限次模型的完整对照；需要逐节核查再作排他结论。
6. **Bogdanov et al., ARES 2025** — [出版商全文](https://link.springer.com/chapter/10.1007/978-3-032-00642-4_20), DOI [10.1007/978-3-032-00642-4_20](https://doi.org/10.1007/978-3-032-00642-4_20). 使用可信见证设备签名车辆轨迹，零知识验证地区行驶政策；展示了报告位置与可信设备签名联合证明已有先例，并测量 Raspberry Pi / phone 等配置；其时空轨迹功能与众包单报告及任务内防重并非同一关系。它不是论证多见证恶意容错的直接对照。
7. **Ernstberger et al., ZKLP, IEEE S&P 2025** — [作者存档摘要/全文](https://discovery.ucl.ac.uk/id/eprint/10211442/), [预印本全文](https://arxiv.org/abs/2404.14983), DOI [10.1109/SP61157.2025.00057](https://doi.org/10.1109/SP61157.2025.00057). 证明隐藏位置满足地理属性及位置邻近，重点是浮点 ZK 算术。文章 Appendix C 还讨论定位可信性选项，不能写成完全忽略真实性。本论文同机性能对照如电路关系、签名数量、库版本不同，不能说它是同功能端到端比较。
8. **Panwar et al., IoT Notary, ACM Transactions on IoT 2022** — [作者全文](https://ics.uci.edu/~dsm/publications/papers/2021/Panwar_2021.pdf), [机构文献记录](https://researchwith.njit.edu/en/publications/iot-notary-attestable-sensor-data-capture-in-iot-environments/), DOI [10.1145/3478290](https://doi.org/10.1145/3478290). 为实时采集传感数据提供安全日志封存与可检查数据采集规则，已经研究可信采集数据完整性。它不支持“签名等价于传感值物理正确”的推断。
9. **Huang et al., BlockSense, TMC 2024** — [作者全文](https://www.comp.hkbu.edu.hk/~henrydai/pubs/BlockSense_Towards_Trustworthy_Mobile_Crowdsensing_via_Proof-of-Data_Blockchain.pdf), [机构记录](https://scholars.hkbu.edu.hk/en/publications/blocksense-towards-trustworthy-mobile-crowdsensing-via-proof-of-d/), DOI [10.1109/TMC.2022.3230758](https://doi.org/10.1109/TMC.2022.3230758). 众包数据质量验证和隐私数据扰动，实地实验；是同领域真实性/质量方向的实证对照，不要把质量验证称成本文单报告策略关系的直接等价基线。
10. **Shen et al., BCS-LPP, Vehicular Communications 2024** — [出版商](https://doi.org/10.1016/j.vehcom.2023.100724). 区块链和众包位置隐私，值得作为 VCS 应用层对照；其文献中时间/防重/可信见证具体性质需逐式核验，不能仅凭名称赋值对比表。当前参考文献已有该条。
11. **IETF RFC 9334, RATS Architecture, 2023** — [全文 §10.2](https://datatracker.ietf.org/doc/html/rfc9334#section-10.2) 与 [Appendix A.2](https://datatracker.ietf.org/doc/html/rfc9334#appendix-A.2). 随机数可以建立 evidence 签发/收集时段，但不能仅凭 nonce 认定某个 claim 的底层数据是在 nonce 之后被采集；传感输入路径、来源和可信时钟需各自假设。作为技术规范引用，非研究论文。
12. **ERC-8262, 2026** — [官方 Review 草案](https://eips.ethereum.org/EIPS/eip-8262), 未定稿标准、非论文。描述 ZK 合规、提交者绑定、多 provider、阈值及签发凭证；与多签发者的合规关系相近，不能声称多签发者 + 门限 + ZK 本身原创。应用于金融合规，与车联网物理测量假设不等价。
13. **Jin et al., PG, CCS 2024** — [作者机构记录/全文](https://ir.cwi.nl/pub/34722), DOI [10.1145/3658644.3670343](https://doi.org/10.1145/3658644.3670343). 已同时研究拜占庭容错和私密多传感融合；传感器与服务器交互、输出交付的模型不同，不能只凭技术差别断言无法适配现稿判定。
14. **Yin et al., CRSF, 2026** — [原始预印本](https://arxiv.org/abs/2609.01096). 研究恶意传感器与服务器合谋、输入参与一致性和 Marzullo 类融合电路；是多见证扩展的挑战性近邻。按预印本引用，不推断已同行评审。
15. **Mitrokotsa, Onete, Vaudenay, Computers & Security 2014** — [出版商](https://doi.org/10.1016/j.cose.2014.06.001). 距离界定用于限制实时 relay，但测距也可能产生位置泄漏；普通签名/哈希、任务绑定和零知识约束自身并不建立非中继的物理接近。

## 允许使用的谨慎研究定位

- **可陈述**：现稿目标是针对一条任务报告，将匿名凭证、隐藏时空合规、明确的任务范围去重和签名/承诺绑定为一个可执行、可验证的关系；正文需明确注册和时空签发的信任假设，报告校验方可见字段及相关事件绑定范围。
- **不能仅凭本次检索宣称**：“首个保护身份与位置的 VCS 众包”“首个匿名任务级防重”“首个带时空的报告认证”“首个多见证 ZK”“报告内容必然真实”或“彻底阻止转借及实时中继”。
- **更有价值的验证**：针对最初公开广播 token 及候选 bearer-bound receipt 各自规范，分别定义可控制的对手知识、可复制消息、凭证持有和签名端点；使用同一实现的正向/跨任务/跨报告/跨持有人篡改测试，定位凭证绑定究竟修复哪一类替换。已授权设备任意提供旧 payload 并重签新 nonce 不是密码学可证明的真实采集。
- **自己论文复用边界**：新论文引用 TST-Audit；清楚区分已有抽象接口、具体微证明实现、对每条传感报告的认证对象及模型。是否能够构成独立科学贡献需与完整微证明接口可允许的各类实现比较，而不是把具体化自动当成新原语。

## 可直接供 BibTeX 核验的已发表条目

```bibtex
@article{He2026TSTAudit,
  author = {He, Lili and Jiang, Sheng and Yang, Zhenkun and Zhang, Lei},
  title = {Trustworthy spatio-temporal coverage auditing for large-scale vehicular crowdsensing: A {Merkle-Sum-Tree} algorithm},
  journal = {Ad Hoc Networks}, volume = {192}, pages = {104345}, year = {2026},
  doi = {10.1016/j.adhoc.2026.104345}
}
@article{Ni2020SPOON,
  author = {Ni, Jianbing and Zhang, Kuan and Xia, Qi and Lin, Xiaodong and Shen, Xuemin},
  title = {Enabling Strong Privacy Preservation and Accurate Task Allocation for Mobile Crowdsensing},
  journal = {IEEE Transactions on Mobile Computing}, volume = {19}, number = {6}, pages = {1317--1331}, year = {2020},
  doi = {10.1109/TMC.2019.2908638}
}
@article{Xu2021TaskMatching,
  author = {Xu, Jie and Lin, Zhaowen and Wu, Jun},
  title = {Privacy-Preserving Task-Matching and Multiple-Submissions Detection in Crowdsourcing},
  journal = {Sensors}, volume = {21}, number = {9}, pages = {3036}, year = {2021},
  doi = {10.3390/s21093036}
}
@article{Zhu2022HybridSensing,
  author = {Zhu, Hanwei and Chau, Sid Chi-Kin and Guarddin, Gladhi and Liang, Weifa},
  title = {Integrating {IoT}-Sensing and Crowdsensing with Privacy: Privacy-Preserving Hybrid Sensing for Smart Cities},
  journal = {ACM Transactions on Internet of Things}, volume = {3}, number = {4}, pages = {31:1--31:30}, year = {2022},
  doi = {10.1145/3549550}
}
@article{Panwar2022IoTNotary,
  author = {Panwar, Nisha and Sharma, Shantanu and Wang, Guoxi and Mehrotra, Sharad and Venkatasubramanian, Nalini and Diallo, Mamadou H. and Sani, Ardalan Amiri},
  title = {{IoT} Notary: Attestable Sensor Data Capture in {IoT} Environments},
  journal = {ACM Transactions on Internet of Things}, volume = {3}, number = {1}, pages = {3:1--3:30}, year = {2022},
  doi = {10.1145/3478290}
}
@article{Brito2025DecentralizedPoL,
  author = {Brito, Eduardo and Hadachi, Amnir and Kamm, Liina and Norbisrath, Ulrich},
  title = {Decentralized Proof-of-Location systems for trust, scalability, and privacy in digital societies},
  journal = {Scientific Reports}, volume = {15}, pages = {19808}, year = {2025},
  doi = {10.1038/s41598-025-04566-4}
}
@inproceedings{Bogdanov2025VehiclePolicy,
  author = {Bogdanov, Dan and Brito, Eduardo and Jaakson, Annika and Laud, Peeter and Rebane, Raul-Martin},
  title = {Zero-Knowledge Proof-of-Location Protocols for Vehicle Subsidies and Taxation Compliance},
  booktitle = {Availability, Reliability and Security}, series = {Lecture Notes in Computer Science}, volume = {15998}, pages = {343--360}, publisher = {Springer}, address = {Cham}, year = {2025},
  doi = {10.1007/978-3-032-00642-4_20}
}
@inproceedings{Ernstberger2025ZKLP,
  author = {Ernstberger, Jens and Zhang, Chengru and Ciprian, Luca and Jovanovic, Philipp and Steinhorst, Sebastian},
  title = {Zero-Knowledge Location Privacy via Accurate Floating-Point {SNARKs}},
  booktitle = {2025 IEEE Symposium on Security and Privacy}, pages = {3440--3459}, year = {2025},
  doi = {10.1109/SP61157.2025.00057}
}
@article{Huang2024BlockSense,
  author = {Huang, Junqin and Kong, Linghe and Cheng, Long and Dai, Hong-Ning and Qiu, Meikang and Chen, Guihai and Liu, Xue and Huang, Gang},
  title = {{BlockSense}: Towards Trustworthy Mobile Crowdsensing via Proof-of-Data Blockchain},
  journal = {IEEE Transactions on Mobile Computing}, volume = {23}, number = {2}, pages = {1016--1033}, year = {2024},
  doi = {10.1109/TMC.2022.3230758}
}
@inproceedings{Jin2024PG,
  author = {Jin, Chenglu and Yin, Chao and van Dijk, Marten and Duan, Sisi and Massacci, Fabio and Reiter, Michael K. and Zhang, Haibin},
  title = {{PG}: Byzantine Fault-Tolerant and Privacy-Preserving Sensor Fusion with Guaranteed Output Delivery},
  booktitle = {Proceedings of the 2024 ACM SIGSAC Conference on Computer and Communications Security}, pages = {3272--3286}, year = {2024},
  doi = {10.1145/3658644.3670343}
}
```

预印本、规范或源码应遵照期刊对发表状态的要求作单独处理。参考文献加入论文前还应复核作者、出版状态和 DOI；上面元数据按出版商及 Crossref 核对，具体内容主张需作者阅读源文核验。
