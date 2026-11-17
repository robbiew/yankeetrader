package qbreplay

import (
	"encoding/json"
	"strings"
	"testing"
)

func sampleOccupied() OccupiedDocument {
	d := sampleChain()
	p := d.Days[0]
	yes := true
	return OccupiedDocument{Format: OccupiedFormat, Profile: OccupiedProfile, Name: "synthetic-schema-test", BeforeSHA256: d.BeforeSHA256, SourceSHA256: d.SourceSHA256, Recipe: OccupiedRecipe{InitialState: 0, Ports: PortRecipe{Days: p.Ports.Days, TimerMinutes: p.Ports.TimerMinutes, Capped: &yes}, Planets: []PlanetRecipe{}, Creation: p.Creation[0], RoutingHelpers: p.HomeHelpers, TailHelpers: []HelperRecipe{}, FinalDay: 306, Aux: p.Aux}}
}
func occupiedJSON(t *testing.T, d OccupiedDocument) []byte {
	t.Helper()
	b, e := json.Marshal(d)
	if e != nil {
		t.Fatal(e)
	}
	return b
}
func TestOccupiedRecipeSeparateSchemaAndRawClocks(t *testing.T) {
	d := sampleOccupied()
	b := occupiedJSON(t, d)
	_, r, e := DecodeOccupied(b)
	if e != nil {
		t.Fatal(e)
	}
	if r.StartupState != 0 || r.Creation.XannoronTimer != [4]byte{1, 2, 3, 0} || r.Ports.TimerMinutes[0] != [4]byte{1, 2, 3, 0} || r.Reports.ScoreClock != "24:00:00" {
		t.Fatal("explicit clocks normalized")
	}
	r.Ports.Days[0] = 0
	if d.Recipe.Ports.Days[0] != 306 {
		t.Fatal("alias")
	}
	if _, _, e := Decode(b); e == nil {
		t.Fatal("v1 admitted v3")
	}
	if _, _, e := DecodeChain(b); e == nil {
		t.Fatal("v2 admitted v3")
	}
	if _, _, e := DecodeOccupied(chainJSON(t, sampleChain())); e == nil {
		t.Fatal("v3 admitted v2")
	}
	if _, _, e := DecodeOccupied(encoded(t, sampleDocument())); e == nil {
		t.Fatal("v3 admitted v1")
	}
}
func TestOccupiedRecipeRejectsUnqualifiedSchema(t *testing.T) {
	cases := map[string]func(*OccupiedDocument){
		"profile":        func(d *OccupiedDocument) { d.Profile = "initial" },
		"state":          func(d *OccupiedDocument) { d.Recipe.InitialState = 1 << 24 },
		"final day":      func(d *OccupiedDocument) { d.Recipe.FinalDay = 307 },
		"mixed port day": func(d *OccupiedDocument) { d.Recipe.Ports.Days[2] = 307 },
		"short ports":    func(d *OccupiedDocument) { d.Recipe.Ports.TimerMinutes = d.Recipe.Ports.TimerMinutes[:999] },
		"cap":            func(d *OccupiedDocument) { *d.Recipe.Ports.Capped = false },
		"creation day":   func(d *OccupiedDocument) { d.Recipe.Creation.BaseDay = 307 },
		"creation raw":   func(d *OccupiedDocument) { d.Recipe.Creation.XannoronTimer = "DEADBEEF" },
		"planet order": func(d *OccupiedDocument) {
			d.Recipe.Planets = []PlanetRecipe{{Record: 4054, Day: 306, TimerMinutes: "01020300"}}
		},
		"missing helpers":  func(d *OccupiedDocument) { d.Recipe.RoutingHelpers = []HelperRecipe{} },
		"tail family":      func(d *OccupiedDocument) { d.Recipe.TailHelpers = []HelperRecipe{{Family: 2, Timer: "00000000"}} },
		"tail raw":         func(d *OccupiedDocument) { d.Recipe.TailHelpers = []HelperRecipe{{Family: 1, Timer: "NaN"}} },
		"report date":      func(d *OccupiedDocument) { d.Recipe.Aux.NewsDate = "2026-11-03" },
		"report clock":     func(d *OccupiedDocument) { d.Recipe.Aux.ScoreClock = "0:00:00" },
		"source oracle":    func(d *OccupiedDocument) { d.SourceSHA256["oracles.json"] = OriginalMaintSHA },
		"source arbitrary": func(d *OccupiedDocument) { d.SourceSHA256["research/yt-maint/after/pins.json"] = OriginalMaintSHA },
		"before inventory": func(d *OccupiedDocument) { delete(d.BeforeSHA256, "YTNEWS.DAT") },
	}
	for name, change := range cases {
		t.Run(name, func(t *testing.T) {
			d := sampleOccupied()
			change(&d)
			if _, _, e := DecodeOccupied(occupiedJSON(t, d)); e == nil {
				t.Fatal("invalid admitted")
			}
		})
	}
	good := string(occupiedJSON(t, sampleOccupied()))
	bad := []string{
		strings.Replace(good, `"initial_state":0`, `"initial_state":null`, 1),
		strings.Replace(good, `"initial_state":0,`, "", 1),
		strings.Replace(good, `"tail_helpers":[]`, `"tail_helpers":null`, 1),
		strings.Replace(good, `"final_day":306`, `"final_day":306,"FINAL_DAY":306`, 1),
		strings.Replace(good, `"caller":4986`, `"caller":70000`, 1),
		strings.Replace(good, `"recipe":{`, `"recipe":{"final_state":0,`, 1),
		good + `{}`, `null`, strings.Repeat(" ", MaxRecipeBytes+1),
	}
	for i, b := range bad {
		if _, _, e := DecodeOccupied([]byte(b)); e == nil {
			t.Fatal("invalid JSON admitted", i)
		}
	}
}
