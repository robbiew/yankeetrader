package qbreplay

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"reflect"
	"time"

	"github.com/robbiew/yankeetrader/internal/qbmaint"
)

const ChainFormat = "qbmaint-replay-v2"
const ChainProfile = "convergence-three-day"

type ChainPortRecipe struct {
	Days         []int    `json:"days"`
	TimerMinutes []string `json:"timer_minutes"`
}
type PlanetRecipe struct {
	Record       int    `json:"record"`
	Day          int    `json:"day"`
	TimerMinutes string `json:"timer_minutes"`
}
type HelperRecipe struct {
	Family int    `json:"family"`
	Caller uint16 `json:"caller"`
	Timer  string `json:"timer"`
}
type CreationRecipe struct {
	WandererDay   int    `json:"wanderer_day"`
	XannoronDay   int    `json:"xannoron_day"`
	BaseDay       int    `json:"base_day"`
	XannoronTimer string `json:"xannoron_timer"`
}
type ChainDayRecipe struct {
	Day          int              `json:"day"`
	InitialState uint32           `json:"initial_state"`
	Ports        ChainPortRecipe  `json:"ports"`
	Planets      []PlanetRecipe   `json:"planets"`
	Creation     []CreationRecipe `json:"creation"`
	HomeHelpers  []HelperRecipe   `json:"home_helpers"`
	TailHelpers  []HelperRecipe   `json:"tail_helpers"`
	Aux          AuxRecipe        `json:"aux"`
}
type ChainDocument struct {
	Format       string            `json:"format"`
	Profile      string            `json:"profile"`
	Name         string            `json:"name"`
	BeforeSHA256 map[string]string `json:"before_sha256"`
	SourceSHA256 map[string]string `json:"source_sha256"`
	Days         []ChainDayRecipe  `json:"days"`
}

