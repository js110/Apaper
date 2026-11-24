package eventreport

import (
	"bytes"
	"crypto/mlkem"
	"crypto/rand"
	"crypto/sha256"
	"encoding/binary"
	"errors"
	"fmt"
	"math/big"
	"os"
	"os/exec"
	"runtime"
	"sort"
	"strconv"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/cloudflare/circl/oprf"
	"github.com/consensys/gnark-crypto/ecc"
	"github.com/consensys/gnark-crypto/ecc/bn254/fr"
	nativeMiMC "github.com/consensys/gnark-crypto/ecc/bn254/fr/mimc"
	tedwards "github.com/consensys/gnark-crypto/ecc/twistededwards"
	"github.com/consensys/gnark-crypto/signature"
	cryptoeddsa "github.com/consensys/gnark-crypto/signature/eddsa"
	"github.com/consensys/gnark/backend/groth16"
	"github.com/consensys/gnark/frontend"
	"github.com/consensys/gnark/frontend/cs/r1cs"
	"github.com/consensys/gnark/logger"
	bbs "github.com/trustbloc/bbs-signature-go/bbs12381g2pub"
)

// Non-SNARK anonymous baselines required by review point 7. Two arms replace the
// Groth16 relation with a standard anonymous-credential or anonymous-token
// mechanism and keep everything else identical to TestProtocolComparisonExperiment:
// the same synthetic task, the same three participant roles, the same
// gateway-side challenge state, and the same report envelope.
//
//   - bbs_credential: BBS+ signatures on BLS12-381 (draft-irtf-cfrg-bbs-signatures
//     family, eprint 2016/663 construction). A trusted institution authenticates the
//     participant, checks the event against the task bounds, and signs eight
//     attributes. The participant discloses seven of them in a randomized
//     presentation, so the gateway gets an unforgeable event assertion and can bind
//     the disclosure to the bytes it actually received, without a circuit or a
//     trusted setup.
//   - privacy_pass: Privacy Pass privately verifiable tokens, token type 0x0001 =
//     VOPRF(P-384, SHA-384) as specified in RFC 9578 section 5 with the HTTP
//     structure of RFC 9577. The issuer never sees the challenge, so issuance is
//     stronger on issuer visibility than any other arm; verification needs the
//     issuer private key, so the gateway cannot redeem on its own.
//
// Both arms are research harnesses, not deployments, and both use different
// curves from the zero-knowledge arm (BLS12-381 / P-384 versus BN254), so the
// timings compare mechanisms, not curves.
const (
	domainNonSnarkNickname  = 601
	domainNonSnarkRequest   = 602
	domainNonSnarkChallenge = 603
)

var errNonSnarkRedeemed = errors.New("token already redeemed")

// ---------- BBS+ anonymous-credential arm ----------

// Attribute layout of the credential. Index 0 stays hidden so that two
// presentations by the same participant are unlinkable to the gateway; the
// remaining seven are disclosed because the gateway needs them to reject
// replays, to enforce the task scope, and to bind the disclosure to the
// received report bytes.
const (
	bbsAttrSerial = iota
	bbsAttrNickname
	bbsAttrTask
	bbsAttrChallenge
	bbsAttrEventX
	bbsAttrEventY
	bbsAttrEventT
	bbsAttrReport
	bbsAttributeCount
)

var bbsDisclosed = []int{bbsAttrNickname, bbsAttrTask, bbsAttrChallenge, bbsAttrEventX, bbsAttrEventY, bbsAttrEventT, bbsAttrReport}

func bbe32(v uint32) []byte {
	out := make([]byte, 32)
	binary.BigEndian.PutUint64(out[24:], uint64(v))
	return out
}

// BBSIssuer is the trusted institution: it authenticates the participant,
// asserts the event, and signs the attribute vector.
type BBSIssuer struct {
	scheme   *bbs.BBSG2Pub
	pub      []byte
	priv     []byte
	task     Task
	taskF    *big.Int
	enrolled map[string]signature.PublicKey
	issued   map[string]struct{}
}

func newBBSIssuer(task Task) (*BBSIssuer, error) {
	if err := task.Validate(); err != nil {
		return nil, err
	}
	tf, err := TaskField(task)
	if err != nil {
		return nil, err
	}
	pub, priv, err := bbs.GenerateKeyPair(sha256.New, nil)
	if err != nil {
		return nil, err
	}
	privBytes, err := priv.Marshal()
	if err != nil {
		return nil, err
	}
	pubBytes, err := pub.Marshal()
	if err != nil {
		return nil, err
	}
	return &BBSIssuer{scheme: bbs.New(), pub: pubBytes, priv: privBytes, task: task, taskF: tf,
		enrolled: make(map[string]signature.PublicKey), issued: make(map[string]struct{})}, nil
}

func (i *BBSIssuer) Enroll(identity signature.PublicKey) {
	i.enrolled[string(identity.Bytes())] = identity
}

func (i *BBSIssuer) Revoke(identity signature.PublicKey) {
	delete(i.enrolled, string(identity.Bytes()))
}

// Nickname is the per-task handle the gateway deduplicates on. It is derived
// from the identity public key, which the issuer knows, so the issuer can
// compute it for every task.
func (i *BBSIssuer) nickname(identityPub []byte, task Task) ([]byte, error) {
	tf, err := TaskField(task)
	if err != nil {
		return nil, err
	}
	h, err := nativeHash(n(domainNonSnarkNickname), digestToField(identityPub), tf)
	if err != nil {
		return nil, err
	}
	return fieldBytes(h), nil
}

// fieldBytes serialises a scalar field element as the 32 big-endian bytes the
// credential attributes use.
func fieldBytes(v *big.Int) []byte {
	var elem fr.Element
	elem.SetBigInt(v)
	out := elem.Bytes()
	return out[:]
}

func nonSnarkChallengeDigest(nonce string) []byte {
	sum := sha256.Sum256([]byte(nonce))
	return sum[:]
}

