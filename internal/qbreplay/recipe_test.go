package qbreplay

import (
	"encoding/json"
	"strings"
	"testing"
)

func sampleDocument() Document {
	zero := uint32(0)
	cap := false
	d := Document{Format: Format, Profile: "initial", Name: "synthetic-schema-test", BeforeSHA256: map[string]string{}, SourceSHA256: map[string]string{"archive/dos-original/YTMAINT.EXE": OriginalMaintSHA}}
	for _, n := range beforeNames {
		d.BeforeSHA256[n] = strings.Repeat("0", 64)
	}
	p := PhaseRecipe{WandererDay: 1, XannoronDay: 1, BaseDay: 1, FinalDay: 1, InitialState: &zero, XannoronTimer: "01020300", Aux: AuxRecipe{NewsDate: "2026-01-01", NewsClock: "00:00:00", ScoreDate: "2026-01-01", ScoreClock: "00:00:00"}}
	p.Ports.Capped = &cap
	for i := 0; i < 1000; i++ {
		p.Ports.Days = append(p.Ports.Days, 1)
		p.Ports.TimerMinutes = append(p.Ports.TimerMinutes, "01020300")
	}
	for i := 0; i < 41; i++ {
		p.HelperOne = append(p.HelperOne, "01020300")
	}
	for i := 0; i < 19; i++ {
		p.HelperTwo = append(p.HelperTwo, "01020300")
	}
	d.Recipe = p
	return d
}
func encoded(t *testing.T, d Document) []byte {
	t.Helper()
	b, e := json.Marshal(d)
	if e != nil {
		t.Fatal(e)
	}
	return b
}
func TestDecodePreservesExplicitZeroStateAndRawResidues(t *testing.T) {
	d := sampleDocument()
	_, r, e := Decode(encoded(t, d))
	if e != nil {
		t.Fatal(e)
	}
	want := [4]byte{1, 2, 3, 0}
	if r.InitialState != 0 || r.Ports.Capped || r.XannoronTimer != want || r.HelperOne[0] != want || r.Ports.TimerMinutes[0] != want {
		t.Fatal("raw zero/default values normalized")
	}
	r.HelperOne[0][0] = 9
	if d.Recipe.HelperOne[0] != "01020300" {
		t.Fatal("alias")
	}
}
func TestDecodeRejectsMalformedSchemaAndInventories(t *testing.T) {
	changes := map[string]func(*Document){"format": func(d *Document) { d.Format = "future" }, "profile": func(d *Document) { d.Profile = "auto" }, "state missing": func(d *Document) { d.Recipe.InitialState = nil }, "state range": func(d *Document) { v := uint32(1 << 24); d.Recipe.InitialState = &v }, "cap missing": func(d *Document) { d.Recipe.Ports.Capped = nil }, "short helpers": func(d *Document) { d.Recipe.HelperOne = d.Recipe.HelperOne[:40] }, "extra helpers": func(d *Document) { d.Recipe.HelperTwo = append(d.Recipe.HelperTwo, "00000000") }, "raw float": func(d *Document) { d.Recipe.XannoronTimer = "0.000001" }, "uppercase hex": func(d *Document) { d.Recipe.HelperOne[0] = "DEADBEEF" }, "before missing": func(d *Document) { delete(d.BeforeSHA256, "YTNEWS.DAT") }, "after target": func(d *Document) { d.SourceSHA256["research/yt-maint/after-YTDATA.DAT.gz"] = OriginalMaintSHA },
		"oracle":          func(d *Document) { d.SourceSHA256["oracles.json"] = OriginalMaintSHA },
		"source control":  func(d *Document) { d.SourceSHA256["scripts/evil"+string(rune(10))+".py"] = OriginalMaintSHA },
		"source identity": func(d *Document) { d.SourceSHA256["archive/dos-original/YTMAINT.EXE"] = strings.Repeat("0", 64) }, "source traversal": func(d *Document) { d.SourceSHA256["../private"] = OriginalMaintSHA }, "source backslash": func(d *Document) { d.SourceSHA256["dir\\private"] = OriginalMaintSHA }, "source stream": func(d *Document) { d.SourceSHA256["file:stream"] = OriginalMaintSHA }, "date missing": func(d *Document) { d.Recipe.Aux.NewsDate = "" }, "port day": func(d *Document) { d.Recipe.Ports.Days[999] = 0 }}
	for n, f := range changes {
		t.Run(n, func(t *testing.T) {
			d := sampleDocument()
			f(&d)
			if _, _, e := Decode(encoded(t, d)); e == nil {
				t.Fatal("invalid recipe admitted")
			}
		})
	}
}
func TestDecodeRejectsDuplicatesUnknownsNullsAndTrailingJSON(t *testing.T) {
	good := string(encoded(t, sampleDocument()))
	bad := []string{strings.Replace(good, `"profile":"initial"`, `"profile":"initial","profile":"initial-wanderer"`, 1), strings.Replace(good, `"profile":"initial"`, `"profile":"initial","PROFILE":"initial"`, 1), strings.Replace(good, `"format":`, `"FORMAT":`, 1), strings.Replace(good, `"initial_state":0`, `"initial_state":null`, 1), strings.Replace(good, `"wanderer_day":1`, `"wanderer_day":null`, 1), strings.Replace(good, `"days":[1,`, `"days":[null,`, 1), strings.Replace(good, `"name":`, `"unexpected":0,"name":`, 1), strings.Replace(good, `"capped":false`, `"capped":0`, 1), good + `{}`, `null`, `[]`, strings.Repeat(" ", MaxRecipeBytes+1), strings.Repeat("[", 100) + strings.Repeat("]", 100)}
	for i, b := range bad {
		if _, _, e := Decode([]byte(b)); e == nil {
			t.Fatal("invalid JSON admitted", i)
		}
	}
}
