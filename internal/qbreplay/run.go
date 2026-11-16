package qbreplay

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"

	"github.com/robbiew/yankeetrader/internal/qbmaint"
)

type Config struct{ RecipePath, BeforeDir, SourceRoot, OutDir string }
type ChainDayReceipt struct {
	Day          int    `json:"day"`
	InitialState uint32 `json:"initial_state"`
	FinalState   uint32 `json:"final_state"`
	Draws        int    `json:"draws"`
}

type Receipt struct {
	Days          []ChainDayReceipt           `json:"days,omitempty"`
	Format        string                      `json:"format"`
	Profile       string                      `json:"profile"`
	Name          string                      `json:"name"`
	RecipeSHA256  string                      `json:"recipe_sha256"`
	BeforeSHA256  map[string]string           `json:"before_sha256"`
	SourceSHA256  map[string]string           `json:"source_sha256"`
	OutputSHA256  map[string]string           `json:"output_sha256"`
	StateEvidence string                      `json:"state_evidence"`
	FinalState    uint32                      `json:"final_state"`
	Draws         int                         `json:"draws"`
	Encounters    []qbmaint.WandererEncounter `json:"encounters"`
}

func digest(b []byte) string { h := sha256.Sum256(b); return hex.EncodeToString(h[:]) }

