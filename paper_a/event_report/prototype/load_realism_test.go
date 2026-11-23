package eventreport

import (
	"bytes"
	"crypto/mlkem"
	"crypto/rand"
	"crypto/sha256"
	"fmt"
	"math/big"
	"os"
	"os/exec"
	"runtime"
	"strconv"
	"strings"
	"sync"
	"syscall"
	"testing"
	"time"

	"github.com/consensys/gnark-crypto/ecc"
	ed "github.com/consensys/gnark-crypto/ecc/bn254/twistededwards"
	"github.com/consensys/gnark/backend/groth16"
	"github.com/consensys/gnark/backend/witness"
	"github.com/consensys/gnark/constraint"
	"github.com/consensys/gnark/frontend"
	"github.com/consensys/gnark/frontend/cs/r1cs"
	"github.com/consensys/gnark/logger"
)

// This file adds two review-requested experiments on top of
// protocol_comparison.log:
//
//  1. TestInterleavedArmComparison — the shared-context and hidden-context
//     active arms are measured in one session with the per-round order drawn
//     at random, replacing the sequential-block order of the original
//     comparison for the acceptance-overhead claim.
//  2. TestGatewayLoadAndMemory — gateway acceptance-path cost: the
//     resident-memory footprint of one proof generation, the single-instance
//     SubmitAndOpen acceptance throughput, and the throughput of stateless
//     Groth16 verification under concurrency, which bounds a deployment of
//     independent verification shards.
//
// Both reuse the synthetic in-process model of TestProtocolComparisonExperiment:
// no network, no physical sensing, no production setup ceremony.

type loadArm struct {
	name    string
	hidden  bool
	ccs     constraint.ConstraintSystem
	pk      groth16.ProvingKey
	vk      groth16.VerifyingKey
	gateway *ActiveGateway
}

type loadParticipant struct {
	fixture        *Fixture
	identityScalar *big.Int
}

type loadPrepared struct {
	challenge  Challenge
	plain      []byte
	envelope   []byte
	tag        *big.Int
	cipher     AccountabilityCiphertext
	proofBytes []byte
	circ       frontend.Circuit
}

type loadEnv struct {
	common        *Fixture
	participants  []loadParticipant
	region        *RegionPolicy
	active        *ActivePolicy
	recipient     *mlkem.DecapsulationKey768
	auditor       ed.PointAffine
	auditorSecret *big.Int
	task          Task
	event         [3]uint32
	cellIndex     int
}

func loadEnvInfo(t *testing.T, name string, files []string) {
	info := func(cmd string, args ...string) string {
		b, e := exec.Command(cmd, args...).Output()
		if e != nil {
			return "unavailable"
		}
		return strings.TrimSpace(string(b))
	}
	fmt.Printf("experiment=%s\nstarted_utc=%s\n", name, time.Now().UTC().Format(time.RFC3339Nano))
	fmt.Printf("go=%s os=%s arch=%s logical_cpus=%d gomaxprocs=%d\n", runtime.Version(), runtime.GOOS, runtime.GOARCH, runtime.NumCPU(), runtime.GOMAXPROCS(0))
	fmt.Printf("cpu=%q memory_bytes=%s os_product=%q os_version=%q os_build=%q\n", info("sysctl", "-n", "machdep.cpu.brand_string"), info("sysctl", "-n", "hw.memsize"), info("sw_vers", "-productName"), info("sw_vers", "-productVersion"), info("sw_vers", "-buildVersion"))
	fmt.Printf("modules=%q\n", info("go", "list", "-m", "github.com/consensys/gnark", "github.com/consensys/gnark-crypto"))
	for _, path := range files {
		b, e := os.ReadFile(path)
		if e != nil {
			t.Fatalf("read %s: %v", path, e)
		}
		fmt.Printf("source_sha256 file=%s digest=%x\n", path, sha256.Sum256(b))
	}
}

func maxRSS(t *testing.T) int64 {
	var ru syscall.Rusage
	if err := syscall.Getrusage(syscall.RUSAGE_SELF, &ru); err != nil {
		t.Fatalf("getrusage: %v", err)
	}
	return ru.Maxrss
}

