package store

import (
	"errors"
	"os"
	"sync"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func TestRadioConcurrentSendRetryReadAndRollback(t *testing.T) {
	s := create(t)
	if err := s.Update(func(w *game.World) error { _, err := w.Join("recipient", "Enemy"); return err }); err != nil {
		t.Fatal(err)
	}
	w, _ := s.View()
	address, _ := w.FindRadioRecipient(1, "Enemy")
	draft, _ := w.PrepareRadio(1, address, "Only once", time.Now())
	bound := s.ForShip(1, w.Players[1].ShipGeneration, 1)
	abort := errors.New("abort send")
	if err := bound.Update(func(w *game.World) error {
		_, err := w.CommitRadio(draft, time.Now())
		if err != nil {
			return err
		}
		return abort
	}); !errors.Is(err, abort) {
		t.Fatal(err)
	}
	w, _ = s.View()
	if len(w.Radio) != 0 || w.NextRadio != 1 {
		t.Fatal("aborted send persisted")
	}
	var wg sync.WaitGroup
	results := make(chan error, 10)
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			results <- bound.Update(func(w *game.World) error { _, err := w.CommitRadio(draft, time.Now()); return err })
		}()
	}
	wg.Wait()
	close(results)
	for err := range results {
		if err != nil {
			t.Fatal(err)
		}
	}
	w, _ = s.View()
	if len(w.Radio) != 1 || w.NextRadio != 2 {
		t.Fatal("retry duplicated message")
	}
	receiver := s.ForShip(2, w.Players[2].ShipGeneration, 1)
	if err := receiver.AcknowledgeRadio(1); err != nil {
		t.Fatal(err)
	}
	second, _ := w.PrepareRadio(1, address, "Arrived after first read", time.Now())
	if err := bound.Update(func(w *game.World) error { _, err := w.CommitRadio(second, time.Now()); return err }); err != nil {
		t.Fatal(err)
	}
	if err := receiver.AcknowledgeRadio(1); err != nil {
		t.Fatal(err)
	}
	w, _ = s.View()
	unread, _ := w.RadioHistory(2, 0, 20, true)
	if len(unread) != 1 || unread[0].ID != 2 {
		t.Fatal("acknowledgement consumed a later message", unread)
	}
	if err := bound.AcknowledgeRadio(2); err == nil {
		t.Fatal("sender marked recipient message read")
	}
	if err := s.AcknowledgeRadio(2); err == nil {
		t.Fatal("unbound acknowledgement accepted")
	}
}

func TestRadioAcknowledgementDoesNotOpenEncounterMutationGate(t *testing.T) {
	s := create(t)
	if err := s.Update(func(w *game.World) error {
		_, _ = w.Join("recipient", "Enemy")
		w.Players[2].Sector = 2
		w.Sectors[2].Defense = &game.SectorDefense{Owner: 1, Fighters: 50}
		address, _ := w.FindRadioRecipient(1, "Enemy")
		draft, _ := w.PrepareRadio(1, address, "Message during encounter", time.Now())
		_, err := w.CommitRadio(draft, time.Now())
		return err
	}); err != nil {
		t.Fatal(err)
	}
	w, _ := s.View()
	bound := s.ForShip(2, w.Players[2].ShipGeneration, 1)
	if err := bound.AcknowledgeRadio(1); err != nil {
		t.Fatal(err)
	}
	called := false
	if err := bound.Update(func(w *game.World) error { called = true; w.Players[2].Credits++; return nil }); !errors.Is(err, game.ErrDefenseEncounter) || called {
		t.Fatal("radio acknowledgement bypassed resource gate", err)
	}
	w, _ = s.View()
	if w.Radio[0].Unread || w.Players[2].Credits != 1005 || w.Players[2].Turns != 500 {
		t.Fatal("acknowledgement changed ship assets")
	}
}

