package game

import (
	"encoding/json"
	"fmt"
	"math"
	prng "math/rand"
	"reflect"
	"strings"
	"testing"
	"time"
)

func lotteryDraws(t *testing.T, values ...float64) func() float64 {
	t.Helper()
	i := 0
	return func() float64 {
		t.Helper()
		if i >= len(values) {
			t.Fatal("unexpected lottery retry/draw")
		}
		v := values[i]
		i++
		return v
	}
}
func awardWorld(t *testing.T) (*World, *Player) { t.Helper(); w, p := setup(t); return w, p }
func winDraws(t *testing.T) func() float64 {
	return lotteryDraws(t, .5, 0, 0, 0, .5, .5, .5, .5, .5, .5, 0, .25)
}

func TestSuperPlanetAwardFreshPrivateAtomicSnapshot(t *testing.T) {
	w, p := awardWorld(t)
	p.Alias = strings.Repeat("A", 41)
	dead, _ := w.Join("dead", "Dead")
	if err := w.RecordDeath(DeathContext{Victim: dead.ID, Generation: dead.ShipGeneration, Sector: dead.Sector, Cause: "hazard"}, clock); err != nil {
		t.Fatal(err)
	}
	next := clock.Add(24 * time.Hour)
	w.superPlanetLottery(next, winDraws(t))
	planet := w.Planets[2]
	if planet == nil || planet.Owner != p.ID || planet.Sector != 8 || len(planet.Name) != 41 || planet.FactionHome != "" || planet.Updated != next || planet.Production != [3]float64{750, 750, 750} || planet.Ground != 1 || planet.Bank != 250000 || planet.Cargo != [3]float64{} || planet.Fighters != 0 || planet.Plasma != 0 || planet.Mines != 0 || planet.Missiles != 0 {
		t.Fatal("fresh award", planet)
	}
	if w.Sectors[8].Planet != 2 || len(w.Radio) != 1 || len(w.News) != 1 {
		t.Fatal("partial award")
	}
	mail := w.Radio[0]
	news := w.News[0]
	if mail.To != p.ID || mail.From != 0 || mail.System != "super-planet" || !strings.Contains(mail.Text, "sector 8!") || !mail.Unread || news.Kind != NewsSuperPlanet || news.Alias != p.Alias || news.PlanetName != "" || news.Outcome != "" {
		t.Fatal(mail, news)
	}
	outsider, _ := w.Join("outsider", "Outsider")
	history, _ := w.RadioHistory(outsider.ID, 0, 20, false)
	if len(history) != 0 {
		t.Fatal("award location leaked")
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
	history, err := w.RadioHistory(p.ID, 0, 20, true)
	if err != nil || len(history) != 1 || history[0].FromAlias != "Super Lottery" {
		t.Fatal(history, err)
	}
	if err = w.AcknowledgeRadio(p.ID, mail.ID); err != nil {
		t.Fatal(err)
	}
}
func TestLotteryOneShotFailuresAndMetadataCapacity(t *testing.T) {
	tests := []struct {
		name  string
		edit  func(*World, *Player)
		draws []float64
	}{
		{"gate", func(*World, *Player) {}, []float64{.499}},
		{"no living", func(w *World, p *Player) {
			_ = w.RecordDeath(DeathContext{Victim: p.ID, Generation: p.ShipGeneration, Sector: p.Sector, Cause: "hazard"}, clock)
		}, []float64{.5}},
		{"occupied slot", func(w *World, p *Player) { p.Credits = 25000; _ = w.CreatePlanet(p.ID, "Existing", clock) }, []float64{.5, 0, 0}},
		{"occupied sector", func(w *World, p *Player) {
			p.Sector = 8
			p.Credits = 25000
			_ = w.CreatePlanet(p.ID, "Existing", clock)
		}, []float64{.5, 0, .02, 0}},
		{"mined sector", func(w *World, p *Player) { w.Sectors[8].Minefield = []MineLayer{{Owner: p.ID, Count: 5}} }, []float64{.5, 0, 0, 0}},
		{"defended sector", func(w *World, p *Player) { w.Sectors[8].Defense = &SectorDefense{Owner: p.ID, Fighters: 10} }, []float64{.5, 0, 0, 0}},
		{"hq", func(w *World, p *Player) { w.Xannor = &XannorState{HQ: 8} }, []float64{.5, 0, 0, 0}},
		{"radio full", func(w *World, p *Player) { w.Radio = make([]RadioMessage, MaxRadioMessages) }, []float64{.5}},
		{"radio sequence", func(w *World, p *Player) { w.NextRadio = math.MaxUint64 }, []float64{.5}},
		{"news sequence", func(w *World, p *Player) { w.NextNews = math.MaxUint64 }, []float64{.5}},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			w, p := awardWorld(t)
			tc.edit(w, p)
			before, _ := json.Marshal(w)
			w.superPlanetLottery(clock.Add(24*time.Hour), lotteryDraws(t, tc.draws...))
			after, _ := json.Marshal(w)
			if string(before) != string(after) {
				t.Fatal("failed draw mutated world")
			}
		})
	}
}
func TestLotteryReservedSlotsAndBounds(t *testing.T) {
	w, p := awardWorld(t)
	w.superPlanetLottery(clock, lotteryDraws(t, .5, 0, .999999, 0, .999999, .999999, .999999, .999999, .999999, .999999, .999999, .999999))
	q := w.Planets[98]
	if q == nil || q.Owner != p.ID || q.Ground != 100 || q.Bank != 999999 || w.Planets[99] != nil || w.Planets[100] != nil {
		t.Fatal(q)
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
	full, err := New(clock, 36, 110)
	if err != nil {
		t.Fatal(err)
	}
	_, _ = full.Join("only", "Only")
	for i := 2; i <= 100; i++ {
		s := 6 + i
		full.Planets[i] = &Planet{ID: i, Sector: s, Name: "Full", Updated: clock}
		full.Sectors[s].Planet = i
	}
	if err = full.Validate(); err != nil {
		t.Fatal(err)
	}
	before, _ := json.Marshal(full)
	full.superPlanetLottery(clock, lotteryDraws(t, .5, 0, 0))
	after, _ := json.Marshal(full)
	if string(before) != string(after) {
		t.Fatal("full capacity changed world")
	}
}
func retirementWorld(t *testing.T) (*World, *Player, *Player) {
	t.Helper()
	w, p := setup(t)
	other, _ := w.Join("other", "Other")
	p.LastLogin = day(clock)
	if err := w.RecordDeath(DeathContext{Victim: p.ID, Generation: p.ShipGeneration, Sector: p.Sector, Cause: "hazard"}, clock); err != nil {
		t.Fatal(err)
	}
	// Dead accounts may retain planets and mines until retirement.
	w.Planets[2] = &Planet{ID: 2, Sector: 8, Owner: p.ID, Name: "Estate", Updated: clock, Ground: 99, Bank: 1000000}
	w.Sectors[8].Planet = 2
	w.Sectors[7].Minefield = []MineLayer{{Owner: other.ID, Count: 1}, {Owner: p.ID, Count: 2}, {Owner: 0, Count: 3}}
	w.Ports[2].Owner = p.ID
	w.Ports[2].Treasury = 900
	return w, p, other
}
func TestRetirementBoundariesIdentityHistoryAndRelease(t *testing.T) {
	for _, days := range []int{13, 14, 15} {
		t.Run(fmt.Sprint(days), func(t *testing.T) {
			w, p, other := retirementWorld(t)
			now := clock.AddDate(0, 0, days)
			// History must retain both participants, and stale drafts must fail after retire.
			draft, err := w.PrepareRadio(other.ID, RadioAddress{ID: p.ID, Alias: p.Alias}, "Old private history", clock)
			if err != nil {
				t.Fatal(err)
			}
			if _, err = w.CommitRadio(draft, clock); err != nil {
				t.Fatal(err)
			}
			messages := append([]RadioMessage(nil), w.Radio...)
			oldGen := p.ShipGeneration
			w.retireInactivePlayers(now)
			if days < 14 {
				if !p.RetiredAt.IsZero() {
					t.Fatal("early retirement")
				}
				return
			}
			if p.RetiredAt != now || p.Death == nil || p.ShipGeneration != oldGen || p.Identity != "local:q" || p.Credits != 0 || p.Turns != 0 || p.StoredScore != 0 || !reflect.DeepEqual(w.Radio, messages) {
				t.Fatal("identity/history/resource policy", p)
			}
			if w.Planets[2].Owner != 0 || w.Planets[2].Ground != 0 || w.Planets[2].Bank != 1000000 || w.Ports[2].Owner != 0 || w.Ports[2].Treasury != 0 || !reflect.DeepEqual(w.Sectors[7].Minefield, []MineLayer{{Owner: other.ID, Count: 1}, {Owner: 0, Count: 3}}) {
				t.Fatal("estate release")
			}
			if _, err = w.FindRadioRecipient(other.ID, fmt.Sprint(p.ID)); err == nil {
				t.Fatal("retired recipient advertised")
			}
			newer, _ := w.Join("new", "New")
			if newer.ID == p.ID {
				t.Fatal("identity reused")
			}
			if err = w.Validate(); err != nil {
				t.Fatal(err)
			}
			if err = w.LoginShip(p.ID, now); err != nil {
				t.Fatal(err)
			}
			if p.Death != nil || !p.RetiredAt.IsZero() || p.ShipGeneration <= oldGen || p.Turns != 500 || w.Planets[2].Owner != 0 {
				t.Fatal("reactivation", p)
			}
			history, err := w.RadioHistory(p.ID, 0, 20, false)
			if err != nil || len(history) != 1 {
				t.Fatal("own private history lost", err)
			}
			if err = w.Validate(); err != nil {
				t.Fatal(err)
			}
		})
	}
}
func TestRetirementRecentDeathLoginAndLivingProtection(t *testing.T) {
	for _, edit := range []func(*Player){func(p *Player) { p.LastLogin = day(clock.AddDate(0, 0, 1)) },
		func(p *Player) { p.LastActivity = day(clock.AddDate(0, 0, 1)) }, func(p *Player) { p.Death.At = clock.AddDate(0, 0, 1) }, func(p *Player) { p.Death = nil; p.Sector = 1 }} {
		w, p, _ := retirementWorld(t)
		edit(p)
		w.retireInactivePlayers(clock.AddDate(0, 0, 14))
		if !p.RetiredAt.IsZero() {
			t.Fatal("recent/living player retired")
		}
	}
	// No expiry-dependent daily cloak loophole; cloak remains turn based.
	w, p, _ := retirementWorld(t)
	p.Cloak = .01
	w.retireInactivePlayers(clock.AddDate(0, 0, 14))
	if p.RetiredAt.IsZero() {
		t.Fatal("cloak blocked retirement")
	}
}
func TestRetirementCapacityBoundedAndReturningAccount(t *testing.T) {
	w, p, _ := retirementWorld(t)
	now := clock.AddDate(0, 0, 14)
	w.retireInactivePlayers(now)
	for w.activePlayers() < MaxActivePlayers {
		if _, err := w.Join(fmt.Sprint(w.NextPlayer), fmt.Sprint(w.NextPlayer)); err != nil {
			t.Fatal(err)
		}
	}
	if err := w.LoginShip(p.ID, now); err == nil || p.RetiredAt.IsZero() {
		t.Fatal("reactivated into full active table")
	}
	if _, err := w.Join("overflow", "Overflow"); err == nil {
		t.Fatal("active capacity exceeded")
	}
	// New IDs beyond50 remain valid owners and retain normal combat rules.
	if w.NextPlayer != 52 {
		t.Fatal(w.NextPlayer)
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
	w.NextPlayer = MaxPlayerIdentities + 1
	// Free one active slot, but never reuse IDs on archive exhaustion.
	for _, q := range w.Players {
		if q.ID != p.ID {
			q.RetiredAt = now
			break
		}
	}
	if _, err := w.Join("archive-full", "Full"); err == nil {
		t.Fatal("exhausted IDs reused")
	}
}
func TestMaintenanceRetirementOrderingReplayAndMetadataExhaustion(t *testing.T) {
	w, p, _ := retirementWorld(t)
	now := clock.AddDate(0, 0, 14)
	if !w.maintain(now, func() float64 { return 0 }) {
		t.Fatal("maintenance skipped")
	}
	if p.RetiredAt.IsZero() || p.Turns != 0 || w.Planets[2].Owner != 0 || w.Planets[2].Ground != 1000 {
		t.Fatal("cleanup before capped10-day growth", w.Planets[2], p)
	}
	before, _ := json.Marshal(w)
	if w.maintain(now, func() float64 { t.Fatal("replay drew"); return 0 }) || w.maintain(clock, func() float64 { t.Fatal("rollback drew"); return 0 }) {
		t.Fatal("daily replay")
	}
	after, _ := json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("replay changed world")
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
	w, p, _ = retirementWorld(t)
	w.NextNews = math.MaxUint64
	w.retireInactivePlayers(now)
	if !p.RetiredAt.IsZero() {
		t.Fatal("unreportable retirement partially committed")
	}
}
func TestVersion18MigrationAndFutureFields(t *testing.T) {
	w, _ := setup(t)
	w.Version = 17
	w.Season = 0
	w.GenerationSeed = nil
	raw, _ := json.Marshal(w)
	if err := w.Upgrade(); err != nil || w.Version != WorldVersion {
		t.Fatal(err)
	}
	for _, edit := range []func(*World){func(w *World) { w.Players[1].RetiredAt = clock },
		func(w *World) { w.Players[1].LastActivity = day(clock) }, func(w *World) { w.Radio = []RadioMessage{{System: "super-planet"}} }, func(w *World) { w.News = []NewsEvent{{Kind: NewsSuperPlanet}} }, func(w *World) { w.NextPlayer = 52 }} {
		var old World
		_ = json.Unmarshal(raw, &old)
		edit(&old)
		if old.Upgrade() == nil {
			t.Fatal("legacy accepted future fields")
		}
	}
}

func TestRetirementTeamCleanupAndSavedInvariants(t *testing.T) {
	w, p, q := retirementWorld(t)
	if err := w.CreateTeam(q.ID, "Survivors", "ABCD"); err != nil {
		t.Fatal(err)
	}
	p.Team = q.Team // Dead noncaptain members are permitted in existing saved worlds.
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
	now := clock.AddDate(0, 0, 14)
	w.retireInactivePlayers(now)
	if p.Team != 0 || w.Teams[q.Team] == nil || w.Teams[q.Team].Captain != q.ID {
		t.Fatal("team membership/captain lost")
	}
	original, _ := json.Marshal(w)
	for _, edit := range []func(*World){
		func(w *World) { w.Players[1].Credits = 1 },
		func(w *World) { w.Players[1].RetiredAt = clock.Add(-time.Hour) },
		func(w *World) { w.Players[1].Death = nil },
		func(w *World) { w.Ports[2].Owner = 1 },
		func(w *World) { w.Planets[2].Owner = 1 },
		func(w *World) { w.Sectors[7].Minefield = []MineLayer{{Owner: 1, Count: 1}} },
		func(w *World) { w.Radio = []RadioMessage{{System: "fake", From: 0}} },
	} {
		var clone World
		_ = json.Unmarshal(original, &clone)
		edit(&clone)
		if clone.Validate() == nil {
			t.Fatal("retired/system invariant accepted")
		}
	}
}

func TestSeededLotteryWorldInvariantsAndPreservedBattleHistory(t *testing.T) {
	for seed := int64(1); seed <= 32; seed++ {
		w, err := New(clock, seed, 20)
		if err != nil {
			t.Fatal(err)
		}
		p, _ := w.Join("pilot", "Pilot")
		r := prng.New(prng.NewSource(seed))
		for i := 1; i <= 32; i++ {
			oldPlanets, oldRadio := len(w.Planets), len(w.Radio)
			w.superPlanetLottery(clock.AddDate(0, 0, i), r.Float64)
			if len(w.Planets)-oldPlanets != len(w.Radio)-oldRadio || len(w.Planets)-oldPlanets > 1 {
				t.Fatal("partial or repeated award", seed)
			}
			for id, planet := range w.Planets {
				if id > 98 || planet.Owner != p.ID || planet.Sector <= 7 || planet.Cargo != [3]float64{} || planet.Fighters != 0 {
					t.Fatal("seeded unsafe award", seed, planet)
				}
			}
			if err = w.Validate(); err != nil {
				t.Fatal(seed, i, err)
			}
		}
	}
	w, p, q := retirementWorld(t)
	p.BattleReports = []BattleReport{{ID: 1, At: clock, Sector: 8, XannorLost: 1, FightersLost: 1, Unread: true}}
	w.NextBattleReport = 2
	reports := append([]BattleReport(nil), p.BattleReports...)
	now := clock.AddDate(0, 0, 14)
	w.retireInactivePlayers(now)
	if !reflect.DeepEqual(p.BattleReports, reports) {
		t.Fatal("retirement changed battle history")
	}
	if err := w.LoginShip(p.ID, now); err != nil {
		t.Fatal(err)
	}
	history, err := w.BattleHistory(p.ID, false)
	if err != nil || !reflect.DeepEqual(history, reports) {
		t.Fatal("return lost own reports", err)
	}
	outsider, err := w.BattleHistory(q.ID, false)
	if err != nil || len(outsider) != 0 {
		t.Fatal("retired reports reassigned", err)
	}
}
