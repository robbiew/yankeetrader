package qbmaint

import (
	"bytes"
	"fmt"
	"github.com/robbiew/yankeetrader/internal/qbrng"
)

// GatewayVictoryBattle records unit-round offense against the retained 37 defenders.
type GatewayVictoryBattle struct {
	InitialState, FinalState                                                                uint32
	InitialForce, InitialDefenders, Force, Defenders, Losses, DefenderLosses, Rounds, Draws int
	Gate                                                                                    [4]byte
}

// GatewayVictoryStats keeps casualty accounting separate from uncollected stock.
// Physical columns are Mercenary, Xannor, neutral; rows are before and after.
type GatewayVictoryStats struct {
	InitialState, FinalState                                             uint32
	Draws, TargetDraws, InitialForce, FinalForce, Losses, DefenderLosses int
	Physical                                                             [2][3]int
	DesertionSectors, FinalSectors                                       []int
	Seeds                                                                []ContinuationSeed
	Activations                                                          []FriendlyStockActivation
	Mines                                                                []GatewayMineStats
	Battles                                                              []GatewayVictoryBattle
	EventOrder                                                           []string
}

// ReplayGatewayVictoryMercenary derives the two retained guarded gateway profiles
// and next-day empty-route continuations from modeled bytes/state/source clocks.
// A victory never falls through into stock pickup. Other outcomes, encounters
// and batch combat are refused atomically; older phase admissions stay unchanged.
func ReplayGatewayVictoryMercenary(before []byte, in EvolvedTailInputs) ([]byte, GatewayVictoryStats, error) {
	fail := func(e any) ([]byte, GatewayVictoryStats, error) {
		return nil, GatewayVictoryStats{}, fmt.Errorf("gateway victory: %v", e)
	}
	if len(before) != WorldRecords*RecordSize || in.State > 0xffffff || len(in.Helpers) > 256 {
		return fail("world/state/helper extent")
	}
	work := bytes.Clone(before)
	raw := func(r, o int) [4]byte { a := (r-1)*RecordSize + o; return [4]byte(work[a : a+4]) }
	get := func(r, o int) int {
		v, ok := integer(raw(r, o))
		if !ok {
			return -999999
		}
		return v
	}
	num := func(r, o int) float64 { return portSingleValue(raw(r, o)) }
	putraw := func(r, o int, v [4]byte) { a := (r-1)*RecordSize + o; copy(work[a:a+4], v[:]) }
	for o, n := range map[int]int{53: 51, 57: 3051, 61: 4051, 93: 4151} {
		if get(1, o) != n {
			return fail("default geometry")
		}
	}
	for r := 2; r <= 51; r++ {
		if num(r, 85) != 0 {
			return fail("active humans")
		}
	}
	for r := 3052; r <= 4051; r++ {
		if num(r, 89) != 0 {
			return fail("tax-funded hiring")
		}
	}
	day := get(1, 81)
	if !bytes.Equal(work[4053*137:4053*137+41], []byte(fmt.Sprintf("%-41s", "Gateway Cache"))) || get(4054, 85) != 13 || raw(4054, 73) != [4]byte{} || num(4054, 117) != 0 || get(3051, 93) != 3 {
		return fail("neutral zero-bank Gateway Cache identity")
	}
	first := day == 308
	if first {
		if get(3051, 81) != 37 || get(3051, 85) != -1 || (get(3051, 129) != 0 && get(3051, 129) != 1) || raw(4054, 129) != encode(37) {
			return fail("guarded first-phase context")
		}
	} else if day == 309 {
		if num(3051, 81) != 0 || num(3051, 85) != 0 || num(3051, 129) != 0 || raw(4054, 129) != encode(40) {
			return fail("cleared gateway and grown next-phase stock")
		}
	} else {
		return fail("only two retained phase days")
	}
	var warps [3001][6]int
	s := GatewayVictoryStats{InitialState: in.State}
	initialOrigin := 0
	total := 0
	for sector := 1; sector <= 3000; sector++ {
		r := 51 + sector
		force, owner := get(r, 81), get(r, 85)
		if force < 0 || force > 100000 {
			return fail("bounded whole physical force")
		}
		if force > 0 {
			column := 0
			switch owner {
			case -2:
				column = 0
			case -1:
				column = 1
			case 0:
				column = 2
				if force != 37 {
					return fail("only retained neutral37")
				}
			default:
				return fail("physical owner")
			}
			s.Physical[0][column] += force
			total += force
			s.DesertionSectors = append(s.DesertionSectors, sector)
			if owner == -2 {
				if initialOrigin != 0 {
					return fail("one initial Mercenary deployment")
				}
				initialOrigin = sector
				s.InitialForce = force
				if first {
					if sector != 2368 || force != 97337 || get(r, 93) != 0 || get(r, 129) != 0 {
						return fail("first-phase origin")
					}
				} else if !(sector == 2192 && force == 97303 || sector == 2054 && force == 96779) {
					return fail("retained next-phase origin/force")
				}
			}
		}
		for j := 0; j < 6; j++ {
			n := get(r, 41+j*4)
			if n < 0 || n > 3000 {
				return fail("bounded directed graph")
			}
			warps[sector][j] = n
		}
	}
	if initialOrigin == 0 || total > 110000 || s.Physical[0][1] > 10000 {
		return fail("physical inventory")
	}
	last := float64(-1)
	for _, c := range in.Helpers {
		v := portSingleValue(c.Timer)
		if !(c.Family == 1 && c.Caller == 0x48cf || c.Family == 2 && c.Caller == 0x4aa4) || v < 0 || v >= 60 || v < last {
			return fail("ordered source helper clocks")
		}
		last = v
	}
	rng := qbrng.New(in.State)
	draw := func() float32 { s.Draws++; return rng.Float32() }
	index := 0
	reseed := func(family int, caller uint16) error {
		if index >= len(in.Helpers) {
			return fmt.Errorf("helper clock exhaustion")
		}
		c := in.Helpers[index]
		if c.Family != family || c.Caller != caller {
			return fmt.Errorf("computed helper chronology")
		}
		index++
		old := rng.State()
		rng.RandomizeMBF(c.Timer)
		s.Seeds = append(s.Seeds, ContinuationSeed{Clock: c, OldState: old, SeededState: rng.State()})
		return nil
	}
	for range s.DesertionSectors {
		draw()
	}
	for origin := 3000; origin >= 1; origin-- {
		r := 51 + origin
		force := get(r, 81)
		if force <= 0 || get(r, 85) != -2 {
			continue
		}
		if len(s.Activations) >= 16 || force < 1 || force > 100000 {
			return fail("activation/force guard")
		}
		a := FriendlyStockActivation{MercenaryActivation: MercenaryActivation{Origin: origin, Force: force, Gate: portSingleBytes(draw())}}
		if get(r, 93) > 0 {
			return fail("occupied-origin branch excluded")
		}
		putraw(r, 81, [4]byte{0, 0, 0x28, 0})
		putraw(r, 85, [4]byte{0, 0, 0x28, 0})
		target := 0
		for retry := 0; retry < 64; retry++ {
			if e := reseed(1, 0x48cf); e != nil {
				return fail(e)
			}
			n := int(float32(draw()*3000)) + 1
			s.TargetDraws++
			a.Candidates = append(a.Candidates, n)
			if n != origin {
				target = n
				break
			}
		}
		if target == 0 {
			return fail("same-origin rejection guard")
		}
		var prev [3001]int
		prev[origin] = -1
		queue := []int{origin}
		for i := 0; i < len(queue) && prev[target] == 0; i++ {
			for _, n := range warps[queue[i]] {
				if n != 0 && prev[n] == 0 {
					prev[n] = queue[i]
					queue = append(queue, n)
				}
			}
		}
		if prev[target] == 0 {
			return fail("unreachable target")
		}
		route := []int{target}
		for route[len(route)-1] != origin {
			route = append(route, prev[route[len(route)-1]])
		}
		for i, j := 0, len(route)-1; i < j; i, j = i+1, j-1 {
			route[i], route[j] = route[j], route[i]
		}
		if len(route) < 2 {
			return fail("nonempty directed route")
		}
		a.Target = target
		a.Route = route
		for _, sector := range route[1:] {
			a.Entered = append(a.Entered, sector)
			rr := 51 + sector
			if num(rr, 129) != 0 {
				if !first || sector != 3000 || force != 97337 || get(rr, 129) != 1 || get(rr, 93) != 3 || len(s.Mines) != 0 {
					return fail("only retained one-mine gateway")
				}
				m := GatewayMineStats{InitialState: rng.State(), InitialForce: force, InitialMines: 1}
				if e := reseed(2, 0x4aa4); e != nil {
					return fail(e)
				}
				bound := 10000
				for range 2 {
					bound = int(float32(draw()*float32(bound))) + 1
					m.Draws++
				}
				m.Rolls = []int{bound}
				m.Losses = min(force, bound)
				force -= m.Losses
				m.Force = force
				m.Spent = 1
				m.FinalState = rng.State()
				s.Losses += m.Losses
				s.Mines = append(s.Mines, m)
				s.EventOrder = append(s.EventOrder, "mine")
				putraw(rr, 129, encode(0))
			}
			// Source selects pickup using the owner/link entering this sector. Its
			// negative-owner attack must continue to the NEXT edge after victory.
			if get(rr, 93) > 0 && (get(rr, 85) == 0 || get(rr, 85) == -2) {
				return fail("pickup excluded from guarded-victory profile")
			}
			if get(rr, 81) != 0 {
				if !first || sector != 3000 || get(rr, 81) != 37 || get(rr, 85) != -1 || len(s.Battles) != 0 {
					return fail("only retained gateway defense")
				}
				b := GatewayVictoryBattle{InitialState: rng.State(), InitialForce: force, InitialDefenders: 37, Gate: portSingleBytes(draw())}
				remaining := 37
				// The defender stays <=37, so the both-sides-over-200 batch path is absent.
				for force > 0 && remaining > 0 {
					if b.Rounds >= 200000 {
						return fail("battle round guard")
					}
					if draw() < .5 {
						remaining--
					} else {
						force--
					}
					b.Rounds++
				}
				b.Force = force
				b.Defenders = remaining
				b.Losses = b.InitialForce - force
				b.DefenderLosses = 37 - remaining
				b.Draws = b.Rounds + 1
				b.FinalState = rng.State()
				if force <= 0 || remaining != 0 {
					return fail("only qualified victorious offense")
				}
				putraw(rr, 81, encode(0))
				putraw(rr, 85, encode(0))
				s.Losses += b.Losses
				s.DefenderLosses += b.DefenderLosses
				s.Battles = append(s.Battles, b)
				s.EventOrder = append(s.EventOrder, "attack")
			}
		}
		a.FinalSector = target
		a.FinalForce = force
		putraw(51+target, 81, encode(force))
		putraw(51+target, 85, encode(-2))
		s.Activations = append(s.Activations, a)
	}
	if index != len(in.Helpers) || first && len(s.Battles) != 1 || !first && (len(s.Battles) != 0 || len(s.Mines) != 0) {
		return fail("complete event/clock inventory")
	}
	for sector := 1; sector <= 3000; sector++ {
		force, owner := get(51+sector, 81), get(51+sector, 85)
		if force <= 0 {
			continue
		}
		column := 2
		if owner == -2 {
			column = 0
			s.FinalSectors = append(s.FinalSectors, sector)
			s.FinalForce += force
		} else if owner == -1 {
			column = 1
		}
		s.Physical[1][column] += force
	}
	if s.FinalForce+s.Losses != s.InitialForce || s.Physical[1][1]+s.DefenderLosses != s.Physical[0][1] || s.Physical[1][2] != s.Physical[0][2] {
		return fail("separate faction casualty conservation")
	}
	s.FinalState = rng.State()
	return work, s, nil
}
