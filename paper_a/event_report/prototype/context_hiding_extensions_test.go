package eventreport

import (
	"bytes"
	"crypto/mlkem"
	"crypto/sha256"
	"fmt"
	"math/big"
	"os"
	"os/exec"
	"runtime"
	"strconv"
	"strings"
	"testing"
	"time"

	ed "github.com/consensys/gnark-crypto/ecc/bn254/twistededwards"
	tedwards "github.com/consensys/gnark-crypto/ecc/twistededwards"
	"github.com/consensys/gnark-crypto/ecc"
	"github.com/consensys/gnark/backend/groth16"
	"github.com/consensys/gnark/frontend"
	"github.com/consensys/gnark/frontend/cs/r1cs"
	"github.com/consensys/gnark/logger"
	circuitEd "github.com/consensys/gnark/std/algebra/native/twistededwards"
	"github.com/consensys/gnark/std/signature/eddsa"
)

// Hidden-context variants of the three extension circuits. Each keeps the
// extension relation of its shared-context counterpart unchanged and replaces
// only the base receipt relation: the issuer signature covers
// (constant, holder, event) instead of (context, holder, event), so the issuer
// never receives the context, challenge, task ID, policy box or report bytes.
// These are research candidates; the shared-context circuits remain the
// manuscript's main evaluated protocol.

type hiddenRegionCandidate struct {
	Base       hiddenContextCandidate
	RegionRoot frontend.Variable `gnark:",public"`
	Siblings   [RegionDepth]frontend.Variable
	Directions [RegionDepth]frontend.Variable
}

func (c *hiddenRegionCandidate) Define(api frontend.API) error {
	if err := c.Base.Define(api); err != nil {
		return err
	}
	current, err := hashFields(api, domainRegionCell, c.Base.Event[0], c.Base.Event[1])
	if err != nil {
		return err
	}
	for i := 0; i < RegionDepth; i++ {
		api.AssertIsBoolean(c.Directions[i])
		left := api.Select(c.Directions[i], c.Siblings[i], current)
		right := api.Select(c.Directions[i], current, c.Siblings[i])
		current, err = hashFields(api, domainRegionNode, left, right)
		if err != nil {
			return err
		}
	}
	api.AssertIsEqual(current, c.RegionRoot)
	return nil
}

type hiddenAccountabilityCandidate struct {
	Region        hiddenRegionCandidate
	Auditor       circuitEd.Point `gnark:",public"`
	CipherR       circuitEd.Point `gnark:",public"`
	CipherS       circuitEd.Point `gnark:",public"`
	Identity      circuitEd.Point
	LinkSignature eddsa.Signature
	Randomness    frontend.Variable
}

func (c *hiddenAccountabilityCandidate) Define(api frontend.API) error {
	if err := c.Region.Define(api); err != nil {
		return err
	}
	curve, err := circuitEd.NewEdCurve(api, tedwards.BN254)
	if err != nil {
		return err
	}
	accountabilityGroupCheck(api, curve, c.Identity)
	accountabilityGroupCheck(api, curve, c.Auditor)
	curve.AssertIsOnCurve(c.CipherR)
	curve.AssertIsOnCurve(c.CipherS)
	api.AssertIsDifferent(c.Randomness, 0)
	api.AssertIsLessOrEqual(c.Randomness, new(big.Int).Sub(curve.Params().Order, big.NewInt(1)))
	bits := api.ToBinary(c.Randomness, curve.Params().Order.BitLen())
	base := circuitEd.Point{X: curve.Params().Base[0], Y: curve.Params().Base[1]}
	rG := accountabilityMultiply(api, curve, base, bits)
	rP := accountabilityMultiply(api, curve, c.Auditor, bits)
	sum := accountabilityAdd(api, curve, c.Identity, rP)
	api.AssertIsEqual(c.CipherR.X, rG.X)
	api.AssertIsEqual(c.CipherR.Y, rG.Y)
	api.AssertIsEqual(c.CipherS.X, sum.X)
	api.AssertIsEqual(c.CipherS.Y, sum.Y)
	d, err := hashFields(api, domainCredential, c.Region.Base.Secret)
	if err != nil {
		return err
	}
	msg, err := hashFields(api, domainIdentityLink, d, c.Identity.X, c.Identity.Y)
	if err != nil {
		return err
	}
	return verifySignature(api, c.LinkSignature, msg, c.Region.Base.Authority)
}

