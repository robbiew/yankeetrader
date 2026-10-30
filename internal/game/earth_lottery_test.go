package game

import (
	"bytes"
	"encoding/json"
	"errors"
	"math"
	"reflect"
	"testing"
	"time"
)

func paidWorld(t *testing.T) (*World, *Player) {
	t.Helper()
	w, p := setup(t)
	p.Credits = 100000
	if err := w.Dock(p.ID, clock); err != nil {
		t.Fatal(err)
	}
	return w, p
}
func paidDigits(value string, calls *int) func() (int, error) {
	return func() (int, error) {
		n := *calls
		*calls++
		if n >= len(value) {
			return -1, errors.New("extra random draw")
		}
		return int(value[n] - '0'), nil
	}
}
func TestPaidLotteryAllTiersDuplicatesAndExactCredits(t *testing.T) {
	for _, tc := range []struct {
		ticket  string
		matches int
	}{{"000000", 0}, {"100000", 1}, {"120000", 2}, {"126000", 3}, {"126700", 4}, {"126780", 5}, {"126788", 6}, {"887621", 6}, {"888888", 2}, {"111111", 1}} {
		t.Run(tc.ticket, func(t *testing.T) {
			w, p := paidWorld(t)
			before := *p
			entry, err := w.PrepareLottery(p.ID, p.DockToken, tc.ticket, clock)
			if err != nil {
				t.Fatal(err)
			}
			calls := 0
			out, err := w.CommitLottery(entry, paidDigits("126788", &calls), clock)
			if err != nil || calls != 6 || out.Matches != tc.matches || out.Award != LotteryPrize(tc.matches) || out.Fee != 5 || out.Balance != 100000-5+out.Award || out.Ticket != tc.ticket || out.Draw != "126788" || out.Remaining != 4 || out.Capped != 0 {
				t.Fatal(out, err, calls)
			}
			if p.Turns != before.Turns || p.StoredScore != before.StoredScore || p.DockToken != before.DockToken || p.LotteryPlays != 1 || p.LotterySequence != 1 || p.LotteryDay != day(clock) || w.Ports[1].Treasury != 0 {
				t.Fatal("resource or cache changes", p)
			}
			if (len(w.News) == 1) != (tc.matches >= 4) {
				t.Fatal("public threshold", w.News)
			}
			if len(w.News) > 0 && (w.News[0].LotteryMatches != tc.matches || w.News[0].LotteryPrize != out.Award || w.News[0].Alias != p.Alias) {
				t.Fatal(w.News)
			}
			if err = w.Validate(); err != nil {
				t.Fatal(err)
			}
		})
	}
	for _, cash := range []int64{4, 5, 6, 1 << 27, 1 << 40, MaxMoney} {
		w, p := paidWorld(t)
		p.Credits = cash
		entry, err := w.PrepareLottery(p.ID, p.DockToken, "000000", clock)
		if cash < 5 {
			if err == nil || p.LotteryPlays != 0 || p.Credits != cash {
				t.Fatal("poor admission")
			}
			continue
		}
		calls := 0
		out, err := w.CommitLottery(entry, paidDigits("126788", &calls), clock)
		if err != nil || p.Credits != cash-5 || out.Balance != cash-5 {
			t.Fatal("fee rounding", out, err)
		}
	}
	for _, matches := range []int{4, 5, 6} {
		w, p := paidWorld(t)
		p.Credits = MaxMoney
		ticket := map[int]string{4: "126700", 5: "126780", 6: "126788"}[matches]
		e, _ := w.PrepareLottery(p.ID, p.DockToken, ticket, clock)
		calls := 0
		out, err := w.CommitLottery(e, paidDigits("126788", &calls), clock)
		if err != nil || out.Award != 5 || out.Capped != LotteryPrize(matches)-5 || out.Balance != MaxMoney || w.News[0].LotteryPrize != 5 {
			t.Fatal("capped receipt", out, err)
		}
		if _, err = w.CommitLottery(e, paidDigits("126788", &calls), clock); err == nil {
			t.Fatal("net-zero replay accepted")
		}
	}
}
func TestPaidLotteryFiniteQuotaUTCAndReplacement(t *testing.T) {
	w, p := paidWorld(t)
	for i := 0; i < 5; i++ {
		e, err := w.PrepareLottery(p.ID, p.DockToken, "000000", clock)
		if err != nil {
			t.Fatal(err)
		}
		calls := 0
		if _, err = w.CommitLottery(e, paidDigits("126788", &calls), clock); err != nil {
			t.Fatal(err)
		}
	}
	if _, err := w.PrepareLottery(p.ID, p.DockToken, "000000", clock); err == nil {
		t.Fatal("sixth play")
	}
	// A new docking session/login/incarnation cannot reset the account's quota.
	if err := w.RecordDeath(DeathContext{Victim: p.ID, Generation: p.ShipGeneration, Sector: p.Sector, Cause: "hazard"}, clock); err != nil {
		t.Fatal(err)
	}
	if err := w.ReplaceShip(p.ID, clock); err != nil {
		t.Fatal(err)
	}
	if err := w.Dock(p.ID, clock); err != nil {
		t.Fatal(err)
	}
	if _, err := w.PrepareLottery(p.ID, p.DockToken, "000000", clock); err == nil {
		t.Fatal("replacement bypass")
	}
	next := clock.AddDate(0, 0, 1)
	if err := w.Dock(p.ID, next); err != nil {
		t.Fatal(err)
	}
	e, err := w.PrepareLottery(p.ID, p.DockToken, "000000", next)
	if err != nil {
		t.Fatal(err)
	}
	if p.LotteryPlays != 5 {
		t.Fatal("quote reset persisted quota")
	}
	calls := 0
	out, err := w.CommitLottery(e, paidDigits("126788", &calls), next.In(time.FixedZone("west", -7*3600)))
	if err != nil || out.Remaining != 4 || p.LotteryPlays != 1 || p.LotteryDay != day(next) {
		t.Fatal(out, err)
	}
	p.DockUntil = next.Add(time.Hour)
	if _, err = w.PrepareLottery(p.ID, p.DockToken, "000000", clock); err == nil {
		t.Fatal("clock rollback")
	}
	// Crossing midnight invalidates a quote instead of silently spending a new day.
	boundary := next.Add(24*time.Hour - time.Second)
	p.DockUntil = boundary.Add(time.Minute)
	e, err = w.PrepareLottery(p.ID, p.DockToken, "000000", boundary)
	if err != nil {
		t.Fatal(err)
	}
	before, _ := json.Marshal(w)
	calls = 0
	if _, err = w.CommitLottery(e, paidDigits("126788", &calls), boundary.Add(time.Second)); err == nil || calls != 0 {
		t.Fatal("midnight quote accepted")
	}
	after, _ := json.Marshal(w)
	if !bytes.Equal(before, after) {
		t.Fatal("midnight mutation")
	}
}
func TestPaidLotteryRejectionsHaveNoResourceOrDrawEffects(t *testing.T) {
	for _, ticket := range []string{"", "12345", "1234567", "12A456", "-12345", "12.456", "12 456", "１２３４５６"} {
		w, p := paidWorld(t)
		if _, err := w.PrepareLottery(p.ID, p.DockToken, ticket, clock); err == nil {
			t.Fatal("ticket", ticket)
		}
	}
	for _, mode := range []string{"credits", "turns", "generation", "team", "sequence", "limit", "maintenance", "dock", "expiry", "remote", "clock", "exhausted"} {
		t.Run(mode, func(t *testing.T) {
			w, p := paidWorld(t)
			e, _ := w.PrepareLottery(p.ID, p.DockToken, "126788", clock)
			now := clock
			switch mode {
			case "credits":
				p.Credits++
			case "turns":
				p.Turns--
			case "generation":
				p.ShipGeneration++
			case "team":
				p.Team = 1
			case "sequence":
				p.LotterySequence = 1
			case "limit":
				v := 9
				w.LotteryDailyLimit = &v
			case "maintenance":
				w.LastMaintenance = day(clock.AddDate(0, 0, 1))
			case "dock":
				p.DockToken = ""
			case "expiry":
				now = p.DockUntil
			case "remote":
				p.Sector = 2
			case "clock":
				now = time.Time{}
			case "exhausted":
				p.LotterySequence = math.MaxUint64
			}
			before, _ := json.Marshal(w)
			calls := 0
			if _, err := w.CommitLottery(e, paidDigits("126788", &calls), now); err == nil || calls != 0 {
				t.Fatal(mode, err, calls)
			}
			after, _ := json.Marshal(w)
			if !bytes.Equal(before, after) {
				t.Fatal("rejection mutation")
			}
		})
	}
	for _, mode := range []string{"invalid-first", "invalid-last", "error", "nil", "news"} {
		t.Run(mode, func(t *testing.T) {
			w, p := paidWorld(t)
			e, _ := w.PrepareLottery(p.ID, p.DockToken, "126788", clock)
			if mode == "news" {
				w.NextNews = math.MaxUint64
			}
			before, _ := json.Marshal(w)
			calls := 0
			draw := paidDigits("126788", &calls)
			if mode == "invalid-first" {
				draw = func() (int, error) { return -1, nil }
			}
			if mode == "invalid-last" {
				draw = paidDigits("12678:", &calls)
			}
			if mode == "error" {
				draw = func() (int, error) { return 0, errors.New("entropy unavailable") }
			}
			if mode == "nil" {
				draw = nil
			}
			if _, err := w.CommitLottery(e, draw, clock); err == nil {
				t.Fatal("accepted", mode)
			}
			after, _ := json.Marshal(w)
			if !bytes.Equal(before, after) {
				t.Fatal("failure mutated", mode)
			}
		})
	}
	for _, limit := range []int{0, 1, 9} {
		w, p := paidWorld(t)
		w.LotteryDailyLimit = &limit
		for i := 0; i < limit; i++ {
			e, err := w.PrepareLottery(p.ID, p.DockToken, "000000", clock)
			if err != nil {
				t.Fatal(err)
			}
			calls := 0
			_, err = w.CommitLottery(e, paidDigits("126788", &calls), clock)
			if err != nil {
				t.Fatal(err)
			}
		}
		if _, err := w.PrepareLottery(p.ID, p.DockToken, "000000", clock); err == nil {
			t.Fatal("configured quota bypass")
		}
	}
}
func TestPaidLotteryVersion22MigrationAndValidation(t *testing.T) {
	w, p := paidWorld(t)
	w.Version = 21
	before := *p
	if err := w.Upgrade(); err != nil || w.Version != WorldVersion || !reflect.DeepEqual(before, *p) || w.LotteryLimit() != 5 {
		t.Fatal("migration gifts", err)
	}
	for _, mode := range []string{"count", "date", "sequence", "config", "news", "unrelated"} {
		t.Run(mode, func(t *testing.T) {
			w, p := paidWorld(t)
			switch mode {
			case "count":
				p.LotteryPlays = 1
			case "date":
				p.LotteryDay = "2026-99-99"
			case "sequence":
				p.LotterySequence = 1
			case "config":
				v := 10
				w.LotteryDailyLimit = &v
			case "news":
				w.News = []NewsEvent{{ID: 1, At: clock, Kind: NewsLottery, Alias: p.Alias, LotteryMatches: 3, LotteryPrize: 10000}}
				w.NextNews = 2
			case "unrelated":
				w.News = []NewsEvent{{ID: 1, At: clock, Kind: NewsLogin, Alias: p.Alias, LotteryPrize: 5}}
				w.NextNews = 2
			}
			if err := w.Validate(); err == nil {
				t.Fatal("invalid state accepted")
			}
			w.Version = 21
			if err := w.Upgrade(); err == nil {
				t.Fatal("future fields accepted in legacy save")
			}
		})
	}
}
