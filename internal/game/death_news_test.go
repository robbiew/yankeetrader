package game

import (
	"bytes"
	"encoding/json"
	"math"
	"testing"
)

func TestGeneralDeathPublicSnapshotsAndCapturedPorts(t *testing.T) {
	w, victim := setup(t)
	killer, _ := w.Join("private-killer-identity", "Public Killer")
	victim.Sector, killer.Sector = 2, 2
	victim.Alias = "Public Victim"
	w.Ports[2].Owner = victim.ID
	ctx := DeathContext{Victim: victim.ID, Generation: victim.ShipGeneration, Sector: 2, Killer: killer.ID, Cause: "combat"}
	if err := w.RecordDeath(ctx, clock); err != nil {
		t.Fatal(err)
	}
	if len(w.News) != 2 {
		t.Fatal(w.News)
	}
	killed, ports := w.News[0], w.News[1]
	if killed.Alias != "Public Killer" || killed.Combat.Operation != "ship-death" || killed.Combat.Target != "Public Victim" || ports.Combat.Operation != "ports-captured" || ports.Combat.Amount != 1 {
		t.Fatal(w.News)
	}
	victim.Alias = "Renamed"
	killer.Alias = "Changed"
	if killed.Alias != "Public Killer" || killed.Combat.Target != "Public Victim" {
		t.Fatal("news changed with live aliases")
	}
	raw, _ := json.Marshal(w.News)
	for _, secret := range []string{victim.Identity, killer.Identity} {
		if bytes.Contains(raw, []byte(secret)) {
			t.Fatal("private identity in news")
		}
	}
	if err := w.RecordDeath(ctx, clock); err == nil {
		t.Fatal("death replay accepted")
	}
	if len(w.News) != 2 {
		t.Fatal("death replay published")
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
}

func TestDeathAndSalvageNewsPreflight(t *testing.T) {
	for _, mode := range []string{"death", "salvage"} {
		t.Run(mode, func(t *testing.T) {
			w, victim := setup(t)
			killer, _ := w.Join("killer", "Killer")
			victim.Sector, killer.Sector = 2, 2
			victim.Fighters, victim.Shields = 0, 0
			w.Ports[2].Owner = victim.ID
			w.NextNews = math.MaxUint64 - 1
			before, _ := json.Marshal(w)
			ctx := DeathContext{Victim: victim.ID, Generation: victim.ShipGeneration, Sector: 2, Killer: killer.ID, Cause: "combat"}
			if mode == "death" {
				if err := w.RecordDeath(ctx, clock); err == nil {
					t.Fatal("exhausted journal allowed death")
				}
			} else {
				if _, err := w.SettleShipSalvage(ctx, func() float64 { return .5 }, clock); err == nil {
					t.Fatal("exhausted journal allowed loot")
				}
			}
			after, _ := json.Marshal(w)
			if string(before) != string(after) {
				t.Fatal("rejected journal partly mutated state")
			}
		})
	}
}

func TestSalvageNewsReportsOnlyAcquiredStocks(t *testing.T) {
	w, victim := setup(t)
	killer, _ := w.Join("killer", "Killer")
	victim.Sector, killer.Sector = 2, 2
	victim.Fighters, victim.Shields = 0, 0
	victim.Holds = 10
	victim.Credits = 100
	victim.Missiles, victim.Plasma, victim.Ground, victim.Mines = 8, 6, 4, 2
	ctx := DeathContext{Victim: victim.ID, Generation: victim.ShipGeneration, Sector: 2, Killer: killer.ID, Cause: "combat"}
	loot, err := w.SettleShipSalvage(ctx, func() float64 { return .5 }, clock)
	if err != nil {
		t.Fatal(err)
	}
	wanted := map[string]int64{"summary": 0, "credits": loot.Credits, "missiles": loot.Missiles, "plasma": loot.Plasma, "ground": loot.Ground, "mines": loot.Mines, "empty-holds": loot.Holds}
	for _, event := range w.News {
		if event.Combat.Operation != "salvage" {
			continue
		}
		amount, ok := wanted[event.Combat.Resource]
		if !ok || amount != event.Combat.Amount {
			t.Fatal("unexpected loot publication", event)
		}
		delete(wanted, event.Combat.Resource)
	}
	if len(wanted) != 0 {
		t.Fatal("unpublished acquired stocks", wanted)
	}
	if err = w.Validate(); err != nil {
		t.Fatal(err)
	}
	empty := w.salvageNews("Killer", "Victim", Salvage{})
	if len(empty) != 2 || empty[1].Combat.Resource != "nothing" {
		t.Fatal("empty salvage not reported", empty)
	}
	cargo := w.salvageNews("Killer", "Victim", Salvage{Holds: 5, Cargo: [3]int64{1, 2, 2}})
	for _, entry := range cargo {
		if entry.Combat.Resource == "empty-holds" {
			t.Fatal("filled holds counted twice")
		}
	}
}
