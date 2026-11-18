package qbmaint

import (
	"bytes"
	"fmt"
	"github.com/robbiew/yankeetrader/internal/qbmbf"
	"github.com/robbiew/yankeetrader/internal/qbrng"
)

// ClearGatewayStockStats separates entering-force receipt text from converted stock.
// The shared receipt shape does not expand the historical friendly-garrison API.
type ClearGatewayStockStats FriendlyStockStats

// ReplayClearGatewayStockMercenary derives the retained twelve positive SINGLE
// stock contexts. It ends after the Mercenary phase, before lottery/publication.
// Unsupported worlds, routes and clock inventories fail without modifying input.
func ReplayClearGatewayStockMercenary(before []byte, in EvolvedTailInputs) ([]byte, ClearGatewayStockStats, error) {
	fail := func(e any) ([]byte, ClearGatewayStockStats, error) {
		return nil, ClearGatewayStockStats{}, fmt.Errorf("clear gateway stock: %v", e)
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
	governor, stock := get(4054, 73), raw(4054, 129)
	admitted := false
	for _, value := range []float32{.25, .5, .75, 1.5, 2.5, 189528.484375, 189528.5, 189528.515625, 189529.5, 0.9999999403953552, 1.0000001192092896, 32767.5} {
		if stock == portSingleBytes(value) {
			admitted = true
		}
	}
	if !admitted || num(3051, 81) != 0 || num(3051, 85) != 0 || get(3051, 93) != 3 || num(3051, 129) != 0 || governor != 0 || raw(4054, 73) != [4]byte{} || !bytes.Equal(work[4053*137:4053*137+41], []byte(fmt.Sprintf("%-41s", "Gateway Cache"))) || get(4054, 85) != 13 || num(4054, 117) != 0 || get(1, 81) != 308 {
		return fail("twelve exact positive stock and clear neutral gateway contexts")
	}
	if get(2419, 81) != 97337 || get(2419, 85) != -2 || num(2419, 93) != 0 || num(2419, 129) != 0 {
		return fail("measured incoming origin")
	}
	var warps [3001][6]int
	s := ClearGatewayStockStats{InitialState: in.State}
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
				if sector != 2368 {
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
	if total > 410000 || xannor > 10000 || merc != 97337 {
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
	index := 0
	for origin := 3000; origin >= 1; origin-- {
		force := get(51+origin, 81)
		if force <= 0 || get(51+origin, 85) != -2 {
			continue
		}
		gate := draw()
		a := FriendlyStockActivation{MercenaryActivation: MercenaryActivation{Origin: origin, Force: force, Gate: portSingleBytes(gate)}}
		if origin != 2368 || len(s.Activations) != 0 {
			return fail("single incoming activation")
		}
		putraw(2419, 81, [4]byte{0, 0, 0x28, 0})
		putraw(2419, 85, [4]byte{0, 0, 0x28, 0})
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
		if len(route) < 2 || route[1] != 3000 {
			return fail("actual first gateway encounter required")
		}
		amount, ok := integer(qbmbf.IntSingle(stock))
		if !ok || amount < 0 {
			return fail("bounded positive SINGLE INT")
		}
		combined, final := 97337, 97337+amount
		if final > 400000 {
			return fail("combined force guard")
		}
		putraw(4054, 129, [4]byte{0, 0, 0x80, 0})
		putraw(3051, 81, encode(final))
		putraw(3051, 85, encode(-2))
		s.Pickup = FriendlyStockPickup{Incoming: 97337, Friendly: 0, Actor: combined, Amount: amount, Force: final, Governor: governor, RawStock: stock, FractionalDiscard: portSingleValue(stock) - float64(amount), Taking: amount > 0}
		a.Target = target
		a.Route = route
		a.Entered = []int{3000}
		a.FinalSector = 3000
		a.FinalForce = final
		a.StoppedForPickup = true
		s.Activations = append(s.Activations, a)
	}
	if len(s.Activations) != 1 || index != len(in.Helpers) {
		return fail("complete single-activation clock inventory")
	}
	final := 0
	for sector := 1; sector <= 3000; sector++ {
		if get(51+sector, 81) > 0 && get(51+sector, 85) == -2 {
			if sector != 3000 {
				return fail("unexpected final deployment")
			}
			final += get(51+sector, 81)
		}
	}
	if final != merc+s.Pickup.Amount {
		return fail("physical pickup conservation")
	}
	s.FinalState = rng.State()
	return work, s, nil
}
