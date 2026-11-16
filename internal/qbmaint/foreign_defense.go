package qbmaint

import (
	"bytes"
	"fmt"

	"github.com/robbiew/yankeetrader/internal/qbrng"
)

// ForeignDefenseInputs supplies modeled encounter context, never an endpoint.
type ForeignDefenseInputs struct {
	Group, Sector, Force int
	State                uint32
}

// ForeignDefenseStats preserves raw source damage counters separately from
// capped saved survivors. PreferredCleared is a routing instruction, not a write
// to world group pointers; the caller must integrate pursuit and moving forces.
type ForeignDefenseStats struct {
	InitialForce, Force, InitialDefenders, Defenders int
	XDamage, DefenderDamage, Draws                   int
	InitialState, FinalState                         uint32
	PreferredCleared                                 bool
}

// ReplayForeignDefense models only the retained hazard-free sector854 Mercenary
// defense branch. It writes physical defenders and, on defeat, canonical owner
// zero. Routing, moving-group deposition, news and score publication are separate.
// Invalid inputs return nil/zero statistics without mutating caller storage.
func ReplayForeignDefense(before []byte, in ForeignDefenseInputs) ([]byte, ForeignDefenseStats, error) {
	fail := func(s string) ([]byte, ForeignDefenseStats, error) {
		return nil, ForeignDefenseStats{}, fmt.Errorf("foreign defense: %s", s)
	}
	if len(before) != WorldRecords*RecordSize || in.State > 0xffffff || in.Group < 2 || in.Group > 20 || in.Sector != 854 || in.Force < 1 || in.Force > 10000 {
		return fail("bounded world/group/sector/force/state")
	}
	raw := func(r, o int) [4]byte { a := (r-1)*RecordSize + o; return [4]byte(before[a : a+4]) }
	for o, v := range map[int]int{53: 51, 57: 3051, 61: 4051, 93: 4151} {
		n, ok := integer(raw(1, o))
		if !ok || n != v {
			return fail("default geometry")
		}
	}
	r := 51 + in.Sector
	defenders, ok := integer(raw(r, 81))
	owner, owned := integer(raw(r, 85))
	if !ok || defenders < 1 || defenders > 100000 || !owned || owner != -2 {
		return fail("bounded whole Mercenary defense")
	}
	if raw(r, 129)[3] != 0 || raw(r, 93)[3] != 0 {
		return fail("mine or planet hazard")
	}
	rng := qbrng.New(in.State)
	stats := ForeignDefenseStats{InitialForce: in.Force, InitialDefenders: defenders, InitialState: in.State}
	for in.Force-stats.XDamage > 0 && defenders-stats.DefenderDamage > 0 {
		if stats.Draws >= 200000 {
			return fail("round guard")
		}
		left, right := in.Force-stats.XDamage, defenders-stats.DefenderDamage
		batch := 500
		if left > 5000 && right > 5000 {
			batch = 5000
		}
		if left < 500 || right < 500 {
			batch = 1
		}
		// RND is an exact 24-bit fraction. The source equality belongs to defense loss.
		if rng.Float32() > .5 {
			stats.XDamage += batch
		} else {
			stats.DefenderDamage += batch
		}
		stats.Draws++
	}
	stats.Force = max(0, in.Force-stats.XDamage)
	stats.Defenders = max(0, defenders-stats.DefenderDamage)
	stats.FinalState = rng.State()
	stats.PreferredCleared = stats.Defenders == 0
	work := bytes.Clone(before)
	put := func(o, n int) { a := (r-1)*RecordSize + o; b := encode(n); copy(work[a:a+4], b[:]) }
	put(81, stats.Defenders)
	if stats.PreferredCleared {
		put(85, 0)
	}
	return work, stats, nil
}
