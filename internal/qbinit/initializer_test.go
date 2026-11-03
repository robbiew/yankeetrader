package qbinit

import (
	"bytes"
	"crypto/sha256"
	_ "embed"
	"encoding/json"
	"errors"
	"fmt"
	"strings"
	"testing"
)

// Only this portable fixture is needed by Go tests, not the research tree,
// original executable, Python, DOSBox or REA.
//
//go:embed testdata/native_initializer.json
var nativeFixture []byte

type golden struct {
	Name, Date, Scoreboard string
	State                  uint32
	WorldSHA               string `json:"world_sha256"`
	Blocks                 map[string]string
	Stats                  struct {
		HQ                  int `json:"hq_sector"`
		Draws               uint64
		FinalState          uint32 `json:"final_state"`
		GraphDraws          uint64 `json:"graph_draws"`
		GraphState          uint32 `json:"graph_state"`
		PlacementDraws      uint64 `json:"placement_draws"`
		PlacementRejections int    `json:"placement_rejections"`
		PlacementState      uint32 `json:"placement_final_state"`
		PlacementTotal      uint64 `json:"placement_total_draws"`
		RepairPairs         int    `json:"repair_pairs"`
		ShortcutWrites      int    `json:"shortcut_writes"`
	}
}

func goldens(t *testing.T) []golden {
	t.Helper()
	var fixture struct {
		Format  string
		Cases   []golden
		PoolSHA string `json:"syllables_sha256"`
	}
	if err := json.Unmarshal(nativeFixture, &fixture); err != nil {
		t.Fatal(err)
	}
	if fixture.Format != "qb-initializer-native-hashes-v1" || len(fixture.Cases) != 10 {
		t.Fatal("native fixture coverage")
	}
	if len(strings.Split(syllableData, ",")) != 908 || hash([]byte(syllableData)) != fixture.PoolSHA {
		t.Fatal("weighted original DATA changed")
	}
	return fixture.Cases
}
func hash(b []byte) string { return fmt.Sprintf("%x", sha256.Sum256(b)) }
func options(g golden) Options {
	return Options{State: g.State, Date: g.Date, Scoreboard: g.Scoreboard}
}

func TestCompleteNativeWorlds(t *testing.T) {
	for _, g := range goldens(t) {
		t.Run(g.Name, func(t *testing.T) {
			t.Parallel()
			r, err := Generate(options(g))
			if err != nil {
				t.Fatal(err)
			}
			if len(r.Bytes) != RecordSize*RecordCount || hash(r.Bytes) != g.WorldSHA {
				t.Fatalf("complete native bytes differ: %s", hash(r.Bytes))
			}
			blocks := map[string][2]int{"configuration": {0, 1}, "players": {1, 51}, "sectors": {51, 3051}, "ports": {3051, 4051}, "planets": {4051, 4151}}
			for name, span := range blocks {
				if hash(r.Bytes[span[0]*RecordSize:span[1]*RecordSize]) != g.Blocks[name] {
					t.Errorf("%s block differs", name)
				}
			}
			want := Stats{HQ: g.Stats.HQ, Draws: g.Stats.Draws, FinalState: g.Stats.FinalState, GraphDraws: g.Stats.GraphDraws, GraphState: g.Stats.GraphState, PlacementDraws: g.Stats.PlacementDraws, PlacementRejections: g.Stats.PlacementRejections, PlacementState: g.Stats.PlacementState, RepairPairs: g.Stats.RepairPairs, ShortcutWrites: g.Stats.ShortcutWrites}
			if r.Stats != want {
				t.Fatalf("stream bookkeeping differs\ngot %+v\nwant %+v", r.Stats, want)
			}
		})
	}
}

