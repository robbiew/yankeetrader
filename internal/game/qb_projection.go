package game

import (
	"crypto/sha256"
	"fmt"
	"math"
	"strings"
	"time"

	"github.com/robbiew/yankeetrader/internal/qbinit"
)

// qbWorldCandidate is the internal unpublished stage used by NewQB36.
// Source fingerprint and stream statistics describe pre-projection bytes, not
// the evolving modern world or its independent bootstrap stream.
type qbWorldCandidate struct {
	world        *World
	sourceSHA256 [32]byte
	stats        qbinit.Stats
	inputs       qbinit.Options
}

func prepareQBWorld(now time.Time, modernSeed int64, inputs qbinit.Options) (*qbWorldCandidate, error) {
	source, err := qbinit.Generate(inputs)
	if err != nil {
		return nil, err
	}
	candidate, err := projectQBSource(now, modernSeed, source)
	if err != nil {
		return nil, err
	}
	candidate.inputs = inputs
	return candidate, nil
}

// projectQBSource admits only the bounded initializer layout and constructs a
// fresh typed world. It does not load DOS files, reuse inactive records, reroll
// collisions, repair an unsafe graph or write an active save.
func projectQBSource(now time.Time, modernSeed int64, source qbinit.Result) (*qbWorldCandidate, error) {
	if now.IsZero() || len(source.Bytes) != qbinit.RecordCount*qbinit.RecordSize {
		return nil, fmt.Errorf("invalid QB candidate clock or record coverage")
	}
	raw := source.Bytes
	for offset, want := range map[int]int{53: 51, 57: 3051, 61: 4051, 93: 4151} {
		value, err := qbInteger(raw, 1, offset, 0, qbinit.RecordCount)
		if err != nil || value != want {
			return nil, fmt.Errorf("invalid QB source record layout")
		}
	}
	hq, err := qbInteger(raw, 1, 117, 1, qbinit.SectorCount)
	if err != nil || hq <= 7 || hq != source.Stats.HQ {
		return nil, fmt.Errorf("QB HQ is protected, invalid or inconsistent")
	}
	pointer, err := qbInteger(raw, 52, 105, 1, qbinit.SectorCount)
	if err != nil || pointer != hq {
		return nil, fmt.Errorf("QB Earth HQ pointer is inconsistent")
	}
	w := &World{NextPlanetGeneration: 101, Season: 1, GenerationSeed: &modernSeed, Version: WorldVersion,
		WarpGeneration: "dos", PortGeneration: "dos", NextBattleReport: 1, NextNews: 1, NextRadio: 1,
		Teams: map[int]*Team{}, Planets: map[int]*Planet{}, Created: now.UTC(), LastMaintenance: day(now),
		NextPlayer: 1, Players: map[int]*Player{}, Sectors: map[int]*Sector{}, Ports: map[int]*Port{},
		Xannor: &XannorState{HQ: hq}}
	table := make(dosWarpTable, qbinit.SectorCount+1)
	for id := 1; id <= qbinit.SectorCount; id++ {
		sector := &Sector{ID: id}
		for column := 0; column < 6; column++ {
			to, e := qbInteger(raw, 51+id, 41+4*column, 0, qbinit.SectorCount)
			if e != nil {
				return nil, e
			}
			if to == 0 || (id == 1 && to == 1) {
				continue
			}
			if to == id || contains(sector.Warps, to) {
				return nil, fmt.Errorf("QB sector %d has self/duplicate warps", id)
			}
			table[id][len(sector.Warps)] = to
			sector.Warps = append(sector.Warps, to)
		}
		fighters, e := qbInteger(raw, 51+id, 81, 0, 10000)
		if e != nil {
			return nil, e
		}
		owner, e := qbInteger(raw, 51+id, 85, -1, 0)
		if e != nil {
			return nil, e
		}
		if id == hq {
			if fighters != 10000 || owner != XannorOwner {
				return nil, fmt.Errorf("QB HQ defenses differ from initializer")
			}
			sector.Defense = &SectorDefense{Owner: XannorOwner, Fighters: 10000}
		} else if fighters != 0 || owner != 0 {
			return nil, fmt.Errorf("unexpected QB initial defense")
		}
		w.Sectors[id] = sector
	}
	if !dosGraphConnected(table, false) || !dosGraphConnected(table, true) {
		return nil, fmt.Errorf("QB graph is not forward/reverse Earth-connected")
	}
	for id := 1; id <= qbinit.PortCount; id++ {
		rec := 3051 + id
		location, e := qbInteger(raw, rec, 93, 1, qbinit.SectorCount)
		if e != nil {
			return nil, e
		}
		if w.Sectors[location].Port != 0 {
			return nil, fmt.Errorf("QB duplicate port location in sector %d", location)
		}
		name := strings.TrimRight(string(raw[(rec-1)*qbinit.RecordSize:(rec-1)*qbinit.RecordSize+41]), " ")
		length, e := qbInteger(raw, rec, 85, 1, 41)
		if e != nil || !clean(name) || length != len(name) || (id == 1 && (name != "Earth" || location != 1)) {
			return nil, fmt.Errorf("invalid QB port name/Earth record")
		}
		class, e := qbInteger(raw, rec, 41, 1, 3)
		if e != nil {
			return nil, e
		}
		port := &Port{ID: id, Sector: location, Name: name, Updated: now.UTC()}
		for offset := range map[int]bool{89: true, 97: true} {
			value, e := qbInteger(raw, rec, offset, 0, 0)
			if e != nil || value != 0 {
				return nil, fmt.Errorf("QB port contains initial ownership/treasury")
			}
		}
		for good := 0; good < 3; good++ {
			stock, e := qbInteger(raw, rec, 49+4*good, 0, 0)
			if e != nil || stock != 0 {
				return nil, fmt.Errorf("QB port is not pre-maintenance")
			}
			rate, e := qbInteger(raw, rec, 61+4*good, 1000, 32766)
			if e != nil {
				return nil, e
			}
			coeff, e := qbInteger(raw, rec, 73+4*good, -100, 100)
			if e != nil || coeff == 0 || (coeff > 0) != (good == 3-class) {
				return nil, fmt.Errorf("invalid QB trade coefficients")
			}
			port.Production[good] = float64(rate)
			port.Supply[good] = float64(rate) * 10
			port.Coefficient[good] = float64(coeff)
		}
		w.Ports[id] = port
		w.Sectors[location].Port = id
	}
	for id := 1; id <= qbinit.SectorCount; id++ {
		link, e := qbInteger(raw, 51+id, 65, 0, qbinit.PortCount)
		if e != nil || link != w.Sectors[id].Port {
			return nil, fmt.Errorf("QB sector/port link mismatch at %d", id)
		}
	}
	if err = w.Validate(); err != nil {
		return nil, err
	}
	// Modern homes and Wanderer use their existing independent bounded stream.
	// A failed bootstrap never escapes as an active/partial candidate.
	if err = bootstrapSeason(w, now, modernSeed, true); err != nil {
		return nil, err
	}
	if w.Xannor == nil || w.Xannor.HQ != hq || w.xannorHome() == nil || w.xannorHome().Sector != hq {
		return nil, fmt.Errorf("QB bootstrap displaced the source HQ")
	}
	return &qbWorldCandidate{world: w, sourceSHA256: sha256.Sum256(raw), stats: source.Stats}, nil
}

func qbInteger(raw []byte, record, offset, minimum, maximum int) (int, error) {
	at := (record-1)*qbinit.RecordSize + offset
	b := raw[at : at+4]
	value := float64(0)
	if b[3] != 0 {
		mantissa := uint32(b[0]) | uint32(b[1])<<8 | uint32(b[2]&0x7f)<<16
		value = math.Ldexp(1+float64(mantissa)/(1<<23), int(b[3])-129)
		if b[2]&0x80 != 0 {
			value = -value
		}
	}
	if value < float64(minimum) || value > float64(maximum) || value != math.Trunc(value) {
		return 0, fmt.Errorf("invalid QB integer in record %d offset %d", record, offset)
	}
	return int(value), nil
}
