package eventreport

import (
	"bytes"
	"crypto/mlkem"
	"crypto/rand"
	"crypto/sha256"
	"errors"
	"fmt"
	"math/big"
	"os"
	"os/exec"
	"runtime"
	"strconv"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/consensys/gnark-crypto/ecc"
	tedwards "github.com/consensys/gnark-crypto/ecc/twistededwards"
	"github.com/consensys/gnark-crypto/ecc/bn254/fr"
	nativeMiMC "github.com/consensys/gnark-crypto/ecc/bn254/fr/mimc"
	"github.com/consensys/gnark-crypto/signature"
	cryptoeddsa "github.com/consensys/gnark-crypto/signature/eddsa"
	"github.com/consensys/gnark/backend/groth16"
	"github.com/consensys/gnark/frontend"
	"github.com/consensys/gnark/frontend/cs/r1cs"
	"github.com/consensys/gnark/logger"
)

// Trusted-issuer baseline required by review: a trusted institution signs a
// cleartext event receipt and the platform deduplicates by a per-task
// pseudonym. No zero-knowledge proof is involved. The issuer sees the
// participant's identity key, the report content and the exact event; the
// platform sees the cleartext receipt. Revocation is enforced only at the
// issuer at signing time. This is a research harness, not a deployment.
const (
	domainBaselinePseudonym = 501
	domainBaselineReceipt   = 502
	domainBaselineRequest   = 503
)

var ErrInvalidReceipt = errors.New("invalid receipt signature")

type BaselineReceipt struct {
	Pseudonym       *big.Int
	Event           [3]uint32
	ReportDigest    *big.Int
	ChallengeDigest *big.Int
	Signature       []byte
}

// BaselineIssuer is the trusted institution. Enrollment maps identity public
// keys to real identities outside this harness; removing a key revokes it.
type BaselineIssuer struct {
	signer   signature.Signer
	task     Task
	taskF    *big.Int
	enrolled map[string]signature.PublicKey
}

func NewBaselineIssuer(signer signature.Signer, task Task) (*BaselineIssuer, error) {
	if err := task.Validate(); err != nil {
		return nil, err
	}
	tf, err := TaskField(task)
	if err != nil {
		return nil, err
	}
	return &BaselineIssuer{signer: signer, task: task, taskF: tf, enrolled: make(map[string]signature.PublicKey)}, nil
}

func (i *BaselineIssuer) Enroll(identity signature.PublicKey) {
	i.enrolled[string(identity.Bytes())] = identity
}

func (i *BaselineIssuer) Revoke(identity signature.PublicKey) {
	delete(i.enrolled, string(identity.Bytes()))
}

// Pseudonym derives the per-task pseudonym from the identity key. The issuer
// knows the identity key, so it can derive this value for ANY task: baseline
// pseudonyms are linkable across tasks by the issuer itself.
func (i *BaselineIssuer) Pseudonym(identity signature.PublicKey, task Task) (*big.Int, error) {
	tf, err := TaskField(task)
	if err != nil {
		return nil, err
	}
	return nativeHash(n(domainBaselinePseudonym), digestToField(identity.Bytes()), tf)
}

func baselineChallengeDigest(nonce string) *big.Int {
	return digestToField([]byte(nonce))
}

func baselineRequestMessage(challengeDigest, reportDigest *big.Int, event [3]uint32) (*big.Int, error) {
	return nativeHash(n(domainBaselineRequest), challengeDigest, reportDigest, n(int64(event[0])), n(int64(event[1])), n(int64(event[2])))
}

func (i *BaselineIssuer) receiptMessage(pseudonym, challengeDigest, reportDigest *big.Int, event [3]uint32) (*big.Int, error) {
	return nativeHash(n(domainBaselineReceipt), i.taskF, pseudonym, challengeDigest, reportDigest, n(int64(event[0])), n(int64(event[1])), n(int64(event[2])))
}

