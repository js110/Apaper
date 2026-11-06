# 当前工作稿：实验与协议事实核对

核对时间：2026-11-04；核对稿件 `paper_a/event_report/manuscript.tex`，矩形与区域电路及测试、`experiments/{benchmark.log,region_benchmark.log,binding.log,tests.log}`，并独立计算各日志均值和样本标准差。以下行号基于核对时的稿件快照。

## 应修改的证据层级和归属

1. **表 1“Accepted/Rejected”需要标明检查层次。** 第 120–122 行的正文已正确区分：强 holder-bound 情况中，自有和复制收据是用 `R1CS.IsSolved` 检查；弱化 bearer 变体中，复制收据还实际构造并验证 Groth16 证明。第 124–131 行的表格直接写 Accepted/Rejected，读者可能理解成全部经过网关端到端验收。建议表标题或表下注明：

   > Entries describe R1CS witness satisfaction; for the copied-receipt bearer case, a Groth16 proof was additionally generated and verified.

   表中 `Own receipt` 在 bearer 变体对应受害者使用自己的 bearer 收据，攻击者持复制收据是另一个格子；不要增加并未测试的主体或将该消融称为初稿原系统复现。

2. **第 133–145 行、摘要第 13 行数字仅属于基础矩形 `Circuit`，并非 Merkle 区域版本。** `benchmark.log` 确认 29,551 约束和 164/364 B 是不含区域树路径的基础电路。第 47、89–90 行引入 `RegionCircuit` 后，紧接着称 “The R1CS contains 29,551 constraints” 有歧义。建议改为 “The rectangular-policy circuit contains ...”，摘要中的 154.48 ms 和 164 B 同样注明 rectangular-policy circuit。新 `region_benchmark.log` 提供深度 8、256 cells 区域扩展的真实指标，可在单列中报告，不能将两个电路的开销混用。两套日志是不同的单次 setup/连续测试批次、没有交替随机运行；差值只能是这两批结果的描述，不能据此声称统计上显著的因果变化。

3. **区域验证已经成为方法的一部分，但现有第 5 节没有汇报对应验证或开销。** `region_test.go` 实际生成并验证两个成员位置的 Groth16 proof；使用错误配置根重验失败；对 5 个 Merkle/签名位置篡改见证和 1 个由可信发行者签名但不在允许列表中的单元，`groth16.Prove` 返回错误；后者先确认满足原矩形电路的约束。`TestRegionPolicyConfiguration` 检查空列表、重复、越界、超过 256、256 cells 及防止外部切片/根修改。建议报告这些具体测试，以及单独的区域基准数据。`experiments/tests.log` 是更早的运行，未列出区域测试；应由当前源代码重新运行并单独保存带区域测试的日志后引用。`region_gateway.go` 包含单独的区域网关，但现有仓库暂无 `RegionGateway` 端到端测试；不能说区域 proof 的网关端去重/重放已由此前 `gateway_test.go` 验证。

4. **第 47、90 行的 task ID 到 Merkle 根“一一绑定”是配置方假设，当前代码没有全局注册/不可变性强制。** `NewRegionPolicy` 接受 Task 和 cells；不同 policy 对象可以使用相同 task ID 和不同 root。`RegionGateway` 在构建时复制该配置并从本地获取 root，但没有全局注册表。既然 root 不进入 issuer 签名的 context，不应表述为“密码学将 root 与 task ID 绑定”。建议改为 “The verifier configuration is assumed to assign each task identifier to a single immutable box and root; the prototype snapshots that configuration.” 第 90 行已写根不在 signed context 中，应保留。

5. **第 134 行的 `a valid synthetic witness` 容易理解为 30 次使用同一 witness。** `benchmark_test.go` 对每轮构造不同的 challenge（计数编码）和报告字节，并重建/签名 witness；同一 fixture、任务、事件和 setup 在各轮重复使用。建议写 “a valid synthetic witness per run, with a common fixture and setup and varying report/context values”。基准使用明文 synthetic bytes 作为 `ContextField` 的 report 输入，并非每轮先实际加密；正文未声称计时含加密，但建议明确“synthetic byte strings”以免与 AES 流程混淆。

6. **图 1 的角色交互为协议示意，不能理解为已实现现场签发。** 当前 `Fixture.Assignment` 在同一软件环境生成签名，`transport.go` 为加解密函数，`Gateway` 只返回 error/成功状态，不实现实际收据请求、签发者观察、传输、自动转发到接收方等服务。第 112 行的软件模拟说明有帮助；第 39 行 caption 建议以 “Protocol workflow” 或 “Conceptual protocol workflow” 标明模型，别声称收据交互或数据转发已现场运行。网关并不解密或认证 AEAD 标签，稿件第 92、106 行已正确陈述。

