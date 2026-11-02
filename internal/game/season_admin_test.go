package game

import (
	"encoding/json"
	"testing"
	"time"
)

func TestAdministrativeSeasonHistoryAndMigration(t *testing.T) {
	w, _ := genesisWorld(t, 32)
	limit := 2
	w.LotteryDailyLimit = &limit
	before, _ := json.Marshal(w)
	next, err := w.AdministrativeCandidate(1, clock.Add(time.Hour), 44)
	if err != nil {
		t.Fatal(err)
	}
	after, _ := json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("candidate mutated source")
	}
	if next.LotteryLimit() != 2 || len(next.SeasonResults) != 1 {
		t.Fatal("settings/history lost")
	}
	r := next.SeasonResults[0]
	if !r.Administrative || r.Winner != "" || r.Player != 0 {
		t.Fatal(r)
	}
	next.SeasonResults[0].Winner = "Fake"
	if next.Validate() == nil {
		t.Fatal("administrative winner accepted")
	}
	next.SeasonResults[0] = r
	next.Version = 29
	if next.Upgrade() == nil {
		t.Fatal("legacy admin record accepted")
	}
	w.Version = 29
	if err = w.Upgrade(); err != nil || w.Version != WorldVersion {
		t.Fatal("migration", err)
	}
	if _, err = w.AdministrativeCandidate(2, clock, 44); err == nil {
		t.Fatal("stale season accepted")
	}
	if _, err = w.AdministrativeCandidate(1, clock.Add(-time.Hour), 44); err == nil {
		t.Fatal("backwards clock accepted")
	}
	// Genesis remains available after an administrative season and retains its record.
	p, err := next.Join("new", "NewWinner")
	if err != nil {
		t.Fatal(err)
	}
	next.Version = WorldVersion
	for i := 2; i <= 21; i++ {
		next.Ports[i].Owner = p.ID
	}
	quote, err := next.PrepareGenesis(p.ID, clock.Add(2*time.Hour))
	if err != nil {
		t.Fatal(err)
	}
	third, _, err := next.GenesisCandidate(quote, clock.Add(2*time.Hour), 77)
	if err != nil || len(third.SeasonResults) != 2 || !third.SeasonResults[0].Administrative || third.SeasonResults[1].Administrative {
		t.Fatal("Genesis after admin", err)
	}
}
