package game

import (
	"encoding/json"
	"errors"
	"testing"
)

func TestMinePlacementLeavesOccupantsSafeUntilDeparture(t *testing.T) {
	w, p := setup(t)
	p.Sector, p.Mines, p.Shields = 8, 10, 1000000
	other, _ := w.Join("occupant", "Occupant")
	other.Sector = 8
	w.Sectors[8].Warps, w.Sectors[7].Warps = []int{7}, []int{8}
	intent, err := w.PrepareMinePlacement(p.ID, 5)
	if err != nil {
		t.Fatal(err)
	}
	if total, err := w.CommitMinePlacement(intent); err != nil || total != 5 {
		t.Fatal(total, err)
	}
	if p.Mines != 5 || p.Turns != 500 || p.MineGraceSector != 8 || other.MineGraceSector != 8 {
		t.Fatal("wrong deployment state", p, other)
	}
	for _, id := range []int{p.ID, other.ID} {
		out, err := w.ResolveMinefield(id, nil, clock)
		if err != nil || out.Bursts != 0 || w.HasMineEncounter(id) || len(w.Sectors[8].Minefield) != 1 || w.Sectors[8].Minefield[0].Count != 5 {
			t.Fatal("new field struck an existing occupant", out, err)
		}
	}
	if err := w.Move(p.ID, 7); err != nil || p.MineGraceSector != 0 {
		t.Fatal("could not depart field", err)
	}
	entry, err := w.PrepareMineEntry(p.ID, 8)
	if err != nil {
		t.Fatal(err)
	}
	out, err := w.CommitMineEntry(entry, func() float64 { return .5 }, clock)
	if err != nil || out.Spent != 5 || p.Shields != 997500 || p.Turns != 498 || p.MineGraceSector != 0 {
		t.Fatal("reentry failed to trigger own mines", out, p, err)
	}
}

func TestMinePlacementGraceDoesNotProtectEntrantsOrWreckHazards(t *testing.T) {
	for _, mode := range []string{"entrant", "wreck"} {
		t.Run(mode, func(t *testing.T) {
			w, p := setup(t)
			p.Sector, p.Mines, p.Shields = 8, 10, 1000000
			entrant, _ := w.Join("entrant", "Entrant")
			entrant.Sector, entrant.Shields = 7, 1000000
			w.Sectors[7].Warps = []int{8}
			intent, _ := w.PrepareMinePlacement(p.ID, 5)
			if _, err := w.CommitMinePlacement(intent); err != nil {
				t.Fatal(err)
			}
			if mode == "entrant" {
				entry, err := w.PrepareMineEntry(entrant.ID, 8)
				if err != nil {
					t.Fatal(err)
				}
				out, err := w.CommitMineEntry(entry, func() float64 { return .5 }, clock)
				if err != nil || out.Spent != 5 || entrant.Shields != 997500 || p.Shields != 1000000 {
					t.Fatal("entrant bypassed deployed field", out, err)
				}
			} else {
				if err := w.dropMines(8, entrant.ID, 1); err != nil {
					t.Fatal(err)
				}
				if p.MineGraceSector != 0 || !w.HasMineEncounter(p.ID) {
					t.Fatal("departure grace bypassed a wreck hazard")
				}
				out, err := w.ResolveMinefield(p.ID, func() float64 { return .5 }, clock)
				if err != nil || out.Spent != 6 {
					t.Fatal(out, err)
				}
			}
		})
	}
}

func TestMinePlacementRejectsExistingHazardStaleAndOverflow(t *testing.T) {
	w, p := setup(t)
	p.Sector, p.Mines = 8, 10
	w.Sectors[8].Minefield = []MineLayer{{Owner: 0, Count: 1}}
	if _, err := w.PrepareMinePlacement(p.ID, 5); !errors.Is(err, ErrMineEncounter) {
		t.Fatal("placement bypassed pre-existing encounter", err)
	}
	p.MineGraceSector = 8
	intent, _ := w.PrepareMinePlacement(p.ID, 5)
	p.Mines--
	if _, err := w.CommitMinePlacement(intent); err == nil {
		t.Fatal("stale stock accepted")
	}
	w.Sectors[8].Minefield[0].Count = MaxQuantity
	intent, _ = w.PrepareMinePlacement(p.ID, 5)
	before, _ := json.Marshal(w)
	if _, err := w.CommitMinePlacement(intent); err == nil {
		t.Fatal("overflow accepted")
	}
	after, _ := json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("failed placement changed departure grace or stock")
	}
}

func TestMineGraceClearedByDeathAndValidated(t *testing.T) {
	w, p := setup(t)
	p.Sector, p.MineGraceSector = 8, 8
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
	p.MineGraceSector = 7
	if err := w.Validate(); err == nil {
		t.Fatal("wrong-sector grace accepted")
	}
	p.MineGraceSector = 8
	if err := w.RecordDeath(DeathContext{Victim: p.ID, Generation: p.ShipGeneration, Sector: 8, Killer: 0, Cause: "mines"}, clock); err != nil {
		t.Fatal(err)
	}
	if p.MineGraceSector != 0 {
		t.Fatal("dead ship kept departure grace")
	}
	if err := w.ReplaceShip(p.ID, clock); err != nil || p.MineGraceSector != 0 || p.Sector != 1 {
		t.Fatal("replacement inherited departure grace", err)
	}
}
