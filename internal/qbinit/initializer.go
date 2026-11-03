// Package qbinit constructs bounded original pre-maintenance initializer bytes.
// It is a source generator, not a playable-world constructor or DOS save importer.
// It preserves original defects and FIELD/FAC residues for verified replay.
package qbinit

import (
	"encoding/binary"
	"errors"
	"fmt"
	"math"
	"strings"
	"time"

	"github.com/robbiew/yankeetrader/internal/qbrng"
)

const (
	RecordSize  = 137
	RecordCount = 4151
	SectorCount = 3000
	PortCount   = 1000
	// DefaultDrawLimit bounds rejected rows/placements and zero shortcut steps.
	// Exhaustion returns no source bytes; it never substitutes a different map.
	DefaultDrawLimit uint64 = 1_000_000
)

// Options supplies the post-RANDOMIZE, pre-first-RND state and a source date.
// Date is YYYY-MM-DD in the bounded 2026..2028 range. Empty Scoreboard selects
// YTSCORE.ASC; it is a record field, never a filesystem destination.
// DrawLimit zero selects DefaultDrawLimit; callers may lower, but not raise it.
type Options struct {
	State      uint32
	Date       string
	Scoreboard string
	DrawLimit  uint64
}

// Stats describes the source stream, before any modern projection/bootstrap.
type Stats struct {
	HQ                  int
	Draws               uint64
	FinalState          uint32
	GraphDraws          uint64
	GraphState          uint32
	PlacementDraws      uint64
	PlacementRejections int
	PlacementState      uint32
	RepairPairs         int
	ShortcutWrites      int
}

// Result owns its complete source bytes. No active world or file is published.
type Result struct {
	Bytes []byte
	Stats Stats
}

// ErrDrawLimit reports exhaustion without returning a partial source candidate.
var ErrDrawLimit = errors.New("QB initializer draw limit exhausted")

type engine struct {
	rng          *qbrng.Generator
	draws, limit uint64
	err          error
	table        [SectorCount + 1][6]int
}

func (e *engine) next() float32 {
	if e.err != nil {
		return 0
	}
	if e.draws == e.limit {
		e.err = ErrDrawLimit
		return 0
	}
	e.draws++
	return e.rng.Float32()
}

func (e *engine) integer(bound int) int {
	return int(float32(e.next()*float32(bound))) + 1
}

