package game

import (
	"encoding/json"
	"fmt"
	"reflect"
	"strings"
	"testing"
	"time"
)

func qbPlayable(t *testing.T) *World {
	t.Helper()
	w, e := NewQB36(clock, 36, 0xc805, "2027-01-01")
	if e != nil {
		t.Fatal(e)
	}
	return w
}
func qbLayout(w *World) string {
	type sector struct {
		Warps []int
		Port  int
	}
	type port struct {
		Sector                  int
		Name                    string
		Production, Coefficient [3]float64
	}
	s := map[int]sector{}
	p := map[int]port{}
	for id, x := range w.Sectors {
		s[id] = sector{x.Warps, x.Port}
	}
	for id, x := range w.Ports {
		p[id] = port{x.Sector, x.Name, x.Production, x.Coefficient}
	}
	hq := 0
	if w.Xannor != nil {
		hq = w.Xannor.HQ
	}
	raw, _ := json.Marshal([]any{s, p, hq})
	return string(raw)
}
func TestQBPlayableRecipeRoundtripValidationAndUpgrade(t *testing.T) {
	w := qbPlayable(t)
	original := qbLayout(w)
	w.Ports[1].Supply[0] = 123 // Evolved state must not be regenerated on load.
	raw, _ := json.Marshal(w)
	var saved World
	if err := json.Unmarshal(raw, &saved); err != nil {
		t.Fatal(err)
	}
	if err := saved.Upgrade(); err != nil {
		t.Fatal(err)
	}
	if err := saved.Validate(); err != nil {
		t.Fatal(err)
	}
	if saved.Ports[1].Supply[0] != 123 || qbLayout(&saved) != original || !reflect.DeepEqual(saved.QBRecipe, w.QBRecipe) {
		t.Fatal("load rerolled or lost provenance")
	}
	for _, mutate := range []func(*World){
		func(w *World) { w.QBRecipe.Profile = "qb36-v2" }, func(w *World) { w.QBRecipe.State = nil }, func(w *World) { *w.QBRecipe.State = 0x1000000 },
		func(w *World) { w.QBRecipe.Date = "2029-01-10" }, func(w *World) { w.QBRecipe.Date = "2026-02-29" }, func(w *World) { w.QBRecipe.SourceSHA256 = "bad" },
		func(w *World) { w.PortGeneration = "" }, func(w *World) { w.WarpGeneration = "" },
	} {
		c := qbPlayable(t)
		mutate(c)
		if c.Validate() == nil {
			t.Fatal("invalid recipe admitted")
		}
	}
	for _, v := range []int{33, 34} {
		old, _ := New(clock, 36, 32)
		old.Version = v
		before := qbLayout(old)
		if err := old.Upgrade(); err != nil || old.QBRecipe != nil || qbLayout(old) != before {
			t.Fatal("upgrade changed old world", err)
		}
	}
	w.Version = 34
	if w.Upgrade() == nil {
		t.Fatal("pre-version recipe accepted")
	}
}
func TestQBPlayableResetsRepeatSourceAndBindRecipe(t *testing.T) {
	w := qbPlayable(t)
	layout := qbLayout(w)
	recipe := w.QBRecipe.Clone()
	p, _ := w.Join("winner", "Winner")
	n := 20
	w.GenesisPorts = &n
	lottery := 7
	w.LotteryDailyLimit = &lottery
	for i := 2; i <= 21; i++ {
		w.Ports[i].Owner = p.ID
	}
	at := clock.Add(time.Hour)
	e, err := w.PrepareGenesis(p.ID, at)
	if err != nil {
		t.Fatal(err)
	}
	// Even a syntactically valid provenance change invalidates the outstanding quote.
	w.QBRecipe.SourceSHA256 = strings.Repeat("0", 64)
	if c, _, err := w.GenesisCandidate(e, at, 77); err == nil || c != nil {
		t.Fatal("stale recipe confirmation admitted")
	}
	w.QBRecipe = recipe.Clone()
	if c, err := w.AdministrativeCandidate(1, at, 77); err != nil || c == nil {
		t.Fatal(err)
	} else {
		if qbLayout(c) != layout || !reflect.DeepEqual(c.QBRecipe, recipe) || c.LastMaintenance != day(at) || c.Season != 2 || !c.SeasonResults[0].Administrative || c.LotteryLimit() != 7 {
			t.Fatal("admin reset lost layout/settings")
		}
	}
	c, out, err := w.GenesisCandidate(e, at, 999)
	if err != nil {
		t.Fatal(err)
	}
	if qbLayout(c) != layout || !reflect.DeepEqual(c.QBRecipe, recipe) || out.NewSeason != 2 || c.SeasonResults[0].Winner != "Winner" || len(c.Players) != 0 || c.LotteryLimit() != 7 {
		t.Fatal("Genesis reset lost recipe/layout/history")
	}
	*c.QBRecipe.State = 1
	if *w.QBRecipe.State != 0xc805 {
		t.Fatal("reset recipe aliases old world")
	}
	w.QBRecipe.SourceSHA256 = strings.Repeat("0", 64)
	before, _ := json.Marshal(w)
	if c, err := w.AdministrativeCandidate(1, at, 77); err == nil || c != nil {
		t.Fatal("fingerprint mismatch reset")
	}
	after, _ := json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("failed candidate mutated current world")
	}
}