func bbsRequestMessage(challengeDigest, reportDigest []byte, event [3]uint32) (*big.Int, error) {
	return nativeHash(n(domainNonSnarkRequest), digestToField(challengeDigest), digestToField(reportDigest),
		n(int64(event[0])), n(int64(event[1])), n(int64(event[2])))
}

// Issue authenticates the request, checks enrollment, bounds, and the one
// credential per task quota, then signs the attributes.
func (i *BBSIssuer) Issue(identity signature.PublicKey, requestSig []byte, challenge Challenge, reportDigest []byte, event [3]uint32) ([][]byte, []byte, error) {
	if _, ok := i.enrolled[string(identity.Bytes())]; !ok {
		return nil, nil, errors.New("identity not enrolled or revoked")
	}
	if err := challenge.Validate(); err != nil {
		return nil, nil, err
	}
	for d := 0; d < 3; d++ {
		if event[d] < i.task.Lower[d] || event[d] > i.task.Upper[d] {
			return nil, nil, errors.New("event outside the task bounds")
		}
	}
	cd := nonSnarkChallengeDigest(challenge.Nonce)
	reqMsg, err := bbsRequestMessage(cd, reportDigest, event)
	if err != nil {
		return nil, nil, err
	}
	var elem fr.Element
	elem.SetBigInt(reqMsg)
	msgBytes := elem.Bytes()
	okSig, err := identity.Verify(requestSig, msgBytes[:], nativeMiMC.NewMiMC())
	if err != nil || !okSig {
		return nil, nil, errors.New("request signature invalid")
	}
	nick, err := i.nickname(identity.Bytes(), i.task)
	if err != nil {
		return nil, nil, err
	}
	if _, exists := i.issued[string(nick)]; exists {
		return nil, nil, errors.New("nickname already issued for this task")
	}
	i.issued[string(nick)] = struct{}{}
	serial := make([]byte, 32)
	if _, err := rand.Read(serial); err != nil {
		return nil, nil, err
	}
	attrs := [][]byte{
		serial,
		nick,
		fieldBytes(i.taskF),
		cd,
		bbe32(event[0]),
		bbe32(event[1]),
		bbe32(event[2]),
		reportDigest,
	}
	sig, err := i.scheme.Sign(attrs, i.priv)
	if err != nil {
		return nil, nil, err
	}
	return attrs, sig, nil
}

// BBSGateway verifies presentations with the issuer public key only, binds them
// to the report bytes it received, and deduplicates on the disclosed nickname.
type BBSGateway struct {
	mu          sync.Mutex
	scheme      *bbs.BBSG2Pub
	issuerPub   []byte
	task        Task
	taskF       *big.Int
	pending     map[string]Challenge
	usedNick    map[string]struct{}
	acceptedIdx map[string]struct{}
}

func newBBSGateway(issuerPub []byte, task Task) (*BBSGateway, error) {
	if err := task.Validate(); err != nil {
		return nil, err
	}
	tf, err := TaskField(task)
	if err != nil {
		return nil, err
	}
	return &BBSGateway{scheme: bbs.New(), issuerPub: issuerPub, task: task, taskF: tf,
		pending: make(map[string]Challenge), usedNick: make(map[string]struct{}),
		acceptedIdx: make(map[string]struct{})}, nil
}