// newLoadEnv builds the synthetic task, region, active set and one participant
// per requested index, identical to the protocol-comparison model.
func newLoadEnv(t *testing.T, people int) *loadEnv {
	t.Helper()
	common, err := NewFixture()
	if err != nil {
		t.Fatal(err)
	}
	participants := make([]loadParticipant, people)
	ids := make([]*big.Int, 0, ActiveCapacity)
	for i := 0; i < people; i++ {
		f, e := NewFixture()
		if e != nil {
			t.Fatal(e)
		}
		f.Authority, f.Issuer = common.Authority, common.Issuer
		id, e := ActiveCredentialID(f.Secret)
		if e != nil {
			t.Fatal(e)
		}
		ids = append(ids, id)
		scalar, e := NewAccountabilityScalar()
		if e != nil {
			t.Fatal(e)
		}
		participants[i] = loadParticipant{f, scalar}
	}
	for candidate := int64(1); len(ids) < ActiveCapacity; candidate++ {
		v := big.NewInt(candidate)
		duplicate := false
		for _, d := range ids {
			if d.Cmp(v) == 0 {
				duplicate = true
				break
			}
		}
		if !duplicate {
			ids = append(ids, v)
		}
	}
	task := Task{ID: "synthetic-comparison-task", Lower: [3]uint32{10, 20, 100}, Upper: [3]uint32{30, 50, 200}}
	cells := make([][2]uint32, 0, RegionCapacity)
	cellIndex := -1
	for y := uint32(20); y <= 50 && len(cells) < RegionCapacity; y++ {
		for x := uint32(10); x <= 30 && len(cells) < RegionCapacity; x++ {
			if x == 20 && y == 30 {
				cellIndex = len(cells)
			}
			cells = append(cells, [2]uint32{x, y})
		}
	}
	if len(cells) != RegionCapacity || cellIndex < 0 {
		t.Fatal("invalid synthetic region")
	}
	region, err := NewRegionPolicy(task, cells)
	if err != nil {
		t.Fatal(err)
	}
	active, err := NewActivePolicy(ids)
	if err != nil {
		t.Fatal(err)
	}
	recipient, err := mlkem.GenerateKey768()
	if err != nil {
		t.Fatal(err)
	}
	auditorSecret, err := NewAccountabilityScalar()
	if err != nil {
		t.Fatal(err)
	}
	auditor, err := AccountabilityPublicKey(auditorSecret)
	if err != nil {
		t.Fatal(err)
	}
	return &loadEnv{common: common, participants: participants, region: region, active: active,
		recipient: recipient, auditor: auditor, auditorSecret: auditorSecret,
		task: task, event: [3]uint32{20, 30, 150}, cellIndex: cellIndex}
}

// newLoadArm compiles and sets up one active arm with its own gateway.
func newLoadArm(t *testing.T, env *loadEnv, name string, hidden bool, circ frontend.Circuit) *loadArm {
	t.Helper()
	start := time.Now()
	ccs, e := frontend.Compile(ecc.BN254.ScalarField(), r1cs.NewBuilder, circ)
	compileNS := time.Since(start).Nanoseconds()
	if e != nil {
		t.Fatal(e)
	}
	start = time.Now()
	pk, vk, e := groth16.Setup(ccs)
	setupNS := time.Since(start).Nanoseconds()
	if e != nil {
		t.Fatal(e)
	}
	gateway, e := NewActiveGateway(env.common.Authority.Public().Bytes(), env.region, env.auditor, env.active, 1, vk, env.recipient)
	if e != nil {
		t.Fatal(e)
	}
	fmt.Printf("ARM %s constraints=%d compile_ns=%d setup_ns=%d\n", name, ccs.GetNbConstraints(), compileNS, setupNS)
	return &loadArm{name: name, hidden: hidden, ccs: ccs, pk: pk, vk: vk, gateway: gateway}
}

