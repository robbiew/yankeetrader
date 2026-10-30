package store

import (
	"encoding/json"
	"errors"
	"os"
	"sync"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func TestLogoutScoresAreBoundMetadataDuringEncounters(t *testing.T) {
	s := create(t)
	if err := s.Update(func(w *game.World) error {
		_, err := w.Join("other", "Enemy")
		if err != nil {
			return err
		}
		w.Players[1].Sector = 8
		w.Sectors[8].Defense = &game.SectorDefense{Owner: 2, Fighters: 100}
		w.Players[1].StoredScore, w.Players[2].StoredScore = 777, 888
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	w, _ := s.View()
	bound := s.ForShip(1, w.Players[1].ShipGeneration, 1)
	if err := s.RefreshScoresOnLogout(time.Now().Add(time.Minute)); err == nil {
		t.Fatal("unbound publication")
	}
	before, _ := os.ReadFile(s.Dir + "/world.json")
	if err := bound.RefreshScoresOnLogout(time.Now().Add(-time.Second)); err == nil {
		t.Fatal("expired logout")
	}
	after, _ := os.ReadFile(s.Dir + "/world.json")
	if string(before) != string(after) {
		t.Fatal("expired save changed world")
	}
	expected, _ := w.PlayerRankings(1, false)
	for _, row := range expected.Players {
		w.Players[row.ID].StoredScore = row.Score
	}
	want, _ := json.Marshal(w)
	if err := bound.RefreshScoresOnLogout(time.Now().Add(time.Minute)); err != nil {
		t.Fatal(err)
	}
	actual, _ := s.View()
	got, _ := json.Marshal(actual)
	if string(got) != string(want) {
		t.Fatal("logout changed more than scores")
	}
	called := false
	if err := bound.Update(func(w *game.World) error { called = true; w.Players[1].Credits++; return nil }); !errors.Is(err, game.ErrDefenseEncounter) || called {
		t.Fatal("logout opened encounter mutation gate", err)
	}
	if err := s.Update(func(w *game.World) error {
		w.Sectors[8].Defense = nil
		w.Sectors[8].Minefield = []game.MineLayer{{Owner: 2, Count: 3}}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	if err := bound.RefreshScoresOnLogout(time.Now().Add(time.Minute)); err != nil {
		t.Fatal(err)
	}
	called = false
	if err := bound.Update(func(w *game.World) error { called = true; w.Players[1].Credits++; return nil }); !errors.Is(err, game.ErrMineEncounter) || called {
		t.Fatal("logout bypassed mine encounter", err)
	}
	mined, _ := s.View()
	if !mined.HasMineEncounter(1) || mined.Sectors[8].Minefield[0].Count != 3 {
		t.Fatal("score publication resolved mines")
	}
	if err := s.Update(func(w *game.World) error {
		return w.RecordDeath(game.DeathContext{Victim: 1, Generation: w.Players[1].ShipGeneration, Sector: 8, Cause: "hazard"}, time.Now())
	}); err != nil {
		t.Fatal(err)
	}
	if err := bound.RefreshScoresOnLogout(time.Now().Add(time.Minute)); err == nil {
		t.Fatal("destroyed session published scores")
	}
	if err := s.Update(func(w *game.World) error { return w.ReplaceShip(1, time.Now()) }); err != nil {
		t.Fatal(err)
	}
	before, _ = os.ReadFile(s.Dir + "/world.json")
	if err := bound.RefreshScoresOnLogout(time.Now().Add(time.Minute)); err == nil {
		t.Fatal("old generation published replacement scores")
	}
	after, _ = os.ReadFile(s.Dir + "/world.json")
	if string(before) != string(after) {
		t.Fatal("stale logout changed replacement world")
	}
}

func TestConcurrentDailyScorePublicationAndRollback(t *testing.T) {
	s := create(t)
	now := time.Now().Add(24 * time.Hour)
	before, _ := os.ReadFile(s.Dir + "/world.json")
	abort := errors.New("abort maintenance")
	if err := s.Update(func(w *game.World) error { w.Maintain(now); return abort }); !errors.Is(err, abort) {
		t.Fatal(err)
	}
	after, _ := os.ReadFile(s.Dir + "/world.json")
	if string(before) != string(after) {
		t.Fatal("partial maintenance/score save")
	}
	var wg sync.WaitGroup
	errs := make(chan error, 8)
	runs := make(chan bool, 8)
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			errs <- s.Update(func(w *game.World) error { runs <- w.Maintain(now); return nil })
		}()
	}
	wg.Wait()
	close(errs)
	close(runs)
	for err := range errs {
		if err != nil {
			t.Fatal(err)
		}
	}
	count := 0
	for ran := range runs {
		if ran {
			count++
		}
	}
	if count != 1 {
		t.Fatal("daily phase repeated", count)
	}
	w, _ := s.View()
	report, _ := w.PlayerRankings(1, false)
	for _, row := range report.Players {
		if w.Players[row.ID].StoredScore != row.Score {
			t.Fatal("incoherent cache")
		}
	}
}