// Generate reproduces the bounded original record writers and random draw order.
// Errors return an empty Result, including when work limits are exhausted.
func Generate(o Options) (Result, error) {
	if o.State > 0xffffff {
		return Result{}, errors.New("QB state exceeds 24 bits")
	}
	date, err := time.Parse("2006-01-02", o.Date)
	if err != nil || date.Format("2006-01-02") != o.Date || date.Year() < 2026 || date.Year() > 2028 {
		return Result{}, errors.New("QB source date must be YYYY-MM-DD in 2026..2028")
	}
	if o.Scoreboard == "" {
		o.Scoreboard = "YTSCORE.ASC"
	}
	if len(o.Scoreboard) > 41 {
		return Result{}, errors.New("QB scoreboard exceeds 41 bytes")
	}
	for _, b := range []byte(o.Scoreboard) {
		if b < 32 || b > 126 {
			return Result{}, errors.New("QB scoreboard requires printable ASCII")
		}
	}
	if o.DrawLimit > DefaultDrawLimit {
		return Result{}, errors.New("QB draw limit exceeds bounded maximum")
	}
	if o.DrawLimit == 0 {
		o.DrawLimit = DefaultDrawLimit
	}
	e := &engine{rng: qbrng.New(o.State), limit: o.DrawLimit}
	hq := int(float32(float32(e.next()*2993) + 1))
	if err := e.graph(); err != nil {
		return Result{}, err
	}
	stats := Stats{HQ: hq}
	stats.RepairPairs, stats.ShortcutWrites = e.repairsAndShortcuts()
	if e.err != nil {
		return Result{}, e.err
	}
	// Graph endpoint includes repair and Earth shortcuts.
	stats.GraphDraws, stats.GraphState = e.draws, e.rng.State()
	data := make([]byte, RecordSize*RecordCount)
	config := data[:RecordSize]
	text(config, o.Scoreboard)
	day := date.YearDay()
	for offset, value := range map[int]int{41: len(o.Scoreboard), 45: date.Year() % 100, 49: 500, 53: 51, 57: 3051, 61: 4051, 65: 25, 69: 1005, 73: 10, 77: 14, 81: day - 1, 85: -1, 93: 4151, 101: 5, 105: 300, 117: hq, 121: 1000, 125: 6324} {
		put(config, offset, value)
	}
	if day == 1 {
		fac := mbf((date.Year() % 100) / 4)
		fac[3] = 0
		copy(config[81:85], fac[:])
	}
	for id := 2; id <= 51; id++ {
		text(record(data, id), "")
	}
	for sector := 1; sector <= SectorCount; sector++ {
		r := record(data, 51+sector)
		text(r, "")
		fac := mbf(sector + 51)
		binary.LittleEndian.PutUint16(fac[:2], uint16(sector))
		for col, to := range e.table[sector] {
			if to != 0 {
				fac = mbf(to)
			} else {
				fac[3] = 0
			}
			copy(r[41+4*col:45+4*col], fac[:])
		}
	}
	if err := e.ports(data, day, hq, &stats); err != nil {
		return Result{}, err
	}
	put(record(data, 51+hq), 81, 10000)
	put(record(data, 51+hq), 85, -1)
	put(record(data, 52), 105, hq)
	for id := 4052; id <= RecordCount; id++ {
		r := record(data, id)
		copy(r, config)
		put(r, 85, 0)
	}
	stats.Draws, stats.FinalState = e.draws, e.rng.State()
	return Result{Bytes: data, Stats: stats}, nil
}

func (e *engine) graph() error {
	for c := 0; c < 6; c++ {
		e.table[1][c] = c + 1
		e.table[c+1][c] = 1
	}
	for s := 1; s <= SectorCount; s++ {
		for e.err == nil {
			for c := 0; c < 6; c++ {
				if e.next() <= float32(.4) && c < 5 {
					offset := e.integer(10)
					if s > SectorCount-10 {
						offset = -offset
					}
					to := s + offset
					if to < 1 || to > SectorCount {
						return errors.New("original QB local index outside universe")
					}
					if e.table[s][c] == 0 && e.table[to][c] == 0 && !has(e.table[s], to) && !has(e.table[to], s) {
						e.table[s][c] = to
						e.table[to][c] = s
					}
				}
				if c == 5 && e.table[s][5] == 0 {
					for e.err == nil {
						if e.next() < float32(.985) {
							break
						}
						to := e.integer(SectorCount)
						if to == s {
							continue
						}
						if e.table[to][5] == 0 {
							e.table[s][5] = to
							e.table[to][5] = s
						}
						break
					}
				}
			}
			if s == 1 || e.table[s] != [6]int{} {
				break
			}
		}
		if e.err != nil {
			return e.err
		}
	}
	return nil
}

func (e *engine) repairsAndShortcuts() (int, int) {
	var seen [SectorCount + 1]bool
	pairs := 0
	for target := 2; target <= SectorCount && e.err == nil; target++ {
		if seen[target] {
			continue
		}
		var prev [SectorCount + 1]int
		prev[1] = -1
		queue := make([]int, 1, SectorCount+1)
		queue[0] = 1
		for head := 0; head < len(queue) && prev[target] == 0; head++ {
			current := queue[head]
			for _, n := range e.table[current] {
				if prev[n] == 0 {
					prev[n] = current
					queue = append(queue, n)
					seen[n] = true
				}
			}
		}
		if prev[target] != 0 {
			continue
		}
		for e.err == nil {
			source := e.integer(target - 1)
			if e.table[source][5] == 0 {
				e.table[source][5] = target
				e.table[target][5] = source
				pairs++
				break
			}
		}
	}
	writes := 0
	position := float32(8 + float32(400*e.next()))
	for position < SectorCount && e.err == nil {
		sector := int(math.Floor(float64(position) + .5))
		if e.table[sector][5] == 0 {
			e.table[sector][5] = 1
			writes++
		}
		position = float32(position + float32(400*e.next()))
	}
	return pairs, writes
}

