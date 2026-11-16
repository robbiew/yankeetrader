package qbmaint

import (
	"bytes"
	"crypto/sha256"
	"fmt"
)

// ConvergenceCreationClocks supplies only day-one creation observations.
type ConvergenceCreationClocks struct {
	WandererDay, XannoronDay, BaseDay int
	XannoronTimer                     [4]byte
}

// ConvergenceDayInputs contains explicit source clocks and one startup RNG state.
// DOS restarts maintenance each day; state continues between phases within a day,
// while the next day begins with its own independently derived startup seed.
// Neither intermediate worlds nor captured RNG endpoints are accepted.
type ConvergenceDayInputs struct {
	Day                      int
	InitialState             uint32
	Ports                    EvolvedPortSchedule
	Planets                  []PlanetClock
	Creation                 *ConvergenceCreationClocks
	HomeHelpers, TailHelpers []ContinuationClock
	Reports                  AuxInputs
}

// ConvergenceDayResult contains owned six-file output and calculated receipts.
type ConvergenceDayResult struct {
	Files   map[string][]byte
	Ports   EvolvedPortStats
	Planets EvolvedPlanetStats
	Homes   ContinuationStats
	Tail    EvolvedTailStats
}

// ReplayConvergenceChain composes the bounded Go phases across all three retained
// days, using only its own six-file outputs as child inputs. Exact measured initial
// files and three consecutive day recipes are required. Any failure returns nil,
// including a late failure after earlier days were privately computed. Inputs are
// readonly; this API has no filesystem, host clock, native target or correction.
func ReplayConvergenceChain(before map[string][]byte, days []ConvergenceDayInputs) ([]ConvergenceDayResult, error) {
	fail := func(s string) ([]ConvergenceDayResult, error) { return nil, fmt.Errorf("convergence chain: %s", s) }
	pins := map[string]string{
		"YTDATA.DAT": "7e470653aabe81d1d3402d8810aca8e2c745e800d0295abcf575d5d7e2a309d3",
		"YTNAME.DAT": "af3183fabb75a3c5ae25b71abf89bd6c7e19a7470e8363214fe9b9b88923d08f",
		"YTNEWS.DAT": "1acaf18a99ffc43c85f96b375476c46a1fd25904ffc75d8a93dce829a27e313a",
	}
	if len(before) != 3 || len(days) != 3 {
		return fail("exact initial three files and three source days required")
	}
	work := map[string][]byte{}
	for name, pin := range pins {
		b, ok := before[name]
		if !ok || fmt.Sprintf("%x", sha256.Sum256(b)) != pin {
			return fail("unmeasured initial input")
		}
		work[name] = bytes.Clone(b)
	}
	// Validate cross-phase calendar identity before running any phase. The phase
	// APIs retain their own detailed clock, caller and profile validation.
	for index, in := range days {
		if in.Day != 306+index || in.InitialState > 0xffffff || len(in.Ports.Days) != 1000 {
			return fail("consecutive days and bounded startup state required")
		}
		for _, day := range in.Ports.Days {
			if day != in.Day {
				return fail("port date differs from source day")
			}
		}
		for _, clock := range in.Planets {
			if clock.Day != in.Day {
				return fail("planet date differs from source day")
			}
		}
		if (index == 0) != (in.Creation != nil) {
			return fail("creation clocks only on first day")
		}
	}
	results := make([]ConvergenceDayResult, 0, 3)
	for _, in := range days {
		row := ConvergenceDayResult{}
		block, stats, err := ReplayEvolvedPorts(work["YTDATA.DAT"], in.Ports)
		if err != nil {
			return fail(err.Error())
		}
		row.Ports = stats
		world := bytes.Clone(work["YTDATA.DAT"])
		copy(world[PortStart:PortStart+PortCount*RecordSize], block)
		world, row.Planets, err = ReplayEvolvedPlanets(world, EvolvedPlanetInputs{State: in.InitialState, Clocks: in.Planets})
		if err != nil {
			return fail(err.Error())
		}
		if in.Creation != nil {
			c := in.Creation
			world, row.Homes, err = ReplayConvergenceDayOneHomes(world, ConvergenceDayOneInputs{State: row.Planets.FinalState, WandererDay: c.WandererDay, XannoronDay: c.XannoronDay, BaseDay: c.BaseDay, XannoronTimer: c.XannoronTimer, Helpers: in.HomeHelpers})
		} else {
			world, row.Homes, err = ReplayExistingHomeContinuation(world, ContinuationInputs{State: row.Planets.FinalState, Helpers: in.HomeHelpers})
		}
		if err != nil {
			return fail(err.Error())
		}
		world, row.Tail, err = ReplayEvolvedNPCTail(world, EvolvedTailInputs{State: row.Homes.FinalState, Helpers: in.TailHelpers})
		if err != nil {
			return fail(err.Error())
		}
		created := [3]bool{}
		if row.Homes.Births != nil {
			for i, key := range []string{"wanderer", "xannoron", "base"} {
				created[i] = row.Homes.Births.Created[i] == key
			}
		}
		row.Files, err = ReplayEvolvedAux(work, world, EvolvedAuxInputs{AuxInputs: in.Reports, FinalDay: in.Day, Created: created})
		if err != nil {
			return fail(err.Error())
		}
		work = row.Files
		results = append(results, row)
	}
	return results, nil
}