func TestQBPlayableCreationRejectsWithoutPartialWorld(t *testing.T) {
	for _, tc := range []struct {
		state uint32
		date  string
		at    time.Time
	}{
		{0xa90a05, "2027-01-01", clock}, {619, "2027-01-01", clock},
		{0x1000000, "2027-01-01", clock}, {0xc805, "2029-01-10", clock},
		{0xc805, "2026-02-29", clock}, {0xc805, "2027-01-01", time.Time{}},
	} {
		if w, err := NewQB36(tc.at, 36, tc.state, tc.date); err == nil || w != nil {
			t.Fatal("partial/unsafe world admitted", tc, err)
		}
	}
}

func TestQBJanuary10RecipeCreationAndReset(t *testing.T) {
	for _, year := range []int{2026, 2027, 2028} {
		date := fmt.Sprintf("%d-01-10", year)
		w, err := NewQB36(clock, 36, 0xc805, date)
		if err != nil {
			t.Fatal(err)
		}
		recipe := w.QBRecipe.Clone()
		raw, _ := json.Marshal(w)
		var loaded World
		if err = json.Unmarshal(raw, &loaded); err != nil {
			t.Fatal(err)
		}
		if err = loaded.Upgrade(); err != nil {
			t.Fatal(err)
		}
		if err = loaded.Validate(); err != nil {
			t.Fatal(err)
		}
		next, err := loaded.AdministrativeCandidate(1, clock.Add(time.Hour), 77)
		if err != nil || !reflect.DeepEqual(next.QBRecipe, recipe) || qbLayout(next) != qbLayout(w) || next.LastMaintenance != day(clock.Add(time.Hour)) {
			t.Fatal("January 10 recipe/reset", err)
		}
		p, err := loaded.Join("jan-captain", "Captain")
		if err != nil {
			t.Fatal(err)
		}
		threshold := 20
		loaded.GenesisPorts = &threshold
		for id := 2; id <= 21; id++ {
			loaded.Ports[id].Owner = p.ID
		}
		at := clock.Add(time.Hour)
		intent, err := loaded.PrepareGenesis(p.ID, at)
		if err != nil {
			t.Fatal(err)
		}
		genesis, receipt, err := loaded.GenesisCandidate(intent, at, 99)
		if err != nil || receipt.NewSeason != 2 || !reflect.DeepEqual(genesis.QBRecipe, recipe) || qbLayout(genesis) != qbLayout(w) {
			t.Fatal("January 10 Genesis recipe/layout", err)
		}
		for _, port := range w.Ports {
			if port.Updated != clock.UTC() {
				t.Fatal("source zero date became a modern watermark")
			}
		}
	}
}
