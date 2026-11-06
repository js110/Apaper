# 单报告稿件独立审阅

核对对象：`paper_a/event_report/manuscript.tex`（2026-11-04 草稿）、`prototype/{circuit.go,native.go,gateway.go,transport.go,*test.go}`、`experiments/benchmark.log`、初稿 `/Users/jiangsheng/Desktop/IEEE/paper/bare_jrnl_new_sample4.tex` 以及用户提供的 TST-Audit 全文。本文是工作审阅，不认定投稿可行性、统计显著性或密码学正式证明已成立。

## 应优先处理

1. **初稿既已声称报告绑定，不能将“加入报告绑定”写成从无到有。** 初稿第 393–404、506–515、562–574 行写明 RSU token 承诺进入空间、时间证明和最终签名，声称它们关联同一事件。可具体比较的是：初稿的广播 token 格式和由车辆生成的 token 承诺中，未明确给出由同一凭证秘密派生并由见证方签名的 holder 值；现稿式 (4)–(7) 明确规定同一 `s` 同时参与凭证、见证消息和任务去重。初稿中承诺“阻止 token resale”属于原稿声称，并不能因此假设原稿实际完全实现，亦不能据手稿不完整就断言某个历史系统被攻破。建议把第 23、27、29 行定位为“an explicit and executable same-secret binding relation, with controlled substitution tests”，并在相关工作中比较规范和抽象层次；不称绑定问题或其通用概念首创。

2. **报告的密码学绑定与采集时真实同源是不同主张。** 第 15、23、43、49 行的 “associated with an event” 应明确是“associated with the issuer-signed event assertion”，因为当前签发端为测试夹具中的签名逻辑，实际传感采集路径、物理接近与真实时钟没有实现。第 47、66–71、94、99 行已有假设，可避免在摘要/引言中产生超出这些假设的读法。所述 nonce 只约束当前签发/提交上下文，不能独立证明传感数据采集时间；RFC 9334 的引文适用于该边界。

3. **相对初稿的功能变化应由作者知情，文章不能照搬。** 初稿支持 Merkle 根表达的一组 geohash 单元，以及 ML-KEM 保护的传送，并声称审计追踪及吊销；目前基本电路只检查三维 32 位矩形，AES-256-GCM 由外部预置密钥保护，既不实现 ML-KEM 密钥交换，也不实现审计开封/吊销。离散区域扩展如正在开发，须按其最终代码和测试纳入；不能将未实现的扩展写为结果。AES/Groth16/EdDSA 的组合不能笼统称为后量子安全。建议在方法中准确表述已实现的功能，不用宣传性地罗列缺项。

4. **当前评估段为计划而非结果。** 第 15、18、29、104–117、126 行仍有 TODO 或将来式，应据真实实验完成后整体改写。`benchmark.log` 记录一次 setup/compile、30 次测量及 1 次预热、29551 个约束、164 B 证明、364 B 序列化公开见证；耗时样本需由数据脚本计算均值、标准差、中位数或分位数。`benchmark_test.go` 测的是单实例真实 Groth16 证明/验证，证明大小不等于完整报告大小，setup 一次不构成分布；有关签发、加解密、整个请求字节数不要引用这组数来填。必须对照 log 中 source SHA-256 与最终提交代码，电路有变化即重新测试。受控对照必须注明测试格式及其攻击者知识、胜负和样本规模。

5. **独立核对 security gate 的“真实证明”与“约束可满足”层次。** `binding_experiment_test.go` 的持有人绑定消融中：对持有者替换的拒绝通过真实 R1CS `IsSolved` 检查；弱化 bearer 变体的替换样例另外生成并验证了真实 Groth16 证明。不得写成“强方案跨持有人替换的真实 proof 被网关拒绝”，除非另外确实执行并记录该案例。该弱化变体是作者构造的实验基线，并非原稿 PCVCS 的复现。`circuit_test.go` 大部分负向测试是修改 witness 后检测 R1CS，不应写成全部逐条生成了真实 proof；`gateway_test.go` 则使用真实生成的 Groth16 proof 和重建的公开输入，包含两条新 challenge 并发同 nullifier 的处理。一个边界样本不等于对每维所有边界的穷举。

## 数学和协议精度