func TestOriginalRawResiduesAndFieldInheritance(t *testing.T) {
	r, err := Generate(Options{State: 0xc805, Date: "2027-01-01", Scoreboard: "SCORES.TXT"})
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(r.Bytes[81:85], []byte{0, 0, 0x40, 0}) {
		t.Fatal("January cancellation zero normalized")
	}
	if !bytes.Equal(record(r.Bytes, 53)[41:45], []byte{2, 0, 0x54, 0}) {
		t.Fatal("sparse warp FAC residue lost")
	}
	if !bytes.Equal(record(r.Bytes, 3052)[49:53], []byte{0, 0, 0xa0, 0}) {
		t.Fatal("port supply zero normalized")
	}
	config := append([]byte(nil), r.Bytes[:RecordSize]...)
	put(config, 85, 0)
	for id := 4052; id <= 4151; id++ {
		if !bytes.Equal(record(r.Bytes, id), config) {
			t.Fatalf("planet %d lost configuration FIELD inheritance", id)
		}
	}
}

func TestOriginalPortOverwriteRetainedInSource(t *testing.T) {
	r, err := Generate(Options{State: 0xa90a05, Date: "2026-11-02"})
	if err != nil {
		t.Fatal(err)
	}
	for _, id := range []int{4, 274} {
		want := mbf(7)
		if !bytes.Equal(record(r.Bytes, 3051+id)[93:97], want[:]) {
			t.Fatalf("port %d no longer in sector7", id)
		}
	}
	winner := mbf(274)
	if !bytes.Equal(record(r.Bytes, 58)[65:69], winner[:]) {
		t.Fatal("original last writer no longer wins")
	}
}

func TestWorkLimitsReturnNoPartialCandidate(t *testing.T) {
	g := goldens(t)[0]
	for _, limit := range []uint64{1, g.Stats.GraphDraws - 1, g.Stats.PlacementTotal - 1, g.Stats.Draws - 1} {
		o := options(g)
		o.DrawLimit = limit
		r, err := Generate(o)
		if !errors.Is(err, ErrDrawLimit) || r.Bytes != nil || r.Stats != (Stats{}) {
			t.Fatalf("limit %d published a partial candidate: %+v %v", limit, r.Stats, err)
		}
	}
	o := options(g)
	o.DrawLimit = g.Stats.Draws
	r, err := Generate(o)
	if err != nil || hash(r.Bytes) != g.WorldSHA {
		t.Fatalf("exact draw budget changed output: %v", err)
	}
}

func TestInputsAndOwnership(t *testing.T) {
	for _, o := range []Options{
		{State: 0x1000000, Date: "2026-11-02"},
		{State: 0xc805, Date: "2026-01-10"}, {State: 0xc805, Date: "2027-01-10"}, {State: 0xc805, Date: "2028-01-10"}, {Date: "2025-12-31"}, {Date: "2029-01-01"},
		{Date: "2026-02-29"}, {Date: "2026-1-01"}, {Date: "2026-11-02T00:00:00Z"},
		{Date: "2026-11-02", Scoreboard: strings.Repeat("x", 42)}, {Date: "2026-11-02", Scoreboard: "a\nb"},
		{Date: "2026-11-02", Scoreboard: "é"}, {Date: "2026-11-02", DrawLimit: DefaultDrawLimit + 1},
	} {
		r, err := Generate(o)
		if err == nil || r.Bytes != nil {
			t.Fatalf("invalid input accepted: %+v", o)
		}
	}
	// Zero is a valid state, not an instruction to substitute the default seed.
	a, err := Generate(Options{State: 0, Date: "2026-11-02", Scoreboard: strings.Repeat("x", 41)})
	if err != nil {
		t.Fatal(err)
	}
	b, err := Generate(Options{State: 0, Date: "2026-11-02", Scoreboard: strings.Repeat("x", 41)})
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(a.Bytes, b.Bytes) {
		t.Fatal("same source inputs are not deterministic")
	}
	a.Bytes[0] ^= 1
	if a.Bytes[0] == b.Bytes[0] {
		t.Fatal("results alias shared state")
	}
}