type hiddenActiveCandidate struct {
	Accountability   hiddenAccountabilityCandidate
	ActiveRoot       frontend.Variable `gnark:",public"`
	ActiveSiblings   [ActiveDepth]frontend.Variable
	ActiveDirections [ActiveDepth]frontend.Variable
}

func (c *hiddenActiveCandidate) Define(api frontend.API) error {
	if err := c.Accountability.Define(api); err != nil {
		return err
	}
	d, err := hashFields(api, domainCredential, c.Accountability.Region.Base.Secret)
	if err != nil {
		return err
	}
	current, err := hashFields(api, domainActiveLeaf, d)
	if err != nil {
		return err
	}
	for i := 0; i < ActiveDepth; i++ {
		api.AssertIsBoolean(c.ActiveDirections[i])
		left := api.Select(c.ActiveDirections[i], c.ActiveSiblings[i], current)
		right := api.Select(c.ActiveDirections[i], current, c.ActiveSiblings[i])
		current, err = hashFields(api, domainActiveNode, left, right)
		if err != nil {
			return err
		}
	}
	api.AssertIsEqual(current, c.ActiveRoot)
	return nil
}

// resignHiddenReceipt replaces the fixture's context-bearing receipt with one
// signed over (constant, holder, event). The issuer input is holder and event
// only; holder is derived by the participant from its secret and the context.
func resignHiddenReceipt(f *Fixture, base *Circuit) error {
	context, ok := base.Context.(*big.Int)
	if !ok {
		return fmt.Errorf("expected native context")
	}
	holder, err := nativeHash(n(domainHolder), f.Secret, context)
	if err != nil {
		return err
	}
	e0, ok0 := base.Event[0].(uint32)
	e1, ok1 := base.Event[1].(uint32)
	e2, ok2 := base.Event[2].(uint32)
	if !ok0 || !ok1 || !ok2 {
		return fmt.Errorf("expected native event coordinates")
	}
	msg, err := nativeHash(n(domainReceipt), n(0), holder, n(int64(e0)), n(int64(e1)), n(int64(e2)))
	if err != nil {
		return err
	}
	base.Receipt, err = sign(f.Issuer, msg)
	return err
}

func hiddenRegionFrom(r *RegionCircuit) *hiddenRegionCandidate {
	return &hiddenRegionCandidate{Base: hiddenContextCandidate(r.Base), RegionRoot: r.RegionRoot, Siblings: r.Siblings, Directions: r.Directions}
}

func hiddenAccountabilityFrom(a *AccountabilityCircuit) *hiddenAccountabilityCandidate {
	return &hiddenAccountabilityCandidate{Region: *hiddenRegionFrom(&a.Region), Auditor: a.Auditor, CipherR: a.CipherR, CipherS: a.CipherS, Identity: a.Identity, LinkSignature: a.LinkSignature, Randomness: a.Randomness}
}

func hiddenActiveFrom(a *ActiveCircuit) *hiddenActiveCandidate {
	return &hiddenActiveCandidate{Accountability: *hiddenAccountabilityFrom(&a.Accountability), ActiveRoot: a.ActiveRoot, ActiveSiblings: a.ActiveSiblings, ActiveDirections: a.ActiveDirections}
}

