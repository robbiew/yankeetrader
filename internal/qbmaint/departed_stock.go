package qbmaint

import (
	"bytes"
	"fmt"
	"github.com/robbiew/yankeetrader/internal/qbmbf"
	"github.com/robbiew/yankeetrader/internal/qbrng"
)

// DepartedStockStats separates the local group's later deployment from the
// incoming pickup actor. Captured reflects cached physical force, not governor.
type DepartedStockStats struct {
	FriendlyStockStats
	Captured      bool
	FinalSectors  []int
	PhysicalForce int
}

// ReplayDepartedStockMercenary derives the retained held/departed local group,
// incoming pickup and lower-sector same-scan activations from modeled phase bytes
// and explicit clocks. It ends before lottery/reports and fails atomically.
// The held-only API retains its original admission and is not widened.
func ReplayDepartedStockMercenary(before []byte, in EvolvedTailInputs) ([]byte, DepartedStockStats, error) {
	fail := func(e any) ([]byte, DepartedStockStats, error) {
		return nil, DepartedStockStats{}, fmt.Errorf("departed stock: %v", e)
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
	putraw := func(r, o int, b [4]byte) { a := (r-1)*RecordSize + o; copy(work[a:a+4], b[:]) }
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
	friendly, governor, stock := get(3051, 81), get(4054, 73), raw(4054, 129)
	admitted := false
	for _, c := range []struct {
		f, g int
		s    float32
	}{{37, 0, 0}, {37, 0, .5}, {37, 0, 37}, {37, -2, 37}} {
		if friendly == 37 && friendly == c.f && governor == c.g && stock == portSingleBytes(c.s) {
			admitted = true
		}
	}
	if !admitted || get(3051, 85) != -2 || get(3051, 93) != 3 || num(3051, 129) != 0 || !bytes.Equal(work[4053*137:4053*137+41], []byte(fmt.Sprintf("%-41s", "Gateway Cache"))) || get(4054, 85) != 13 || num(4054, 117) != 0 {
		return fail("exact departed gateway contexts")
	}
	if get(2419, 81) != 97337 || get(2419, 85) != -2 || num(2419, 93) != 0 || num(2419, 129) != 0 {
		return fail("measured incoming origin")
	}
	var warps [3001][6]int
	s := DepartedStockStats{FriendlyStockStats: FriendlyStockStats{InitialState: in.State}}
	total, merc, xannor := 0, 0, 0
	for sector := 1; sector <= 3000; sector++ {
		r := 51 + sector
		force, owner := get(r, 81), get(r, 85)
		if force < 0 || force > 400000 {
			return fail("bounded whole physical force")
		}
		if force > 0 {
			if owner != 0 && owner != -1 && owner != -2 {
				return fail("physical owner")
			}
			if owner == 0 && force != 37 {
				return fail("only retained neutral37 physical force")
			}
			if owner == -1 {
				xannor += force
			}
			s.DesertionSectors = append(s.DesertionSectors, sector)
			total += force
			if owner == -2 {
				merc += force
				if sector != 2368 && sector != 3000 {
					return fail("additional Mercenary origin")
				}
			}
		}
		for j := 0; j < 6; j++ {
			n := get(r, 41+4*j)
			if n < 0 || n > 3000 {
				return fail("bounded directed graph")
			}
			warps[sector][j] = n
		}
	}
	if total > 410000 || xannor > 10000 || merc != 97337+friendly {
		return fail("physical force inventory")
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
	index, pickups, incoming := 0, 0, 0
	for origin := 3000; origin >= 1; origin-- {
		force := get(51+origin, 81)
		if force <= 0 || get(51+origin, 85) != -2 {
			continue
		}
		if len(s.Activations) >= 16 || origin != 2368 && force != 37 || origin == 2368 && force != 97337 {
			return fail("bounded local/incoming activation")
		}
		if len(s.Activations) == 0 && origin != 3000 {
			return fail("descending local activation first")
		}
		if origin == 2368 {
			incoming++
			if incoming != 1 {
				return fail("incoming activation once")
			}
		}
		gate := draw()
		a := FriendlyStockActivation{MercenaryActivation: MercenaryActivation{Origin: origin, Force: force, Gate: portSingleBytes(gate)}}
		if get(51+origin, 93) > 0 && gate < float32(.66) {
			if origin != 3000 || force != 37 {
				return fail("only local gateway hold")
			}
			a.Held = true
			s.Activations = append(s.Activations, a)
			continue
		}
		putraw(51+origin, 81, [4]byte{0, 0, 0x28, 0})
		putraw(51+origin, 85, [4]byte{0, 0, 0x28, 0})
		target := 0
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
			return fail("nonempty source route")
		}
		a.Target = target
		a.Route = route
		for _, sector := range route[1:] {
			a.Entered = append(a.Entered, sector)
			r := 51 + sector
			if num(r, 129) != 0 {
				return fail("mine encounter")
			}
			if get(r, 93) > 0 {
				if sector != 3000 || origin != 2368 || force != 97337 || pickups != 0 {
					return fail("only incoming gateway pickup")
				}
				local, owner := get(r, 81), get(r, 85)
				if (local != 0 && local != 37) || (owner != 0 && owner != -2) || local > 0 && owner != -2 {
					return fail("cached empty/friendly gateway")
				}
				amount, ok := integer(qbmbf.IntSingle(stock))
				if !ok || amount < 0 {
					return fail("bounded positive SINGLE INT")
				}
				actor, final := force+local, force+local+amount
				if final > 400000 {
					return fail("combined force guard")
				}
				putraw(4054, 129, [4]byte{0, 0, 0x80, 0})
				putraw(r, 81, encode(final))
				putraw(r, 85, encode(-2))
				s.Pickup = FriendlyStockPickup{Incoming: force, Friendly: local, Actor: actor, Amount: amount, Force: final, Governor: governor, RawStock: stock, FractionalDiscard: portSingleValue(stock) - float64(amount), Taking: amount > 0}
				s.Captured = local == 0
				pickups++
				force = final
				a.StoppedForPickup = true
				a.FinalSector = sector
				break
			}
			if get(r, 81) != 0 {
				return fail("merge or foreign defense excluded")
			}
		}
		if !a.StoppedForPickup {
			a.FinalSector = target
			putraw(51+target, 81, encode(force))
			putraw(51+target, 85, encode(-2))
		}
		a.FinalForce = force
		s.Activations = append(s.Activations, a)
	}
	if incoming != 1 || pickups != 1 || len(s.Activations) < 2 || index != len(in.Helpers) {
		return fail("complete mutable scan/clock inventory")
	}
	for sector := 1; sector <= 3000; sector++ {
		if get(51+sector, 81) > 0 && get(51+sector, 85) == -2 {
			s.FinalSectors = append(s.FinalSectors, sector)
			s.PhysicalForce += get(51+sector, 81)
		}
	}
	if s.PhysicalForce != merc+s.Pickup.Amount {
		return fail("separate local and pickup force conservation")
	}
	s.FinalState = rng.State()
	return work, s, nil
}