7. **硬件及统计数字已复算通过。** 日志声明 Apple M1、16 GiB、macOS 27.2、Go 1.25.6、gnark 0.14.0、gnark-crypto 0.19.0；1 次预热后 30 次。矩形电路 `compile_ns=40,596,833`、`setup_ns=1,648,448,209`，故 40.60 ms 和 1.648 s 正确。证明均值 154.477576 ms、样本 SD 12.824867 ms；验证均值 1.0328959 ms、样本 SD 0.1327098 ms；表中四舍五入正确。30 行 proof 均为 164 B，public witness 均为 364 B。验证一次 setup/compile 无法估计这些步骤的方差；正文已称 one run。`benchmark_test.go` 的计时只包 `groth16.Prove` / `groth16.Verify`，不含构造 witness、签名、加解密、通信、网关操作与序列化；正文描述正确。

8. **基准代码来源哈希匹配当前文件。** 对 `circuit.go`、`native.go`、`go.mod`、`go.sum`、`benchmark_test.go` 以及区域的 `region.go`、`region_benchmark_test.go` 运行 SHA-256，均与相应日志记录一致。若后续修改任一相关代码，应重新跑并核对；现有时间统计不应跟未纳入摘要的其他版本混用。

9. **区域基准可复用的已计算值（需按其独立运行与测试范围表述）。** 深度 8、256 cells，35,516 约束，单次 compile 47.293833 ms / setup 2.369307666 s，30 次证明均值 223.654878 ms、样本 SD 12.339065 ms，验证均值 1.009539 ms、样本 SD 0.036652 ms，proof / public witness 164 / 396 B。预热 1 次；这些是局部库调用，不含物理观察、网络和 gateway 状态操作，不代表设备部署性能。

10. **第 115–117 行与目前保存的 tests.log 基本一致。** `modified encrypted report` 的真实 proof 在网关被拒；未知、过期 challenge 检查真实发生；两个挑战分别对应有效 proof，同一 tag 并发提交，一成功、一 duplicate。`OpenReport` 的错误 key、任务 ID 和改密文均另测。R1CS 中确有 certified identity、order-two、off-curve issuer 以及 off-curve signature R。需要避免把 R1CS 负例全部写成真实网络攻击或每项均有可验证 proof 的对抗结果。`tests.log` 的旧 ablation 提示字符串比最新 `binding.log` 短；应以最新日志和当前源码为准。

## 其他措辞与结论

- 第 104 行“更换 bytes 导致 context 不同，除非哈希碰撞”是条件性说法；构造为 SHA-256 再模素数，严格说还需排除两个不同 digest **归约到同一 field 元素**，并非只有 SHA-256 原始摘要相同。建议改 “except when the resulting reduced context values collide”。与最终作者所采用的安全假设保持一致。
- 第 154–158 行满足章节名 `Discussion` 且没有声称真实部署。用户偏好第 6 节重点讨论已观察到的价值而非铺陈不足；可用实验发现和成本解释展开，最后用一句压缩 issuer observation、enrolment、key management 和 gateway-state 假设；不要删除方法中对物理真实性、跨任务隐私与接收方解密的必要界定。
- 第 160–161 行 “local experiments verify the stated substitution cases” 可接受但不等于形式化安全证明，应保持后半句的范围；“isolates effect” 是一个特定 attacker 知道同任务、challenge、receipt、context、event 且有自己合法凭证的受控构造，正文已说明，结论中可加 “in the tested scenario” 避免泛化。
- 第 13 行摘要 “an event within ... policy” 应明确这是可信签发方断言的事件，现有末句涉及 observation 假设，但把前一句改为 “an issuer-asserted event” 更直接。不能把签名/随机挑战解释为已证明真实感知时间、真实物理位置或采样内容的准确性。
- 第 63 行的标量任务编码 `$u$` 与向量策略上界 `\boldsymbol u` 符号非常接近；可将任务字段改记 `$\mathsf{tid}$`。两个字段分别在网关外部由同一可信任务配置构造，电路不检查哈希 context preimage。
- 第 90 行区域根代表已编码的有限坐标对，原地理多边形到网格的取整、边界单元定义不是电路内部完成；不应声称其自动支持任意连续多边形的精确包含证明。