// SignReceipt is the issuance round: the participant authenticates with its
// identity key and hands the issuer the challenge, the full report and the
// event. The issuer checks enrollment (revocation), the request signature and
// the policy box, then signs the cleartext receipt.
func (i *BaselineIssuer) SignReceipt(identity signature.PublicKey, requestSig []byte, challenge Challenge, report []byte, event [3]uint32) (*BaselineReceipt, error) {
	pub, ok := i.enrolled[string(identity.Bytes())]
	if !ok {
		return nil, fmt.Errorf("identity not enrolled or revoked")
	}
	if err := challenge.Validate(); err != nil {
		return nil, err
	}
	for d := 0; d < 3; d++ {
		if event[d] < i.task.Lower[d] || event[d] > i.task.Upper[d] {
			return nil, fmt.Errorf("event outside the task bounds")
		}
	}
	cd := baselineChallengeDigest(challenge.Nonce)
	rd := digestToField(report)
	reqMsg, err := baselineRequestMessage(cd, rd, event)
	if err != nil {
		return nil, err
	}
	var elem fr.Element
	elem.SetBigInt(reqMsg)
	msgBytes := elem.Bytes()
	okSig, err := pub.Verify(requestSig, msgBytes[:], nativeMiMC.NewMiMC())
	if err != nil || !okSig {
		return nil, fmt.Errorf("request signature invalid")
	}
	pseudonym, err := i.Pseudonym(identity, i.task)
	if err != nil {
		return nil, err
	}
	msg, err := i.receiptMessage(pseudonym, cd, rd, event)
	if err != nil {
		return nil, err
	}
	elem.SetBigInt(msg)
	msgBytes = elem.Bytes()
	sig, err := i.signer.Sign(msgBytes[:], nativeMiMC.NewMiMC())
	if err != nil {
		return nil, err
	}
	return &BaselineReceipt{Pseudonym: pseudonym, Event: event, ReportDigest: rd, ChallengeDigest: cd, Signature: sig}, nil
}

// BaselineGateway verifies the issuer's cleartext receipt and deduplicates by
// the per-task pseudonym, with the same single-instance atomic state model as
// Gateway. It cannot check enrollment or revocation: those live at the issuer.
type BaselineGateway struct {
	mu             sync.Mutex
	issuerPub      signature.PublicKey
	task           Task
	taskF          *big.Int
	pending        map[string]Challenge
	usedPseudonyms map[string]struct{}
}

func newBaselineGateway(issuerPub signature.PublicKey, task Task) (*BaselineGateway, error) {
	if err := task.Validate(); err != nil {
		return nil, err
	}
	tf, err := TaskField(task)
	if err != nil {
		return nil, err
	}
	return &BaselineGateway{issuerPub: issuerPub, task: task, taskF: tf, pending: make(map[string]Challenge), usedPseudonyms: make(map[string]struct{})}, nil
}

func (g *BaselineGateway) Issue(now, ttl int64) (Challenge, error) {
	g.mu.Lock()
	defer g.mu.Unlock()
	for nonce, c := range g.pending {
		if now >= c.ExpiresAt {
			delete(g.pending, nonce)
		}
	}
	for {
		var random [32]byte
		if _, err := rand.Read(random[:]); err != nil {
			return Challenge{}, err
		}
		c := Challenge{Nonce: fmt.Sprintf("%x", random), ExpiresAt: now + ttl}
		if _, exists := g.pending[c.Nonce]; !exists {
			g.pending[c.Nonce] = c
			return c, nil
		}
	}
}

func (g *BaselineGateway) Submit(nonce string, receipt *BaselineReceipt, report []byte, now int64) error {
	g.mu.Lock()
	defer g.mu.Unlock()
	c, exists := g.pending[nonce]
	if !exists {
		return ErrUnknownChallenge
	}
	if now <= 0 || now >= c.ExpiresAt {
		return ErrExpiredChallenge
	}
	if receipt == nil || receipt.Pseudonym == nil || receipt.Pseudonym.Sign() < 0 || receipt.Pseudonym.Cmp(fr.Modulus()) >= 0 {
		return fmt.Errorf("invalid pseudonym")
	}
	for d := 0; d < 3; d++ {
		if receipt.Event[d] < g.task.Lower[d] || receipt.Event[d] > g.task.Upper[d] {
			return fmt.Errorf("event outside the task bounds")
		}
	}
	key := receipt.Pseudonym.String()
	if _, exists := g.usedPseudonyms[key]; exists {
		return ErrDuplicateReport
	}
	// Reconstruct the digest fields from the stored challenge and the actual
	// received report, never from submitter-asserted values.
	cd := baselineChallengeDigest(nonce)
	rd := digestToField(report)
	msg, err := nativeHash(n(domainBaselineReceipt), g.taskF, receipt.Pseudonym, cd, rd, n(int64(receipt.Event[0])), n(int64(receipt.Event[1])), n(int64(receipt.Event[2])))
	if err != nil {
		return err
	}
	var elem fr.Element
	elem.SetBigInt(msg)
	msgBytes := elem.Bytes()
	ok, err := g.issuerPub.Verify(receipt.Signature, msgBytes[:], nativeMiMC.NewMiMC())
	if err != nil || !ok {
		return ErrInvalidReceipt
	}
	delete(g.pending, nonce)
	g.usedPseudonyms[key] = struct{}{}
	return nil
}

