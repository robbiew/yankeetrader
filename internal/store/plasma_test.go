package store

import (
	"encoding/json"
	"errors"
	"math"
	"os"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func plasmaStore(t *testing.T) (Store, Store) {
	t.Helper()
	s := create(t)
	err := s.Update(func(w *game.World) error {
		w.Planets = map[int]*game.Planet{}
		for i, p := range w.Sectors {
			p.Planet = 0
			p.Defense = nil
			p.Minefield = nil
			p.Warps = nil
			if i < 8 {
				p.Warps = []int{i + 1}
			}
		}
		p := w.Players[1]
		p.Plasma = 64
		p.Turns = 37
		p.Shields = 1_000_000
		p.Fighters = 0
		p.Cloak = 0
		return nil
	})
	if err != nil {
		t.Fatal(err)
	}
	return s, s.ForShip(1, 0, 1)
}
func plasmaBytes(t *testing.T, s Store) []byte {
	t.Helper()
	b, e := os.ReadFile(s.Dir + "/world.json")
	if e != nil {
		t.Fatal(e)
	}
	return b
}
func plasmaQuote(t *testing.T, b Store, to int, count int64) game.PlasmaIntent {
	t.Helper()
	entry, e := b.PreparePlasma(to, count, time.Now, time.Now().Add(time.Minute))
	if e != nil {
		t.Fatal(e)
	}
	return entry
}
func TestPlasmaStoreSingleUseCancellationAndTampering(t *testing.T) {
	for _, mode := range []string{"commit", "cancel", "replace", "altered", "cross-login"} {
		t.Run(mode, func(t *testing.T) {
			s, b := plasmaStore(t)
			entry := plasmaQuote(t, b, 2, 1)
			before := plasmaBytes(t, s)
			original := entry
			switch mode {
			case "cancel":
				b.CancelPlasma(entry)
			case "replace":
				_ = plasmaQuote(t, b, 3, 1)
			case "altered":
				entry.Count = 2
			case "cross-login":
				b = s.ForShip(1, 0, 1)
			}
			out, err := b.LaunchPlasma(entry, func() float64 { t.Fatal("empty course must not sample"); return 0 }, time.Now, time.Now().Add(time.Minute))
			if mode != "commit" {
				if err == nil || out.Launched != 0 || string(before) != string(plasmaBytes(t, s)) {
					t.Fatal("false commit", out, err)
				}
				return
			}
			if err != nil || out.BoltsRemaining != 63 || out.TurnsRemaining != 36 {
				t.Fatal(out, err)
			}
			saved := plasmaBytes(t, s)
			out, err = b.LaunchPlasma(original, func() float64 { return .5 }, time.Now, time.Now().Add(time.Minute))
			if err == nil || out.Launched != 0 || string(saved) != string(plasmaBytes(t, s)) {
				t.Fatal("replayed launch", out, err)
			}
		})
	}
}
func TestPlasmaStoreStaleWorldAndHolesCannotSpendOrSample(t *testing.T) {
	for _, mode := range []string{"stock", "hidden-ship", "planet", "route", "generation", "holes"} {
		t.Run(mode, func(t *testing.T) {
			s, b := plasmaStore(t)
			if mode == "holes" {
				if err := b.StartDisruption(func() float64 { return .6 }, time.Now, time.Now().Add(time.Minute)); err != nil {
					t.Fatal(err)
				}
			}
			entry := plasmaQuote(t, b, 2, 1)
			if mode == "holes" {
				b.ship.disruption.Locations = [2]int{6, 7}
			} else {
				if err := s.Update(func(w *game.World) error {
					switch mode {
					case "stock":
						w.Players[1].Plasma--
					case "hidden-ship":
						p, e := w.Join("hidden", "PRIVATE ALIAS")
						if e != nil {
							return e
						}
						p.Sector = 4
						p.Cloak = 1
					case "planet":
						w.NextPlanetGeneration++
					case "route":
						w.Sectors[4].Warps = []int{6}
					case "epoch":
						w.Season++
					case "generation":
						w.Players[1].ShipGeneration++
					}
					return nil
				}); err != nil {
					t.Fatal(err)
				}
			}
			before := plasmaBytes(t, s)
			out, err := b.LaunchPlasma(entry, func() float64 { t.Fatal("stale sampled RNG"); return 0 }, time.Now, time.Now().Add(time.Minute))
			if err == nil || out.Launched != 0 || string(before) != string(plasmaBytes(t, s)) {
				t.Fatal(out, err)
			}
		})
	}
}
func TestConcurrentPlasmaConfirmationsOnlyOneLaunchCommits(t *testing.T) {
	s, b := plasmaStore(t)
	other := s.ForShip(1, 0, 1)
	first, second := plasmaQuote(t, b, 2, 1), plasmaQuote(t, other, 2, 1)
	results := make(chan error, 2)
	for _, job := range []struct {
		bound Store
		quote game.PlasmaIntent
	}{{b, first}, {other, second}} {
		go func(job struct {
			bound Store
			quote game.PlasmaIntent
		}) {
			_, e := job.bound.LaunchPlasma(job.quote, func() float64 { return .5 }, time.Now, time.Now().Add(time.Minute))
			results <- e
		}(job)
	}
	won := 0
	for i := 0; i < 2; i++ {
		if <-results == nil {
			won++
		}
	}
	w, e := s.View()
	if e != nil || won != 1 || w.Players[1].Plasma != 63 || w.Players[1].Turns != 36 {
		t.Fatal(won, e)
	}
}
func TestPlasmaRollbackIncludesLateDeathEstateProjectionAndCapacity(t *testing.T) {
	for _, mode := range []string{"late-rng", "capacity", "budget", "future-planet", "late-abort", "hole-loop"} {
		t.Run(mode, func(t *testing.T) {
			s, b := plasmaStore(t)
			if mode == "hole-loop" {
				if e := b.StartDisruption(func() float64 { return 0 }, time.Now, time.Now().Add(time.Minute)); e != nil {
					t.Fatal(e)
				}
			}
			if e := s.Update(func(w *game.World) error {
				p, e := w.Join("victim", "Victim")
				if e != nil {
					return e
				}
				p.Sector = 2
				p.Fighters = 0
				p.Shields = 1
				p.Credits = 1000
				p.Mines = 0
				w.Ports[2].Owner = p.ID
				if mode == "capacity" {
					w.Players[1].Credits = game.MaxMoney
				}
				if mode == "budget" {
					p.Fighters = game.MaxQuantity
					p.Shields = game.MaxQuantity
					w.Sectors[2].Defense = &game.SectorDefense{Owner: game.MercenaryOwner, Fighters: game.MaxQuantity}
				}
				at := time.Now()
				if mode == "future-planet" {
					at = at.Add(time.Hour)
				}
				w.Planets[2] = &game.Planet{ID: 2, Generation: 101, Sector: 2, Owner: p.ID, Name: "Target", Updated: at, Production: [3]float64{10000, 10000, 10000}, Ground: 5000}
				w.Sectors[2].Planet = 2
				w.NextPlanetGeneration = 102
				return nil
			}); e != nil {
				t.Fatal(e)
			}
			n := int64(1)
			if mode == "budget" {
				n = 64
			}
			entry := plasmaQuote(t, b, 2, n)
			before := plasmaBytes(t, s)
			calls := 0
			rng := func() float64 {
				calls++
				if mode == "late-rng" && calls >= 15 {
					return math.NaN()
				}
				if mode == "budget" {
					return 0
				}
				if mode == "hole-loop" {
					return .125
				}
				return .5
			}
			var err error
			if mode == "late-abort" {
				err = b.Update(func(w *game.World) error {
					_, e := w.CommitPlasma(entry, rng, time.Now())
					if e != nil {
						return e
					}
					return errors.New("late report failure")
				})
			} else {
				out, e := b.LaunchPlasma(entry, rng, time.Now, time.Now().Add(time.Minute))
				err = e
				if out.Launched != 0 {
					t.Fatal("aborted receipt exposed", out)
				}
			}
			if err == nil || string(before) != string(plasmaBytes(t, s)) {
				t.Fatal("partial launch saved", mode, err)
			}
		})
	}
}
func TestPlasmaDeadlineRecheckedAfterWorldAndCacheLocks(t *testing.T) {
	for _, mode := range []string{"world", "cache"} {
		t.Run(mode, func(t *testing.T) {
			s, b := plasmaStore(t)
			entry := plasmaQuote(t, b, 2, 1)
			before := plasmaBytes(t, s)
			release, held, done := make(chan struct{}), make(chan struct{}), make(chan struct{})
			if mode == "world" {
				go func() { _ = s.locked(func() error { close(held); <-release; return nil }); close(done) }()
			} else {
				go func() { b.ship.arrivalMu.Lock(); close(held); <-release; b.ship.arrivalMu.Unlock(); close(done) }()
			}
			<-held
			result := make(chan error, 1)
			deadline := time.Now().Add(25 * time.Millisecond)
			go func() { _, e := b.LaunchPlasma(entry, func() float64 { return .5 }, time.Now, deadline); result <- e }()
			time.Sleep(50 * time.Millisecond)
			close(release)
			<-done
			if e := <-result; e == nil || string(before) != string(plasmaBytes(t, s)) {
				t.Fatal("expired write", e)
			}
		})
	}
}
func TestPlasmaCommittedDurabilityWarningAndVersion25Migration(t *testing.T) {
	s, b := plasmaStore(t)
	w, e := s.View()
	if e != nil {
		t.Fatal(e)
	}
	w.Version = 25
	bytes, _ := json.Marshal(w)
	if e = os.WriteFile(s.Dir+"/world.json", bytes, 0600); e != nil {
		t.Fatal(e)
	}
	entry := plasmaQuote(t, b, 2, 1)
	if string(plasmaBytes(t, s)) != string(bytes) {
		t.Fatal("read-only quote wrote migration")
	}
	b.syncDirectory = func(string) error { return errors.New("sync failed") }
	out, e := b.LaunchPlasma(entry, func() float64 { return .5 }, time.Now, time.Now().Add(time.Minute))
	var committed *DurabilityError
	if !errors.As(e, &committed) || out.Launched != 1 {
		t.Fatal(out, e)
	}
	w, e = s.View()
	if e != nil || w.Version != game.WorldVersion || w.Players[1].Turns != 36 || w.Players[1].Plasma != 63 {
		t.Fatal(e)
	}
	if _, e = b.LaunchPlasma(entry, func() float64 { return .5 }, time.Now, time.Now().Add(time.Minute)); e == nil {
		t.Fatal("committed warning replay")
	}
}

func TestPlasmaQuoteCannotCrossRealResetAndReusedID(t *testing.T) {
	s, b, at := genesisStore(t)
	if e := s.Update(func(w *game.World) error { w.Players[1].Plasma = 10; return nil }); e != nil {
		t.Fatal(e)
	}
	quote := plasmaQuote(t, b, 2, 1)
	now := func() time.Time { return at }
	deadline := time.Now().Add(time.Minute)
	genesis, e := b.PrepareGenesis(now, deadline)
	if e != nil {
		t.Fatal(e)
	}
	if _, e = b.ResetSeason(genesis, now, deadline); e != nil {
		t.Fatal(e)
	}
	if e = s.Update(func(w *game.World) error {
		p, e := w.Join("private", "New Occupant")
		if e == nil {
			p.Plasma = 10
		}
		return e
	}); e != nil {
		t.Fatal(e)
	}
	before := plasmaBytes(t, s)
	if _, e = b.LaunchPlasma(quote, func() float64 { t.Fatal("obsolete RNG"); return .5 }, time.Now, deadline); !errors.Is(e, game.ErrSeasonChanged) {
		t.Fatal(e)
	}
	if string(before) != string(plasmaBytes(t, s)) {
		t.Fatal("reset ship spent an old launch")
	}
}

func TestPlasmaLocalWreckAftermathFailureRollsBackDeathAndLoot(t *testing.T) {
	s, _ := plasmaStore(t)
	if e := s.Update(func(w *game.World) error {
		victim := w.Players[1]
		victim.Sector = 8
		victim.Shields = 1
		victim.Mines = 1000
		source, e := w.Join("second", "Source")
		if e != nil {
			return e
		}
		source.Sector = 8
		source.Plasma = 1
		source.Fighters = 0
		source.Shields = 1_000_000
		w.Ports[2].Owner = victim.ID
		return nil
	}); e != nil {
		t.Fatal(e)
	}
	b := s.ForShip(2, 0, 1)
	entry := plasmaQuote(t, b, 8, 1)
	before := plasmaBytes(t, s)
	calls := 0
	out, e := b.LaunchPlasma(entry, func() float64 {
		calls++
		if calls > 220 {
			return math.NaN()
		}
		return .5
	}, time.Now, time.Now().Add(time.Minute))
	if e == nil || out.Launched != 0 || calls <= 220 || string(before) != string(plasmaBytes(t, s)) {
		t.Fatal("aftermath partially saved", out, e, calls)
	}
}

func TestPlasmaLateHQFailureRollsBackCreditsRevengeAndNews(t *testing.T) {
	for _, mode := range []string{"future-planet", "news-capacity"} {
		t.Run(mode, func(t *testing.T) {
			s, b := plasmaStore(t)
			if e := s.Update(func(w *game.World) error {
				w.Xannor = &game.XannorState{HQ: 8}
				w.Sectors[1].Warps = []int{8}
				w.Sectors[8].Defense = &game.SectorDefense{Owner: game.XannorOwner, Fighters: 1}
				if mode == "news-capacity" {
					w.NextNews = math.MaxUint64
				} else {
					w.Planets[2] = &game.Planet{ID: 2, Generation: 101, Sector: 8, Name: "Later", Updated: time.Now().Add(time.Hour), Production: [3]float64{1, 1, 1}}
					w.Sectors[8].Planet = 2
					w.NextPlanetGeneration = 102
				}
				return nil
			}); e != nil {
				t.Fatal(e)
			}
			quote := plasmaQuote(t, b, 8, 1)
			before := plasmaBytes(t, s)
			out, e := b.LaunchPlasma(quote, func() float64 { return .5 }, time.Now, time.Now().Add(time.Minute))
			if e == nil || out.Launched != 0 || string(before) != string(plasmaBytes(t, s)) {
				t.Fatal("partial HQ victory", out, e)
			}
		})
	}
}

func TestPlasmaDeadlineDuringDrawReturnsExpiryAndNoReceipt(t *testing.T) {
	s, b := plasmaStore(t)
	if e := s.Update(func(w *game.World) error {
		w.Sectors[2].Defense = &game.SectorDefense{Owner: game.MercenaryOwner, Fighters: game.MaxQuantity}
		return nil
	}); e != nil {
		t.Fatal(e)
	}
	quote := plasmaQuote(t, b, 2, 1)
	before := plasmaBytes(t, s)
	out, e := b.LaunchPlasma(quote, func() float64 { time.Sleep(50 * time.Millisecond); return .5 }, time.Now, time.Now().Add(25*time.Millisecond))
	if e == nil || e.Error() != "session time expired" || out.Launched != 0 || string(before) != string(plasmaBytes(t, s)) {
		t.Fatal("expired random work saved or misreported", out, e)
	}
}
