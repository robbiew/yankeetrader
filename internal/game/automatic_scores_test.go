package game

import (
	"encoding/json"
	"testing"
	"time"
)

func TestMaintenancePublishesCurrentScoresOncePerDay(t *testing.T) {
	w, p := setup(t)
	other, _ := w.Join("scores:dead", "Dead")
	if err := w.RecordDeath(DeathContext{Victim: other.ID, Generation: other.ShipGeneration, Sector: other.Sector, Cause: "hazard"}, clock); err != nil {
		t.Fatal(err)
	}
	p.StoredScore, other.StoredScore = -1, 999
	p.Credits = 100000
	p.Turns = 17
	w.Ports[2].Owner = p.ID
	w.Sectors[3].Defense = &SectorDefense{Owner: p.ID, Fighters: 100}
	expected, _ := w.PlayerRankings(p.ID, false)
	if !w.Maintain(clock.Add(24 * time.Hour)) {
		t.Fatal("maintenance skipped")
	}
	for _, row := range expected.Players {
		if w.Players[row.ID].StoredScore != row.Score {
			t.Fatal("wrong published score", row)
		}
	}
	if p.Credits != 100000 || p.Turns != 500 || other.StoredScore != 0 {
		t.Fatal("maintenance changed resource policy")
	}
	// Same-day and rollback attempts must neither repeat maintenance nor publish
	// newly changed assets outside an authorized refresh boundary.
	p.Credits++
	before, _ := json.Marshal(w)
	if w.Maintain(clock.Add(24*time.Hour)) || w.Maintain(clock) {
		t.Fatal("maintenance replayed")
	}
	after, _ := json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("replay changed cache or assets")
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
}

func TestMaintenanceScoresWithoutLivingCaller(t *testing.T) {
	for _, dead := range []bool{false, true} {
		w, err := New(clock, 36, 8)
		if err != nil {
			t.Fatal(err)
		}
		if dead {
			p, _ := w.Join("last", "Last")
			if err := w.RecordDeath(DeathContext{Victim: p.ID, Generation: p.ShipGeneration, Sector: p.Sector, Cause: "hazard"}, clock); err != nil {
				t.Fatal(err)
			}
			p.StoredScore = 777
		}
		if !w.Maintain(clock.Add(24 * time.Hour)) {
			t.Fatal("maintenance did not run")
		}
		for _, p := range w.Players {
			if p.StoredScore != 0 {
				t.Fatal("dead account earned score")
			}
		}
		if err := w.Validate(); err != nil {
			t.Fatal(err)
		}
	}
}
