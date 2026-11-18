package qbmaint

import (
	"bytes"
	"fmt"
	"github.com/robbiew/yankeetrader/internal/qbrng"
)

// MercenaryDefenseStats records the calculated eager combat gate and unit-round
// losses for the retained small attackers; it is not a general combat primitive.
type MercenaryDefenseStats struct {
	InitialState, FinalState                         uint32
	InitialForce, InitialDefenders, Force, Defenders int
	Losses, DefenderLosses, Rounds, Draws            int
	Gate                                             [4]byte
}

// DefenderStockStats distinguishes a fatal attack from the next extinct scan.
type DefenderStockStats struct {
	InitialState, FinalState uint32
	Draws, TargetDraws       int
	DesertionSectors         []int
	Seeds                    []ContinuationSeed
	Activation               *FriendlyStockActivation
	Battle                   *MercenaryDefenseStats
}

// ReplayDefenderStockMercenary derives the retained fatal Mercenary offense and
// unchanged-stock/extinct next-day phase from modeled bytes/state/source clocks.
// It ends before lottery/reports/final metadata, refuses unsupported outcomes
// atomically and does not widen historical stock or foreign-defense admission.
func ReplayDefenderStockMercenary(before []byte, in EvolvedTailInputs) ([]byte, DefenderStockStats, error) {
	fail := func(e any) ([]byte, DefenderStockStats, error) {
		return nil, DefenderStockStats{}, fmt.Errorf("defender stock: %v", e)
	}
	if len(before) != WorldRecords*RecordSize || in.State > 0xffffff || len(in.Helpers) > 64 {
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
	day, attacker, defenders, stock := get(1, 81), get(2419, 81), get(3051, 81), get(4054, 129)
	admitted := false
	if day == 308 {
		admitted = (attacker == 1 && defenders == 37 && (stock == 0 || stock == 37) || attacker == 37 && (defenders == 37 || defenders == 1000) && stock == 37) && get(2419, 85) == -2
	} else if day == 309 {
		admitted = attacker == 0 && (defenders == 37 && (stock == 3 || stock == 40) || (defenders == 964 || defenders == 1) && stock == 40) && raw(2419, 81) == [4]byte{0, 0, 0x28, 0} && raw(2419, 85) == [4]byte{0, 0, 0x28, 0}
	}
	if !admitted || get(3051, 85) != -1 || get(3051, 93) != 3 || num(3051, 129) != 0 || num(2419, 93) != 0 || num(2419, 129) != 0 || !bytes.Equal(work[4053*137:4053*137+41], []byte(fmt.Sprintf("%-41s", "Gateway Cache"))) || get(4054, 85) != 13 || raw(4054, 73) != [4]byte{} || num(4054, 117) != 0 || raw(4054, 129) != encode(stock) {
		return fail("four fatal/extinct gateway contexts and exact residues")
	}
	var warps [3001][6]int
	s := DefenderStockStats{InitialState: in.State}
	merc, total, xannor := 0, 0, 0
	for sector := 1; sector <= 3000; sector++ {
		r := 51 + sector
		force, owner := get(r, 81), get(r, 85)
		if force < 0 || force > 100000 {
			return fail("whole bounded physical force")
		}
		if force > 0 {
			if owner != 0 && owner != -1 && owner != -2 {
				return fail("physical owner")
			}
			if owner == 0 && force != 37 {
				return fail("only retained neutral37 forces")
			}
			total += force
			if owner == -1 {
				xannor += force
			}
			s.DesertionSectors = append(s.DesertionSectors, sector)
			if owner == -2 {
				if sector != 2368 || force != attacker {
					return fail("single initial attacker or extinction")
				}
				merc += force
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
	if merc != attacker || total > 110000 || xannor > 10000 {
		return fail("actual Mercenary inventory")
	}
	last := float64(-1)
	for _, c := range in.Helpers {
		v := portSingleValue(c.Timer)
		if c.Family != 1 || c.Caller != 0x48cf || v < 0 || v >= 60 || v < last {
			return fail("source target helper clocks")
		}
		last = v
	}
	rng := qbrng.New(in.State)
	draw := func() float32 { s.Draws++; return rng.Float32() }
	for range s.DesertionSectors {
		draw()
	}
	if attacker == 0 {
		if len(in.Helpers) != 0 {
			return fail("extinct phase has no helper calls")
		}
		s.FinalState = rng.State()
		return work, s, nil
	}
	a := &FriendlyStockActivation{MercenaryActivation: MercenaryActivation{Origin: 2368, Force: attacker, Gate: portSingleBytes(draw())}}
	putraw(2419, 81, [4]byte{0, 0, 0x28, 0})
	putraw(2419, 85, [4]byte{0, 0, 0x28, 0})
	target, index := 0, 0
	for retry := 0; retry < 64; retry++ {
		if index >= len(in.Helpers) {
			return fail("target clock exhaustion")
		}
		c := in.Helpers[index]
		index++
		old := rng.State()
		rng.RandomizeMBF(c.Timer)
		s.Seeds = append(s.Seeds, ContinuationSeed{Clock: c, OldState: old, SeededState: rng.State()})
		n := int(float32(draw()*3000)) + 1
		s.TargetDraws++
		a.Candidates = append(a.Candidates, n)
		if n != 2368 {
			target = n
			break
		}
	}
	if target == 0 {
		return fail("same-origin rejection guard")
	}
	var prev [3001]int
	prev[2368] = -1
	queue := []int{2368}
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
	for route[len(route)-1] != 2368 {
		route = append(route, prev[route[len(route)-1]])
	}
	for i, j := 0, len(route)-1; i < j; i, j = i+1, j-1 {
		route[i], route[j] = route[j], route[i]
	}
	if len(route) < 2 || route[1] != 3000 {
		return fail("actual first gateway fatal entry")
	}
	a.Target = target
	a.Route = route
	a.Entered = []int{3000}
	battle := &MercenaryDefenseStats{InitialState: rng.State(), InitialForce: attacker, InitialDefenders: defenders, Gate: portSingleBytes(draw())}
	// Every admitted attacker is <=37, so min(force,defense)<=200 throughout:
	// the original DOUBLE200/150 branch cannot run in this retained profile.
	force, remaining := attacker, defenders
	for force > 0 && remaining > 0 {
		if battle.Rounds >= 200000 {
			return fail("combat round guard")
		}
		if draw() < .5 {
			remaining--
		} else {
			force--
		}
		battle.Rounds++
	}
	battle.Draws = battle.Rounds + 1
	battle.Force = force
	battle.Defenders = remaining
	battle.Losses = attacker - force
	battle.DefenderLosses = defenders - remaining
	battle.FinalState = rng.State()
	if force != 0 || remaining <= 0 {
		return fail("only measured fatal offense with survivors")
	}
	if index != len(in.Helpers) {
		return fail("surplus target helper clocks")
	}
	putraw(3051, 81, encode(remaining))
	// Source does not clear the stale Xannor group-pointer cache or take stock.
	s.Activation = a
	s.Battle = battle
	s.FinalState = rng.State()
	return work, s, nil
}