// TestHiddenExtensionsExperiment benchmarks the hidden-context variants of the
// region, accountability and active circuits through the same gateway flow as
// TestEndToEndExperiment: synthetic, sequential, in-process, no network. The
// gateways are unchanged; only the compiled relation and verification key
// differ, because the hidden variants keep the identical public-input layout.
func TestHiddenExtensionsExperiment(t *testing.T) {
	value := os.Getenv("EVENT_HIDDEN_EXT_RUNS")
	if value == "" {
		t.Skip("set EVENT_HIDDEN_EXT_RUNS to run the experiment")
	}
	runs, err := strconv.Atoi(value)
	if err != nil || runs < 1 || runs > 254 {
		t.Fatal("EVENT_HIDDEN_EXT_RUNS must be in [1,254]")
	}
	logger.Disable()
	info := func(name string, args ...string) string {
		b, e := exec.Command(name, args...).Output()
		if e != nil {
			return "unavailable"
		}
		return strings.TrimSpace(string(b))
	}
	fmt.Printf("experiment=event-report-hidden-extensions-inprocess-v1\nstarted_utc=%s\n", time.Now().UTC().Format(time.RFC3339Nano))
	fmt.Printf("go=%s os=%s arch=%s logical_cpus=%d gomaxprocs=%d\n", runtime.Version(), runtime.GOOS, runtime.GOARCH, runtime.NumCPU(), runtime.GOMAXPROCS(0))
	fmt.Printf("cpu=%q memory_bytes=%s os_product=%q os_version=%q os_build=%q\n", info("sysctl", "-n", "machdep.cpu.brand_string"), info("sysctl", "-n", "hw.memsize"), info("sw_vers", "-productName"), info("sw_vers", "-productVersion"), info("sw_vers", "-buildVersion"))
	fmt.Printf("modules=%q\n", info("go", "list", "-m", "github.com/consensys/gnark", "github.com/consensys/gnark-crypto"))
	for _, path := range []string{"circuit.go", "native.go", "region.go", "accountability.go", "revocation.go", "gateway.go", "region_gateway.go", "accountability_gateway.go", "active_gateway.go", "transport.go", "kem_transport.go", "context_hiding_candidate_test.go", "context_hiding_extensions_test.go", "go.mod", "go.sum"} {
		b, e := os.ReadFile(path)
		if e != nil {
			t.Fatalf("read %s: %v", path, e)
		}
		fmt.Printf("source_sha256 file=%s digest=%x\n", path, sha256.Sum256(b))
	}
	fmt.Printf("backend=Groth16 curve=BN254 region_depth=8 region_cells=256 active_depth=8 active_credentials=256 runs=%d warmup=1\n", runs)
	fmt.Println("model=single_process_sequential_synthetic; excludes network, physical event observation, initial key enrollment, setup amortization, trusted clock implementation, disk storage; fixture re-signs credential, issuer certificate and receipt per iteration, hidden arms re-sign the receipt over (constant,holder,event)")
	fmt.Println("issuer_input=holder_and_event_only; issuer does not receive context, challenge, task ID, policy box or report bytes")

	common, err := NewFixture()
	if err != nil {
		t.Fatal(err)
	}
	type participant struct {
		fixture        *Fixture
		identityScalar *big.Int
	}
	people := make([]participant, runs+1)
	ids := make([]*big.Int, 0, ActiveCapacity)
	for i := range people {
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
		identityScalar, e := NewAccountabilityScalar()
		if e != nil {
			t.Fatal(e)
		}
		people[i] = participant{f, identityScalar}
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
	task := Task{ID: "synthetic-hidden-ext-task", Lower: [3]uint32{10, 20, 100}, Upper: [3]uint32{30, 50, 200}}
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
	authorityBytes := common.Authority.Public().Bytes()
	event := [3]uint32{20, 30, 150}

	type variant struct {
		name   string
		shared frontend.Circuit
		hidden frontend.Circuit
	}
	variants := []variant{
		{"region", &RegionCircuit{}, &hiddenRegionCandidate{}},
		{"accountability", &AccountabilityCircuit{}, &hiddenAccountabilityCandidate{}},
		{"active", &ActiveCircuit{}, &hiddenActiveCandidate{}},
	}
	for _, v := range variants {
		sharedCCS, e := frontend.Compile(ecc.BN254.ScalarField(), r1cs.NewBuilder, v.shared)
		if e != nil {
			t.Fatal(e)
		}
		start := time.Now()
		ccs, e := frontend.Compile(ecc.BN254.ScalarField(), r1cs.NewBuilder, v.hidden)
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
		fmt.Printf("VARIANT %s shared_constraints=%d hidden_constraints=%d compile_ns=%d setup_ns=%d\n", v.name, sharedCCS.GetNbConstraints(), ccs.GetNbConstraints(), compileNS, setupNS)

		var regionGW *RegionGateway
		var accountGW *AccountabilityGateway
		var activeGW *ActiveGateway
		switch v.name {
		case "region":
			regionGW, e = NewRegionGateway(authorityBytes, region, vk, recipient)
		case "accountability":
			accountGW, e = NewAccountabilityGateway(authorityBytes, region, auditor, vk, recipient)
		case "active":
			activeGW, e = NewActiveGateway(authorityBytes, region, auditor, active, 1, vk, recipient)
		}
		if e != nil {
			t.Fatal(e)
		}
		issue := func(now, ttl int64) (Challenge, error) {
			switch v.name {
			case "region":
				return regionGW.Issue(now, ttl)
			case "accountability":
				return accountGW.Issue(now, ttl)
			default:
				return activeGW.Issue(now, ttl)
			}
		}

		if v.name == "region" {
			fmt.Println("sample,challenge_ns,encrypt_ns,fixture_sign_and_witness_ns,prove_ns,proof_serialize_ns,gateway_verify_decrypt_dedup_ns,total_to_accept_ns,plaintext_bytes,envelope_bytes,proof_bytes,nonce_ascii_bytes,nullifier_bytes,component_sum_bytes")
		} else {
			fmt.Println("sample,challenge_ns,encrypt_ns,fixture_sign_and_witness_ns,prove_ns,proof_serialize_ns,gateway_verify_decrypt_dedup_ns,total_to_accept_ns,audit_open_ns,plaintext_bytes,envelope_bytes,proof_bytes,nonce_ascii_bytes,nullifier_bytes,identity_cipher_bytes,component_sum_bytes")
		}
		for i, person := range people {
			plain := []byte(fmt.Sprintf("synthetic vehicular observation %08d", i))
			totalStart := time.Now()
			start = time.Now()
			challenge, e := issue(1000, 60)
			challengeNS := time.Since(start).Nanoseconds()
			if e != nil {
				t.Fatal(e)
			}
			start = time.Now()
			envelope, e := SealReportMLKEM(recipient.EncapsulationKey(), plain, task.ID)
			encryptNS := time.Since(start).Nanoseconds()
			if e != nil {
				t.Fatal(e)
			}
			start = time.Now()
			regionAssignment, e := region.Assignment(person.fixture, challenge, envelope, event, cellIndex)
			if e != nil {
				t.Fatal(e)
			}
			if e = resignHiddenReceipt(person.fixture, &regionAssignment.Base); e != nil {
				t.Fatal(e)
			}
			var assignment frontend.Circuit
			var cipher AccountabilityCiphertext
			var identity ed.PointAffine
			switch v.name {
			case "region":
				assignment = hiddenRegionFrom(regionAssignment)
			default:
				randomness, e := NewAccountabilityScalar()
				if e != nil {
					t.Fatal(e)
				}
				identity, e = AccountabilityPublicKey(person.identityScalar)
				if e != nil {
					t.Fatal(e)
				}
				account, c, e := NewAccountabilityAssignment(regionAssignment, person.fixture.Authority, identity, auditor, randomness)
				if e != nil {
					t.Fatal(e)
				}
				cipher = c
				if v.name == "accountability" {
					assignment = hiddenAccountabilityFrom(account)
				} else {
					full, e := active.Assignment(account)
					if e != nil {
						t.Fatal(e)
					}
					assignment = hiddenActiveFrom(full)
				}
			}
			witness, e := frontend.NewWitness(assignment, ecc.BN254.ScalarField())
			if e != nil {
				t.Fatal(e)
			}
			fixtureNS := time.Since(start).Nanoseconds()
			start = time.Now()
			proof, e := groth16.Prove(ccs, pk, witness)
			proveNS := time.Since(start).Nanoseconds()
			if e != nil {
				t.Fatal(e)
			}
			start = time.Now()
			var proofBuffer bytes.Buffer
			if _, e = proof.WriteTo(&proofBuffer); e != nil {
				t.Fatal(e)
			}
			serializeNS := time.Since(start).Nanoseconds()
			tag, ok := regionAssignment.Base.Nullifier.(*big.Int)
			if !ok {
				t.Fatal("unexpected nullifier type")
			}
			start = time.Now()
			var opened []byte
			var record *AcceptedAccountabilityRecord
			switch v.name {
			case "region":
				opened, e = regionGW.SubmitAndOpen(challenge.Nonce, envelope, tag, proof, 1001)
			case "accountability":
				opened, record, e = accountGW.SubmitAndOpen(challenge.Nonce, envelope, tag, cipher, proofBuffer.Bytes(), 1001)
			default:
				opened, record, e = activeGW.SubmitAndOpen(challenge.Nonce, envelope, tag, cipher, proofBuffer.Bytes(), 1001)
			}
			gatewayNS := time.Since(start).Nanoseconds()
			if e != nil || !bytes.Equal(opened, plain) {
				t.Fatalf("gateway sample %d (%s): %v", i, v.name, e)
			}
			totalNS := time.Since(totalStart).Nanoseconds()
			auditNS := int64(0)
			if v.name != "region" {
				if record == nil {
					t.Fatalf("missing record sample %d (%s)", i, v.name)
				}
				start = time.Now()
				openedIdentity, e := record.OpenIdentity(auditorSecret)
				auditNS = time.Since(start).Nanoseconds()
				if e != nil || !openedIdentity.Equal(&identity) {
					t.Fatalf("auditor sample %d (%s): %v", i, v.name, e)
				}
			}
			nullifierEncoding := tag.FillBytes(make([]byte, 32))
			componentSum := len(envelope) + proofBuffer.Len() + len(challenge.Nonce) + len(nullifierEncoding)
			label := strconv.Itoa(i)
			if i == 0 {
				label = "warmup"
			}
			if v.name == "region" {
				fmt.Printf("%s,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n", label, challengeNS, encryptNS, fixtureNS, proveNS, serializeNS, gatewayNS, totalNS, len(plain), len(envelope), proofBuffer.Len(), len(challenge.Nonce), len(nullifierEncoding), componentSum)
			} else {
				rBytes, sBytes := cipher.R.Bytes(), cipher.S.Bytes()
				cipherBytes := len(rBytes) + len(sBytes)
				componentSum += cipherBytes
				fmt.Printf("%s,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n", label, challengeNS, encryptNS, fixtureNS, proveNS, serializeNS, gatewayNS, totalNS, auditNS, len(plain), len(envelope), proofBuffer.Len(), len(challenge.Nonce), len(nullifierEncoding), cipherBytes, componentSum)
			}
		}

		// Receipt-substitution checks at the constraint layer, mirroring
		// TestHiddenContextCandidate, plus gateway-level duplicate rejection.
		person := people[0]
		challenge, e := issue(2000, 60)
		if e != nil {
			t.Fatal(e)
		}
		envelope, e := SealReportMLKEM(recipient.EncapsulationKey(), []byte("binding check report"), task.ID)
		if e != nil {
			t.Fatal(e)
		}
		valid, e := region.Assignment(person.fixture, challenge, envelope, event, cellIndex)
		if e != nil {
			t.Fatal(e)
		}
		if e = resignHiddenReceipt(person.fixture, &valid.Base); e != nil {
			t.Fatal(e)
		}
		savedReceipt := valid.Base.Receipt
		checkAssignment := func(r *RegionCircuit) frontend.Circuit {
			switch v.name {
			case "region":
				return hiddenRegionFrom(r)
			default:
				randomness, e := NewAccountabilityScalar()
				if e != nil {
					t.Fatal(e)
				}
				identity, e := AccountabilityPublicKey(person.identityScalar)
				if e != nil {
					t.Fatal(e)
				}
				account, _, e := NewAccountabilityAssignment(r, person.fixture.Authority, identity, auditor, randomness)
				if e != nil {
					t.Fatal(e)
				}
				if v.name == "accountability" {
					return hiddenAccountabilityFrom(account)
				}
				full, e := active.Assignment(account)
				if e != nil {
					t.Fatal(e)
				}
				return hiddenActiveFrom(full)
			}
		}
		wrong, e := region.Assignment(person.fixture, challenge, []byte("other report bytes"), event, cellIndex)
		if e != nil {
			t.Fatal(e)
		}
		wrong.Base.Receipt = savedReceipt
		bad, e := frontend.NewWitness(checkAssignment(wrong), ecc.BN254.ScalarField())
		if e != nil {
			t.Fatal(e)
		}
		if ccs.IsSolved(bad) == nil {
			t.Fatalf("%s accepted reused receipt under altered context", v.name)
		}
		// Use a second enrolled participant so the active-tree membership stays
		// satisfiable and the rejection isolates the receipt-holder binding.
		other := people[1].fixture
		x, e := region.Assignment(other, challenge, envelope, event, cellIndex)
		if e != nil {
			t.Fatal(e)
		}
		x.Base.Receipt = savedReceipt
		bad2, e := frontend.NewWitness(checkAssignment(x), ecc.BN254.ScalarField())
		if e != nil {
			t.Fatal(e)
		}
		if ccs.IsSolved(bad2) == nil {
			t.Fatalf("%s accepted reused receipt under another holder", v.name)
		}
		// A fresh challenge and a fresh valid proof for the same participant
		// must still be rejected by the gateway's recorded task tag.
		challenge2, e := issue(3000, 60)
		if e != nil {
			t.Fatal(e)
		}
		envelope2, e := SealReportMLKEM(recipient.EncapsulationKey(), []byte("second report same task"), task.ID)
		if e != nil {
			t.Fatal(e)
		}
		again, e := region.Assignment(person.fixture, challenge2, envelope2, event, cellIndex)
		if e != nil {
			t.Fatal(e)
		}
		if e = resignHiddenReceipt(person.fixture, &again.Base); e != nil {
			t.Fatal(e)
		}
		var againAssignment frontend.Circuit
		var againCipher AccountabilityCiphertext
		switch v.name {
		case "region":
			againAssignment = hiddenRegionFrom(again)
		default:
			randomness, e := NewAccountabilityScalar()
			if e != nil {
				t.Fatal(e)
			}
			identity, e := AccountabilityPublicKey(person.identityScalar)
			if e != nil {
				t.Fatal(e)
			}
			account, c, e := NewAccountabilityAssignment(again, person.fixture.Authority, identity, auditor, randomness)
			if e != nil {
				t.Fatal(e)
			}
			againCipher = c
			if v.name == "accountability" {
				againAssignment = hiddenAccountabilityFrom(account)
			} else {
				full, e := active.Assignment(account)
				if e != nil {
					t.Fatal(e)
				}
				againAssignment = hiddenActiveFrom(full)
			}
		}
		witness, e := frontend.NewWitness(againAssignment, ecc.BN254.ScalarField())
		if e != nil {
			t.Fatal(e)
		}
		proof, e := groth16.Prove(ccs, pk, witness)
		if e != nil {
			t.Fatal(e)
		}
		var proofBuffer bytes.Buffer
		if _, e = proof.WriteTo(&proofBuffer); e != nil {
			t.Fatal(e)
		}
		tag, _ := again.Base.Nullifier.(*big.Int)
		var dupErr error
		switch v.name {
		case "region":
			_, dupErr = regionGW.SubmitAndOpen(challenge2.Nonce, envelope2, tag, proof, 3001)
		case "accountability":
			_, _, dupErr = accountGW.SubmitAndOpen(challenge2.Nonce, envelope2, tag, againCipher, proofBuffer.Bytes(), 3001)
		default:
			_, _, dupErr = activeGW.SubmitAndOpen(challenge2.Nonce, envelope2, tag, againCipher, proofBuffer.Bytes(), 3001)
		}
		if dupErr != ErrDuplicateReport {
			t.Fatalf("%s duplicate submission: got %v, want ErrDuplicateReport", v.name, dupErr)
		}
		fmt.Printf("RESULT variant=%s substituted_context=R1CS_rejected substituted_holder=R1CS_rejected duplicate_nullifier=gateway_rejected\n", v.name)
	}
	// Rectangle hidden variant: fixed-witness prove/verify timing, matching
	// the benchmark.log methodology (no gateway flow in this arm).
	sharedRect, e := frontend.Compile(ecc.BN254.ScalarField(), r1cs.NewBuilder, &Circuit{})
	if e != nil {
		t.Fatal(e)
	}
	start := time.Now()
	rectCCS, e := frontend.Compile(ecc.BN254.ScalarField(), r1cs.NewBuilder, &hiddenContextCandidate{})
	rectCompileNS := time.Since(start).Nanoseconds()
	if e != nil {
		t.Fatal(e)
	}
	start = time.Now()
	rectPK, rectVK, e := groth16.Setup(rectCCS)
	rectSetupNS := time.Since(start).Nanoseconds()
	if e != nil {
		t.Fatal(e)
	}
	fmt.Printf("VARIANT rectangle shared_constraints=%d hidden_constraints=%d compile_ns=%d setup_ns=%d\n", sharedRect.GetNbConstraints(), rectCCS.GetNbConstraints(), rectCompileNS, rectSetupNS)
	rectChallenge := Challenge{Nonce: strings.Repeat("ab", 32), ExpiresAt: 2000}
	rectAssignment, e := people[0].fixture.Assignment(task, rectChallenge, []byte("rectangle hidden benchmark"), event)
	if e != nil {
		t.Fatal(e)
	}
	if e = resignHiddenReceipt(people[0].fixture, rectAssignment); e != nil {
		t.Fatal(e)
	}
	rectWitness, e := frontend.NewWitness((*hiddenContextCandidate)(rectAssignment), ecc.BN254.ScalarField())
	if e != nil {
		t.Fatal(e)
	}
	rectPublic, e := rectWitness.Public()
	if e != nil {
		t.Fatal(e)
	}
	fmt.Println("sample,prove_ns,verify_ns,proof_bytes")
	for i := 0; i <= runs; i++ {
		start = time.Now()
		proof, e := groth16.Prove(rectCCS, rectPK, rectWitness)
		proveNS := time.Since(start).Nanoseconds()
		if e != nil {
			t.Fatal(e)
		}
		start = time.Now()
		e = groth16.Verify(proof, rectVK, rectPublic)
		verifyNS := time.Since(start).Nanoseconds()
		if e != nil {
			t.Fatal(e)
		}
		var buf bytes.Buffer
		if _, e = proof.WriteTo(&buf); e != nil {
			t.Fatal(e)
		}
		label := strconv.Itoa(i)
		if i == 0 {
			label = "warmup"
		}
		fmt.Printf("%s,%d,%d,%d\n", label, proveNS, verifyNS, buf.Len())
	}
	fmt.Println("RESULT variant=rectangle fixed_witness_prove_verify=30_measured (methodology of benchmark.log; no gateway flow)")
	fmt.Println("SCOPE research candidates; issuer signature input is (constant,holder,event); synthetic in-process demonstration without deployed issuers or network; privacy gain not measured by this benchmark")
	fmt.Printf("completed_utc=%s\n", time.Now().UTC().Format(time.RFC3339Nano))
}