- 第 45、59–82 行标量任务值 `$u$` 与向量上界 `\boldsymbol u` 仅字体不同，阅读中容易混淆；建议标量改为 `$\tau$` 或 `$\mathsf{tid}$` 并同步所有相关式子，特别是 `$N=H_{105}(s,\mathsf{tid})$`。
- 第 64、85、92 行应明确上下文和任务标识间的一致性由网关以同一可信 Task 同时重建保证，而不是电路内部从 context 摘要提取/验证任务记录。若将 verifier 视为不可信，当前叙述不能成立；威胁模型已信任网关配置，应保持一致。
- 第 57、85 行应明确：签发者 W 非单位元、在曲线上且经固定阶乘法检验属于指定子群；CA A 由网关 `validateAuthority` 验证规范编码、非单位元、曲线及子群。不能笼统称三个签名的 R 均已进行完整子群检验；现代码检查各 R 在曲线上，进一步规范性和安全性要对照库与独立安全审计。
- 第 94、101 行：任务内 tag 是确定性 MiMC 输出；高熵秘密和近似伪随机/隐藏假设是跨任务不可链接的必要条件之一。两任务输出不同只是测试事实，不构成不可链接证明。注册权威、签发者、报告接收方以及网络观察者视图各不相同，不要把“对 gateway 隐藏”扩大为“对所有参与者隐藏”。
- 第 59、87、101 行正确指出外部密钥和 gateway 不解密。强调 `SealReport` 的随机 96 位 GCM nonce 和 task ID 关联数据，对同 key 的 nonce 碰撞概率及消息量有规范要求；AEAD 接收者的 `OpenReport` 能检查密文有效性，gateway proof 接受并不等同 AEAD 成功验证。只表述库实际实现，不把加密前明文真实/时空合法性视为密码学保证。
- 第 66 行提到收到 holder 值并由 issuer 按物理观察签发是**协议接口及环境假设**；`Fixture.Assignment` 为本地实验中直接计算和签名，并非已完成的 RSU 交互协议/现场系统。建议在方法中使用“the protocol specifies”而非“the deployed issuer observes”，不要主张现场验证或真实时间采集。
- 第 87 行用“proof verifies the specified relation”作为直观表述可以，但若写定理，应给明确的验证密钥与可信设置、知识健全性、签名 unforgeability、哈希抗碰撞/字段编码等假设，并区分条件性论证与形式化归约；不能凭负例实验声称已数学证明安全。

## 引文和创新叙事

- TST-Audit 已发表论文第 4 页抽象微证明确有 credential、隐藏坐标/时间、公开 grid/epoch、scoped nullifier 与可选 edge challenge；微证明接口未指定本稿同一报告载荷与持有人签名关系，但接口可被扩展，不能宣称先前设计不可能做到。第 27、34 行对此有合适限制。
- SPOON、Xu 等已涉及匿名众包、报告、防重复；Brito 2026 已研究内容来源与时空事件见证，Bogdanov 2025 结合可信设备签名和私密地理策略，ZKLP 已处理位置属性证明。第 32–38 行避免了“首次”的绝对说法，但应结合真实受控消融提出“相同 holder secret 如何改变接收结果”这一可检验的具体差别，而不是只把功能堆叠称创新。
- `research/literature_review.md` 提供的 Waterloo 作者 PDF URL 现在跳转到学校说明页（UWaterloo Scholar 于 2026-04-30 关闭）。BibTeX SPOON 条目使用 DOI，并不依赖失效链接；若交付阅读清单应更新为出版商 DOI 或其他真实作者版本。Brito 的 arXiv 页面注明获 ICSA 2026 companion workshop 接收，应在确认正式会议记录前按 arXiv 引用，不推断同行评审状态。
- 初稿审计指出本地旧代码存在 fallback 验证问题；这只能说明当前可查源码快照，不能推断初稿论文当年运行环境或全部原始实验。初稿旧数值不要迁移为新关系的结果。

## 第 6 节与用户偏好

第 6 节标题已为 `Discussion`；没有声称做过真实部署。当前第 120–123 行几乎全部重复前文边界，与用户“突出长处、缺陷一句带过”的偏好不吻合。可在完整结果出来后以“受控替换实验说明同一凭证秘密参与见证与去重所带来的意义；测得的证明/验证开销反映在具体测试环境下的可行性”组织 2 段讨论，再以一句综合边界结尾，例如：

> These guarantees apply to issuer-asserted events and to the stated credential, key-management, and gateway-state assumptions.

必要的具体威胁假设仍保留在第 3–4 节；压缩讨论不应删掉影响结果解释的关键条件。避免提真实设备部署可行性、现网实验或未来实机计划，因为尚无实测。

## 构建与其他

- 将新稿、`sn-jnl.cls`、`sn-mathphys-num.bst` 和 `draft_sections/cited_sources.bib` 复制到隔离目录，`latexmk -pdf -interaction=nonstopmode -halt-on-error manuscript.tex` 成功，7 页，无未定义引文、交叉引用或 overfull 警告。模板依赖仍需在最终交付包中一起提供；主文件第 3 行提到 workspace README，但当前路径下未核实有该 README，建议改为可执行的简短构建说明。
- 作者、顺序及联系信息当前沿用较新的重投稿稿件，与初稿第三作者不同。最终提交前需由实际作者确认名单、邮箱和单位。经父代理指示，当前草稿暂采用较新的作者名单；本次审阅不擅自更改。
- 文章中的实验和个人贡献/资金/数据声明由责任作者核验，不能从另一项研究的稿件直接复制。
