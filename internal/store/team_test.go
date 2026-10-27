package store

import (
	"encoding/json"
	"os"
	"sync"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func TestCompetingTeamJoinsAndCaptainSuccession(t *testing.T) {
	s := create(t)
	if err := s.Update(func(w *game.World) error {
		if err := w.CreateTeam(1, "Orion", "ABCD"); err != nil {
			return err
		}
		for _, alias := range []string{"Two", "Three", "Four", "Five"} {
			_, err := w.Join(alias, alias)
			if err != nil {
				return err
			}
		}
		for _, id := range []int{2, 3} {
			if err := w.JoinTeam(id, 1, "ABCD"); err != nil {
				return err
			}
		}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	var wg sync.WaitGroup
	results := make(chan error, 2)
	for _, id := range []int{4, 5} {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			results <- s.Update(func(w *game.World) error { return w.JoinTeam(id, 1, "abcd") })
		}(id)
	}
	wg.Wait()
	close(results)
	success := 0
	for err := range results {
		if err == nil {
			success++
		}
	}
	w, err := s.View()
	if err != nil {
		t.Fatal(err)
	}
	if success != 1 || len(w.ListTeams()[0].Members) != 4 {
		t.Fatal("fifth member admitted", success, w.ListTeams())
	}
	if err = s.Update(func(w *game.World) error { return w.LeaveTeam(1, 1) }); err != nil {
		t.Fatal(err)
	}
	results = make(chan error, 2)
	for _, id := range []int{2, 3} {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			results <- s.Update(func(w *game.World) error { _, err := w.VisitTeam(id); return err })
		}(id)
	}
	wg.Wait()
	close(results)
	for err := range results {
		if err != nil {
			t.Fatal(err)
		}
	}
	w, err = s.View()
	if err != nil {
		t.Fatal(err)
	}
	if w.Teams[1].Captain != 2 && w.Teams[1].Captain != 3 {
		t.Fatal("invalid successor")
	}
	captain := w.Teams[1].Captain
	if err = s.Update(func(w *game.World) error { return w.ChangeTeamPassword(1, 1, "WXYZ") }); err == nil {
		t.Fatal("old captain authorized")
	}
	w, _ = s.View()
	if w.Teams[1].Captain != captain {
		t.Fatal("successor overwritten")
	}
}

func TestTeamSaveUpgradeAndMalformedLegacyMembership(t *testing.T) {
	s := create(t)
	w, _ := s.View()
	w.Players[1].Credits = 100000
	w.Players[1].AvoidSectors = []int{2, 3}
	w.Ports[2].Owner, w.Ports[2].Treasury = 1, 777
	if err := w.CreatePlanet(1, "Home", time.Now()); err != nil {
		t.Fatal(err)
	}
	w.Version = 2
	w.Teams = nil
	b, _ := json.Marshal(w)
	if err := os.WriteFile(s.Dir+"/world.json", b, 0600); err != nil {
		t.Fatal(err)
	}
	current, err := s.View()
	if err != nil || current.Version != 3 || current.Teams == nil || current.Players[1].Credits != 75000 || current.Ports[2].Owner != 1 || current.Ports[2].Treasury != 777 || current.Planets[2].Owner != 1 || len(current.Players[1].AvoidSectors) != 2 {
		t.Fatal("v2 upgrade failed", current, err)
	}
	disk, _ := os.ReadFile(s.Dir + "/world.json")
	if string(disk) != string(b) {
		t.Fatal("read-only upgrade wrote save")
	}
	if err = s.Update(func(w *game.World) error { return w.CreateTeam(1, "Orion", "ABCD") }); err != nil {
		t.Fatal(err)
	}
	current, err = s.View()
	if err != nil || current.Version != 3 || current.Teams[1].Captain != 1 {
		t.Fatal("upgraded team not saved", err)
	}
	// Experimental, manually assigned legacy IDs cannot grant invented membership.
	w.Players[1].Team = 1
	b, _ = json.Marshal(w)
	if err = os.WriteFile(s.Dir+"/world.json", b, 0600); err != nil {
		t.Fatal(err)
	}
	if _, err = s.View(); err == nil {
		t.Fatal("orphan legacy membership silently accepted")
	}
	disk, _ = os.ReadFile(s.Dir + "/world.json")
	if string(disk) != string(b) {
		t.Fatal("invalid legacy save rewritten")
	}
}