func TestVersionTenRadioUpgradeAndMalformedArchive(t *testing.T) {
	s := create(t)
	w, _ := s.View()
	w.Version, w.NextRadio = 10, 0
	w.Season = 0
	w.GenerationSeed = nil
	w.NextBattleReport = 0
	w.NextNews = 0
	w.Players[1].Sector, w.Players[1].MineGraceSector = 8, 8
	data, _ := marshalHistoricalWorld(w)
	path := s.Dir + "/world.json"
	if err := os.WriteFile(path, data, 0600); err != nil {
		t.Fatal(err)
	}
	upgraded, err := s.View()
	if err != nil || upgraded.Version != game.WorldVersion || upgraded.NextRadio != 1 || len(upgraded.Radio) != 0 || upgraded.Players[1].MineGraceSector != 8 {
		t.Fatal("radio upgrade invented messages or lost grace", err)
	}
	unchanged, _ := os.ReadFile(path)
	if string(data) != string(unchanged) {
		t.Fatal("read rewrote legacy save")
	}
	if err := s.Update(func(w *game.World) error { return nil }); err != nil {
		t.Fatal(err)
	}
	persisted, err := s.View()
	if err != nil || persisted.Version != game.WorldVersion || persisted.NextRadio != 1 {
		t.Fatal("radio upgrade not persisted", err)
	}
	w.NextRadio = 1
	data, _ = marshalHistoricalWorld(w)
	if err := os.WriteFile(path, data, 0600); err != nil {
		t.Fatal(err)
	}
	if _, err := s.View(); err == nil {
		t.Fatal("unversioned radio metadata accepted")
	}
}

func TestTeamRadioConcurrentRetryAndRollback(t *testing.T) {
	s := create(t)
	if err := s.Update(func(w *game.World) error {
		if _, err := w.Join("recipient", "Enemy"); err != nil {
			return err
		}
		if err := w.CreateTeam(1, "Orion", "ABCD"); err != nil {
			return err
		}
		return w.JoinTeam(2, 1, "ABCD")
	}); err != nil {
		t.Fatal(err)
	}
	w, _ := s.View()
	address, _ := w.FindTeamRadioRecipients(1)
	draft, err := w.PrepareTeamRadio(1, address, "One atomic batch", time.Now())
	if err != nil {
		t.Fatal(err)
	}
	bound := s.ForShip(1, w.Players[1].ShipGeneration, 1)
	abort := errors.New("abort")
	if err := bound.Update(func(w *game.World) error {
		if _, err := w.CommitTeamRadio(draft, time.Now()); err != nil {
			return err
		}
		return abort
	}); !errors.Is(err, abort) {
		t.Fatal(err)
	}
	w, _ = s.View()
	if len(w.Radio) != 0 || w.NextRadio != 1 {
		t.Fatal("aborted batch persisted")
	}
	var wg sync.WaitGroup
	results := make(chan error, 8)
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			results <- bound.Update(func(w *game.World) error { _, err := w.CommitTeamRadio(draft, time.Now()); return err })
		}()
	}
	wg.Wait()
	close(results)
	for err := range results {
		if err != nil {
			t.Fatal(err)
		}
	}
	w, _ = s.View()
	if len(w.Radio) != 2 || w.NextRadio != 3 {
		t.Fatal("retry duplicated batch", w.Radio)
	}
	receiver := s.ForShip(2, w.Players[2].ShipGeneration, 1)
	if err := receiver.AcknowledgeRadio(2); err != nil {
		t.Fatal(err)
	}
	w, _ = s.View()
	if w.Radio[1].Unread || !w.Radio[0].Unread {
		t.Fatal("shared read receipt")
	}
	// Reopening the same files retains separate private copies.
	reopened, err := s.View()
	if err != nil || len(reopened.Radio) != 2 {
		t.Fatal(err)
	}
}

func TestTeamRadioCommittedSyncWarningRetainsWholeBatch(t *testing.T) {
	s := create(t)
	if err := s.Update(func(w *game.World) error {
		if _, err := w.Join("recipient", "Enemy"); err != nil {
			return err
		}
		if err := w.CreateTeam(1, "Orion", "ABCD"); err != nil {
			return err
		}
		return w.JoinTeam(2, 1, "ABCD")
	}); err != nil {
		t.Fatal(err)
	}
	w, _ := s.View()
	address, _ := w.FindTeamRadioRecipients(1)
	draft, err := w.PrepareTeamRadio(1, address, "Committed once", time.Now())
	if err != nil {
		t.Fatal(err)
	}
	bound := s.ForShip(1, w.Players[1].ShipGeneration, 1)
	bound.syncDirectory = func(string) error { return errors.New("injected sync failure") }
	err = bound.Update(func(w *game.World) error { _, err := w.CommitTeamRadio(draft, time.Now()); return err })
	var durability *DurabilityError
	if !errors.As(err, &durability) {
		t.Fatal(err)
	}
	w, _ = s.View()
	if len(w.Radio) != 2 || w.NextRadio != 3 {
		t.Fatal("committed batch lost", w.Radio)
	}
	bound.syncDirectory = nil
	if err := bound.Update(func(w *game.World) error { _, err := w.CommitTeamRadio(draft, time.Now()); return err }); err != nil {
		t.Fatal(err)
	}
	w, _ = s.View()
	if len(w.Radio) != 2 {
		t.Fatal("retry after committed warning duplicated mail")
	}
}
