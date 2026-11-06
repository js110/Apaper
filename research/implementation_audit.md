# PCVCS 初版与 ZCRSC 原型实现核查

核查日期 2026-11-04。目标是判断可以复用哪些代码以及哪些实验主张需要重新验证；本次没有修改 `/Users/jiangsheng/Desktop/IEEE` 的仓库。这里的行为演示针对**当前本机工作树与 Python 环境**，不能直接推断用户提供的 2026-04-21 初版 PDF 当时使用的代码提交、依赖或机器。

## 一、来源与版本边界

- 初版实现目录：`/Users/jiangsheng/Desktop/IEEE/PCVCS`，独立嵌套 Git 仓库，远端 `https://github.com/js110/PCVCS.git`，当前 HEAD `ac6e7b2e6b6d308e0668d94df8bbed291f3931c2`。工作树已有修改：包括 `experiments/modules/security_tester.py` 等；`run_iotj_evaluation.py` 和部分结果为未跟踪文件。不能在未核对作者的历史提交和产物后，将当前工作树当作 PDF 的确切源码。
- 当前论文的 ZCRSC 原型仓库：`https://github.com/js110/ZCRSC-PAPER`；只读分析使用浅克隆 `/tmp/apaper-zcrsc-audit`，HEAD `1ea0bea3f8eed635105c7f7b5bfd966babc368b8`。其 `prototype/zkdepth` 是 gnark/Groth16/BN254 实现，带 EdDSA/MiMC 签名电路和单进程网关，范围不是完整初版 PCVCS 服务。
- `PCVCS/README.md` 说明 `data/scenario_*_events.json` 为 SUMO TraCI 加项目后处理的产物，默认 `sumo/simple_test.cfg` 使用合成网格 `sumo/simple_grid.net.xml`。上海网络文件未接入默认流程；这些文件不是现实车辆位置观测或真实在场记录。
- 现存实验快照 `iotj_reproducible_results/20260407_225632/probe/20260407_225632/environment_snapshot.json` 记录 Darwin、Python 3.14.3、`USE_REAL_CRYPTO=1`，但不记录库是否真正加载。`run_performance_evaluation.py:105-114` 同时硬编码 AMD Ryzen 5 5500GT；不能以硬编码日志代替实际 CPU 记录，也不能因此推定初版 PDF 使用了这个快照。

## 二、必须阻止无效后端进入论文实验

### 1. Bulletproofs 适配器

`PCVCS/common/bulletproofs_backend.py:7-35, 93-95, 122-124, 142-158` 动态库未加载时，证明生成改用哈希占位，`fallback_range_proof_verify` 无条件 `return True`。`common/crypto_adapters.py:125-140` 只检查 Python 包装函数是否导入成功来设置 `_bp_real`，即使底层动态库为 `None` 也可报告 true，不能用此标志判断真实 Bulletproofs 可用。

更重要的是，`PCVCS/src/lib.rs:24-47, 66-90` 中 prove 和 verify 均 `let _ = (l, u)`，调用的是 64-bit Bulletproofs range proof。该源文件忽略传入的策略范围 L、U；即使有对应编译库，也不能单凭此代码声称验证了任意任务窗口 `[L,U]`。此处仅基于源码审核，未在本机编译 Rust 动态库重复实验。

### 2. LSAG / 环签名

`PCVCS/common/lrs_backend.py:149-166` 找不到本地原生库时使用 HMAC 占位签名，且 `fallback_lsag_verify` 无条件返回 true。`common/crypto_adapters.py:44-51` 同样在包装模块导入成功时置 `_lrs_real=True`，不能代表原生 LSAG 库实际加载。另 `common/crypto.py` 是 HMAC 示例并暴露 `signer_index_hint`，不提供可声称的环匿名性。应逐条按执行路径判定，不要将此处对一个模块的发现套用为对所有代码版本的结论。

### 3. KEM

`common/kem_layer.py:5-10, 19-28, 30-45, 52-69` 在 `kyber_py` 不存在时生成无关随机 pk/sk；客户端求 `SHA256(ct || pk)`，服务端求 `SHA256(ct || sk)`，一般不会一致。本机最小测试确认无该依赖且双方密钥不相等；这条回退路径不是可使用的 KEM 或保密信道。源码另使用可选 `kyber_py.kyber.Kyber512`，不应未核验就称其为通过 FIPS 203 合规性认证的 ML-KEM。

### 4. 安全测试路径

当前 `experiments/modules/security_tester.py:244-263` 根据测试记录自行携带的 `sample['type']` 选择地理、时间或重放分支，默认分支返回 true，函数没有统一验证 RSU 签名、Merkle 证明及环签名。因此其分类攻击识别测试只能说明这些测试分支的输出，不直接证明完整密码协议能拒绝伪造。

复现的本机负向检查（不输出密钥，使用 `PYTHONDONTWRITEBYTECODE`）：

