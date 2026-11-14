package qbmaint

import "fmt"

// InitialRecipe contains explicit source-qualified phase days, measured helper
// TIMERs and the startup state for the admitted ordinary initial world. It is
// not a modern save recipe or an invitation to infer clocks from native targets.
type InitialRecipe struct {
	Ports                                       PortSchedule
	WandererDay, XannoronDay, BaseDay, FinalDay int
	InitialState                                uint32
	HelperOne, HelperTwo                        [][4]byte
	XannoronTimer                               [4]byte
	Aux                                         AuxInputs
}
type InitialStats struct {
	Ports      PortStats
	Wanderer   WandererStats
	Xannoron   XannoronStats
	Mobile     MobileStats
	Base       BaseStats
	Tail       TailStats
	Draws      int
	FinalState uint32
}

// ReplayInitialMaintenance composes only the qualified all-inactive initial
// plain-route profile into six DOS files. It takes original before files and an
// explicit recipe, never after bytes, correction tables, host clocks or modern
// gameplay saves. Unsupported phases return no partial files/statistics.
// Input maps, files and recipe slices are readonly. Outputs own their storage.
func ReplayInitialMaintenance(before map[string][]byte, recipe InitialRecipe) (map[string][]byte, InitialStats, error) {
	fail := func(phase string, e error) (map[string][]byte, InitialStats, error) {
		return nil, InitialStats{}, fmt.Errorf("initial maintenance %s: %w", phase, e)
	}
	if len(before) != 3 || len(recipe.HelperOne) < 41 || len(recipe.HelperOne) > 42 || len(recipe.HelperTwo) != 19 {
		return fail("inventory", fmt.Errorf("three before files and 41/42+19 helpers required"))
	}
	for _, n := range []string{"YTDATA.DAT", "YTNAME.DAT", "YTNEWS.DAT"} {
		if _, ok := before[n]; !ok {
			return fail("inventory", fmt.Errorf("missing %s", n))
		}
	}
	var stats InitialStats
	block, p, e := ReplayCleanPorts(before["YTDATA.DAT"], recipe.Ports)
	if e != nil {
		return fail("ports", e)
	}
	stats.Ports = p
	world := append([]byte(nil), before["YTDATA.DAT"]...)
	copy(world[PortStart:PortStart+len(block)], block)
	world, w, e := ReplayWandererBirth(world, WandererInputs{Day: recipe.WandererDay, State: recipe.InitialState, HelperTimer: recipe.HelperOne[0]})
	if e != nil {
		return fail("Wanderer", e)
	}
	stats.Wanderer = w
	world, x, e := ReplayXannoronBirth(world, XannoronInputs{Day: recipe.XannoronDay, State: w.FinalState, TimerSeconds: recipe.XannoronTimer})
	if e != nil {
		return fail("Xannoron", e)
	}
	stats.Xannoron = x
	mobileIn := MobileInputs{State: x.FinalState}
	copy(mobileIn.HelperOne[:], recipe.HelperOne[1:40])
	copy(mobileIn.HelperTwo[:], recipe.HelperTwo)
	world, m, e := ReplayInitialMobileGroups(world, mobileIn)
	if e != nil {
		return fail("mobile groups", e)
	}
	stats.Mobile = m
	world, b, e := ReplayMercenaryBaseBirth(world, BaseInputs{Day: recipe.BaseDay, State: m.FinalState, HelperTimer: recipe.HelperOne[40]})
	if e != nil {
		return fail("base", e)
	}
	stats.Base = b
	tailIn := TailInputs{State: b.FinalState}
	if len(recipe.HelperOne) == 42 {
		timer := recipe.HelperOne[41]
		tailIn.CandidateTimer = &timer
	}
	t, e := ReplayInitialNPCTail(world, tailIn)
	if e != nil {
		return fail("tail", e)
	}
	stats.Tail = t
	world, e = ReplayInactiveRanks(world, recipe.FinalDay)
	if e != nil {
		return fail("ranks", e)
	}
	out, e := ReplayInitialAux(before, world, recipe.Aux)
	if e != nil {
		return fail("auxiliary", e)
	}
	out["YTDATA.DAT"] = world
	stats.Draws = w.Draws + x.Draws + m.Draws + b.Draws + t.Draws
	stats.FinalState = t.FinalState
	return out, stats, nil
}
