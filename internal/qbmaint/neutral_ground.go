package qbmaint

import (
	"bytes"
	"fmt"

	"github.com/robbiew/yankeetrader/internal/qbrng"
)

// NeutralGroundInputs carries modeled encounter context, never an RNG endpoint.
type NeutralGroundInputs struct {
	Group, Sector, Force int
	State                uint32
}

// NeutralGroundStats retains the source's signed final force, separately from
// capped group death. Routing, pointer clearing, pursuit and news are caller work.
type NeutralGroundStats struct {
	InitialForce, RawForce, Force, InitialGround, Ground, Draws int
	InitialState, FinalState                                    uint32
}

// ReplayNeutralGroundAssault models only unscreened neutral Route Haven at sector
// 854/slot2 with ground in (500000,505000]. Each spent ground point destroys
// INT(SINGLE(RND*1000))+1 attackers. Production assault/capture is excluded.
// It returns an owned world with only the ground field changed; errors return
// nil/zero statistics and never mutate inputs or publish partial results.
func ReplayNeutralGroundAssault(before []byte, in NeutralGroundInputs) ([]byte, NeutralGroundStats, error) {
	fail := func(s string) ([]byte, NeutralGroundStats, error) {
		return nil, NeutralGroundStats{}, fmt.Errorf("neutral ground assault: %s", s)
	}
	if len(before) != WorldRecords*RecordSize || in.Group < 2 || in.Group > 20 || in.Sector != 854 || in.Force < 1 || in.Force > 10000 || in.State > 0xffffff {
		return fail("bounded world/group/sector/force/state")
	}
	raw := func(r, o int) [4]byte { a := (r-1)*RecordSize + o; return [4]byte(before[a : a+4]) }
	for o, v := range map[int]int{53: 51, 57: 3051, 61: 4051, 93: 4151} {
		n, ok := integer(raw(1, o))
		if !ok || n != v {
			return fail("default geometry")
		}
	}
	link, ok := integer(raw(905, 93))
	if !ok || link != 2 || raw(905, 81)[3] != 0 || raw(905, 129)[3] != 0 {
		return fail("unscreened slot2 route without mines")
	}
	at := 4052 * RecordSize
	length, named := integer(raw(4053, 85))
	ground := portSingleValue(raw(4053, 77))
	if !named || length != 11 || !bytes.Equal(before[at:at+41], []byte(fmt.Sprintf("%-41s", "Route Haven"))) || raw(4053, 73)[3] != 0 || ground <= 500000 || ground > 505000 {
		return fail("strong neutral Route Haven required")
	}
	stats := NeutralGroundStats{InitialForce: in.Force, RawForce: in.Force, InitialGround: int(ground), Ground: int(ground), InitialState: in.State}
	rng := qbrng.New(in.State)
	for stats.RawForce > 0 {
		if stats.Draws >= 10000 || stats.Ground <= 0 {
			return fail("round/ground bound; production assault excluded")
		}
		stats.Ground--
		// Preserve the source SINGLE multiplication before INT, including the
		// largest 24-bit draw, which yields the maximum damage of 1000.
		damage := int(float32(rng.Float32()*float32(1000))) + 1
		stats.RawForce -= damage
		stats.Draws++
	}
	stats.Force = 0
	stats.FinalState = rng.State()
	world := bytes.Clone(before)
	b := encode(stats.Ground)
	copy(world[at+77:at+81], b[:])
	return world, stats, nil
}
