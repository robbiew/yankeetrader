package qbreplay

import (
	"encoding/json"
	"strings"
	"testing"
)

func sampleEvolvedChain() EvolvedChainDocument {
	d := EvolvedChainDocument(sampleChain())
	d.Format = EvolvedChainFormat
	d.Profile = EvolvedChainProfile
	d.BeforeSHA256["YTDATA.DAT"] = "f545d697b28d93910407cfeb7baac96666062ebe3cb5ac3334d6a3e85f5e45b7"
	return d
}
func evolvedChainJSON(t *testing.T, d EvolvedChainDocument) []byte {
	t.Helper()
	b, e := json.Marshal(d)
	if e != nil {
		t.Fatal(e)
	}
	return b
}
func TestDecodeEvolvedChainExplicitRawClocksAndSeparateSchema(t *testing.T) {
	d := sampleEvolvedChain()
	b := evolvedChainJSON(t, d)
	_, r, e := DecodeEvolvedChain(b)
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
		t.Fatal("v1 admitted v4")
	}
	if _, _, e := DecodeEvolvedChain(encoded(t, sampleDocument())); e == nil {
		t.Fatal("v4 admitted v1")
	}
}
func TestDecodeEvolvedChainRejectsMalformedRecipes(t *testing.T) {
	cases := map[string]func(*EvolvedChainDocument){
		"profile":           func(d *EvolvedChainDocument) { d.Profile = "initial" },
		"missing day":       func(d *EvolvedChainDocument) { d.Days = d.Days[:2] },
		"reordered day":     func(d *EvolvedChainDocument) { d.Days[1], d.Days[2] = d.Days[2], d.Days[1] },
		"state":             func(d *EvolvedChainDocument) { d.Days[2].InitialState = 1 << 24 },
		"missing port":      func(d *EvolvedChainDocument) { d.Days[0].Ports.TimerMinutes = d.Days[0].Ports.TimerMinutes[:999] },
		"mixed day":         func(d *EvolvedChainDocument) { d.Days[1].Ports.Days[5] = 306 },
		"planet order":      func(d *EvolvedChainDocument) { d.Days[1].Planets[0].Record = 4053 },
		"missing creation":  func(d *EvolvedChainDocument) { d.Days[0].Creation = []CreationRecipe{} },
		"repeated creation": func(d *EvolvedChainDocument) { d.Days[2].Creation = d.Days[0].Creation },
		"calendar":          func(d *EvolvedChainDocument) { d.Days[0].Creation[0].BaseDay = 305 },
		"timer":             func(d *EvolvedChainDocument) { d.Days[0].Creation[0].XannoronTimer = "DEADBEEF" },
		"family":            func(d *EvolvedChainDocument) { d.Days[1].HomeHelpers[0].Family = 3 },
		"tail timer":        func(d *EvolvedChainDocument) { d.Days[2].TailHelpers = []HelperRecipe{{Family: 1, Timer: "NaN"}} },
		"report date":       func(d *EvolvedChainDocument) { d.Days[2].Aux.NewsDate = "2026-11-03" },
		"report clock":      func(d *EvolvedChainDocument) { d.Days[2].Aux.ScoreClock = "0:00:00" },
		"oracle source":     func(d *EvolvedChainDocument) { d.SourceSHA256["oracles.json"] = OriginalMaintSHA },
		"arbitrary pins":    func(d *EvolvedChainDocument) { d.SourceSHA256["research/yt-maint/after/pins.json"] = OriginalMaintSHA },
		"before inventory":  func(d *EvolvedChainDocument) { delete(d.BeforeSHA256, "YTNEWS.DAT") },
	}
	for name, change := range cases {
		t.Run(name, func(t *testing.T) {
			d := sampleEvolvedChain()
			change(&d)
			if _, _, e := DecodeEvolvedChain(evolvedChainJSON(t, d)); e == nil {
				t.Fatal("invalid recipe admitted")
			}
		})
	}
	good := string(evolvedChainJSON(t, sampleEvolvedChain()))
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
		if _, _, e := DecodeEvolvedChain([]byte(b)); e == nil {
			t.Fatal("invalid JSON admitted", i)
		}
	}
}

func TestEvolvedChainAllLayoutsAndVersionSeparation(t *testing.T) {
	for _, pin := range []string{"40947d888c7bd9192acfc12d2531d6414fe6392c9c815ead42ea4d28ef6325bf", "0e5d8934af1be3debc72708ecdd3e2825a2c4000398253fc8b793340907669a6", "277c3cadeea74b02596c3d832566ff7de5b39a7a5a1b8edbd9a2ac563edd31b6"} {
		d := sampleEvolvedChain()
		d.BeforeSHA256["YTDATA.DAT"] = pin
		d.Days[0].Planets = []PlanetRecipe{}
		for i := 1; i < 3; i++ {
			d.Days[i].Planets = append(d.Days[i].Planets[:1], d.Days[i].Planets[2:]...)
		}
		if _, _, e := DecodeEvolvedChain(evolvedChainJSON(t, d)); e != nil {
			t.Fatal("three-home context", e)
		}
		d.Days[0].Planets = []PlanetRecipe{{Record: 4053, Day: 306, TimerMinutes: "00000000"}}
		if _, _, e := DecodeEvolvedChain(evolvedChainJSON(t, d)); e == nil {
			t.Fatal("ordinary planet invented for absent-slot profile")
		}
	}
	d := sampleEvolvedChain()
	raw := evolvedChainJSON(t, d)
	if _, _, e := DecodeChain(raw); e == nil {
		t.Fatal("v2 admitted v4")
	}
	if _, _, e := DecodeOccupied(raw); e == nil {
		t.Fatal("v3 admitted v4")
	}
	for _, raw := range [][]byte{chainJSON(t, sampleChain()), occupiedJSON(t, sampleOccupied()), encoded(t, sampleDocument())} {
		if _, _, e := DecodeEvolvedChain(raw); e == nil {
			t.Fatal("v4 admitted legacy schema")
		}
	}
	d.BeforeSHA256["YTDATA.DAT"] = strings.Repeat("0", 64)
	if _, _, e := DecodeEvolvedChain(evolvedChainJSON(t, d)); e == nil {
		t.Fatal("unqualified original pin")
	}
	d = sampleEvolvedChain()
	d.SourceSHA256["research/yt-maint/convergence-chain-controls/pins.json"] = OriginalMaintSHA
	if _, _, e := DecodeEvolvedChain(evolvedChainJSON(t, d)); e == nil {
		t.Fatal("unqualified source provenance family")
	}
}
