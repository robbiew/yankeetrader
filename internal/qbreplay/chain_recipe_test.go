package qbreplay

import (
	"encoding/json"
	"fmt"
	"strings"
	"testing"
)

func sampleChain() ChainDocument {
	old := sampleDocument()
	d := ChainDocument{Format: ChainFormat, Profile: ChainProfile, Name: "synthetic-schema-test", BeforeSHA256: old.BeforeSHA256, SourceSHA256: old.SourceSHA256, Days: []ChainDayRecipe{}}
	for i := 0; i < 3; i++ {
		p := ChainDayRecipe{Day: 306 + i, InitialState: 0, Creation: []CreationRecipe{}, Planets: []PlanetRecipe{}, HomeHelpers: []HelperRecipe{{Family: 1, Caller: 0x137a, Timer: "01020300"}}, TailHelpers: []HelperRecipe{}, Aux: AuxRecipe{NewsDate: fmt.Sprintf("2026-11-%02d", 2+i), ScoreDate: fmt.Sprintf("2026-11-%02d", 2+i), NewsClock: "00:00:00", ScoreClock: "24:00:00"}}
		for n := 0; n < 1000; n++ {
			p.Ports.Days = append(p.Ports.Days, p.Day)
			p.Ports.TimerMinutes = append(p.Ports.TimerMinutes, "01020300")
		}
		records := []int{4052, 4053, 4150, 4151}
		if i == 0 {
			records = []int{4053}
			p.Creation = append(p.Creation, CreationRecipe{WandererDay: 306, XannoronDay: 306, BaseDay: 306, XannoronTimer: "01020300"})
		}
		for _, r := range records {
			p.Planets = append(p.Planets, PlanetRecipe{Record: r, Day: p.Day, TimerMinutes: "01020300"})
		}
		d.Days = append(d.Days, p)
	}
	return d
}
func chainJSON(t *testing.T, d ChainDocument) []byte {
	t.Helper()
	b, e := json.Marshal(d)
	if e != nil {
		t.Fatal(e)
	}
	return b
}
func TestDecodeChainExplicitRawClocksAndSeparateSchema(t *testing.T) {
	d := sampleChain()
	b := chainJSON(t, d)
	_, r, e := DecodeChain(b)
	if e != nil {
		t.Fatal(e)
	}
	want := [4]byte{1, 2, 3, 0}
	if r[0].InitialState != 0 || r[0].Creation.XannoronTimer != want || r[2].Ports.TimerMinutes[0] != want || r[1].HomeHelpers[0].Timer != want || r[2].Reports.ScoreClock != "24:00:00" {
		t.Fatal("explicit zeros/clocks normalized")
	}
	r[0].Ports.Days[0] = 0
	if d.Days[0].Ports.Days[0] != 306 {
		t.Fatal("decoded storage aliases input")
	}
	if _, _, e := Decode(b); e == nil {
		t.Fatal("v1 admitted v2")
	}
	if _, _, e := DecodeChain(encoded(t, sampleDocument())); e == nil {
		t.Fatal("v2 admitted v1")
	}
}
func TestDecodeChainRejectsMalformedRecipes(t *testing.T) {
	cases := map[string]func(*ChainDocument){
		"profile":           func(d *ChainDocument) { d.Profile = "initial" },
		"missing day":       func(d *ChainDocument) { d.Days = d.Days[:2] },
		"reordered day":     func(d *ChainDocument) { d.Days[1], d.Days[2] = d.Days[2], d.Days[1] },
		"state":             func(d *ChainDocument) { d.Days[2].InitialState = 1 << 24 },
		"missing port":      func(d *ChainDocument) { d.Days[0].Ports.TimerMinutes = d.Days[0].Ports.TimerMinutes[:999] },
		"mixed day":         func(d *ChainDocument) { d.Days[1].Ports.Days[5] = 306 },
		"planet order":      func(d *ChainDocument) { d.Days[1].Planets[0].Record = 4053 },
		"missing creation":  func(d *ChainDocument) { d.Days[0].Creation = []CreationRecipe{} },
		"repeated creation": func(d *ChainDocument) { d.Days[2].Creation = d.Days[0].Creation },
		"calendar":          func(d *ChainDocument) { d.Days[0].Creation[0].BaseDay = 305 },
		"timer":             func(d *ChainDocument) { d.Days[0].Creation[0].XannoronTimer = "DEADBEEF" },
		"family":            func(d *ChainDocument) { d.Days[1].HomeHelpers[0].Family = 3 },
		"tail timer":        func(d *ChainDocument) { d.Days[2].TailHelpers = []HelperRecipe{{Family: 1, Timer: "NaN"}} },
		"report date":       func(d *ChainDocument) { d.Days[2].Aux.NewsDate = "2026-11-03" },
		"report clock":      func(d *ChainDocument) { d.Days[2].Aux.ScoreClock = "0:00:00" },
		"oracle source":     func(d *ChainDocument) { d.SourceSHA256["oracles.json"] = OriginalMaintSHA },
		"arbitrary pins":    func(d *ChainDocument) { d.SourceSHA256["research/yt-maint/after/pins.json"] = OriginalMaintSHA },
		"before inventory":  func(d *ChainDocument) { delete(d.BeforeSHA256, "YTNEWS.DAT") },
	}
	for name, change := range cases {
		t.Run(name, func(t *testing.T) {
			d := sampleChain()
			change(&d)
			if _, _, e := DecodeChain(chainJSON(t, d)); e == nil {
				t.Fatal("invalid recipe admitted")
			}
		})
	}
	good := string(chainJSON(t, sampleChain()))
	bad := []string{
		strings.Replace(good, `"initial_state":0`, `"initial_state":null`, 1),
		strings.Replace(good, `"initial_state":0,`, "", 1),
		strings.Replace(good, `"creation":[]`, `"creation":null`, 1),
		strings.Replace(good, `"day":306`, `"day":306,"DAY":306`, 1),
		strings.Replace(good, `"family":1`, `"Family":1`, 1),
		strings.Replace(good, `"timer":"01020300"`, `"timer":null`, 1),
		strings.Replace(good, `"caller":4986`, `"caller":70000`, 1),
		strings.Replace(good, `"format":`, `"expected_world":"oracle","format":`, 1),
		good + `{}`, `null`, strings.Repeat(" ", MaxRecipeBytes+1),
	}
	for i, b := range bad {
		if _, _, e := DecodeChain([]byte(b)); e == nil {
			t.Fatal("invalid JSON admitted", i)
		}
	}
}