func (g *BBSGateway) Issue(now, ttl int64) (Challenge, error) {
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

// disclosedFor rebuilds the disclosed attribute list for a challenge, a report
// digest, and an event, in ascending index order as VerifyProof expects.
// Submit is the gateway acceptance path: freshness, a BBS+ presentation check
// under the issuer public key, the report-byte binding, and nickname dedup.
func (g *BBSGateway) Submit(nonce string, presentation []byte, attrs [][]byte, report []byte, now int64) error {
	g.mu.Lock()
	defer g.mu.Unlock()
	c, exists := g.pending[nonce]
	if !exists {
		return ErrUnknownChallenge
	}
	if now <= 0 || now >= c.ExpiresAt {
		return ErrExpiredChallenge
	}
	if len(attrs) != len(bbsDisclosed) {
		return errors.New("disclosed attribute count mismatch")
	}
	if !bytes.Equal(attrs[1], fieldBytes(g.taskF)) {
		return errors.New("credential bound to another task")
	}
	if !bytes.Equal(attrs[2], nonSnarkChallengeDigest(nonce)) {
		return errors.New("presentation bound to another challenge")
	}
	event := [3]uint32{
		uint32(binary.BigEndian.Uint64(attrs[3][24:])),
		uint32(binary.BigEndian.Uint64(attrs[4][24:])),
		uint32(binary.BigEndian.Uint64(attrs[5][24:])),
	}
	for d := 0; d < 3; d++ {
		if event[d] < g.task.Lower[d] || event[d] > g.task.Upper[d] {
			return errors.New("event outside the task bounds")
		}
	}
	// The binding to the received bytes: the gateway digests what it actually
	// got and requires the issuer-signed attribute to be equal.
	if !bytes.Equal(attrs[6], reportDigestOf(report)) {
		return errors.New("report digest does not match the received report")
	}
	key := string(attrs[0])
	if _, seen := g.usedNick[key]; seen {
		return ErrDuplicateReport
	}
	if err := g.scheme.VerifyProof(attrs, presentation, attrs[2], g.issuerPub); err != nil {
		return err
	}
	delete(g.pending, nonce)
	g.usedNick[key] = struct{}{}
	g.acceptedIdx[key+nonce] = struct{}{}
	return nil
}

func reportDigestOf(report []byte) []byte {
	sum := sha256.Sum256(report)
	return sum[:]
}

// ---------- Privacy Pass token arm (RFC 9578 section 5, token type 0x0001) ----------

const (
	ppTokenType       = 0x0001
	ppNonceBytes      = 32
	ppDigestBytes     = 32
	ppKeyIDBytes      = 32
	ppAuthenticatorNb = 48 // Nk for VOPRF(P-384, SHA-384)
)

type PPIssuer struct {
	suite    oprf.Suite
	server   oprf.VerifiableServer
	public   []byte
	keyID    []byte
	redeemed map[string]struct{}
	metadata []byte // cleartext the redeemer must read to bind a report
}

func newPPIssuer() (*PPIssuer, error) {
	suite := oprf.SuiteP384
	seed := make([]byte, 32)
	if _, err := rand.Read(seed); err != nil {
		return nil, err
	}
	// RFC 9578 section 5.5 derives the key pair from a seed with the
	// "PrivacyPass" information string; circl's DeriveKey takes a 32-byte seed.
	skI, err := oprf.DeriveKey(suite, oprf.VerifiableMode, seed, []byte("PrivacyPass"))
	if err != nil {
		return nil, err
	}
	pkBytes, err := skI.Public().MarshalBinary()
	if err != nil {
		return nil, err
	}
	sum := sha256.Sum256(pkBytes)
	return &PPIssuer{suite: suite, server: oprf.NewVerifiableServer(suite, skI), public: pkBytes,
		keyID: sum[:], redeemed: make(map[string]struct{})}, nil
}

func ppTokenInput(nonce []byte, challengeDigest []byte, keyID []byte) []byte {
	out := binary.BigEndian.AppendUint16(nil, ppTokenType)
	out = append(out, nonce...)
	out = append(out, challengeDigest...)
	out = append(out, keyID...)
	return out
}

// PPGateway holds the issuer public key only, as a Privacy Pass Origin does.
type PPGateway struct {
	mu         sync.Mutex
	keyID      []byte
	pending    map[string]Challenge
	used       map[string]struct{}
	currentNow int64
}

func newPPGateway(keyID []byte) *PPGateway {
	return &PPGateway{keyID: keyID, pending: make(map[string]Challenge), used: make(map[string]struct{})}
}

func (g *PPGateway) Issue(now, ttl int64) (Challenge, error) {
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

// CheckFields is everything an Origin can do without the issuer private key:
// parse the token and compare the fields it recomputes from its own challenge.
// It accepts a forged authenticator, which is why redemption needs the issuer.
func (g *PPGateway) CheckFields(nonce string, token []byte) error {
	g.mu.Lock()
	defer g.mu.Unlock()
	c, exists := g.pending[nonce]
	if !exists {
		return ErrUnknownChallenge
	}
	if g.currentNow <= 0 || g.currentNow >= c.ExpiresAt {
		return ErrExpiredChallenge
	}
	if len(token) != 2+ppNonceBytes+ppDigestBytes+ppKeyIDBytes+ppAuthenticatorNb {
		return errors.New("malformed token")
	}
	if binary.BigEndian.Uint16(token[:2]) != ppTokenType {
		return errors.New("unsupported token type")
	}
	if !bytes.Equal(token[2+ppNonceBytes+ppDigestBytes:2+ppNonceBytes+ppDigestBytes+ppKeyIDBytes], g.keyID) {
		return errors.New("unknown token key")
	}
	if !bytes.Equal(token[2+ppNonceBytes:2+ppNonceBytes+ppDigestBytes], nonSnarkChallengeDigest(nonce)) {
		return errors.New("token bound to another challenge")
	}
	key := fmt.Sprintf("%x", token[2:2+ppNonceBytes])
	if _, seen := g.used[key]; seen {
		return ErrDuplicateReport
	}
	return nil
}

// MarkUsed records a token the issuer has just redeemed. Without this callback
// the Origin has no single-use state of its own, which is what the replay
// measurement below exercises.
func (g *PPGateway) MarkUsed(token []byte) {
	g.mu.Lock()
	defer g.mu.Unlock()
	g.used[fmt.Sprintf("%x", token[2:2+ppNonceBytes])] = struct{}{}
}

// Redeem is the issuer-side redemption RPC: it verifies the authenticator under
// the issuer private key and enforces single use.
func (i *PPIssuer) Redeem(nonce string, token []byte, publicMetadata []byte) error {
	input := ppTokenInput(token[2:2+ppNonceBytes], token[2+ppNonceBytes:2+ppNonceBytes+ppDigestBytes], token[2+ppNonceBytes+ppDigestBytes:2+ppNonceBytes+ppDigestBytes+ppKeyIDBytes])
	authenticator := token[len(token)-ppAuthenticatorNb:]
	if !i.server.VerifyFinalize(input, authenticator) {
		return errors.New("token authenticator invalid")
	}
	key := fmt.Sprintf("%x", token[2:len(token)])
	if _, seen := i.redeemed[key]; seen {
		return errNonSnarkRedeemed
	}
	// The Origin forwards the cleartext metadata that carries the event and the
	// report digest, because the token itself binds to nothing else.
	i.metadata = append(i.metadata, publicMetadata...)
	i.redeemed[key] = struct{}{}
	return nil
}

// ---------- the experiment ----------

func TestNonSnarkAnonymousBaseline(t *testing.T) {
	value := os.Getenv("EVENT_NONSNARK_RUNS")
	if value == "" {
		t.Skip("set EVENT_NONSNARK_RUNS to run the experiment")
	}
	runs, err := strconv.Atoi(value)
	if err != nil || runs < 1 || runs > 254 {
		t.Fatal("EVENT_NONSNARK_RUNS must be in [1,254]")
	}
	logger.Disable()
	info := func(name string, args ...string) string {
		b, e := exec.Command(name, args...).Output()
		if e != nil {
			return "unavailable"
		}
		return strings.TrimSpace(string(b))
	}
	fmt.Printf("experiment=event-report-nonsnark-anonymous-inprocess-v1\nstarted_utc=%s\n", time.Now().UTC().Format(time.RFC3339Nano))
	fmt.Printf("go=%s os=%s arch=%s logical_cpus=%d gomaxprocs=%d\n", runtime.Version(), runtime.GOOS, runtime.GOARCH, runtime.NumCPU(), runtime.GOMAXPROCS(0))
	fmt.Printf("cpu=%q memory_bytes=%s os_product=%q os_version=%q os_build=%q\n", info("sysctl", "-n", "machdep.cpu.brand_string"), info("sysctl", "-n", "hw.memsize"), info("sw_vers", "-productName"), info("sw_vers", "-productVersion"), info("sw_vers", "-buildVersion"))
	fmt.Printf("modules=%q\n", info("go", "list", "-m", "github.com/consensys/gnark", "github.com/consensys/gnark-crypto", "github.com/cloudflare/circl", "github.com/trustbloc/bbs-signature-go"))
	for _, path := range []string{"circuit.go", "native.go", "region.go", "accountability.go", "revocation.go", "gateway.go", "region_gateway.go", "accountability_gateway.go", "active_gateway.go", "transport.go", "kem_transport.go", "context_hiding_candidate_test.go", "context_hiding_extensions_test.go", "protocol_comparison_test.go", "nonsnark_baseline_test.go", "go.mod", "go.sum"} {
		b, e := os.ReadFile(path)
		if e != nil {
			t.Fatalf("read %s: %v", path, e)
		}
		fmt.Printf("source_sha256 file=%s digest=%x\n", path, sha256.Sum256(b))
	}
	fmt.Printf("backend=Groth16 curve=BN254 curve_bbs=BLS12-381 curve_pp=P-384-SHA384 region_depth=8 region_cells=256 active_depth=8 active_credentials=256 runs=%d warmup=1\n", runs)
	fmt.Println("model=single_process_sequential_synthetic; excludes network, physical event observation, initial key enrollment, setup amortization, trusted clock implementation, disk storage; every arm re-signs credential, issuer certificate and receipt per iteration")
	fmt.Println("round_trips=3_for_zk_bbs_and_trusted_arms, 4_for_privacy_pass (challenge, issuance, submission, issuer redemption RPC)")

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
	task := Task{ID: "synthetic-nonsnark-task", Lower: [3]uint32{10, 20, 100}, Upper: [3]uint32{30, 50, 200}}
	otherTask := Task{ID: "synthetic-nonsnark-task-b", Lower: [3]uint32{10, 20, 100}, Upper: [3]uint32{30, 50, 200}}
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
	reportFor := func(i int) []byte { return []byte(fmt.Sprintf("synthetic vehicular observation %08d", i)) }

	// ---- Arm 1: hidden-context Groth16 relation (the paper's scheme) ----
	{
		start := time.Now()
		ccs, e := frontend.Compile(ecc.BN254.ScalarField(), r1cs.NewBuilder, &hiddenActiveCandidate{})
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
		fmt.Printf("ARM hidden_active constraints=%d compile_ns=%d setup_ns=%d\n", ccs.GetNbConstraints(), compileNS, setupNS)
		fmt.Println("sample,challenge_ns,encrypt_ns,sign_and_witness_ns,prove_ns,gateway_verify_decrypt_dedup_ns,total_to_accept_ns,plaintext_bytes,envelope_bytes,proof_bytes,nonce_ascii_bytes,component_sum_bytes")
		totals := make([]int64, 0, runs)
		for i, person := range people {
			plain := reportFor(i)
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
			if e = resignHiddenReceipt(person.fixture, &regionAssignment.Base); e != nil {
				t.Fatal(e)
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
			assignment := hiddenActiveFrom(full)
			witness, e := frontend.NewWitness(assignment, ecc.BN254.ScalarField())
			if e != nil {
				t.Fatal(e)
			}
			signNS := time.Since(start).Nanoseconds()
			start = time.Now()
			proof, e := groth16.Prove(ccs, pk, witness)
			proveNS := time.Since(start).Nanoseconds()
			if e != nil {
				t.Fatal(e)
			}
			var proofBuffer bytes.Buffer
			if _, e = proof.WriteTo(&proofBuffer); e != nil {
				t.Fatal(e)
			}
			tag, ok := full.Accountability.Region.Base.Nullifier.(*big.Int)
			if !ok {
				t.Fatal("unexpected nullifier type")
			}
			start = time.Now()
			opened, record, e := gateway.SubmitAndOpen(challenge.Nonce, envelope, tag, cipher, proofBuffer.Bytes(), 1001)
			gatewayNS := time.Since(start).Nanoseconds()
			if e != nil || !bytes.Equal(opened, plain) || record == nil {
				t.Fatalf("gateway sample %d (hidden_active): %v", i, e)
			}
			totalNS := time.Since(totalStart).Nanoseconds()
			cipherBytes := len(cipher.R.Bytes()) + len(cipher.S.Bytes())
			label := strconv.Itoa(i)
			if i == 0 {
				label = "warmup"
			} else {
				totals = append(totals, totalNS)
			}
			fmt.Printf("%s,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n", label, challengeNS, encryptNS, signNS, proveNS, gatewayNS, totalNS,
				len(plain), len(envelope), proofBuffer.Len(), len(challenge.Nonce),
				len(envelope)+proofBuffer.Len()+len(challenge.Nonce)+32+cipherBytes)
		}
		fmt.Printf("STAT arm=hidden_active median_total_to_accept_ns=%d\n", medianNS(totals))
	}

	// ---- Arm 2: BBS+ anonymous credential ----
	{
		issuer, e := newBBSIssuer(task)
		if e != nil {
			t.Fatal(e)
		}
		issuerB, e := newBBSIssuer(otherTask)
		if e != nil {
			t.Fatal(e)
		}
		for _, person := range people {
			issuer.Enroll(person.identityKey.Public())
			issuerB.Enroll(person.identityKey.Public())
		}
		gw, e := newBBSGateway(issuer.pub, task)
		if e != nil {
			t.Fatal(e)
		}
		fmt.Printf("ARM bbs_credential constraints=0 compile_ns=0 setup_ns=0 curve=BLS12-381 attributes=%d disclosed=%d issuer_pub_bytes=%d\n",
			bbsAttributeCount, len(bbsDisclosed), len(issuer.pub))
		fmt.Println("sample,challenge_ns,request_sign_ns,issuer_verify_and_sign_ns,derive_presentation_ns,gateway_verify_dedup_ns,total_to_accept_ns,plaintext_bytes,credential_bytes,presentation_bytes,disclosed_bytes,envelope_bytes,nonce_ascii_bytes,issuer_request_bytes,component_sum_bytes")
		totals := make([]int64, 0, runs)
		for i, person := range people {
			plain := reportFor(i)
			rd := reportDigestOf(plain)
			totalStart := time.Now()
			start := time.Now()
			challenge, e := gw.Issue(1000, 60)
			challengeNS := time.Since(start).Nanoseconds()
			if e != nil {
				t.Fatal(e)
			}
			start = time.Now()
			cd := nonSnarkChallengeDigest(challenge.Nonce)
			reqMsg, e := bbsRequestMessage(cd, rd, event)
			if e != nil {
				t.Fatal(e)
			}
			var elem fr.Element
			elem.SetBigInt(reqMsg)
			reqBytes := elem.Bytes()
			requestSig, e := person.identityKey.Sign(reqBytes[:], nativeMiMC.NewMiMC())
			if e != nil {
				t.Fatal(e)
			}
			// Issuance request wire: identity public key 32 + request signature
			// 64 + challenge digest 32 + report digest 32 + event 12. The issuer
			// never receives the report bytes themselves, only their digest.
			requestTotal := 32 + len(requestSig) + 32 + 32 + 12
			requestSignNS := time.Since(start).Nanoseconds()
			start = time.Now()
			attrs, credential, e := issuer.Issue(person.identityKey.Public(), requestSig, challenge, rd, event)
			if e != nil {
				t.Fatal(e)
			}
			issuerNS := time.Since(start).Nanoseconds()
			start = time.Now()
			presentation, e := issuer.scheme.DeriveProof(attrs, credential, cd, issuer.pub, bbsDisclosed)
			if e != nil {
				t.Fatal(e)
			}
			deriveNS := time.Since(start).Nanoseconds()
			disclosed := make([][]byte, 0, len(bbsDisclosed))
			for _, idx := range bbsDisclosed {
				disclosed = append(disclosed, attrs[idx])
			}
			envelope, e := SealReportMLKEM(recipient.EncapsulationKey(), plain, task.ID)
			if e != nil {
				t.Fatal(e)
			}
			start = time.Now()
			if e := gw.Submit(challenge.Nonce, presentation, disclosed, plain, 1001); e != nil {
				t.Fatalf("bbs gateway sample %d: %v", i, e)
			}
			gatewayNS := time.Since(start).Nanoseconds()
			totalNS := time.Since(totalStart).Nanoseconds()
			label := strconv.Itoa(i)
			if i == 0 {
				label = "warmup"
			} else {
				totals = append(totals, totalNS)
			}
			fmt.Printf("%s,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n", label, challengeNS, requestSignNS, issuerNS, deriveNS, gatewayNS, totalNS,
				len(plain), len(credential), len(presentation), 32*len(bbsDisclosed), len(envelope), len(challenge.Nonce), requestTotal,
				len(presentation)+32*len(bbsDisclosed)+len(challenge.Nonce))
		}
		fmt.Printf("STAT arm=bbs_credential median_total_to_accept_ns=%d\n", medianNS(totals))

		// Rejection behaviour uses fresh identities the measured runs never touched,
		// because this arm allows one credential per nickname per task.
		type bbsBundle struct {
			nonce        string
			presentation []byte
			disclosed    [][]byte
			plain        []byte
		}
		newSubmission := func(iss *BBSIssuer, g *BBSGateway, key signature.Signer, reportText string, ev [3]uint32, now int64) (*bbsBundle, error) {
			challenge, e := g.Issue(now, 60)
			if e != nil {
				return nil, e
			}
			plain := []byte(reportText)
			rd := reportDigestOf(plain)
			cd := nonSnarkChallengeDigest(challenge.Nonce)
			reqMsg, e := bbsRequestMessage(cd, rd, ev)
			if e != nil {
				return nil, e
			}
			var elem fr.Element
			elem.SetBigInt(reqMsg)
			reqBytes := elem.Bytes()
			sig, e := key.Sign(reqBytes[:], nativeMiMC.NewMiMC())
			if e != nil {
				return nil, e
			}
			attrs, credential, e := iss.Issue(key.Public(), sig, challenge, rd, ev)
			if e != nil {
				return nil, e
			}
			presentation, e := iss.scheme.DeriveProof(attrs, credential, cd, iss.pub, bbsDisclosed)
			if e != nil {
				return nil, e
			}
			disclosed := make([][]byte, 0, len(bbsDisclosed))
			for _, idx := range bbsDisclosed {
				disclosed = append(disclosed, attrs[idx])
			}
			return &bbsBundle{challenge.Nonce, presentation, disclosed, plain}, nil
		}
		first, e := cryptoeddsa.New(tedwards.BN254, rand.Reader)
		if e != nil {
			t.Fatal(e)
		}
		second, e := cryptoeddsa.New(tedwards.BN254, rand.Reader)
		if e != nil {
			t.Fatal(e)
		}
		for _, iss := range []*BBSIssuer{issuer, issuerB} {
			iss.Enroll(first.Public())
			iss.Enroll(second.Public())
		}
		bundle, e := newSubmission(issuer, gw, first, "bbs rejection check report", event, 2000)
		if e != nil {
			t.Fatal(e)
		}
		var validErr error
		// Every rejection case derives its own presentation and is verified once: the
		// BBS+ library mutates shared generator state, so re-verifying one
		// presentation is not deterministic (quantified by the probe below). The
		// checks that reuse bundle.nonce must run before any later Issue call, which
		// prunes expired challenges from the pending map.
		tampered := make([][]byte, len(bundle.disclosed))
		copy(tampered, bundle.disclosed)
		tampered[6] = reportDigestOf([]byte("different report"))
		tamperErr := gw.Submit(bundle.nonce, bundle.presentation, tampered, bundle.plain, 2001)
		mismatchErr := gw.Submit(bundle.nonce, bundle.presentation, bundle.disclosed, []byte("other bytes on the wire"), 2002)
		// The untampered presentation on the untampered report must be accepted.
		validErr = gw.Submit(bundle.nonce, bundle.presentation, bundle.disclosed, bundle.plain, 2003)
		// The presentation with a forged nickname is derived separately.
		bundleForged, e := newSubmission(issuer, gw, second, "bbs forged nickname report", event, 2200)
		if e != nil {
			t.Fatal(e)
		}
		forged := make([][]byte, len(bundleForged.disclosed))
		copy(forged, bundleForged.disclosed)
		forged[0] = bbe32(4242)
		forgedErr := gw.Submit(bundleForged.nonce, bundleForged.presentation, forged, bundleForged.plain, 2201)
		// A second credential for the same nickname inside the same task.
		_, quotaErr := newSubmission(issuer, gw, first, "second credential same task", event, 3000)
		// A credential signed for another task must not be presentable here.
		cross, e := newSubmission(issuerB, gw, second, "credential of another task", event, 3100)
		crossTaskErr := error(nil)
		if e == nil {
			crossTaskErr = gw.Submit(cross.nonce, cross.presentation, cross.disclosed, cross.plain, 3101)
		} else {
			crossTaskErr = e
		}
		// Revocation: an accepted record stays accepted, because the gateway has no
		// issuer-side state to consult.
		third, e := cryptoeddsa.New(tedwards.BN254, rand.Reader)
		if e != nil {
			t.Fatal(e)
		}
		for _, iss := range []*BBSIssuer{issuer, issuerB} {
			iss.Enroll(third.Public())
		}
		bundle2, e := newSubmission(issuer, gw, third, "bbs revocation check report", event, 4000)
		if e != nil {
			t.Fatal(e)
		}
		if e := gw.Submit(bundle2.nonce, bundle2.presentation, bundle2.disclosed, bundle2.plain, 4001); e != nil {
			t.Fatalf("bbs valid submission for the revocation check: %v", e)
		}
		acceptedBefore := len(gw.acceptedIdx)
		issuer.Revoke(third.Public())
		_, revokedErr := newSubmission(issuer, gw, third, "post revocation", event, 5000)
		// The issuer knows the identity public key, so it derives the nickname of
		// any task and matches it against the gateway records it observes.
		nickA, e := issuer.nickname(third.Public().Bytes(), task)
		if e != nil {
			t.Fatal(e)
		}
		nickB, e := issuerB.nickname(third.Public().Bytes(), otherTask)
		if e != nil {
			t.Fatal(e)
		}
		matchesGateway := bytes.Equal(nickA, bundle2.disclosed[0]) && !bytes.Equal(nickA, nickB)
		fmt.Printf("RESULT arm=bbs_credential tampered_report=%v forged_nickname=%v report_mismatch=%v valid_submission=%v second_credential_same_task=%v cross_task_credential=%v revoked_identity=%v revoked_record_retained_at_gateway=%v issuer_nickname_matches_gateway=%v issuer_other_task_nickname=derived accepted_records=%d\n",
			errLabel(tamperErr), errLabel(forgedErr), errLabel(mismatchErr), errLabel(validErr), errLabel(quotaErr), errLabel(crossTaskErr), errLabel(revokedErr), acceptedBefore <= len(gw.acceptedIdx), matchesGateway, acceptedBefore)
		// Determinism probe: the BBS+ library mutates shared point state, so a
		// presentation verified twice in the same process can flip its outcome.
		// Every measured submission derives its own presentation and is verified
		// once; this probe records what a second verification would do.
		repeatAgree, repeatTotal := 0, 5
		for k := 0; k < repeatTotal; k++ {
			probeKey, e := cryptoeddsa.New(tedwards.BN254, rand.Reader)
			if e != nil {
				t.Fatal(e)
			}
			issuer.Enroll(probeKey.Public())
			probe, e := newSubmission(issuer, gw, probeKey, fmt.Sprintf("determinism probe %d", k), event, int64(6000+60*k))
			if e != nil {
				t.Fatal(e)
			}
			firstErr := issuer.scheme.VerifyProof(probe.disclosed, probe.presentation, probe.disclosed[2], issuer.pub)
			secondErr := issuer.scheme.VerifyProof(probe.disclosed, probe.presentation, probe.disclosed[2], issuer.pub)
			if (firstErr == nil) == (secondErr == nil) {
				repeatAgree++
			}
		}
		fmt.Printf("RESULT arm=bbs_credential reverify_same_presentation_agrees=%dof%d (library mutates shared generator state across VerifyProof calls)\n", repeatAgree, repeatTotal)
		fmt.Println("STRUCTURE arm=bbs_credential issuer sees identity key, challenge, exact event and report digest; gateway sees the exact event in cleartext and a task-scoped nickname; presentation is untraceable inside the task set; no active-set membership proof at the gateway; revocation enforced only at issuance")
	}

	// ---- Arm 3: Privacy Pass privately verifiable tokens ----
	{
		issuer, e := newPPIssuer()
		if e != nil {
			t.Fatal(e)
		}
		gw := newPPGateway(issuer.keyID)
		client := oprf.NewVerifiableClient(issuer.suite, issuer.server.PublicKey())
		params := issuer.suite.Group().Params()
		fmt.Printf("ARM privacy_pass constraints=0 compile_ns=0 setup_ns=0 token_type=0x%04x suite=%s Ne=%d Ns=%d Nk=%d\n",
			ppTokenType, issuer.suite.Identifier(), params.CompressedElementLength, params.ScalarLength, ppAuthenticatorNb)
		fmt.Println("sample,challenge_ns,blind_ns,issuer_evaluate_ns,finalize_ns,issuer_redeem_ns,gateway_state_ns,total_to_accept_ns,plaintext_bytes,token_request_bytes,token_response_bytes,token_bytes,envelope_bytes,nonce_ascii_bytes,component_sum_bytes")
		totals := make([]int64, 0, runs)
		for i := range people {
			plain := reportFor(i)
			envelope, e := SealReportMLKEM(recipient.EncapsulationKey(), plain, task.ID)
			if e != nil {
				t.Fatal(e)
			}
			totalStart := time.Now()
			start := time.Now()
			challenge, e := gw.Issue(1000, 60)
			challengeNS := time.Since(start).Nanoseconds()
			if e != nil {
				t.Fatal(e)
			}
			cd := nonSnarkChallengeDigest(challenge.Nonce)
			tokenNonce := make([]byte, ppNonceBytes)
			if _, e = rand.Read(tokenNonce); e != nil {
				t.Fatal(e)
			}
			input := ppTokenInput(tokenNonce, cd, issuer.keyID)
			start = time.Now()
			fd, req, e := client.Blind([][]byte{input})
			blindNS := time.Since(start).Nanoseconds()
			if e != nil {
				t.Fatal(e)
			}
			blinded, e := req.Elements[0].MarshalBinaryCompress()
			if e != nil {
				t.Fatal(e)
			}
			requestBytes := append(binary.BigEndian.AppendUint16(nil, ppTokenType), byte(issuer.keyID[len(issuer.keyID)-1]))
			requestBytes = append(requestBytes, blinded...)
			start = time.Now()
			eval, e := issuer.server.Evaluate(req)
			evaluateNS := time.Since(start).Nanoseconds()
			if e != nil {
				t.Fatal(e)
			}
			evaluated, e := eval.Elements[0].MarshalBinaryCompress()
			if e != nil {
				t.Fatal(e)
			}
			proofBytes, e := eval.Proof.MarshalBinary()
			if e != nil {
				t.Fatal(e)
			}
			responseBytes := append(append([]byte{}, evaluated...), proofBytes...)
			start = time.Now()
			out, e := client.Finalize(fd, eval)
			finalizeNS := time.Since(start).Nanoseconds()
			if e != nil {
				t.Fatal(e)
			}
			token := append([]byte{}, input[:2+ppNonceBytes+ppDigestBytes+ppKeyIDBytes]...)
			token = append(token, out[0]...)
			// Redemption carries the cleartext metadata the token cannot bind.
			metadata := append(bbe32(event[0]), bbe32(event[1])...)
			metadata = append(metadata, bbe32(event[2])...)
			metadata = append(metadata, reportDigestOf(plain)...)
			gw.currentNow = 1001
			start = time.Now()
			if e := gw.CheckFields(challenge.Nonce, token); e != nil {
				t.Fatalf("privacy pass gateway sample %d: %v", i, e)
			}
			gatewayNS := time.Since(start).Nanoseconds()
			start = time.Now()
			if e := issuer.Redeem(challenge.Nonce, token, metadata); e != nil {
				t.Fatalf("privacy pass redeem sample %d: %v", i, e)
			}
			redeemNS := time.Since(start).Nanoseconds()
			totalNS := time.Since(totalStart).Nanoseconds()
			label := strconv.Itoa(i)
			if i == 0 {
				label = "warmup"
			} else {
				totals = append(totals, totalNS)
			}
			fmt.Printf("%s,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n", label, challengeNS, blindNS, evaluateNS, finalizeNS, redeemNS, gatewayNS, totalNS,
				len(plain), len(requestBytes), len(responseBytes), len(token), len(envelope), len(challenge.Nonce),
				len(token)+len(metadata)+len(envelope)+len(challenge.Nonce))
		}
		fmt.Printf("STAT arm=privacy_pass median_total_to_accept_ns=%d\n", medianNS(totals))

		// Issuer blindness of the issuance message: the TokenRequest carries no
		// challenge, no report, and no event coordinate.
		challenge, e := gw.Issue(5000, 60)
		if e != nil {
			t.Fatal(e)
		}
		cd := nonSnarkChallengeDigest(challenge.Nonce)
		tokenNonce := make([]byte, ppNonceBytes)
		if _, e = rand.Read(tokenNonce); e != nil {
			t.Fatal(e)
		}
		input := ppTokenInput(tokenNonce, cd, issuer.keyID)
		fd, req, e := client.Blind([][]byte{input})
		if e != nil {
			t.Fatal(e)
		}
		blinded, e := req.Elements[0].MarshalBinaryCompress()
		if e != nil {
			t.Fatal(e)
		}
		requestBytes := append(binary.BigEndian.AppendUint16(nil, ppTokenType), byte(issuer.keyID[len(issuer.keyID)-1]))
		requestBytes = append(requestBytes, blinded...)
		plain := reportFor(200)
		leaks := 0
		for _, probe := range [][]byte{[]byte(challenge.Nonce), cd, reportDigestOf(plain), plain, bbe32(event[0]), bbe32(event[1]), bbe32(event[2])} {
			if bytes.Contains(requestBytes, probe) {
				leaks++
			}
		}
		out, e := client.Finalize(fd, req2Eval(t, issuer, req))
		if e != nil {
			t.Fatal(e)
		}
		token := append([]byte{}, input[:len(input)]...)
		token = append(token, out[0]...)

		// A forged authenticator passes every gateway-side field check; only an
		// issuer holding skI can tell it apart.
		forged := make([]byte, len(token))
		copy(forged, token)
		if _, e := rand.Read(forged[len(forged)-ppAuthenticatorNb:]); e != nil {
			t.Fatal(e)
		}
		gw.currentNow = 5001
		forgeGatewayErr := gw.CheckFields(challenge.Nonce, forged)
		forgeIssuerErr := issuer.Redeem(challenge.Nonce, forged, nil)
		// Replaying a valid token: the issuer rejects the second redemption. An
		// Origin that does not get the redemption callback back has no state of
		// its own and accepts the replay.
		redeemOnce := issuer.Redeem(challenge.Nonce, token, nil)
		replayIssuer := issuer.Redeem(challenge.Nonce, token, nil)
		gwNoState := gw.CheckFields(challenge.Nonce, token)
		gw.MarkUsed(token)
		gwWithState := gw.CheckFields(challenge.Nonce, token)
		// One challenge can buy several tokens; nothing in the issuance protocol
		// limits one participant to a single report per task.
		extra := 0
		for k := 0; k < 3; k++ {
			n2 := make([]byte, ppNonceBytes)
			if _, e := rand.Read(n2); e != nil {
				t.Fatal(e)
			}
			in2 := ppTokenInput(n2, cd, issuer.keyID)
			fd2, req2, e := client.Blind([][]byte{in2})
			if e != nil {
				t.Fatal(e)
			}
			ev2, e := issuer.server.Evaluate(req2)
			if e != nil {
				t.Fatal(e)
			}
			out2, e := client.Finalize(fd2, ev2)
			if e != nil {
				t.Fatal(e)
			}
			tok2 := append([]byte{}, in2...)
			tok2 = append(tok2, out2[0]...)
			if e := issuer.Redeem(challenge.Nonce, tok2, nil); e == nil {
				extra++
			}
		}
		fmt.Printf("RESULT arm=privacy_pass issuance_request_leaks=%dof7 gateway_accepts_forged_without_issuer_key=%v issuer_redeem_rejects_forged=%v redeem_valid=%v replay_rejected_by_issuer=%v replay_at_gateway_without_callback=%v replay_at_gateway_with_callback=%v tokens_per_challenge_redeemable=%dof3\n",
			leaks, errLabel(forgeGatewayErr), errLabel(forgeIssuerErr), errLabel(redeemOnce), errLabel(replayIssuer), errLabel(gwNoState), errLabel(gwWithState), extra)
		fmt.Println("STRUCTURE arm=privacy_pass issuer input is a blinded element only; the token binds to SHA256(challenge) and to nothing else, so report bytes and event coordinates must travel as cleartext metadata that the redeemer reads; the Origin cannot verify a token without the issuer private key, so redemption is an extra round trip and the single-use state lives at the issuer; there is no per-participant quota and no credential-membership proof")
	}

	// ---- Arm 4: trusted-issuer cleartext receipt (existing weak baseline) ----
	{
		issuer, e := NewBaselineIssuer(common.Issuer, task)
		if e != nil {
			t.Fatal(e)
		}
		for _, person := range people {
			issuer.Enroll(person.identityKey.Public())
		}
		gw, e := newBaselineGateway(common.Issuer.Public(), task)
		if e != nil {
			t.Fatal(e)
		}
		fmt.Println("ARM trusted_baseline constraints=0 compile_ns=0 setup_ns=0")
		fmt.Println("sample,challenge_ns,request_sign_ns,issuer_verify_and_sign_ns,gateway_verify_dedup_ns,total_to_accept_ns,plaintext_bytes,receipt_bytes,nonce_ascii_bytes,request_bytes,component_sum_bytes")
		totals := make([]int64, 0, runs)
		for i, person := range people {
			plain := reportFor(i)
			totalStart := time.Now()
			start := time.Now()
			challenge, e := gw.Issue(1000, 60)
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
			reqBytes := elem.Bytes()
			sig, e := person.identityKey.Sign(reqBytes[:], nativeMiMC.NewMiMC())
			if e != nil {
				t.Fatal(e)
			}
			requestSignNS := time.Since(start).Nanoseconds()
			start = time.Now()
			receipt, e := issuer.SignReceipt(person.identityKey.Public(), sig, challenge, plain, event)
			if e != nil {
				t.Fatal(e)
			}
			issuerNS := time.Since(start).Nanoseconds()
			start = time.Now()
			if e := gw.Submit(challenge.Nonce, receipt, plain, 1001); e != nil {
				t.Fatalf("baseline gateway sample %d: %v", i, e)
			}
			gatewayNS := time.Since(start).Nanoseconds()
			totalNS := time.Since(totalStart).Nanoseconds()
			label := strconv.Itoa(i)
			if i == 0 {
				label = "warmup"
			} else {
				totals = append(totals, totalNS)
			}
			// Wire fields follow TestProtocolComparisonExperiment exactly: the
			// receipt carries pseudonym 32 + event 12 + report digest 32 +
			// challenge digest 32 + EdDSA signature, and the request carries the
			// identity public key, the request signature, both digests, the event,
			// and the cleartext report the issuer must read.
			receiptBytes := 32 + 12 + 32 + 32 + len(receipt.Signature)
			requestTotal := 32 + len(sig) + 32 + 32 + 12 + len(plain)
			fmt.Printf("%s,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n", label, challengeNS, requestSignNS, issuerNS, gatewayNS, totalNS,
				len(plain), receiptBytes, len(challenge.Nonce), requestTotal, len(plain)+receiptBytes+len(challenge.Nonce))
		}
		fmt.Printf("STAT arm=trusted_baseline median_total_to_accept_ns=%d\n", medianNS(totals))
	}

	fmt.Println("SCOPE synthetic in-process comparison; no deployed issuers, no network, no HTTP framing; BLS12-381 and P-384 timings are not attributable to the curve choice relative to the BN254 zero-knowledge arm; BBS+ uses the trustbloc bbs12381g2pub implementation and Privacy Pass uses cloudflare/circl oprf")
	fmt.Printf("completed_utc=%s\n", time.Now().UTC().Format(time.RFC3339Nano))
}

func req2Eval(t *testing.T, issuer *PPIssuer, req *oprf.EvaluationRequest) *oprf.Evaluation {
	t.Helper()
	eval, e := issuer.server.Evaluate(req)
	if e != nil {
		t.Fatal(e)
	}
	return eval
}

func medianNS(values []int64) int64 {
	if len(values) == 0 {
		return 0
	}
	sorted := append([]int64{}, values...)
	sort.Slice(sorted, func(i, j int) bool { return sorted[i] < sorted[j] })
	return sorted[len(sorted)/2]
}

func errLabel(e error) string {
	if e == nil {
		return "accepted"
	}
	return "rejected"
}