// Run snapshots and checks the declared inputs before replay, then publishes a
// complete bundle under a newly reserved OUT/replay directory. Existing paths
// are never reused. Declared hashes are checked, not cryptographically trusted.
func Run(c Config) (Receipt, error) {
	fail := func(e error) (Receipt, error) { return Receipt{}, e }
	if c.RecipePath == "" || c.BeforeDir == "" || c.SourceRoot == "" || c.OutDir == "" {
		return fail(fmt.Errorf("recipe, before, source-root and out are required"))
	}
	data, e := readLimited(c.RecipePath, MaxRecipeBytes)
	if e != nil {
		return fail(e)
	}
	var envelope struct {
		Format string `json:"format"`
	}
	if e = json.Unmarshal(data, &envelope); e != nil {
		return fail(e)
	}
	var d Document
	var r qbmaint.InitialRecipe
	var chain []qbmaint.ConvergenceDayInputs
	if envelope.Format == ChainFormat {
		var v ChainDocument
		v, chain, e = DecodeChain(data)
		d = Document{Format: v.Format, Profile: v.Profile, Name: v.Name, BeforeSHA256: v.BeforeSHA256, SourceSHA256: v.SourceSHA256}
	} else {
		d, r, e = Decode(data)
	}
	if e != nil {
		return fail(e)
	}
	beforeRoot, e := directory(c.BeforeDir)
	if e != nil {
		return fail(e)
	}
	sourceRoot, e := directory(c.SourceRoot)
	if e != nil {
		return fail(e)
	}
	cleanOut := filepath.Clean(c.OutDir)
	parent, e := directory(filepath.Dir(cleanOut))
	if e != nil {
		return fail(e)
	}
	out := filepath.Join(parent, filepath.Base(cleanOut))
	// Resolve existing ancestors rather than comparing path strings, including
	// case aliases and symlinked directories on case-insensitive filesystems.
	for _, root := range []string{beforeRoot, sourceRoot} {
		inside, e := within(parent, root)
		if e != nil {
			return fail(e)
		}
		if inside {
			return fail(fmt.Errorf("output must be outside input/source trees"))
		}
	}
	if _, e = os.Lstat(out); e == nil {
		return fail(fmt.Errorf("output path already exists"))
	} else if !os.IsNotExist(e) {
		return fail(e)
	}
	names := make([]string, 0, len(d.SourceSHA256))
	for n := range d.SourceSHA256 {
		names = append(names, n)
	}
	sort.Strings(names)
	for _, n := range names {
		path, e := containedFile(sourceRoot, n)
		if e != nil {
			return fail(e)
		}
		f, e := os.Open(path)
		if e != nil {
			return fail(e)
		}
		h := sha256.New()
		_, copyErr := io.Copy(h, f)
		closeErr := f.Close()
		if copyErr != nil {
			return fail(copyErr)
		}
		if closeErr != nil {
			return fail(closeErr)
		}
		if hex.EncodeToString(h.Sum(nil)) != d.SourceSHA256[n] {
			return fail(fmt.Errorf("source hash differs: %s", n))
		}
	}
	before := map[string][]byte{}
	for _, n := range beforeNames {
		path, e := containedFile(beforeRoot, n)
		if e != nil {
			return fail(e)
		}
		limit := 1 << 20
		if n == "YTDATA.DAT" {
			limit = qbmaint.WorldRecords * qbmaint.RecordSize
		}
		b, e := readLimited(path, limit)
		if e != nil {
			return fail(e)
		}
		if digest(b) != d.BeforeSHA256[n] {
			return fail(fmt.Errorf("before hash differs: %s", n))
		}
		before[n] = b
	}
	var files map[string][]byte
	var stats qbmaint.InitialStats
	var encounters []qbmaint.WandererEncounter
	receipt := Receipt{Format: "qbmaint-receipt-v1", Profile: d.Profile, Name: d.Name, RecipeSHA256: digest(data), BeforeSHA256: d.BeforeSHA256, SourceSHA256: d.SourceSHA256, OutputSHA256: map[string]string{}, StateEvidence: "modeled-not-native-endpoint"}
	if d.Profile == ChainProfile {
		rows, err := qbmaint.ReplayConvergenceChain(before, chain)
		if err != nil {
			return fail(err)
		}
		files = map[string][]byte{}
		receipt.Format = "qbmaint-receipt-v2"
		for i, row := range rows {
			draws := row.Ports.RNGDraws + row.Planets.Draws + row.Homes.Draws + row.Tail.Draws
			receipt.Days = append(receipt.Days, ChainDayReceipt{Day: chain[i].Day, InitialState: chain[i].InitialState, FinalState: row.Tail.FinalState, Draws: draws})
			receipt.Draws += draws
			receipt.FinalState = row.Tail.FinalState
			if len(row.Files) != 6 {
				return fail(fmt.Errorf("unexpected chain inventory"))
			}
			for _, n := range outputNames {
				b, ok := row.Files[n]
				if !ok {
					return fail(fmt.Errorf("missing chain output"))
				}
				files[fmt.Sprintf("day-%d/%s", i+1, n)] = b
			}
		}
	} else {
		if d.Profile == "initial" {
			files, stats, e = qbmaint.ReplayInitialMaintenance(before, r)
		} else {
			var late qbmaint.WandererInitialStats
			files, late, e = qbmaint.ReplayInitialMaintenanceWithWanderer(before, r)
			stats = late.InitialStats
			encounters = late.Encounters
		}
		if e != nil {
			return fail(e)
		}
		if len(files) != 6 {
			return fail(fmt.Errorf("unexpected replay output inventory"))
		}
		for _, n := range outputNames {
			if _, ok := files[n]; !ok {
				return fail(fmt.Errorf("missing output: %s", n))
			}
		}
		receipt.FinalState = stats.FinalState
		receipt.Draws = stats.Draws
		receipt.Encounters = encounters
	}
	for n, b := range files {
		receipt.OutputSHA256[n] = digest(b)
	}
	rb, e := json.MarshalIndent(receipt, "", "  ")
	if e != nil {
		return fail(e)
	}
	rb = append(rb, '\n')
	if e = publish(parent, out, files, rb); e != nil {
		return fail(e)
	}
	return receipt, nil
}
func directory(path string) (string, error) {
	abs, e := filepath.Abs(path)
	if e != nil {
		return "", e
	}
	abs, e = filepath.EvalSymlinks(abs)
	if e != nil {
		return "", e
	}
	st, e := os.Stat(abs)
	if e != nil {
		return "", e
	}
	if !st.IsDir() {
		return "", fmt.Errorf("directory required: %s", path)
	}
	return abs, nil
}
func within(path, root string) (bool, error) {
	ri, e := os.Stat(root)
	if e != nil {
		return false, e
	}
	for {
		st, e := os.Stat(path)
		if e != nil {
			return false, e
		}
		if os.SameFile(st, ri) {
			return true, nil
		}
		p := filepath.Dir(path)
		if p == path {
			return false, nil
		}
		path = p
	}
}
func containedFile(root, name string) (string, error) {
	if !safeRelative(name) {
		return "", fmt.Errorf("invalid relative path")
	}
	p, e := filepath.EvalSymlinks(filepath.Join(root, filepath.FromSlash(name)))
	if e != nil {
		return "", e
	}
	inside, e := within(filepath.Dir(p), root)
	if e != nil {
		return "", e
	}
	if !inside {
		return "", fmt.Errorf("file escapes input/source root: %s", name)
	}
	st, e := os.Stat(p)
	if e != nil {
		return "", e
	}
	if !st.Mode().IsRegular() {
		return "", fmt.Errorf("regular file required: %s", name)
	}
	return p, nil
}
func readLimited(path string, limit int) ([]byte, error) {
	st, e := os.Stat(path)
	if e != nil {
		return nil, e
	}
	if !st.Mode().IsRegular() || st.Size() > int64(limit) {
		return nil, fmt.Errorf("regular file within size limit required: %s", path)
	}
	f, e := os.Open(path)
	if e != nil {
		return nil, e
	}
	defer f.Close()
	st, e = f.Stat()
	if e != nil {
		return nil, e
	}
	if !st.Mode().IsRegular() || st.Size() > int64(limit) {
		return nil, fmt.Errorf("regular file within size limit required: %s", path)
	}
	b, e := io.ReadAll(io.LimitReader(f, int64(limit)+1))
	if e != nil {
		return nil, e
	}
	if len(b) > limit {
		return nil, fmt.Errorf("file exceeds size limit")
	}
	return b, nil
}
func publish(parent, out string, files map[string][]byte, receipt []byte) (err error) {
	stage, e := os.MkdirTemp(parent, ".qbmaint-replay-")
	if e != nil {
		return e
	}
	defer os.RemoveAll(stage)
	write := func(n string, b []byte) error {
		if e := os.MkdirAll(filepath.Dir(filepath.Join(stage, n)), 0700); e != nil {
			return e
		}
		f, e := os.OpenFile(filepath.Join(stage, n), os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
		if e != nil {
			return e
		}
		written, we := f.Write(b)
		if we == nil && written != len(b) {
			we = io.ErrShortWrite
		}
		if we == nil {
			we = f.Sync()
		}
		ce := f.Close()
		if we != nil {
			return we
		}
		return ce
	}
	names := make([]string, 0, len(files))
	for n := range files {
		if !safeRelative(n) || n == "receipt.json" {
			return fmt.Errorf("invalid bundle path")
		}
		names = append(names, n)
	}
	sort.Strings(names)
	for _, n := range names {
		if e = write(n, files[n]); e != nil {
			return e
		}
	}
	if e = write("receipt.json", receipt); e != nil {
		return e
	}
	if e = os.Mkdir(out, 0700); e != nil {
		return e
	}
	defer func() {
		if err != nil {
			_ = os.Remove(out)
		}
	}()
	return os.Rename(stage, filepath.Join(out, "replay"))
}
