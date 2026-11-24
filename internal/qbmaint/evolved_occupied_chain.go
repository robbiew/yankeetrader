package qbmaint

import (
	"bytes"
	"crypto/sha256"
	"fmt"
)

// EvolvedOccupiedDayInputs supplies source clocks and one DOS-process startup
// state per day. The shape is shared with convergence recipes; admission is not.
// Creation clocks belong only to day306. No child world or endpoint is accepted.
type EvolvedOccupiedDayInputs ConvergenceDayInputs

// EvolvedOccupiedDayResult owns its six files and calculated receipts. Initial
// is populated only for the existing day306 API; later phase fields describe
// children. Each child's startup seed is independent of the prior final state.
type EvolvedOccupiedDayResult struct {
	Day     int
	Files   map[string][]byte
	Initial *OccupiedStats
	Ports   EvolvedPortStats
	Planets EvolvedPlanetStats
	Mobile  EvolvedOccupiedMobileStats
	Tail    EvolvedOccupiedTailStats
	Reports OccupiedReportStats
}

// ReplayEvolvedOccupiedChain composes the four retained occupied-combat profiles
// across days306..308. Only pinned original three files and three source recipes
// enter. Internally calculated six-file outputs alone supply child input. Any
// error, including a late child/report failure, returns nil results atomically.
func ReplayEvolvedOccupiedChain(before map[string][]byte, days []EvolvedOccupiedDayInputs) ([]EvolvedOccupiedDayResult, error) {
	fail := func(e any) ([]EvolvedOccupiedDayResult, error) {
		return nil, fmt.Errorf("evolved occupied chain: %v", e)
	}
	pins := map[string]bool{
		"40947d888c7bd9192acfc12d2531d6414fe6392c9c815ead42ea4d28ef6325bf": true,
		"0e5d8934af1be3debc72708ecdd3e2825a2c4000398253fc8b793340907669a6": true,
		"277c3cadeea74b02596c3d832566ff7de5b39a7a5a1b8edbd9a2ac563edd31b6": true,
		"f545d697b28d93910407cfeb7baac96666062ebe3cb5ac3334d6a3e85f5e45b7": true,
	}
	if len(before) != 3 || len(days) != 3 || !pins[fmt.Sprintf("%x", sha256.Sum256(before["YTDATA.DAT"]))] {
		return fail("four measured original worlds and three source days required")
	}
	// Validate every cross-phase calendar before calculating any private child.
	for i, d := range days {
		if d.Day != 306+i || d.InitialState > 0xffffff || len(d.Ports.Days) != 1000 || len(d.Ports.TimerMinutes) != 1000 || (i == 0) != (d.Creation != nil) {
			return fail("ordered day/state/clocks/creation inventory")
		}
		for _, day := range d.Ports.Days {
			if day != d.Day {
				return fail("port/source day mismatch")
			}
		}
		for _, clock := range d.Planets {
			if clock.Day != d.Day {
				return fail("planet/source day mismatch")
			}
		}
		date := fmt.Sprintf("2026-11-%02d", i+2)
		if d.Reports.NewsDate != date || d.Reports.ScoreDate != date {
			return fail("separate report/source date mismatch")
		}
	}
	// The original occupied API authenticates side files and all first-day guards.
	first := days[0]
	work, initial, err := ReplayOccupiedFiles(before, OccupiedInputs{StartupState: first.InitialState, Ports: PortSchedule{Days: first.Ports.Days, TimerMinutes: first.Ports.TimerMinutes, Capped: true}, Planets: first.Planets, Creation: *first.Creation, RoutingHelpers: first.HomeHelpers, TailHelpers: first.TailHelpers, FinalDay: first.Day, Reports: first.Reports})
	if err != nil {
		return fail(err)
	}
	results := []EvolvedOccupiedDayResult{{Day: 306, Files: work, Initial: &initial}}
	for _, d := range days[1:] {
		row := EvolvedOccupiedDayResult{Day: d.Day}
		block, ports, e := ReplayEvolvedPorts(work["YTDATA.DAT"], d.Ports)
		if e != nil {
			return fail(e)
		}
		row.Ports = ports
		world := bytes.Clone(work["YTDATA.DAT"])
		copy(world[PortStart:PortStart+PortCount*RecordSize], block)
		world, row.Planets, e = ReplayEvolvedOccupiedPlanets(world, EvolvedPlanetInputs{State: d.InitialState, Clocks: d.Planets})
		if e != nil {
			return fail(e)
		}
		world, row.Mobile, e = ReplayEvolvedOccupiedHomeMobile(world, ContinuationInputs{State: row.Planets.FinalState, Helpers: d.HomeHelpers})
		if e != nil {
			return fail(e)
		}
		world, row.Tail, e = ReplayEvolvedOccupiedTail(world, EvolvedTailInputs{State: row.Mobile.FinalState, Helpers: d.TailHelpers})
		if e != nil {
			return fail(e)
		}
		world, e = ReplayInactiveRanks(world, d.Day)
		if e != nil {
			return fail(e)
		}
		files, reports, e := ReplayEvolvedOccupiedAux(work, world, d.Reports, row.Mobile.Events, row.Tail)
		if e != nil {
			return fail(e)
		}
		row.Reports = reports
		files["YTDATA.DAT"] = world
		row.Files = files
		work = files
		results = append(results, row)
	}
	return results, nil
}