// loadPrepare runs challenge issuance, envelope sealing, witness building and
// proving, and serializes the proof. With measureProve it additionally returns
// the prove wall time, the increase of the process resident-memory high-water
// mark across the call, and the bytes allocated during the call.
func loadPrepare(t *testing.T, env *loadEnv, arm *loadArm, person loadParticipant, seq int, measureProve bool) (loadPrepared, int64, int64, int64) {
	t.Helper()
	challenge, e := arm.gateway.Issue(1000, 60)
	if e != nil {
		t.Fatal(e)
	}
	plain := []byte(fmt.Sprintf("synthetic vehicular observation %08d", seq))
	envelope, e := SealReportMLKEM(env.recipient.EncapsulationKey(), plain, env.task.ID)
	if e != nil {
		t.Fatal(e)
	}
	regionAssignment, e := env.region.Assignment(person.fixture, challenge, envelope, env.event, env.cellIndex)
	if e != nil {
		t.Fatal(e)
	}
	if arm.hidden {
		if e = resignHiddenReceipt(person.fixture, &regionAssignment.Base); e != nil {
			t.Fatal(e)
		}
	}
	randomness, e := NewAccountabilityScalar()
	if e != nil {
		t.Fatal(e)
	}
	identity, e := AccountabilityPublicKey(person.identityScalar)
	if e != nil {
		t.Fatal(e)
	}
	account, cipher, e := NewAccountabilityAssignment(regionAssignment, person.fixture.Authority, identity, env.auditor, randomness)
	if e != nil {
		t.Fatal(e)
	}
	full, e := env.active.Assignment(account)
	if e != nil {
		t.Fatal(e)
	}
	var assignment frontend.Circuit = full
	if arm.hidden {
		assignment = hiddenActiveFrom(full)
	}
	witness, e := frontend.NewWitness(assignment, ecc.BN254.ScalarField())
	if e != nil {
		t.Fatal(e)
	}
	tag, ok := full.Accountability.Region.Base.Nullifier.(*big.Int)
	if !ok {
		t.Fatal("unexpected nullifier type")
	}
	var proveNS, rssDelta, allocDelta int64
	if measureProve {
		var ms0, ms1 runtime.MemStats
		rss0 := maxRSS(t)
		runtime.ReadMemStats(&ms0)
		start := time.Now()
		proof, e := groth16.Prove(arm.ccs, arm.pk, witness)
		proveNS = time.Since(start).Nanoseconds()
		runtime.ReadMemStats(&ms1)
		rssDelta = maxRSS(t) - rss0
		allocDelta = int64(ms1.TotalAlloc) - int64(ms0.TotalAlloc)
		if e != nil {
			t.Fatal(e)
		}
		var buf bytes.Buffer
		if _, e = proof.WriteTo(&buf); e != nil {
			t.Fatal(e)
		}
		return loadPrepared{challenge, plain, envelope, tag, cipher, buf.Bytes(), assignment}, proveNS, rssDelta, allocDelta
	}
	start := time.Now()
	proof, e := groth16.Prove(arm.ccs, arm.pk, witness)
	proveNS = time.Since(start).Nanoseconds()
	if e != nil {
		t.Fatal(e)
	}
	var buf bytes.Buffer
	if _, e = proof.WriteTo(&buf); e != nil {
		t.Fatal(e)
	}
	return loadPrepared{challenge, plain, envelope, tag, cipher, buf.Bytes(), assignment}, proveNS, 0, 0
}

// loadSubmit runs the gateway acceptance path for one prepared submission and
// returns its wall time.
func loadSubmit(t *testing.T, arm *loadArm, p loadPrepared) (int64, error) {
	t.Helper()
	start := time.Now()
	opened, record, e := arm.gateway.SubmitAndOpen(p.challenge.Nonce, p.envelope, p.tag, p.cipher, p.proofBytes, 1001)
	gatewayNS := time.Since(start).Nanoseconds()
	if e != nil {
		return gatewayNS, e
	}
	if len(opened) == 0 || record == nil {
		return gatewayNS, fmt.Errorf("gateway accepted without plaintext or record")
	}
	return gatewayNS, nil
}