func (e *engine) ports(data []byte, day, hq int, stats *Stats) error {
	start := e.draws
	locations := make([]int, 4, PortCount)
	copy(locations, []int{1, 3, 5, 7})
	var occupied [SectorCount + 1]bool
	for _, s := range []int{1, 2, 3, 4} {
		occupied[s] = true
	} // Original placement defect.
	for len(locations) < PortCount && e.err == nil {
		s := e.integer(SectorCount-1) + 1
		if occupied[s] {
			stats.PlacementRejections++
			continue
		}
		locations = append(locations, s)
		occupied[s] = true
	}
	stats.PlacementDraws, stats.PlacementState = e.draws-start, e.rng.State()
	pool := strings.Split(syllableData, ",")
	for i, s := range locations {
		if e.err != nil {
			return e.err
		}
		id := i + 1
		r := record(data, 3051+id)
		for j := 0; j < 3; j++ {
			put(r, 61+j*4, e.integer(31767)+999)
		}
		var coeff [3]int
		for j := range coeff {
			coeff[j] = -e.integer(100)
		}
		name := "Earth"
		if id != 1 {
			name = e.name(pool)
		}
		if len(name) > 41 {
			return fmt.Errorf("QB name exceeds record field: %d", id)
		}
		text(r, name)
		klass := e.integer(3)
		coeff[3-klass] *= -1
		for j, c := range coeff {
			put(r, 73+j*4, c)
		}
		for _, offset := range []int{49, 53, 57, 89, 97, 101, 105, 109, 129} {
			copy(r[offset:offset+4], []byte{0, 0, 0xa0, 0})
		}
		put(r, 41, klass)
		put(r, 45, day-10)
		put(r, 85, len(name))
		put(r, 93, s)
		if id == 1 {
			put(r, 117, hq)
			put(r, 121, 1000)
			put(r, 125, 6324)
		}
		put(record(data, 51+s), 65, id) // Last writer wins, including original collisions.
	}
	return e.err
}

func (e *engine) name(pool []string) string {
	first := e.next()
	chunks := int(float32(float32(first*e.next())*3)) + 2
	var name strings.Builder
	for j := 0; j < chunks; j++ {
		part := pool[e.integer(len(pool))-1]
		if len(part) > 4 {
			name.WriteByte(' ')
			part = strings.ToUpper(part[:1]) + part[1:]
		}
		name.WriteString(part)
	}
	s := strings.TrimPrefix(name.String(), " ")
	return strings.ToUpper(s[:1]) + s[1:]
}

func has(row [6]int, n int) bool {
	for _, v := range row {
		if v == n {
			return true
		}
	}
	return false
}
func record(data []byte, id int) []byte { return data[(id-1)*RecordSize : id*RecordSize] }
func text(r []byte, s string) {
	for i := 0; i < 41; i++ {
		r[i] = ' '
	}
	copy(r[:41], s)
}
func put(r []byte, offset, value int) {
	b := mbf(value)
	copy(r[offset:offset+4], b[:])
}

// All serialized numeric values here are exactly representable integers, not
// general MBF arithmetic. Noncanonical zero residues are written explicitly.
func mbf(value int) [4]byte {
	if value == 0 {
		return [4]byte{}
	}
	b := math.Float32bits(float32(value))
	return [4]byte{byte(b), byte(b >> 8), byte((b>>16)&0x7f) | byte((b>>24)&0x80), byte((b>>23)&255) + 2}
}