// TestProtocolComparisonExperiment compares three arms under one synthetic
// task in one process: the shared-context active circuit, its hidden-context
// candidate, and the trusted-issuer cleartext baseline. Sequential, in-process,
// no network; the same exclusion model as TestEndToEndExperiment applies.
func TestProtocolComparisonExperiment(t *testing.T) {
	value := os.Getenv("EVENT_COMPARISON_RUNS")
	if value == "" {
		t.Skip("set EVENT_COMPARISON_RUNS to run the experiment")
	}
	runs, err := strconv.Atoi(value)
	if err != nil || runs < 1 || runs > 254 {
		t.Fatal("EVENT_COMPARISON_RUNS must be in [1,254]")
	}
	logger.Disable()
	info := func(name string, args ...string) string {
		b, e := exec.Command(name, args...).Output()
		if e != nil {
			return "unavailable"
		}
		return strings.TrimSpace(string(b))
	}
	fmt.Printf("experiment=event-report-protocol-comparison-inprocess-v1\nstarted_utc=%s\n", time.Now().UTC().Format(time.RFC3339Nano))
	fmt.Printf("go=%s os=%s arch=%s logical_cpus=%d gomaxprocs=%d\n", runtime.Version(), runtime.GOOS, runtime.GOARCH, runtime.NumCPU(), runtime.GOMAXPROCS(0))
	fmt.Printf("cpu=%q memory_bytes=%s os_product=%q os_version=%q os_build=%q\n", info("sysctl", "-n", "machdep.cpu.brand_string"), info("sysctl", "-n", "hw.memsize"), info("sw_vers", "-productName"), info("sw_vers", "-productVersion"), info("sw_vers", "-buildVersion"))
	fmt.Printf("modules=%q\n", info("go", "list", "-m", "github.com/consensys/gnark", "github.com/consensys/gnark-crypto"))
	for _, path := range []string{"circuit.go", "native.go", "region.go", "accountability.go", "revocation.go", "gateway.go", "region_gateway.go", "accountability_gateway.go", "active_gateway.go", "transport.go", "kem_transport.go", "context_hiding_candidate_test.go", "context_hiding_extensions_test.go", "protocol_comparison_test.go", "go.mod", "go.sum"} {
		b, e := os.ReadFile(path)
		if e != nil {
			t.Fatalf("read %s: %v", path, e)
		}
		fmt.Printf("source_sha256 file=%s digest=%x\n", path, sha256.Sum256(b))
	}
	fmt.Printf("backend=Groth16 curve=BN254 region_depth=8 region_cells=256 active_depth=8 active_credentials=256 runs=%d warmup=1\n", runs)
	fmt.Println("model=single_process_sequential_synthetic; excludes network, physical event observation, initial key enrollment, setup amortization, trusted clock implementation, disk storage; fixture re-signs credential, issuer certificate and receipt per iteration")
	fmt.Println("round_trips=3_for_all_arms (challenge, issuance, submission)")

	common, err := NewFixture()
	if err != nil {
		t.Fatal(err)
	}
	type participant struct {
		fixture        *Fixture
		identityScalar *big.Int
		identityKey    signature.Signer
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
		identityKey, e := cryptoeddsa.New(tedwards.BN254, rand.Reader)
		if e != nil {
			t.Fatal(e)
		}
		people[i] = participant{f, identityScalar, identityKey}
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
	authorityBytes := common.Authority.Public().Bytes()
	event := [3]uint32{20, 30, 150}

	// ---- ZK arms: shared-context and hidden-context active circuits ----
	type zkArm struct {
		name   string
		hidden bool
		circ   frontend.Circuit
	}
	for _, arm := range []zkArm{{"shared_active", false, &ActiveCircuit{}}, {"hidden_active", true, &hiddenActiveCandidate{}}} {
		start := time.Now()
		ccs, e := frontend.Compile(ecc.BN254.ScalarField(), r1cs.NewBuilder, arm.circ)
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
		gateway, e := NewActiveGateway(authorityBytes, region, auditor, active, 1, vk, recipient)
		if e != nil {
			t.Fatal(e)
		}
		fmt.Printf("ARM %s constraints=%d compile_ns=%d setup_ns=%d\n", arm.name, ccs.GetNbConstraints(), compileNS, setupNS)
		fmt.Println("sample,challenge_ns,encrypt_ns,fixture_sign_and_witness_ns,prove_ns,proof_serialize_ns,gateway_verify_decrypt_dedup_ns,total_to_accept_ns,audit_open_ns,plaintext_bytes,envelope_bytes,proof_bytes,nonce_ascii_bytes,nullifier_bytes,identity_cipher_bytes,component_sum_bytes")
		for i, person := range people {
			plain := []byte(fmt.Sprintf("synthetic vehicular observation %08d", i))
			totalStart := time.Now()
			start = time.Now()
			challenge, e := gateway.Issue(1000, 60)
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
			account, cipher, e := NewAccountabilityAssignment(regionAssignment, person.fixture.Authority, identity, auditor, randomness)
			if e != nil {
				t.Fatal(e)
			}
			full, e := active.Assignment(account)
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
			tag, ok := full.Accountability.Region.Base.Nullifier.(*big.Int)
			if !ok {
				t.Fatal("unexpected nullifier type")
			}
			start = time.Now()
			opened, record, e := gateway.SubmitAndOpen(challenge.Nonce, envelope, tag, cipher, proofBuffer.Bytes(), 1001)
			gatewayNS := time.Since(start).Nanoseconds()
			if e != nil || !bytes.Equal(opened, plain) || record == nil {
				t.Fatalf("gateway sample %d (%s): %v", i, arm.name, e)
			}
			totalNS := time.Since(totalStart).Nanoseconds()
			start = time.Now()
			openedIdentity, e := record.OpenIdentity(auditorSecret)
			auditNS := time.Since(start).Nanoseconds()
			if e != nil || !openedIdentity.Equal(&identity) {
				t.Fatalf("auditor sample %d (%s): %v", i, arm.name, e)
			}
			rBytes, sBytes := cipher.R.Bytes(), cipher.S.Bytes()
			nullifierEncoding := tag.FillBytes(make([]byte, 32))
			cipherBytes := len(rBytes) + len(sBytes)
			componentSum := len(envelope) + proofBuffer.Len() + len(challenge.Nonce) + len(nullifierEncoding) + cipherBytes
			label := strconv.Itoa(i)
			if i == 0 {
				label = "warmup"
			}
			fmt.Printf("%s,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n", label, challengeNS, encryptNS, fixtureNS, proveNS, serializeNS, gatewayNS, totalNS, auditNS, len(plain), len(envelope), proofBuffer.Len(), len(challenge.Nonce), len(nullifierEncoding), cipherBytes, componentSum)
		}
		// Duplicate rejection with a fresh challenge and proof.
		person := people[0]
		challenge, e := gateway.Issue(2000, 60)
		if e != nil {
			t.Fatal(e)
		}
		envelope, e := SealReportMLKEM(recipient.EncapsulationKey(), []byte("second report same task"), task.ID)
		if e != nil {
			t.Fatal(e)
		}
		regionAssignment, e := region.Assignment(person.fixture, challenge, envelope, event, cellIndex)
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
		account, cipher, e := NewAccountabilityAssignment(regionAssignment, person.fixture.Authority, identity, auditor, randomness)
		if e != nil {
			t.Fatal(e)
		}
		full, e := active.Assignment(account)
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
		proof, e := groth16.Prove(ccs, pk, witness)
		if e != nil {
			t.Fatal(e)
		}
		var proofBuffer bytes.Buffer
		if _, e = proof.WriteTo(&proofBuffer); e != nil {
			t.Fatal(e)
		}
		tag, _ := full.Accountability.Region.Base.Nullifier.(*big.Int)
		_, _, dupErr := gateway.SubmitAndOpen(challenge.Nonce, envelope, tag, cipher, proofBuffer.Bytes(), 2001)
		if dupErr != ErrDuplicateReport {
			t.Fatalf("%s duplicate submission: got %v, want ErrDuplicateReport", arm.name, dupErr)
		}
		fmt.Printf("RESULT arm=%s duplicate_nullifier=gateway_rejected\n", arm.name)
	}

	// ---- Trusted-issuer cleartext baseline ----
	issuer, err := NewBaselineIssuer(common.Issuer, task)
	if err != nil {
		t.Fatal(err)
	}
	for _, person := range people {
		issuer.Enroll(person.identityKey.Public())
	}
	baseGW, err := newBaselineGateway(common.Issuer.Public(), task)
	if err != nil {
		t.Fatal(err)
	}
	fmt.Println("ARM trusted_baseline constraints=0 compile_ns=0 setup_ns=0")
	fmt.Println("sample,challenge_ns,request_sign_ns,issuer_verify_and_sign_ns,gateway_verify_dedup_ns,total_to_accept_ns,plaintext_bytes,receipt_bytes,nonce_ascii_bytes,request_bytes,component_sum_bytes")
	for i, person := range people {
		plain := []byte(fmt.Sprintf("synthetic vehicular observation %08d", i))
		totalStart := time.Now()
		start := time.Now()
		challenge, e := baseGW.Issue(1000, 60)
		challengeNS := time.Since(start).Nanoseconds()
		if e != nil {
			t.Fatal(e)
		}
		start = time.Now()
		cd := baselineChallengeDigest(challenge.Nonce)
		rd := digestToField(plain)
		reqMsg, e := baselineRequestMessage(cd, rd, event)
		if e != nil {
			t.Fatal(e)
		}
		var elem fr.Element
		elem.SetBigInt(reqMsg)
		msgBytes := elem.Bytes()
		reqSig, e := person.identityKey.Sign(msgBytes[:], nativeMiMC.NewMiMC())
		requestSignNS := time.Since(start).Nanoseconds()
		if e != nil {
			t.Fatal(e)
		}
		start = time.Now()
		receipt, e := issuer.SignReceipt(person.identityKey.Public(), reqSig, challenge, plain, event)
		issuerNS := time.Since(start).Nanoseconds()
		if e != nil {
			t.Fatal(e)
		}
		start = time.Now()
		e = baseGW.Submit(challenge.Nonce, receipt, plain, 1001)
		gatewayNS := time.Since(start).Nanoseconds()
		if e != nil {
			t.Fatalf("baseline sample %d: %v", i, e)
		}
		totalNS := time.Since(totalStart).Nanoseconds()
		// Receipt wire fields: pseudonym 32 + event 12 + report digest 32 +
		// challenge digest 32 + EdDSA signature 64. Request wire fields:
		// identity public key 32 + request signature 64 + digests 64 + event 12,
		// plus the cleartext report itself, which the issuer must read.
		receiptBytes := 32 + 12 + 32 + 32 + len(receipt.Signature)
		requestBytes := 32 + len(reqSig) + 32 + 32 + 12 + len(plain)
		componentSum := len(plain) + receiptBytes + len(challenge.Nonce)
		label := strconv.Itoa(i)
		if i == 0 {
			label = "warmup"
		}
		fmt.Printf("%s,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n", label, challengeNS, requestSignNS, issuerNS, gatewayNS, totalNS, len(plain), receiptBytes, len(challenge.Nonce), requestBytes, componentSum)
	}
	// Rejection checks use a freshly enrolled identity whose pseudonym has not
	// been consumed by the measured runs.
	checkIdentity, e := cryptoeddsa.New(tedwards.BN254, rand.Reader)
	if e != nil {
		t.Fatal(e)
	}
	issuer.Enroll(checkIdentity.Public())
	challenge, e := baseGW.Issue(2000, 60)
	if e != nil {
		t.Fatal(e)
	}
	plain := []byte("baseline binding check report")
	cd := baselineChallengeDigest(challenge.Nonce)
	rd := digestToField(plain)
	reqMsg, e := baselineRequestMessage(cd, rd, event)
	if e != nil {
		t.Fatal(e)
	}
	var elem fr.Element
	elem.SetBigInt(reqMsg)
	msgBytes := elem.Bytes()
	reqSig, e := checkIdentity.Sign(msgBytes[:], nativeMiMC.NewMiMC())
	if e != nil {
		t.Fatal(e)
	}
	receipt, e := issuer.SignReceipt(checkIdentity.Public(), reqSig, challenge, plain, event)
	if e != nil {
		t.Fatal(e)
	}
	// Tampered report: the gateway recomputes the digest from received bytes.
	if e = baseGW.Submit(challenge.Nonce, receipt, []byte("tampered report"), 2001); e != ErrInvalidReceipt {
		t.Fatalf("baseline tampered report: got %v, want ErrInvalidReceipt", e)
	}
	// Forged signature.
	forged := *receipt
	forged.Signature = append([]byte(nil), receipt.Signature...)
	forged.Signature[0] ^= 0x01
	if e = baseGW.Submit(challenge.Nonce, &forged, plain, 2001); e != ErrInvalidReceipt {
		t.Fatalf("baseline forged signature: got %v, want ErrInvalidReceipt", e)
	}
	// Cross-task receipt: signed under a different task ID.
	otherTask := task
	otherTask.ID = "synthetic-comparison-other-task"
	otherIssuer, e := NewBaselineIssuer(common.Issuer, otherTask)
	if e != nil {
		t.Fatal(e)
	}
	otherIssuer.Enroll(checkIdentity.Public())
	crossReceipt, e := otherIssuer.SignReceipt(checkIdentity.Public(), reqSig, challenge, plain, event)
	if e != nil {
		t.Fatal(e)
	}
	if e = baseGW.Submit(challenge.Nonce, crossReceipt, plain, 2001); e != ErrInvalidReceipt {
		t.Fatalf("baseline cross-task receipt: got %v, want ErrInvalidReceipt", e)
	}
	// Valid submission, then duplicate with a fresh challenge and receipt.
	if e = baseGW.Submit(challenge.Nonce, receipt, plain, 2001); e != nil {
		t.Fatal(e)
	}
	challenge2, e := baseGW.Issue(3000, 60)
	if e != nil {
		t.Fatal(e)
	}
	cd2 := baselineChallengeDigest(challenge2.Nonce)
	reqMsg2, e := baselineRequestMessage(cd2, rd, event)
	if e != nil {
		t.Fatal(e)
	}
	elem.SetBigInt(reqMsg2)
	msgBytes2 := elem.Bytes()
	reqSig2, e := checkIdentity.Sign(msgBytes2[:], nativeMiMC.NewMiMC())
	if e != nil {
		t.Fatal(e)
	}
	receipt2, e := issuer.SignReceipt(checkIdentity.Public(), reqSig2, challenge2, plain, event)
	if e != nil {
		t.Fatal(e)
	}
	if e = baseGW.Submit(challenge2.Nonce, receipt2, plain, 3001); e != ErrDuplicateReport {
		t.Fatalf("baseline duplicate pseudonym: got %v, want ErrDuplicateReport", e)
	}
	// Revocation is issuer-side only: after removal the issuer refuses, but a
	// receipt signed before revocation still verifies at the gateway.
	issuer.Revoke(checkIdentity.Public())
	if _, e = issuer.SignReceipt(checkIdentity.Public(), reqSig2, challenge2, plain, event); e == nil {
		t.Fatal("baseline issuer accepted a revoked identity")
	}
	fmt.Println("RESULT arm=trusted_baseline tampered_report=rejected forged_signature=rejected cross_task_receipt=rejected duplicate_pseudonym=gateway_rejected revoked_identity=issuer_refused pre_revocation_receipt=gateway_still_valid")
	// Cross-task linkability: the issuer derives the same participant's
	// pseudonyms under two tasks and matches them to submitted receipts.
	pA, e := issuer.Pseudonym(checkIdentity.Public(), task)
	if e != nil {
		t.Fatal(e)
	}
	pB, e := issuer.Pseudonym(checkIdentity.Public(), otherTask)
	if e != nil {
		t.Fatal(e)
	}
	if pA.Cmp(receipt.Pseudonym) != 0 || pB.Cmp(crossReceipt.Pseudonym) != 0 {
		t.Fatal("issuer pseudonym derivation mismatch")
	}
	fmt.Println("RESULT arm=trusted_baseline issuer_cross_task_link=2/2 (issuer knows identity keys and can derive every task pseudonym)")
	fmt.Println("STRUCTURE arm=shared_active issuer_input_bytes=76 (context 32, holder 32, event 12); issuer cannot compute task tags without the participant secret")
	fmt.Println("STRUCTURE arm=hidden_active issuer_input_bytes=44 (holder 32, event 12); issuer receives no context, challenge, task ID, policy box or report bytes")
	fmt.Println("STRUCTURE arm=trusted_baseline issuer sees identity key, full report and exact event; gateway sees cleartext event and per-task pseudonym; revocation checkable only at the issuer; no auditable anonymity, no region-membership or active-credential proof at the gateway")
	fmt.Println("SCOPE synthetic in-process comparison; no deployed issuers, no network; baseline has no ZK relation, so constraint/prove columns are zero by construction")
	fmt.Printf("completed_utc=%s\n", time.Now().UTC().Format(time.RFC3339Nano))
}