```bash
cd /Users/jiangsheng/Desktop/IEEE/PCVCS
USE_REAL_CRYPTO=1 PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from common import bulletproofs_backend as bp, lrs_backend as lr, crypto_adapters as a, kem_layer as kem
from experiments.modules.security_tester import SecurityTester
print('Bulletproof shared lib loaded:', bool(bp._lib))
print('LSAG shared lib loaded:', bool(lr._lib))
print('adapter flags:', a._bp_real, a._lrs_real)
print('arbitrary range proof accepted:', bp.range_proof_verify_py(0,1,b'X'*32,b'invalid'))
print('arbitrary ring signature accepted:', lr.lsag_verify_py(b'tampered',[b'A'*32],b'invalid',b'Z'*32,b'ctx'))
pk,sk=kem.kem_keygen(); ct,kc=kem.kem_encaps(pk); ks=kem.kem_decaps(sk,ct)
print('kyber library available:', bool(kem._kyber_lib), 'session keys match:', kc == ks)
tester=SecurityTester(); sample=tester.generate_valid_sample()
sample['geohash']='NOT-IN-TASK-AREA'; sample['merkle_proof']=[]
sample['token']['signature_hex']='00'*64; sample['lsag_signature']['sig']='00'*32
print('tampered sample accepted by verify_sample:',tester.verify_sample(sample))
PY
```

本机结果为动态 Bulletproof/LSAG 均未加载、包装层标志均 true、任意伪造示例都被接受、`kyber_py` 未加载且 KEM 密钥不一致、篡改样本被 `verify_sample` 接受；PyNaCl Ed25519 真实库可用。由于包装加载行为受机器和环境影响，这些是当前机器实测，不能代表全部历史运行。

### 5. 单独 packet verifier 的信任边界

`verifier/verify_packet_real.py:12-29` 在验证证明前就把 nonce 加入内存集合，无效报告可先占用 nonce；`33-36, 41-66` 从提交包本身读取 Merkle root 和环成员，再验证提交的地理路径/环。需要外部受信的任务策略、登记成员和上下文，否则数学上验证了攻击者自行指定的集合并不能确立授权。代码在验证器侧直接读取 `packet_obj['geohash7']`，因此不能把此路径描述为让该验证器完全不知道 geohash 的零知识位置验证。这里只分析当前源代码，无主张作者的完整线上系统一定采用它。

### 6. 成本与计量

`run_performance_evaluation.py:311-354` 客户端预先构建 Merkle root/path，计时区段把 root/proof 赋给临时变量并计时一次 `range_proof_prove`；它不等同于实际生成完整零知识 Merkle 位置证明。`_generate_full_report:452-481` 按固定字段大小、推定 Merkle 高度、采样适配器输出长度及假设 KEM 摊销计算报告总大小，不是对实际端到端密文报告统一序列化后逐字节测量。不能把这些数字直接重用作新协议的真实完整零知识证明、密文传输或跨论文同条件对比。

## 三、可复用的 ZCRSC 原型

`prototype/zkdepth/circuit.go` 定义具体 Groth16/BN254 电路：边界范围约束、授权来源公钥、MiMC 消息摘要、gnark 的 twisted-Edwards BN254 EdDSA 验签、签发者公钥去重和 policy relation。`gateway.go` 从被验证者配置的任务、报告摘要、nonce 和到期时间重建公开上下文；验证成功后在互斥锁内消费挑战。`circuit_test.go`、`gateway_test.go` 设计了证明生成/验证、范围篡改、证明跨报告/任务上下文替换、错误决策、过期与并发重放等检查。

可优先复用：

1. gnark 签名验证、区间约束、确定性上下文和真实 Groth16 证明流水线；实现时明确 BN254 曲线和 gnark EdDSA，不称 Ed25519 或直接兼容 IEEE 1609.2。
2. 单进程 challenge 消费/并发测试的模式；有效证明之外需新增参与者凭证的 task-scoped nullifier 原子性，二者不是同一个机制。
3. 将四状态 robust-depth 几何视作可选参照，不应把当前任务变成纯多源融合。

它尚不包含车载平台、合法参与者匿名资格、同一匿名秘密与报告/时空凭证绑定、每任务防重复、可核验真实物理采集、实际安全网络传输、动态签发者名单、持久化跨节点状态。论文只能描述新增原型中实际完成和验证的功能。

核查命令及本次结果：

```bash
cd /tmp/apaper-zcrsc-audit/prototype
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_robust_depth.py
# 6 tests, OK: 包括候选算法对穷举 oracle、两后端原生判定等价、故障预算下语义边界

cd zkdepth
go test ./...
# 首次因 proxy.golang.org 获取 gnark v0.14.0 与 gnark-crypto v0.19.0 超时而 setup failed；不应报告 Go 测试通过。
# goproxy.cn 的模块信息端点可达。主任务已开始使用该镜像解决依赖，最终结论以其实际测试输出为准。
```

## 四、新原型最低可接受验证

- 原生后端缺失应明确失败，禁止静默回退和以模块导入成功冒充密码学可用。
- 正向应真实生成、验证证明；反向应修改每个关系中的任务、策略、报告摘要、签发者密钥/签名、匿名凭证、nullifier、位置/时间，以及重复请求和 challenge，确认校验失败。
- 可信 verifier 服务器自行构造任务 policy、认证 roster/凭证根、验证密钥；不能从攻击者的报告包接受。
- 对 nonce 和防重状态，在验证成功之后同一原子事务提交；失败不消费 token、并发只接受一次。进程内状态、重启后持久性、多实例一致性分别标注范围。
- 区分“报告字节绑定”和“受信传感器物理采集、现场在场”；后者需额外的实际机制/可信假设，不从 hash、RSU 签名或 SNARK 单独推断。
- 公布硬件、软件、环境、种子、库版本和是否运行真实 cryptographic path；证明/公开输入/报告密文大小要直接按实际序列化字节计量。
