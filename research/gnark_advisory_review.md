# gnark 安全公告及隔离升级核查

核查日期：2026-11-04。范围为 `paper_a/event_report/prototype` 当时已有的 Go 源码和测试；升级试验在 `/tmp/apaper_gnark_upgrade/prototype` 进行，未改工作区源代码、go.mod 或基准日志。包依赖和可执行路径审查不是安全证明，不保证不存在其他实现问题。

## 对 GHSA-3mvx-pp85-pm65 的路径判断

官方 [GHSA-3mvx-pp85-pm65](https://github.com/Consensys-Incorporated/gnark/security/advisories/GHSA-3mvx-pp85-pm65) 将 gnark `< v0.16.2` 列为受影响包版本，官方修复版本为 `>= v0.16.2`。当前工作区记录的 v0.14.0 落在该包版本范围内；这并不意味着其每个电路都调用了每条受影响 gadget。

公告逐项点名的关键路径包括 `std/math/emulated`、`std/algebra/native/sw_grumpkin`、若干 emulated pairing、`std/algebra/native/sw_bls12377` 和 `std/math/uints` 的按字节操作。当前电路实际调用的是 `std/algebra/native/twistededwards`、`std/signature/eddsa`、field MiMC 和 `std/math/cmp`，区间输入通过 `ToBinary(...,32)` 限位；SHA-256 在电路外由 Go 标准库执行。`go list -deps` 能列出 `std/math/uints`，因为 `std/hash` 接口文件声明了 `uints.U8` 类型；但核对电路的 MiMC 写入路径和项目调用，未发现调用公告所述 `uints` 中 `twoArgFn`、`Not` 或电路内 SHA-2/3 byte gadget。未在当前依赖输出中发现上述 emulated 或 sw_grumpkin 直接路径。

因此，**现有证据尚未显示本电路触发该公告列出的具体攻击路径**；不能因此宣称 v0.14.0 整体无风险，也不能仅因为依赖包在版本范围内就声称本协议已经可被攻击。未知的间接路径、其他公告和 malicious-prover 场景仍需持续审查。

## 另一个直接相关的 EdDSA 标量边界

官方 [GHSA-95v9-hv42-pwrj](https://github.com/Consensys-Incorporated/gnark/security/advisories/GHSA-95v9-hv42-pwrj) 讨论 EdDSA/ECDSA signature scalar malleability 和补丁边界。核对 v0.14.0 实际库 `std/signature/eddsa/eddsa.go`，其签名验证使用 `AssertIsLessOrEqual(sig.S, curve.Params().Order)`，允许 `S == order`。官方公告追加说明指出该等号情形后续修复，通常需要非常特殊的哈希前像条件；这不等于证明本协议可被利用。本协议 nullifier 从参与者 secret 和 task ID 派生，并非从签名 `(R,S)` 派生，公告中签名型 nullifier 的攻击解释不应直接套用。

隔离下载的 v0.16.2 源码改为 `cmp.IsLess(sig.S, order)` 并断言为真，即严格 `< order`。建议以修复后的库和全新测试/基准作为投稿实现，同时保持主动公钥曲线/子群检查和现有恶意样本测试。

另有 [GHSA-7fx8-hmgc-82jp](https://github.com/Consensys-Incorporated/gnark/security/advisories/GHSA-7fx8-hmgc-82jp)，其具体问题涉及 emulated fake-GLV 与 ECDSA/P256Verify；本电路使用 native twisted Edwards EdDSA，目前未看到该路径，但该公告要求 v0.16.4 修复。因此这里进一步试验 v0.16.4，而不只满足上一公告的最低 v0.16.2。

## 隔离升级和测试

1. 在独立 `/tmp/apaper_gnark_upgrade/prototype` 拷贝工作区 Go 文件和模块，执行 `go get github.com/consensys/gnark@v0.16.2`。该版本需要 Go `>= 1.25.7`，依赖 gnark-crypto `v0.21.0`。隔离 `go test -count=1 -timeout=10m ./...` 返回成功。
2. 随后执行 `go get github.com/consensys/gnark@v0.16.4`；结果 `go.mod` 是 Go `1.26.8`、gnark `v0.16.4`、gnark-crypto `v0.21.1-0.20260913224755-1409fe592052`。Go 自动下载工具链后 `go version` 显示 `go1.26.8 darwin/arm64`。
3. 由于并行任务更新了区域网关与 ML-KEM 功能，再次从工作区复制所有 `.go` 到隔离目录，并在隔离目录运行 `go test -count=1 -timeout=10m -v ./...`；退出码 0，总运行约 13.581 秒。复制后逐字节比较了当时工作区所有 `.go` 文件和隔离副本，没有差异。完整日志位于 `/tmp/apaper_gnark_upgrade/tests_0164_latest.log`。
4. 日志显示 11 个顶层常规测试 PASS，覆盖 holder 绑定消融、矩形电路正负样本、真实 Groth16、密钥点、基础 Gateway、ML-KEM 报文、区域 Gateway、区域证明、区域配置、AES-GCM。两个基准测试因未设置 opt-in 环境变量而 SKIP，故此结果不构成升级后性能结论。

建议应用升级前再次核对并行改动后的源码差异，固定依赖版本并重新执行全部测试；测试通过只能证明该测试集合在这个环境下通过，不能代替恶意 prover 的约束审计。升级后旧版性能日志仍是 v0.14.0 的真实记录，不能被当作 v0.16.4 的性能或约束数。若投稿稿件改用新版本，应重新记录各基准，确保日志哈希、图表和正文一致。

补充冒烟试验：隔离 v0.16.4 在 `EVENT_BENCH_RUNS=1 EVENT_REGION_BENCH_RUNS=1` 下两个基准函数均通过；矩形和区域电路分别编译为 29,833 与 35,798 个约束（v0.14.0 分别为 29,551 与 35,516），序列化证明仍均为 164 B。只运行 1 个计时样本，不能用于论文的性能均值或新旧版本可靠比较。日志 `/tmp/apaper_gnark_upgrade/smoke_benchmark_0164.log`。