// TestInterleavedArmComparison re-measures the shared-context and
// hidden-context active arms in one session with the per-round order drawn at
// random, closing the measurement-drift caveat of the sequential comparison.
func TestInterleavedArmComparison(t *testing.T) {
	value := os.Getenv("EVENT_INTERLEAVED_RUNS")
	if value == "" {
		t.Skip("set EVENT_INTERLEAVED_RUNS to run the experiment")
	}
	runs, err := strconv.Atoi(value)
	if err != nil || runs < 2 || runs > 200 {
		t.Fatal("EVENT_INTERLEAVED_RUNS must be in [2,200]")
	}
	logger.Disable()
	loadEnvInfo(t, "event-report-interleaved-arm-comparison-inprocess-v1", []string{
		"circuit.go", "native.go", "region.go", "accountability.go", "revocation.go",
		"gateway.go", "region_gateway.go", "accountability_gateway.go", "active_gateway.go",
		"transport.go", "kem_transport.go", "context_hiding_candidate_test.go",
		"context_hiding_extensions_test.go", "load_realism_test.go", "go.mod", "go.sum",
	})
	fmt.Printf("backend=Groth16 curve=BN254 region_depth=8 active_depth=8 arms=shared_active,hidden_active runs=%d warmup=1 ordering=random_per_round\n", runs)
	fmt.Println("model=single_process_inprocess_synthetic; components per run as in protocol_comparison: challenge issue, envelope seal, fixture sign and witness, prove, serialize, gateway verify+decrypt+dedup; total_to_accept excludes compile, setup, enrollment and network")

	env := newLoadEnv(t, runs+1)
	shared := newLoadArm(t, env, "shared_active", false, &ActiveCircuit{})
	hidden := newLoadArm(t, env, "hidden_active", true, &hiddenActiveCandidate{})

	// Warmup: one acceptance-path run per arm, reported but excluded below.
	for _, arm := range []*loadArm{shared, hidden} {
		totalStart := time.Now()
		p, _, _, _ := loadPrepare(t, env, arm, env.participants[0], 0, false)
		if _, e := loadSubmit(t, arm, p); e != nil {
			t.Fatalf("warmup %s: %v", arm.name, e)
		}
		fmt.Printf("warmup arm=%s total_to_accept_ns=%d\n", arm.name, time.Since(totalStart).Nanoseconds())
	}

	fmt.Println("round,arm,slot,first,prove_ns,total_to_accept_ns")
	var seed [8]byte
	for round := 1; round <= runs; round++ {
		if _, e := rand.Read(seed[:]); e != nil {
			t.Fatal(e)
		}
		order := []*loadArm{shared, hidden}
		first := "shared"
		if seed[0]&1 == 1 {
			order = []*loadArm{hidden, shared}
			first = "hidden"
		}
		for slot, arm := range order {
			totalStart := time.Now()
			p, proveNS, _, _ := loadPrepare(t, env, arm, env.participants[round], round, false)
			if _, e := loadSubmit(t, arm, p); e != nil {
				t.Fatalf("round %d arm %s: %v", round, arm.name, e)
			}
			fmt.Printf("%d,%s,%d,%s,%d,%d\n", round, arm.name, slot, first, proveNS, time.Since(totalStart).Nanoseconds())
		}
	}
	fmt.Println("SCOPE randomized per-round order within one session; every round runs both arms for the same participant index; no new circuits, setups or fixtures beyond the two arms")
	fmt.Printf("completed_utc=%s\n", time.Now().UTC().Format(time.RFC3339Nano))
}

