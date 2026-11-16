package qbmaint

import (
	"fmt"
	"math"
	"math/big"

	"github.com/robbiew/yankeetrader/internal/qbmbf"
)

// EvolvedPortSchedule carries caller-authenticated calendar and raw TIMER/60
// observations for the retained three-day convergence profile.
type EvolvedPortSchedule struct {
	Days         []int
	TimerMinutes [][4]byte
}

// EvolvedPortStats summarizes record writes; this bounded port gate draws no RNG.
type EvolvedPortStats struct {
	Ports, Bytes, Day, RatePromotions int
	ClassCounts                       [3]int
	ElapsedMin, ElapsedMax            [4]byte
	RNGDraws                          int
}

// ReplayEvolvedPorts models only the retained convergence profile: initial day
// 306 followed by consecutive full-stock days 307/308, with zero treasuries and
// asking prices. It returns only the port block. It takes no native target,
// child before-world, RNG or correction inputs; errors return no partial block.
func ReplayEvolvedPorts(before []byte, s EvolvedPortSchedule) ([]byte, EvolvedPortStats, error) {
	fail := func(message string) ([]byte, EvolvedPortStats, error) {
		return nil, EvolvedPortStats{}, fmt.Errorf("evolved ports: %s", message)
	}
	if len(before) != WorldRecords*RecordSize || len(s.Days) != 1000 || len(s.TimerMinutes) != 1000 {
		return fail("default world and complete source schedule required")
	}
	day := s.Days[0]
	if day < 306 || day > 308 {
		return fail("only convergence days 306..308 admitted")
	}
	read := func(b []byte, o int) [4]byte { return [4]byte(b[o : o+4]) }
	for o, n := range map[int]int{53: 51, 57: 3051, 61: 4051, 93: 4151} {
		v, ok := integer(read(before, o))
		if !ok || v != n {
			return fail("default geometry")
		}
	}
	for i, timer := range s.TimerMinutes {
		if s.Days[i] != day {
			return fail("one source day per complete block required")
		}
		v := portSingleValue(timer)
		if v < 0 || v >= 1 {
			return fail("midnight TIMER minutes in [0,1) required")
		}
		if i > 0 && qbmbf.CompareSingle(timer, s.TimerMinutes[i-1]).Carry {
			return fail("nonmonotone clock schedule")
		}
	}
	block := append([]byte(nil), before[PortStart:PortStart+PortCount*RecordSize]...)
	stats := EvolvedPortStats{Ports: 1000, Bytes: len(block), Day: day}
	for i := 0; i < 1000; i++ {
		rec := block[i*RecordSize : (i+1)*RecordSize]
		get := func(o int) float64 { return portSingleValue(read(rec, o)) }
		initial := day == 306
		last := day - 1
		if initial {
			last = 296
		}
		if get(45) != float64(last) || get(101) < 0 || get(101) >= 1 {
			return fail("initial or consecutive source dates/times required")
		}
		if get(89) != 0 || get(97) != 0 {
			return fail("zero treasury/asking-price profile required")
		}
		var rates [3][4]byte
		var stocks [3]*big.Rat
		var coeff [3]int
		for j := 0; j < 3; j++ {
			rates[j] = read(rec, 61+4*j)
			rate := portSingleValue(rates[j])
			stock := get(49 + 4*j)
			if rate < 1000 || rate > 40000 {
				return fail("bounded retained cargo rates")
			}
			v, ok := integer(read(rec, 73+4*j))
			if !ok || v == 0 || v < -100 || v > 100 {
				return fail("original coefficient magnitudes")
			}
			if v < 0 {
				v = -v
			}
			coeff[j] = v
			if initial {
				if get(101) != 0 || stock != 0 || rate != math.Trunc(rate) || rate > 32766 {
					return fail("clean capped initial port required")
				}
			} else if math.Abs(stock-10*rate) > math.Max(1, stock)*math.Ldexp(1, -22) {
				return fail("only retained full-stock evolved inputs")
			}
			stocks[j] = new(big.Rat).SetFloat64(stock)
		}
		delta, ok := qbmbf.SubtractSingle(s.TimerMinutes[i], read(rec, 101))
		if !ok {
			return fail("clock subtraction")
		}
		fraction, e := qbmbf.DivideSingle(delta, encode(1440))
		if e != nil {
			return fail("clock division")
		}
		elapsed, ok := qbmbf.AddSingle(encode(day-last), fraction)
		if !ok {
			return fail("elapsed sum")
		}
		value := portSingleValue(elapsed)
		if value < 0 || value > 10 {
			elapsed = encode(10)
			value = 10
		}
		if !initial && (value < .999 || value > 1.001) {
			return fail("consecutive-day elapsed bound")
		}
		if i == 0 || qbmbf.CompareSingle(elapsed, stats.ElapsedMin).Carry {
			stats.ElapsedMin = elapsed
		}
		if i == 0 || qbmbf.CompareSingle(stats.ElapsedMax, elapsed).Carry {
			stats.ElapsedMax = elapsed
		}
		for j, rate := range rates {
			product, ok := qbmbf.MultiplySingle(rate, elapsed)
			if !ok {
				return fail("single production product")
			}
			// The source retains this sum in its wider array. Rational arithmetic keeps
			// all low bits until the individual SINGLE assignments, including ties.
			stocks[j].Add(stocks[j], new(big.Rat).SetFloat64(portSingleValue(product)))
			threshold := new(big.Rat).Mul(new(big.Rat).SetFloat64(portSingleValue(rate)), big.NewRat(10, 1))
			if stocks[j].Cmp(threshold) > 0 {
				promoted := new(big.Rat).Quo(new(big.Rat).Set(stocks[j]), big.NewRat(10, 1))
				v, _ := promoted.Float32()
				rates[j] = portSingleBytes(v)
				stats.RatePromotions++
			}
		}
		sum, ok := qbmbf.AddSingle(rates[0], rates[1])
		if !ok {
			return fail("rate total")
		}
		sum, ok = qbmbf.AddSingle(sum, rates[2])
		if !ok || portSingleValue(sum) > 1000000 {
			return fail("selected port plague outside profile")
		}
		maximum := new(big.Rat)
		selected := -1
		for j, stock := range stocks {
			if stock.Cmp(maximum) > 0 {
				v, _ := stock.Float32()
				maximum.SetFloat64(float64(v))
				selected = j
			}
		}
		if selected < 0 {
			return fail("positive cargo maximum")
		}
		class := 3 - selected
		stats.ClassCounts[class-1]++
		put := func(o int, v [4]byte) { copy(rec[o:o+4], v[:]) }
		put(41, encode(class))
		put(45, encode(day))
		for j := 0; j < 3; j++ {
			v, _ := stocks[j].Float32()
			put(49+4*j, portSingleBytes(v))
			put(61+4*j, rates[j])
			sign := -1
			if j == selected {
				sign = 1
			}
			put(73+4*j, encode(sign*coeff[j]))
		}
		put(101, s.TimerMinutes[i])
	}
	return block, stats, nil
}

// These adapters are bounded to exact raw SINGLE values. No host float32 is
// used for wider sums; final positive stock/rate quantization is nearest-even,
// matching the independent reference for this retained finite range only.
func portSingleValue(raw [4]byte) float64 {
	if raw[3] == 0 {
		return 0
	}
	m := uint32(raw[0]) | uint32(raw[1])<<8 | uint32(raw[2]&127)<<16 | 1<<23
	v := math.Ldexp(float64(m), int(raw[3])-152)
	if raw[2]&128 != 0 {
		v = -v
	}
	return v
}
func portSingleBytes(value float32) [4]byte {
	if value == 0 {
		return [4]byte{}
	}
	b := math.Float32bits(value)
	m := b & 0x7fffff
	if b>>31 != 0 {
		m |= 0x800000
	}
	return [4]byte{byte(m), byte(m >> 8), byte(m >> 16), byte(((b >> 23) & 255) + 2)}
}
