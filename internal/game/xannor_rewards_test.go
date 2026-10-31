package game

import (
	"encoding/json"
	"math"
	"reflect"
	"testing"
)

func hqRewardWorld(t *testing.T) (*World, *Player, *Player) {
	t.Helper()
	w := mobileWorld(t, 12)
	p, _ := w.Join("actor-key", "Captain")
	other, _ := w.Join("other-key", "Other")
	p.Sector, p.Fighters, p.Missiles = 7, 10000, 3
	other.Credits = 12345
	w.Sectors[7].Warps = []int{8}
	w.Sectors[8].Warps = []int{7, 9}
	w.Sectors[9].Warps = []int{8}
	w.Sectors[8].Defense = &SectorDefense{Owner: XannorOwner, Fighters: 1}
	w.Ports[2].Owner = other.ID
	w.Ports[2].Treasury = 9876
	w.Planets[2] = &Planet{Generation: uint64(2), ID: 2, Sector: 10, Owner: other.ID, Name: "Private Bank", Updated: clock, Ground: 100, Bank: 765432}
	w.Sectors[10].Planet = 2
	return w, p, other
}
func commitHQReward(t *testing.T, w *World, p *Player, missiles bool) (*XannorHQReward, error) {
	t.Helper()
	if missiles {
		v, err := w.NewVisibility(p.ID)
		if err != nil {
			return nil, err
		}
		entry, err := w.PrepareMissile(p.ID, 9, 3, v)
		if err != nil {
			return nil, err
		}
		out, err := w.CommitMissile(entry, v, func() float64 { return .9 }, clock)
		if err != nil {
			return nil, err
		}
		if len(out.Primary.HQRewards) == 0 {
			return nil, nil
		}
		if len(out.Primary.HQRewards) != 1 {
			t.Fatal(out)
		}
		return &out.Primary.HQRewards[0], nil
	}
	entry, err := w.PrepareDefenseFight(p.ID, 8, 10000, false)
	if err != nil {
		return nil, err
	}
	out, err := w.CommitDefense(entry, func() float64 { return .9 }, clock)
	return out.HQReward, err
}
func TestHQRewardExactCapacityRecipientAndPublicSnapshot(t *testing.T) {
	for _, missiles := range []bool{false, true} {
		for _, balance := range []int64{0, 1005, 1 << 30, 1 << 44, MaxMoney - XannorHQBonus, MaxMoney - XannorHQBonus + 1, MaxMoney - 1, MaxMoney} {
			w, p, q := hqRewardWorld(t)
			p.Credits = balance
			p.StoredScore = 777
			reward, err := commitHQReward(t, w, p, missiles)
			if err != nil {
				t.Fatal(err)
			}
			amount := min(XannorHQBonus, MaxMoney-balance)
			if reward == nil || reward.Player != p.ID || reward.Sector != 8 || reward.Credits != amount || p.Credits != balance+amount {
				t.Fatal(missiles, balance, reward, p.Credits)
			}
			if q.Credits != 12345 || w.Ports[2].Treasury != 9876 || w.Planets[2].Bank != 765432 || p.StoredScore != 777 {
				t.Fatal("award leaked to another financial store/cache")
			}
			if !w.HasXannorRevenge(p.ID) || w.Sectors[8].Defense != nil || len(w.News) != 1 || w.News[0].Kind != NewsXannorHQ || w.News[0].Alias != "Captain" {
				t.Fatal(w.News, w.Xannor)
			}
			p.Alias = "Renamed"
			if w.News[0].Alias != "Captain" {
				t.Fatal("news is not a snapshot")
			}
			if err = w.Validate(); err != nil {
				t.Fatal(err)
			}
		}
	}
	// Both team members exist, but the current actor alone receives the reward.
	w, p, q := hqRewardWorld(t)
	if err := w.CreateTeam(q.ID, "Reward Team", "TST1"); err != nil {
		t.Fatal(err)
	}
	p.Team = q.Team
	p.Sector, q.Sector = 1, 7
	q.Fighters = 10000
	if _, err := commitHQReward(t, w, q, false); err != nil {
		t.Fatal(err)
	}
	if q.Credits != 12345+XannorHQBonus || p.Credits != 1005 || w.News[0].Alias != "Other" || !w.HasXannorRevenge(q.ID) {
		t.Fatal("team split/actor mismatch")
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
}
func TestHQRewardRequiresActualXannorForceAndCurrentHQ(t *testing.T) {
	for _, missiles := range []bool{false, true} {
		for _, mode := range []string{"mercenary", "human", "away", "moved", "partial", "empty", "retreat"} {
			w, p, q := hqRewardWorld(t)
			switch mode {
			case "mercenary":
				w.Sectors[8].Defense.Owner = MercenaryOwner
			case "human":
				w.Sectors[8].Defense.Owner = q.ID
			case "away":
				w.Xannor.HQ = 9
			case "partial":
				w.Sectors[8].Defense.Fighters = MaxQuantity
			case "empty":
				w.Sectors[8].Defense = nil
			}
			if mode == "partial" && !missiles {
				intent, err := w.PrepareDefenseFight(p.ID, 8, 1, false)
				if err != nil {
					t.Fatal(err)
				}
				if _, err = w.CommitDefense(intent, func() float64 { return 0 }, clock); err != nil {
					t.Fatal(err)
				}
			} else if mode == "moved" {
				if missiles {
					v, _ := w.NewVisibility(p.ID)
					intent, _ := w.PrepareMissile(p.ID, 9, 3, v)
					w.Xannor.HQ = 9
					if _, err := w.CommitMissile(intent, v, func() float64 { return .9 }, clock); err != nil {
						t.Fatal(err)
					}
				} else {
					intent, _ := w.PrepareDefenseFight(p.ID, 8, 10000, false)
					w.Xannor.HQ = 9
					if _, err := w.CommitDefense(intent, func() float64 { return .9 }, clock); err != nil {
						t.Fatal(err)
					}
				}
			} else if mode == "retreat" {
				p.Sector = 8
				intent, err := w.PrepareDefenseRetreat(p.ID)
				if err != nil {
					t.Fatal(err)
				}
				if _, err = w.CommitDefense(intent, func() float64 { return .9 }, clock); err != nil {
					t.Fatal(err)
				}
			} else {
				_, err := commitHQReward(t, w, p, missiles)
				if mode != "empty" && err != nil {
					t.Fatal(mode, err)
				}
			}
			if p.Credits != 1005 || w.Xannor.Revenge != nil || len(w.News) != 0 {
				t.Fatal("nonvictory paid", mode, missiles, p.Credits, w.News)
			}
		}
	}
}
func TestHQRewardReplayStaleGenerationAndRestoredVictory(t *testing.T) {
	for _, missiles := range []bool{false, true} {
		w, p, _ := hqRewardWorld(t)
		v, _ := w.NewVisibility(p.ID)
		mi, _ := w.PrepareMissile(p.ID, 9, 3, v)
		fi, _ := w.PrepareDefenseFight(p.ID, 8, 10000, false)
		if _, err := commitHQReward(t, w, p, missiles); err != nil {
			t.Fatal(err)
		}
		raw, _ := json.Marshal(w)
		var err error
		if missiles {
			_, err = w.CommitMissile(mi, v, func() float64 { t.Fatal("replay drew"); return 0 }, clock)
		} else {
			_, err = w.CommitDefense(fi, func() float64 { t.Fatal("replay drew"); return 0 }, clock)
		}
		after, _ := json.Marshal(w)
		if err == nil || string(after) != string(raw) {
			t.Fatal("stale victory paid again")
		}
		// An actual newly deployed HQ force, fought on a new confirmation, can pay.
		w.Sectors[8].Defense = &SectorDefense{Owner: XannorOwner, Fighters: 1}
		p.Sector = 7
		p.Missiles = 3
		if _, err = commitHQReward(t, w, p, missiles); err != nil {
			t.Fatal(err)
		}
		if p.Credits != 1005+2*XannorHQBonus || len(w.News) != 2 {
			t.Fatal("restored HQ did not pay once")
		}
		// An old ship's confirmation cannot acquire a restored force's reward.
		w.Sectors[8].Defense = &SectorDefense{Owner: XannorOwner, Fighters: 1}
		p.Sector = 7
		p.Missiles = 3
		v, _ = w.NewVisibility(p.ID)
		mi, _ = w.PrepareMissile(p.ID, 9, 3, v)
		fi, _ = w.PrepareDefenseFight(p.ID, 8, 10000, false)
		p.ShipGeneration++
		if missiles {
			_, err = w.CommitMissile(mi, v, func() float64 { t.Fatal("old generation drew"); return 0 }, clock)
		} else {
			_, err = w.CommitDefense(fi, func() float64 { t.Fatal("old generation drew"); return 0 }, clock)
		}
		if err == nil || p.Credits != 1005+2*XannorHQBonus {
			t.Fatal("old incarnation paid")
		}
	}
}
func TestHQRewardFatalAftermathAndCounterRecipient(t *testing.T) {
	w, p, q := hqRewardWorld(t)
	p.Shields = 0
	w.Sectors[8].Minefield = []MineLayer{{Owner: q.ID, Count: 1}}
	reward, err := commitHQReward(t, w, p, false)
	if err != nil || reward == nil || reward.Credits != XannorHQBonus || p.Death == nil || p.Credits != 1005+XannorHQBonus || w.Xannor.Revenge != nil || w.News[0].Kind != NewsXannorHQ {
		t.Fatal("mine death did not settle credited bonus", reward, p, err)
	}
	if err = w.Validate(); err != nil {
		t.Fatal(err)
	}
	if err = w.ReplaceShip(p.ID, clock); err != nil || p.Credits != 1005 {
		t.Fatal("replacement revived/repaid bonus", err)
	}
	w, p, q = hqRewardWorld(t)
	p.Shields = 0
	q.Sector = 9
	q.Cloak = 0
	q.Fighters, q.Shields, q.Missiles = 10000, 10000, 1
	v1, _ := w.NewVisibility(p.ID)
	shot, e := w.PrepareMissile(p.ID, 9, 3, v1)
	if e != nil {
		t.Fatal(e)
	}
	fatal, e := w.CommitMissile(shot, v1, func() float64 { return .9 }, clock)
	if e != nil || len(fatal.Primary.HQRewards) != 1 || fatal.Primary.HQRewards[0].Credits != XannorHQBonus || !fatal.Counter.Destroyed || p.Death == nil || w.Xannor.Revenge != nil {
		t.Fatal("retaliation lost/misattributed primary reward", fatal, e)
	}
	if e = w.Validate(); e != nil {
		t.Fatal(e)
	}
	w, p, q = hqRewardWorld(t)
	p.Shields = 10000
	q.Sector = 9
	q.Cloak = 0
	q.Fighters, q.Shields, q.Missiles = 10000, 10000, 1
	// Forward route avoids HQ; only the surviving target's return route crosses it.
	w.Sectors[7].Warps = []int{9}
	w.Sectors[9].Warps = []int{8}
	w.Sectors[8].Warps = []int{7}
	v, _ := w.NewVisibility(p.ID)
	intent, err := w.PrepareMissile(p.ID, 9, 1, v)
	if err != nil {
		t.Fatal(err)
	}
	out, err := w.CommitMissile(intent, v, func() float64 { return .9 }, clock)
	if err != nil || len(out.Primary.HQRewards) != 0 || len(out.Counter.HQRewards) != 1 || out.Counter.HQRewards[0].Player != q.ID || q.Credits != 12345+XannorHQBonus || p.Credits != 1005 {
		t.Fatal("counter payout attributed to launcher", out, err)
	}
	if !w.HasXannorRevenge(q.ID) || w.News[0].Alias != "Other" {
		t.Fatal(w.News, w.Xannor)
	}
	if err = w.Validate(); err != nil {
		t.Fatal(err)
	}
}
func TestHQRewardNewsCapacityAndValidation(t *testing.T) {
	for _, mode := range []string{"full", "sequence", "clock"} {
		w, p, _ := hqRewardWorld(t)
		if mode == "full" {
			for i := 0; i < MaxNewsEvents; i++ {
				w.appendNews(NewsEvent{At: clock, Kind: NewsLogin, Alias: "Other"})
			}
		}
		if mode == "sequence" {
			w.NextNews = math.MaxUint64
		}
		if mode == "clock" {
			_ = w.RecordLogin(p.ID, clock.AddDate(0, 0, 1))
		}
		_, err := commitHQReward(t, w, p, false)
		if mode == "full" {
			if err != nil || len(w.News) != MaxNewsEvents || w.News[MaxNewsEvents-1].Kind != NewsXannorHQ {
				t.Fatal(err)
			}
		} else if err == nil || p.Credits != 1005 || w.Sectors[8].Defense == nil {
			t.Fatal("unreportable fighter victory partially applied", mode, err)
		}
	}
	w, p, _ := hqRewardWorld(t)
	if _, err := commitHQReward(t, w, p, false); err != nil {
		t.Fatal(err)
	}
	raw, _ := json.Marshal(w)
	for _, edit := range []func(*NewsEvent){func(e *NewsEvent) { e.Alias = "\x1b" }, func(e *NewsEvent) { e.Team = 1 }, func(e *NewsEvent) { e.TeamName = "private" }, func(e *NewsEvent) { e.PortCount = 1 }, func(e *NewsEvent) { e.PlanetName = "private" }, func(e *NewsEvent) { e.Outcome = "1000000" }} {
		var clone World
		_ = json.Unmarshal(raw, &clone)
		edit(&clone.News[0])
		if clone.Validate() == nil {
			t.Fatal("private or malformed HQ news accepted", clone.News)
		}
	}
	before := w.Players[p.ID].Credits
	w.Version = 19
	w.NextPlanetGeneration = 0
	for _, planet := range w.Planets {
		planet.Generation = 0
	}
	w.Season = 0
	w.GenerationSeed = nil
	if w.Upgrade() == nil {
		t.Fatal("legacy accepted victory news")
	}
	w.News = nil
	if err := w.Upgrade(); err != nil || w.Version != WorldVersion || w.Players[p.ID].Credits != before {
		t.Fatal("migration changed credits", err)
	}
	if !reflect.DeepEqual(w.Xannor.Revenge, &XannorRevengeTarget{Player: p.ID, Generation: p.ShipGeneration}) {
		t.Fatal("migration changed pending revenge")
	}
}
