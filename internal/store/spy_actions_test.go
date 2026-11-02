package store

import (
	"errors"
	"fmt"
	"math"
	"os"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func TestPlanetReportSpyTriggerAndFreeReads(t *testing.T) {
	for _, mode := range []string{"missing", "blocked", "free", "invalid", "no-turns", "expired", "rng-failure", "committed-warning"} {
		t.Run(mode, func(t *testing.T) {
			s, b, v := sharedSpyStore(t)
			sector := 3
			if err := s.Update(func(w *game.World) error {
				if mode == "blocked" {
					w.Sectors[3].Defense = &game.SectorDefense{Owner: 2, Fighters: 1}
				}
				if mode == "free" {
					w.Sectors[3].Planet = 2
					w.Planets[2] = &game.Planet{ID: 2, Generation: 10, Sector: 3, Owner: 1, Name: "Home", Updated: w.Created}
				}
				if mode == "no-turns" {
					w.Players[1].Turns = 0
				}
				return nil
			}); err != nil {
				t.Fatal(err)
			}
			if mode == "invalid" {
				sector = 999
			}
			deadline := time.Now().Add(time.Hour)
			if mode == "expired" {
				deadline = time.Now().Add(-time.Second)
			}
			if mode == "rng-failure" {
				b.ship.spyRNG = func() float64 { return math.NaN() }
			}
			if mode == "free" {
				b.ship.spyRNG = func() float64 { t.Fatal("free report advanced spies"); return 0 }
			}
			if mode == "committed-warning" {
				b.syncDirectory = func(string) error { return errors.New("sync") }
			}
			before, _ := os.ReadFile(s.Dir + "/world.json")
			w, _ := s.View()
			turns := w.Players[1].Turns
			out, caller, err := b.PlanetReport(sector, time.Now, deadline)
			spent := mode == "missing" || mode == "blocked" || mode == "committed-warning"
			var warning *DurabilityError
			if mode == "committed-warning" && !errors.As(err, &warning) {
				t.Fatal(err)
			}
			if spent && (!out.TurnSpent || caller.Turns != turns-1 || out.Available) {
				t.Fatal(out, caller, err)
			}
			if mode == "free" && (err != nil || out.TurnSpent || !out.Available || caller.Turns != turns) {
				t.Fatal(out, err)
			}
			if !spent && mode != "free" && err == nil {
				t.Fatal("failed query accepted")
			}
			_, reports, e := b.SpySnapshot(false)
			if e != nil {
				t.Fatal(e)
			}
			if (len(reports) > 0) != spent || sharedTargetVisible(t, b, v) != spent {
				t.Fatal("query/spies/reveal did not settle together")
			}
			after, _ := os.ReadFile(s.Dir + "/world.json")
			if !spent && string(before) != string(after) {
				t.Fatal("free/failed query changed save")
			}
		})
	}
}
func TestMissileSpyScanDoesNotExpandQuotedTargets(t *testing.T) {
	s, b, v := sharedSpyStore(t)
	if err := s.Update(func(w *game.World) error {
		w.Sectors[2].Minefield = nil
		w.Sectors[2].Defense = &game.SectorDefense{Owner: game.MercenaryOwner, Fighters: 10}
		w.Players[1].Missiles = 10
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	deadline := time.Now().Add(time.Hour)
	entry, _, err := b.PrepareMissiles(2, 1, v, time.Now, deadline)
	if err != nil {
		t.Fatal(err)
	}
	if len(entry.Sectors[0].Ships) != 0 {
		t.Fatal("hidden ship entered original quote")
	}
	out, err := b.LaunchMissiles(entry, v, func() float64 { return .5 }, time.Now, deadline)
	if err != nil || len(out.Primary.ShipImpacts) != 0 || !sharedTargetVisible(t, b, v) {
		t.Fatal(out, err)
	}
	w, _ := s.View()
	if w.Players[2].Shields != 100 || w.Players[2].Cloak != .5 {
		t.Fatal("new reveal expanded volley")
	}
	_, reports, _ := b.SpySnapshot(false)
	if len(reports) != 1 || reports[0].DefenseFighters != 10 {
		t.Fatal("scan did not snapshot pre-impact state", reports)
	}
	if _, err = b.LaunchMissiles(entry, v, func() float64 { return .5 }, time.Now, deadline); err == nil {
		t.Fatal("launch confirmation replayed")
	}
}
func TestWeaponSpyRollbackAndSpentPlasmaRetry(t *testing.T) {
	for _, mode := range []string{"plasma-unreachable", "plasma-warning", "plasma-stale", "missile-rng"} {
		t.Run(mode, func(t *testing.T) {
			s, b, v := sharedSpyStore(t)
			deadline := time.Now().Add(time.Hour)
			if err := s.Update(func(w *game.World) error {
				w.Players[1].Plasma = 3
				w.Players[1].Missiles = 3
				w.Sectors[1].Warps = []int{2}
				w.Sectors[2].Warps = nil
				w.Sectors[2].Minefield = nil
				w.Sectors[2].Defense = &game.SectorDefense{Owner: game.MercenaryOwner, Fighters: 10}
				return nil
			}); err != nil {
				t.Fatal(err)
			}
			before, _ := os.ReadFile(s.Dir + "/world.json")
			var err error
			committed := mode == "plasma-unreachable" || mode == "plasma-warning"
			if mode == "missile-rng" {
				entry, _, e := b.PrepareMissiles(2, 1, v, time.Now, deadline)
				if e != nil {
					t.Fatal(e)
				}
				_, err = b.LaunchMissiles(entry, v, func() float64 { return math.NaN() }, time.Now, deadline)
			} else {
				entry, e := b.PreparePlasma(8, 1, time.Now, deadline)
				if e != nil {
					t.Fatal(e)
				}
				if mode == "plasma-stale" {
					if e = s.Update(func(w *game.World) error { w.Players[1].Credits++; return nil }); e != nil {
						t.Fatal(e)
					}
					before, _ = os.ReadFile(s.Dir + "/world.json")
				}
				if mode == "plasma-warning" {
					b.syncDirectory = func(string) error { return errors.New("sync") }
				}
				out, e := b.LaunchPlasma(entry, func() float64 { return .5 }, time.Now, deadline)
				err = e
				if committed && (!out.RouteUnavailable || out.Launched != 1) {
					t.Fatal(out, e)
				}
				if _, e = b.LaunchPlasma(entry, func() float64 { return .5 }, time.Now, deadline); e == nil {
					t.Fatal("plasma confirmation replayed")
				}
			}
			var warning *DurabilityError
			if mode == "plasma-warning" && !errors.As(err, &warning) {
				t.Fatal(err)
			}
			if !committed && err == nil {
				t.Fatal("failed weapon accepted")
			}
			_, reports, e := b.SpySnapshot(false)
			if e != nil {
				t.Fatal(e)
			}
			if (len(reports) > 0) != committed || sharedTargetVisible(t, b, v) != committed {
				t.Fatal("partial weapon/private settlement", err)
			}
			after, _ := os.ReadFile(s.Dir + "/world.json")
			if !committed && string(before) != string(after) {
				t.Fatal("failed weapon changed save")
			}
		})
	}
}

func TestSpyActionLockWaitExpiry(t *testing.T) {
	for _, lock := range []string{"world", "session", "visibility"} {
		t.Run(lock, func(t *testing.T) {
			s, b, v := sharedSpyStore(t)
			before, _ := os.ReadFile(s.Dir + "/world.json")
			release := func() {}
			switch lock {
			case "world":
				held, done := make(chan struct{}), make(chan error, 1)
				unblock := make(chan struct{})
				go func() { done <- s.locked(func() error { close(held); <-unblock; return nil }) }()
				<-held
				release = func() {
					close(unblock)
					if e := <-done; e != nil {
						t.Fatal(e)
					}
				}
			case "session":
				b.ship.spyMu.Lock()
				release = b.ship.spyMu.Unlock
			case "visibility":
				_, finish := v.StageAntiCloak()
				release = func() { finish(false) }
			}
			result := make(chan error, 1)
			deadline := time.Now().Add(20 * time.Millisecond)
			go func() { _, _, e := b.PlanetReport(3, time.Now, deadline); result <- e }()
			time.Sleep(40 * time.Millisecond)
			release()
			if e := <-result; e == nil {
				t.Fatal("expired lock waiter charged query")
			}
			after, _ := os.ReadFile(s.Dir + "/world.json")
			_, reports, e := b.SpySnapshot(false)
			if e != nil || len(reports) != 0 || string(before) != string(after) || sharedTargetVisible(t, b, v) {
				t.Fatal("expired waiter published state", e)
			}
		})
	}
}
func TestMissileConfirmationAlterationAndForeignLogin(t *testing.T) {
	s, b, v := sharedSpyStore(t)
	if err := s.Update(func(w *game.World) error {
		w.Sectors[2].Minefield = nil
		w.Sectors[2].Defense = &game.SectorDefense{Owner: game.MercenaryOwner, Fighters: 100}
		w.Players[1].Missiles = 3
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	deadline := time.Now().Add(time.Hour)
	quote, _, err := b.PrepareMissiles(2, 1, v, time.Now, deadline)
	if err != nil {
		t.Fatal(err)
	}
	altered := quote
	altered.Count = 2
	if _, err = b.LaunchMissiles(altered, v, func() float64 { return .5 }, time.Now, deadline); err == nil {
		t.Fatal("altered confirmation accepted")
	}
	other := s.ForShip(1, 0, 1)
	otherV, err := other.SessionVisibility()
	if err != nil {
		t.Fatal(err)
	}
	if _, err = other.LaunchMissiles(quote, otherV, func() float64 { return .5 }, time.Now, deadline); err == nil {
		t.Fatal("foreign login replayed confirmation")
	}
	b.CancelMissiles(quote)
	if _, err = b.LaunchMissiles(quote, v, func() float64 { return .5 }, time.Now, deadline); err == nil {
		t.Fatal("cancelled confirmation replayed")
	}
	_, reports, _ := b.SpySnapshot(false)
	w, _ := s.View()
	if len(reports) != 0 || w.Players[1].Missiles != 3 || sharedTargetVisible(t, b, v) {
		t.Fatal("rejected confirmation published effects")
	}
}

func TestMissileSpyOnceAcrossCommittedWarningAndConcurrentRetry(t *testing.T) {
	for _, warning := range []bool{false, true} {
		t.Run(fmt.Sprint(warning), func(t *testing.T) {
			s, b, v := sharedSpyStore(t)
			if err := s.Update(func(w *game.World) error {
				w.Sectors[2].Minefield = nil
				w.Sectors[2].Defense = &game.SectorDefense{Owner: game.MercenaryOwner, Fighters: 100}
				w.Players[1].Missiles = 3
				return nil
			}); err != nil {
				t.Fatal(err)
			}
			if warning {
				b.syncDirectory = func(string) error { return errors.New("sync") }
			}
			deadline := time.Now().Add(time.Hour)
			quote, _, err := b.PrepareMissiles(2, 1, v, time.Now, deadline)
			if err != nil {
				t.Fatal(err)
			}
			results := make(chan error, 8)
			for i := 0; i < 8; i++ {
				go func() {
					_, e := b.LaunchMissiles(quote, v, func() float64 { return .5 }, time.Now, deadline)
					results <- e
				}()
			}
			committed := 0
			for i := 0; i < 8; i++ {
				e := <-results
				var w *DurabilityError
				if e == nil || errors.As(e, &w) {
					committed++
				}
			}
			if committed != 1 {
				t.Fatal("repeated missile settlement", committed)
			}
			w, _ := s.View()
			_, reports, _ := b.SpySnapshot(false)
			if w.Players[1].Missiles != 2 || len(reports) != 1 || !sharedTargetVisible(t, b, v) {
				t.Fatal("duplicate charge or missing private state")
			}
		})
	}
}