// TestGatewayLoadAndMemory measures (a) the resident-memory footprint of one
// proof generation, (b) the acceptance-path throughput of a single gateway
// instance, and (c) the throughput of stateless Groth16 verification under
// concurrency, which bounds independent verification shards.
func TestGatewayLoadAndMemory(t *testing.T) {
	if os.Getenv("EVENT_LOAD_SUBMITS") == "" && os.Getenv("EVENT_LOAD_VERIFY_RUNS") == "" {
		t.Skip("set EVENT_LOAD_SUBMITS and/or EVENT_LOAD_VERIFY_RUNS to run the experiment")
	}
	envInt := func(name string, def int) int {
		v := os.Getenv(name)
		if v == "" {
			return def
		}
		n, e := strconv.Atoi(v)
		if e != nil || n < 1 {
			t.Fatalf("%s must be a positive integer", name)
		}
		return n
	}
	submits := envInt("EVENT_LOAD_SUBMITS", 60)
	verifies := envInt("EVENT_LOAD_VERIFY_RUNS", 400)
	procsEnv := os.Getenv("EVENT_LOAD_PROCS")
	if procsEnv == "" {
		procsEnv = "1,2,4,8"
	}
	levels := make([]int, 0, 8)
	for _, s := range strings.Split(procsEnv, ",") {
		n, e := strconv.Atoi(strings.TrimSpace(s))
		if e != nil || n < 1 {
			t.Fatal("EVENT_LOAD_PROCS entries must be positive integers")
		}
		levels = append(levels, n)
	}
	logger.Disable()
	loadEnvInfo(t, "event-report-gateway-load-memory-v1", []string{
		"circuit.go", "native.go", "region.go", "accountability.go", "revocation.go",
		"gateway.go", "region_gateway.go", "accountability_gateway.go", "active_gateway.go",
		"transport.go", "kem_transport.go", "context_hiding_candidate_test.go",
		"context_hiding_extensions_test.go", "load_realism_test.go", "go.mod", "go.sum",
	})
	fmt.Printf("backend=Groth16 curve=BN254 arm=hidden_active submits=%d verify_runs_per_level=%d procs=%s\n", submits, verifies, procsEnv)

	env := newLoadEnv(t, submits+2)
	hidden := newLoadArm(t, env, "hidden_active", true, &hiddenActiveCandidate{})

	// (a) Proving memory: cold first proof after compile+setup, then one warm
	// repeat, on a participant index unused below.
	_, coldProve, coldRSS, coldAlloc := loadPrepare(t, env, hidden, env.participants[submits+1], 1000, true)
	_, warmProve, warmRSS, warmAlloc := loadPrepare(t, env, hidden, env.participants[submits], 1001, true)
	var ms runtime.MemStats
	runtime.ReadMemStats(&ms)
	fmt.Printf("MEMORY prove=cold wall_ns=%d maxrss_delta_bytes=%d total_alloc_delta_bytes=%d\n", coldProve, coldRSS, coldAlloc)
	fmt.Printf("MEMORY prove=warm wall_ns=%d maxrss_delta_bytes=%d total_alloc_delta_bytes=%d\n", warmProve, warmRSS, warmAlloc)
	fmt.Printf("MEMORY process_peak_rss_bytes=%d heap_alloc_bytes=%d sys_bytes=%d gomaxprocs=%d\n", maxRSS(t), ms.HeapAlloc, ms.Sys, runtime.GOMAXPROCS(0))

	// (b) Single-instance acceptance path: pre-generate submissions on the live
	// gateway (challenges pending), then submit sequentially; the gateway holds
	// one lock across verify, AEAD open and dedup.
	prepared := make([]loadPrepared, submits)
	for i := 0; i < submits; i++ {
		prepared[i], _, _, _ = loadPrepare(t, env, hidden, env.participants[i], i, false)
	}
	fmt.Println("sample,submit_ns")
	seqStart := time.Now()
	for i, p := range prepared {
		gatewayNS, e := loadSubmit(t, hidden, p)
		if e != nil {
			t.Fatalf("submit %d: %v", i, e)
		}
		fmt.Printf("%d,%d\n", i, gatewayNS)
	}
	seqTotal := time.Since(seqStart).Nanoseconds()
	fmt.Printf("RESULT single_instance_submits=%d total_ns=%d mean_ns=%.0f throughput_per_s=%.2f\n",
		submits, seqTotal, float64(seqTotal)/float64(submits), float64(submits)*float64(time.Second)/float64(seqTotal))

	// (c) Stateless verification throughput under concurrency: each worker
	// deserializes its own proof copies and public witnesses; verification is
	// read-only and repeatable, unlike the stateful acceptance path above.
	poolSize := submits
	if poolSize > 32 {
		poolSize = 32
	}
	poolProofs := make([][]byte, poolSize)
	poolCircs := make([]frontend.Circuit, poolSize)
	for i := 0; i < poolSize; i++ {
		poolProofs[i] = prepared[i].proofBytes
		poolCircs[i] = prepared[i].circ
	}
	fmt.Println("stage,procs,verifies,wall_ns,verifies_per_s,mean_ns")
	for _, p := range levels {
		wall, count := runVerifyPool(t, hidden, poolProofs, poolCircs, p, verifies)
		fmt.Printf("verify,%d,%d,%d,%.2f,%.0f\n", p, count, wall,
			float64(count)*float64(time.Second)/float64(wall), float64(wall)/float64(count))
	}
	fmt.Println("SCOPE memory is the process high-water delta across one groth16.Prove on this machine, cold and warm; single-instance throughput reflects one gateway mutex; the concurrency levels bound independent verification shards, not one instance; no network or storage")
	fmt.Printf("completed_utc=%s\n", time.Now().UTC().Format(time.RFC3339Nano))
}

func runVerifyPool(t *testing.T, arm *loadArm, proofs [][]byte, circs []frontend.Circuit, procs, total int) (int64, int) {
	t.Helper()
	per := total / procs
	if per < 1 {
		per = 1
	}
	var wg sync.WaitGroup
	var mu sync.Mutex
	count := 0
	start := time.Now()
	for w := 0; w < procs; w++ {
		wg.Add(1)
		go func(worker int) {
			defer wg.Done()
			ps := make([]groth16.Proof, len(proofs))
			ws := make([]witness.Witness, len(circs))
			for i := range proofs {
				ps[i] = groth16.NewProof(ecc.BN254)
				if _, e := ps[i].ReadFrom(bytes.NewReader(proofs[i])); e != nil {
					t.Errorf("worker %d proof %d: %v", worker, i, e)
					return
				}
				pub, e := frontend.NewWitness(circs[i], ecc.BN254.ScalarField(), frontend.PublicOnly())
				if e != nil {
					t.Errorf("worker %d witness %d: %v", worker, i, e)
					return
				}
				ws[i] = pub
			}
			local := 0
			for j := 0; j < per; j++ {
				i := (worker + j) % len(ps)
				if e := groth16.Verify(ps[i], arm.vk, ws[i]); e != nil {
					t.Errorf("worker %d verify %d: %v", worker, j, e)
					return
				}
				local++
			}
			mu.Lock()
			count += local
			mu.Unlock()
		}(w)
	}
	wg.Wait()
	return time.Since(start).Nanoseconds(), count
}
