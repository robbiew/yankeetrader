package qbreplay

import (
	"bytes"
	"encoding/json"
	"fmt"
	"github.com/robbiew/yankeetrader/internal/qbmaint"
	"io"
	"reflect"
)

const OccupiedFormat = "qbmaint-replay-v3"
const OccupiedProfile = "occupied-day306"

type OccupiedRecipe struct {
	InitialState   uint32         `json:"initial_state"`
	Ports          PortRecipe     `json:"ports"`
	Planets        []PlanetRecipe `json:"planets"`
	Creation       CreationRecipe `json:"creation"`
	RoutingHelpers []HelperRecipe `json:"routing_helpers"`
	TailHelpers    []HelperRecipe `json:"tail_helpers"`
	FinalDay       int            `json:"final_day"`
	Aux            AuxRecipe      `json:"aux"`
}
type OccupiedDocument struct {
	Format       string            `json:"format"`
	Profile      string            `json:"profile"`
	Name         string            `json:"name"`
	BeforeSHA256 map[string]string `json:"before_sha256"`
	SourceSHA256 map[string]string `json:"source_sha256"`
	Recipe       OccupiedRecipe    `json:"recipe"`
}

// DecodeOccupied admits an explicit standalone research schema. Missing/null,
// duplicate, noncanonical or oracle fields never fall through to older profiles.
func DecodeOccupied(data []byte) (OccupiedDocument, qbmaint.OccupiedInputs, error) {
	fail := func(e any) (OccupiedDocument, qbmaint.OccupiedInputs, error) {
		return OccupiedDocument{}, qbmaint.OccupiedInputs{}, fmt.Errorf("occupied recipe: %v", e)
	}
	if len(data) > MaxRecipeBytes {
		return fail("recipe exceeds size limit")
	}
	scan := json.NewDecoder(bytes.NewReader(data))
	if e := uniqueJSON(scan); e != nil {
		return fail(e)
	}
	if _, e := scan.Token(); e != io.EOF {
		return fail("one JSON document required")
	}
	if e := exactFields(data, reflect.TypeOf(OccupiedDocument{})); e != nil {
		return fail(e)
	}
	var d OccupiedDocument
	if e := json.Unmarshal(data, &d); e != nil {
		return fail(e)
	}
	if d.Format != OccupiedFormat || d.Profile != OccupiedProfile || !validName(d.Name) {
		return fail("explicit occupied format/profile/name")
	}
	if len(d.BeforeSHA256) != 3 {
		return fail("three before hashes")
	}
	for _, n := range beforeNames {
		if !validHash(d.BeforeSHA256[n]) {
			return fail("before hash")
		}
	}
	if len(d.SourceSHA256) < 1 || len(d.SourceSHA256) > 256 || d.SourceSHA256["archive/dos-original/YTMAINT.EXE"] != OriginalMaintSHA {
		return fail("immutable original maintenance identity")
	}
	for n, h := range d.SourceSHA256 {
		if !(sourceReference(n) || n == "research/yt-maint/occupied-route-controls/pins.json" || n == "research/yt-maint/occupied-replay-native/rea.json") || !validHash(h) {
			return fail("bounded source reference/hash")
		}
	}
	p := d.Recipe
	if p.InitialState > 0xffffff || p.FinalDay != 306 || p.Ports.Capped == nil || !*p.Ports.Capped || len(p.Ports.Days) != 1000 || len(p.Ports.TimerMinutes) != 1000 || len(p.Planets) > 2 || len(p.RoutingHelpers) < 1 || len(p.RoutingHelpers) > 256 || len(p.TailHelpers) > 256 {
		return fail("bounded complete source clock inventory")
	}
	if p.Aux.NewsDate != "2026-11-02" || p.Aux.ScoreDate != "2026-11-02" || !reportClock(p.Aux.NewsClock) || !reportClock(p.Aux.ScoreClock) {
		return fail("day306 report calendars/clocks")
	}
	r := qbmaint.OccupiedInputs{StartupState: p.InitialState, FinalDay: p.FinalDay, Ports: qbmaint.PortSchedule{Capped: true, Days: append([]int(nil), p.Ports.Days...)}, Reports: qbmaint.AuxInputs{NewsDate: p.Aux.NewsDate, NewsClock: p.Aux.NewsClock, ScoreDate: p.Aux.ScoreDate, ScoreClock: p.Aux.ScoreClock}}
	for i, s := range p.Ports.TimerMinutes {
		if p.Ports.Days[i] != 306 {
			return fail("same day306 port calendars")
		}
		raw, e := rawSingle(s)
		if e != nil {
			return fail(e)
		}
		r.Ports.TimerMinutes = append(r.Ports.TimerMinutes, raw)
	}
	for i, c := range p.Planets {
		if c.Record != 4053+i || c.Day != 306 {
			return fail("ascending ordinary planet source clocks")
		}
		raw, e := rawSingle(c.TimerMinutes)
		if e != nil {
			return fail(e)
		}
		r.Planets = append(r.Planets, qbmaint.PlanetClock{Record: c.Record, Day: c.Day, TimerMinutes: raw})
	}
	c := p.Creation
	if c.WandererDay != 306 || c.XannoronDay != 306 || c.BaseDay != 306 {
		return fail("creation dates")
	}
	raw, e := rawSingle(c.XannoronTimer)
	if e != nil {
		return fail(e)
	}
	r.Creation = qbmaint.ConvergenceCreationClocks{WandererDay: 306, XannoronDay: 306, BaseDay: 306, XannoronTimer: raw}
	for _, entry := range []struct {
		in   []HelperRecipe
		out  *[]qbmaint.ContinuationClock
		tail bool
	}{{p.RoutingHelpers, &r.RoutingHelpers, false}, {p.TailHelpers, &r.TailHelpers, true}} {
		for _, c := range entry.in {
			if c.Family != 1 && c.Family != 2 || entry.tail && c.Family != 1 {
				return fail("helper family")
			}
			raw, e := rawSingle(c.Timer)
			if e != nil {
				return fail(e)
			}
			*entry.out = append(*entry.out, qbmaint.ContinuationClock{Family: c.Family, Caller: c.Caller, Timer: raw})
		}
	}
	return d, r, nil
}