// DecodeChain has an explicit separate schema: no v1 widening, child worlds,
// endpoint states or output oracles. Empty creation arrays are explicit on days
// two/three; null, absent, duplicate and noncanonical fields are refused.
func DecodeChain(data []byte) (ChainDocument, []qbmaint.ConvergenceDayInputs, error) {
	fail := func(e error) (ChainDocument, []qbmaint.ConvergenceDayInputs, error) { return ChainDocument{}, nil, e }
	if len(data) > MaxRecipeBytes {
		return fail(fmt.Errorf("recipe exceeds size limit"))
	}
	scan := json.NewDecoder(bytes.NewReader(data))
	if e := uniqueJSON(scan); e != nil {
		return fail(e)
	}
	if _, e := scan.Token(); e != io.EOF {
		return fail(fmt.Errorf("one JSON document required"))
	}
	if e := exactFields(data, reflect.TypeOf(ChainDocument{})); e != nil {
		return fail(e)
	}
	var d ChainDocument
	if e := json.Unmarshal(data, &d); e != nil {
		return fail(e)
	}
	if d.Format != ChainFormat || d.Profile != ChainProfile || !validName(d.Name) || len(d.Days) != 3 {
		return fail(fmt.Errorf("explicit three-day format/profile/name required"))
	}
	if len(d.BeforeSHA256) != 3 {
		return fail(fmt.Errorf("exact three before hashes required"))
	}
	for _, n := range beforeNames {
		if !validHash(d.BeforeSHA256[n]) {
			return fail(fmt.Errorf("invalid before hash: %s", n))
		}
	}
	if len(d.SourceSHA256) < 1 || len(d.SourceSHA256) > 256 || d.SourceSHA256["archive/dos-original/YTMAINT.EXE"] != OriginalMaintSHA {
		return fail(fmt.Errorf("immutable maintenance identity required"))
	}
	for n, h := range d.SourceSHA256 {
		if (!chainSourceReference(n)) || !validHash(h) {
			return fail(fmt.Errorf("invalid source reference/hash: %s", n))
		}
	}
	result := make([]qbmaint.ConvergenceDayInputs, 0, 3)
	for index, p := range d.Days {
		wantPlanets := 4
		if index == 0 {
			wantPlanets = 1
		}
		if p.Day != 306+index || p.InitialState > 0xffffff || len(p.Ports.Days) != 1000 || len(p.Ports.TimerMinutes) != 1000 || len(p.Planets) != wantPlanets || len(p.HomeHelpers) < 1 || len(p.HomeHelpers) > 256 || len(p.TailHelpers) > 256 {
			return fail(fmt.Errorf("complete ordered day/state/clock inventory required"))
		}
		date := time.Date(2026, 1, p.Day, 0, 0, 0, 0, time.UTC).Format("2006-01-02")
		if p.Aux.NewsDate != date || p.Aux.ScoreDate != date || !reportClock(p.Aux.NewsClock) || !reportClock(p.Aux.ScoreClock) {
			return fail(fmt.Errorf("explicit source report dates/clocks required"))
		}
		r := qbmaint.ConvergenceDayInputs{Day: p.Day, InitialState: p.InitialState, Ports: qbmaint.EvolvedPortSchedule{Days: append([]int(nil), p.Ports.Days...)}, Reports: qbmaint.AuxInputs{NewsDate: p.Aux.NewsDate, NewsClock: p.Aux.NewsClock, ScoreDate: p.Aux.ScoreDate, ScoreClock: p.Aux.ScoreClock}}
		for i, s := range p.Ports.TimerMinutes {
			if p.Ports.Days[i] != p.Day {
				return fail(fmt.Errorf("mixed port day"))
			}
			raw, e := rawSingle(s)
			if e != nil {
				return fail(e)
			}
			r.Ports.TimerMinutes = append(r.Ports.TimerMinutes, raw)
		}
		records := []int{4052, 4053, 4150, 4151}
		if index == 0 {
			records = []int{4053}
		}
		for i, c := range p.Planets {
			if c.Day != p.Day || c.Record != records[i] {
				return fail(fmt.Errorf("ordered planet calendar required"))
			}
			raw, e := rawSingle(c.TimerMinutes)
			if e != nil {
				return fail(e)
			}
			r.Planets = append(r.Planets, qbmaint.PlanetClock{Record: c.Record, Day: c.Day, TimerMinutes: raw})
		}
		if index == 0 {
			if len(p.Creation) != 1 {
				return fail(fmt.Errorf("one first-day creation clock set required"))
			}
			c := p.Creation[0]
			if c.WandererDay != p.Day || c.XannoronDay != p.Day || c.BaseDay != p.Day {
				return fail(fmt.Errorf("same-day creation dates required"))
			}
			raw, e := rawSingle(c.XannoronTimer)
			if e != nil {
				return fail(e)
			}
			r.Creation = &qbmaint.ConvergenceCreationClocks{WandererDay: c.WandererDay, XannoronDay: c.XannoronDay, BaseDay: c.BaseDay, XannoronTimer: raw}
		} else if len(p.Creation) != 0 {
			return fail(fmt.Errorf("creation clocks only on first day"))
		}
		for _, entry := range []struct {
			in  []HelperRecipe
			out *[]qbmaint.ContinuationClock
		}{{p.HomeHelpers, &r.HomeHelpers}, {p.TailHelpers, &r.TailHelpers}} {
			for _, c := range entry.in {
				if c.Family != 1 && c.Family != 2 {
					return fail(fmt.Errorf("helper family 1 or 2 required"))
				}
				raw, e := rawSingle(c.Timer)
				if e != nil {
					return fail(e)
				}
				*entry.out = append(*entry.out, qbmaint.ContinuationClock{Family: c.Family, Caller: c.Caller, Timer: raw})
			}
		}
		result = append(result, r)
	}
	return d, result, nil
}
func reportClock(s string) bool {
	if s == "24:00:00" {
		return true
	}
	v, e := time.Parse("15:04:05", s)
	return e == nil && v.Format("15:04:05") == s
}

func chainSourceReference(n string) bool {
	return sourceReference(n) || n == "research/yt-maint/convergence-chain-controls/pins.json" || n == "research/yt-maint/occupied-route-controls/pins.json" || n == "research/yt-maint/placement-cache-controls/pins.json"
}
