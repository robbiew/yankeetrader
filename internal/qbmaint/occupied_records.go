package qbmaint

import (
	"bytes"
	"crypto/sha256"
	"fmt"
)

// OccupiedInputs supplies only original startup state and explicit source clocks.
// Helpers are separated at the Base-birth boundary; states/events/worlds at
// intermediate phases are calculated internally, never accepted as corrections.
type OccupiedInputs struct {
	StartupState                uint32
	Ports                       PortSchedule
	Planets                     []PlanetClock
	Creation                    ConvergenceCreationClocks
	RoutingHelpers, TailHelpers []ContinuationClock
	FinalDay                    int
	Reports                     AuxInputs
}

// OccupiedStats retains calculated receipts for each composed phase.
type OccupiedStats struct {
	Ports   PortStats
	Planets EvolvedPlanetStats
	Routing OccupiedRoutingStats
	Tail    EvolvedTailStats
	Reports OccupiedReportStats
}

// ReplayOccupiedFiles composes the retained occupied day-306 research profiles
// into six owned DOS files. It performs no IO and does not select modern policy.
// Only pinned original before inputs are admitted; all failures are atomic.
func ReplayOccupiedFiles(before map[string][]byte, in OccupiedInputs) (map[string][]byte, OccupiedStats, error) {
	fail := func(e any) (map[string][]byte, OccupiedStats, error) {
		return nil, OccupiedStats{}, fmt.Errorf("occupied files: %v", e)
	}
	if len(before) != 3 || in.StartupState > 0xffffff || in.FinalDay != 306 || !in.Ports.Capped || in.Reports.NewsDate != "2026-11-02" || in.Reports.ScoreDate != "2026-11-02" {
		return fail("bounded original inputs and day306 chronology")
	}
	for _, name := range []string{"YTDATA.DAT", "YTNAME.DAT", "YTNEWS.DAT"} {
		if _, ok := before[name]; !ok {
			return fail("missing before file")
		}
	}
	world := before["YTDATA.DAT"]
	if !occupiedBeforeHashes[fmt.Sprintf("%x", sha256.Sum256(world))] || fmt.Sprintf("%x", sha256.Sum256(before["YTNAME.DAT"])) != "af3183fabb75a3c5ae25b71abf89bd6c7e19a7470e8363214fe9b9b88923d08f" || fmt.Sprintf("%x", sha256.Sum256(before["YTNEWS.DAT"])) != "1acaf18a99ffc43c85f96b375476c46a1fd25904ffc75d8a93dce829a27e313a" {
		return fail("unmeasured original before files")
	}
	for _, d := range in.Ports.Days {
		if d != 306 {
			return fail("day306 port clocks")
		}
	}
	var s OccupiedStats
	block, p, e := ReplayCleanPorts(world, in.Ports)
	if e != nil {
		return fail(e)
	}
	s.Ports = p
	world = bytes.Clone(world)
	copy(world[PortStart:], block)
	world, s.Planets, e = ReplayOccupiedPlanets(world, OccupiedPlanetInputs{State: in.StartupState, Clocks: in.Planets})
	if e != nil {
		return fail(e)
	}
	world, s.Routing, e = ReplayOccupiedHomeMobile(world, OccupiedRoutingInputs{State: s.Planets.FinalState, Helpers: in.RoutingHelpers, Creation: in.Creation})
	if e != nil {
		return fail(e)
	}
	world, s.Tail, e = ReplayEvolvedNPCTail(world, EvolvedTailInputs{State: s.Routing.FinalState, Helpers: in.TailHelpers})
	if e != nil {
		return fail(e)
	}
	world, e = ReplayInactiveRanks(world, in.FinalDay)
	if e != nil {
		return fail(e)
	}
	files, reports, e := ReplayOccupiedAux(before, world, in.Reports, s.Routing.Events)
	if e != nil {
		return fail(e)
	}
	s.Reports = reports
	files["YTDATA.DAT"] = world
	return files, s, nil
}

var occupiedBeforeHashes = map[string]bool{
	"0e5d8934af1be3debc72708ecdd3e2825a2c4000398253fc8b793340907669a6": true,
	"1522c4e0ebc60b6678825289ba7128174a0e72add90f538f89c63a1f6ebbc008": true,
	"277c3cadeea74b02596c3d832566ff7de5b39a7a5a1b8edbd9a2ac563edd31b6": true,
	"40947d888c7bd9192acfc12d2531d6414fe6392c9c815ead42ea4d28ef6325bf": true,
	"5f758fc6559124ed665fa4d523bf08bb08f99dca71d2047fca11cefa0a13e8a2": true,
	"70e270190c2a4bb9dc246a0d53d5cb270a9df04805a7b70d4fd452d509e8ab2b": true,
	"9d5dcb72ff9fb127e45d3449704af5edbab6abc519af2c707c702df1625db14a": true,
	"f3791778af7ec503dd98e34b030c328c66c4a9e0431fc43dffa5eb1d12816a4c": true,
	"f545d697b28d93910407cfeb7baac96666062ebe3cb5ac3334d6a3e85f5e45b7": true,
	"fae728912fae47d5bc9a64dfc4a6cd1c47a5a25fe022ceca2962f87370088c8a": true,
}
