package store

import (
	"errors"
	"os"
	"reflect"
	"sync"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func rewardStore(t *testing.T, missiles bool) (Store, time.Time, game.DefenseIntent, game.MissileIntent, *game.Visibility) {
	t.Helper()
	st, next, fi := revengeStore(t)
	at := next.Add(-24 * time.Hour)
	var mi game.MissileIntent
	var v *game.Visibility
	if missiles {
		if err := st.Update(func(w *game.World) error {
			w.Players[1].Missiles = 1
			var err error
			v, err = w.NewVisibility(1)
			if err != nil {
				return err
			}
			mi, err = w.PrepareMissile(1, 8, 1, v)
			return err
		}); err != nil {
			t.Fatal(err)
		}
	}
	return st, at, fi, mi, v
}
func rewardCommit(w *game.World, at time.Time, missiles bool, fi game.DefenseIntent, mi game.MissileIntent, v *game.Visibility) (*game.XannorHQReward, error) {
	if missiles {
		out, err := w.CommitMissile(mi, v, func() float64 { return .9 }, at)
		if err != nil {
			return nil, err
		}
		if len(out.Primary.HQRewards) != 1 {
			return nil, errors.New("expected one HQ receipt")
		}
		return &out.Primary.HQRewards[0], nil
	}
	out, err := w.CommitDefense(fi, func() float64 { return .9 }, at)
	return out.HQReward, err
}
func TestHQRewardAtomicRollbackValidationMetadataAndDurability(t *testing.T) {
	for _, missiles := range []bool{false, true} {
		st, at, fi, mi, v := rewardStore(t, missiles)
		if err := st.Update(func(w *game.World) error { w.Players[1].Credits = game.MaxMoney - 1; return nil }); err != nil {
			t.Fatal(err)
		}
		path := st.Dir + "/world.json"
		before, _ := os.ReadFile(path)
		for _, validation := range []bool{false, true} {
			err := st.Update(func(w *game.World) error {
				reward, err := rewardCommit(w, at, missiles, fi, mi, v)
				if err != nil {
					return err
				}
				if reward == nil || reward.Credits != 1 || w.Players[1].Credits != game.MaxMoney || !w.HasXannorRevenge(1) || w.Sectors[8].Defense != nil || len(w.News) != 1 {
					t.Fatal("incomplete reward fixture", reward)
				}
				if validation {
					w.NextNews = 0
					return nil
				}
				return errors.New("abort after all effects")
			})
			if err == nil {
				t.Fatal("failed reward update saved")
			}
			after, _ := os.ReadFile(path)
			if string(after) != string(before) {
				t.Fatal("reward/news/force/revenge partly committed")
			}
		}
		// News exhaustion must reject the entire combat, including launched ammo.
		if err := st.Update(func(w *game.World) error { w.NextNews = ^uint64(0); return nil }); err != nil {
			t.Fatal(err)
		}
		blocked, _ := os.ReadFile(path)
		if err := st.Update(func(w *game.World) error { _, err := rewardCommit(w, at, missiles, fi, mi, v); return err }); err == nil {
			t.Fatal("unreportable victory accepted")
		}
		after, _ := os.ReadFile(path)
		if string(after) != string(blocked) {
			t.Fatal("unreportable victory partly saved")
		}
		if err := st.Update(func(w *game.World) error { w.NextNews = 1; return nil }); err != nil {
			t.Fatal(err)
		}
		st.syncDirectory = func(string) error { return errors.New("sync failure after rename") }
		err := st.Update(func(w *game.World) error { _, err := rewardCommit(w, at, missiles, fi, mi, v); return err })
		var committed *DurabilityError
		if !errors.As(err, &committed) {
			t.Fatal(err)
		}
		fresh := Store{Dir: st.Dir}
		saved, err := fresh.View()
		if err != nil {
			t.Fatal(err)
		}
		if saved.Players[1].Credits != game.MaxMoney || !saved.HasXannorRevenge(1) || len(saved.News) != 1 || saved.News[0].Kind != game.NewsXannorHQ {
			t.Fatal("committed reward missing", saved.News)
		}
		raw, _ := os.ReadFile(path)
		if err = fresh.Update(func(w *game.World) error { _, err := rewardCommit(w, at, missiles, fi, mi, v); return err }); err == nil {
			t.Fatal("committed victory replayed")
		}
		after, _ = os.ReadFile(path)
		if string(raw) != string(after) {
			t.Fatal("retry duplicated committed reward")
		}
	}
}
func TestHQRewardConcurrentContendersPayOnlyVictor(t *testing.T) {
	for _, missiles := range []bool{false, true} {
		st, at, fi, mi, v := rewardStore(t, missiles)
		fi2 := game.DefenseIntent{}
		mi2 := game.MissileIntent{}
		var v2 *game.Visibility
		if err := st.Update(func(w *game.World) error {
			q, err := w.Join("challenger", "Challenger")
			if err != nil {
				return err
			}
			q.Sector = 7
			q.Fighters = 10000
			q.Missiles = 1
			if missiles {
				v2, err = w.NewVisibility(q.ID)
				if err != nil {
					return err
				}
				mi2, err = w.PrepareMissile(q.ID, 8, 1, v2)
			} else {
				fi2, err = w.PrepareDefenseFight(q.ID, 8, 10000, false)
			}
			return err
		}); err != nil {
			t.Fatal(err)
		}
		var wg sync.WaitGroup
		results := make(chan error, 8)
		for i := 0; i < 8; i++ {
			wg.Add(1)
			go func(second bool) {
				defer wg.Done()
				a, b, c := fi, mi, v
				if second {
					a, b, c = fi2, mi2, v2
				}
				results <- st.Update(func(w *game.World) error { _, err := rewardCommit(w, at, missiles, a, b, c); return err })
			}(i%2 == 1)
		}
		wg.Wait()
		close(results)
		wins := 0
		for err := range results {
			if err == nil {
				wins++
			}
		}
		if wins != 1 {
			t.Fatal("double settlement", missiles, wins)
		}
		saved, err := (Store{Dir: st.Dir}).View()
		if err != nil {
			t.Fatal(err)
		}
		if saved.Players[1].Credits+saved.Players[2].Credits != 2010+game.XannorHQBonus || len(saved.News) != 1 || saved.Sectors[8].Defense != nil {
			t.Fatal("duplicate/missing payout", saved.News)
		}
		victor := saved.Xannor.Revenge.Player
		if saved.Players[victor].Credits != 1005+game.XannorHQBonus || saved.News[0].Alias != saved.Players[victor].Alias {
			t.Fatal("paid wrong contender")
		}
	}
}
func TestHQRewardVersion19MigrationNoBackfillAndFutureRejection(t *testing.T) {
	st, _, _, _, _ := rewardStore(t, false)
	w, _ := st.View()
	w.Version = 19
	w.Season = 0
	w.GenerationSeed = nil
	// A pending target from an old victory must never become a payment claim.
	w.Xannor.Revenge = &game.XannorRevengeTarget{Player: 1, Generation: w.Players[1].ShipGeneration}
	raw, _ := marshalHistoricalWorld(w)
	path := st.Dir + "/world.json"
	if err := os.WriteFile(path, raw, 0600); err != nil {
		t.Fatal(err)
	}
	loaded, err := st.View()
	if err != nil || loaded.Version != game.WorldVersion {
		t.Fatal(err)
	}
	expected := *w
	expected.Version = game.WorldVersion
	expected.Season = 1
	if !reflect.DeepEqual(&expected, loaded) {
		t.Fatal("migration paid/backfilled/altered old state")
	}
	unchanged, _ := os.ReadFile(path)
	if string(unchanged) != string(raw) {
		t.Fatal("read-only migration wrote")
	}
	if err = st.Update(func(*game.World) error { return nil }); err != nil {
		t.Fatal(err)
	}
	saved, _ := st.View()
	if saved.Version != game.WorldVersion || saved.Players[1].Credits != 1005 || len(saved.News) != 0 {
		t.Fatal("migration invented reward")
	}
	w.News = []game.NewsEvent{{ID: 1, At: w.Created, Kind: game.NewsXannorHQ, Alias: "Captain"}}
	w.NextNews = 2
	raw, _ = marshalHistoricalWorld(w)
	_ = os.WriteFile(path, raw, 0600)
	if _, err = st.View(); err == nil {
		t.Fatal("legacy input accepted new victory news")
	}
}

func TestHQRewardAtomicFatalMineAftermathAndReplacement(t *testing.T) {
	st, at, fi, _, _ := rewardStore(t, false)
	if err := st.Update(func(w *game.World) error {
		w.Players[1].Shields = 0
		w.Sectors[8].Minefield = []game.MineLayer{{Owner: 0, Count: 1}}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	w, _ := st.View()
	var err error
	fi, err = w.PrepareDefenseFight(1, 8, 10000, false)
	if err != nil {
		t.Fatal(err)
	}
	path := st.Dir + "/world.json"
	before, _ := os.ReadFile(path)
	commit := func(w *game.World) error {
		out, err := w.CommitDefense(fi, func() float64 { return .9 }, at)
		if err != nil {
			return err
		}
		if out.HQReward == nil || out.HQReward.Credits != game.XannorHQBonus || !out.Mines.Destroyed || w.Players[1].Credits != 1005+game.XannorHQBonus || w.Xannor.Revenge != nil {
			t.Fatal("missing combined victory/death effects", out)
		}
		return nil
	}
	if err = st.Update(func(w *game.World) error {
		if err := commit(w); err != nil {
			return err
		}
		return errors.New("abort after death")
	}); err == nil {
		t.Fatal("aborted aftermath saved")
	}
	after, _ := os.ReadFile(path)
	if string(before) != string(after) {
		t.Fatal("partial bonus/death persisted")
	}
	if err = st.Update(commit); err != nil {
		t.Fatal(err)
	}
	fresh := Store{Dir: st.Dir}
	saved, err := fresh.View()
	if err != nil || saved.Players[1].Death == nil || len(saved.News) != 1 || saved.Sectors[8].Defense != nil {
		t.Fatal("aftermath reload", err)
	}
	if _, err = fresh.ForShip(1, fi.Generation, 1).DefenseEncounter(fi, func() float64 { return .9 }, at, time.Now().Add(time.Minute)); err == nil {
		t.Fatal("dead incarnation redeemed reward")
	}
	if err = fresh.Update(func(w *game.World) error { return w.LoginShip(1, at) }); err != nil {
		t.Fatal(err)
	}
	saved, _ = fresh.View()
	if saved.Players[1].Credits != 1005 || len(saved.News) != 1 || saved.HasXannorRevenge(1) {
		t.Fatal("replacement restored or repaid bonus")
	}
}
