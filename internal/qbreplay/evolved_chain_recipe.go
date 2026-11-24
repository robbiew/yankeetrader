package qbreplay

import (
	"bytes"
	"encoding/json"
	"fmt"
	"github.com/robbiew/yankeetrader/internal/qbmaint"
	"io"
	"reflect"
	"time"
)

const EvolvedChainFormat = "qbmaint-replay-v4"
const EvolvedChainProfile = "evolved-occupied-three-day"

// EvolvedChainDocument shares clock field shapes, with independent version,
// original-pin/layout and source admission. v1-v3 decoding remains unchanged.
type EvolvedChainDocument ChainDocument

// DecodeEvolvedChain rejects absent/null/duplicate/unknown fields and all oracle
// inputs. Child layouts derive from the declared qualified original, not targets.
func DecodeEvolvedChain(data []byte) (EvolvedChainDocument, []qbmaint.EvolvedOccupiedDayInputs, error) {
	fail := func(e error) (EvolvedChainDocument, []qbmaint.EvolvedOccupiedDayInputs, error) {
		return EvolvedChainDocument{}, nil, e
	}
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
	if e := exactFields(data, reflect.TypeOf(EvolvedChainDocument{})); e != nil {
		return fail(e)
	}
	var d EvolvedChainDocument
	if e := json.Unmarshal(data, &d); e != nil {
		return fail(e)
	}
	if d.Format != EvolvedChainFormat || d.Profile != EvolvedChainProfile || !validName(d.Name) || len(d.Days) != 3 {
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
		if (!evolvedChainSourceReference(n)) || !validHash(h) {
			return fail(fmt.Errorf("invalid source reference/hash: %s", n))
		}
	}
	layout := []int{4052, 4150, 4151}
	first := []int{}
	switch d.BeforeSHA256["YTDATA.DAT"] {
	case "40947d888c7bd9192acfc12d2531d6414fe6392c9c815ead42ea4d28ef6325bf", "0e5d8934af1be3debc72708ecdd3e2825a2c4000398253fc8b793340907669a6", "277c3cadeea74b02596c3d832566ff7de5b39a7a5a1b8edbd9a2ac563edd31b6":
	case "f545d697b28d93910407cfeb7baac96666062ebe3cb5ac3334d6a3e85f5e45b7":
		first = []int{4053}
		layout = []int{4052, 4053, 4150, 4151}
	default:
		return fail(fmt.Errorf("four qualified evolved occupied originals required"))
	}
	result := make([]qbmaint.EvolvedOccupiedDayInputs, 0, 3)
	for index, p := range d.Days {
		records := layout
		if index == 0 {
			records = first
		}
		wantPlanets := len(records)
		if p.Day != 306+index || p.InitialState > 0xffffff || len(p.Ports.Days) != 1000 || len(p.Ports.TimerMinutes) != 1000 || len(p.Planets) != wantPlanets || len(p.HomeHelpers) < 1 || len(p.HomeHelpers) > 256 || len(p.TailHelpers) > 256 {
			return fail(fmt.Errorf("complete ordered day/state/clock inventory required"))
		}
		date := time.Date(2026, 1, p.Day, 0, 0, 0, 0, time.UTC).Format("2006-01-02")
		if p.Aux.NewsDate != date || p.Aux.ScoreDate != date || !reportClock(p.Aux.NewsClock) || !reportClock(p.Aux.ScoreClock) {
			return fail(fmt.Errorf("explicit source report dates/clocks required"))
		}
		r := qbmaint.EvolvedOccupiedDayInputs{Day: p.Day, InitialState: p.InitialState, Ports: qbmaint.EvolvedPortSchedule{Days: append([]int(nil), p.Ports.Days...)}, Reports: qbmaint.AuxInputs{NewsDate: p.Aux.NewsDate, NewsClock: p.Aux.NewsClock, ScoreDate: p.Aux.ScoreDate, ScoreClock: p.Aux.ScoreClock}}
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
func evolvedChainSourceReference(n string) bool {
	return sourceReference(n) || n == "research/yt-maint/evolved-combat-controls/pins.json"
}
