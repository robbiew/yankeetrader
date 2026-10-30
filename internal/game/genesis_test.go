package game

import (
	"encoding/json"
	"errors"
	"fmt"
	"math"
	"reflect"
	"testing"
	"time"
)

func genesisWorld(t *testing.T, count int) (*World, *Player) {
	t.Helper()
	w, e := New(clock, 36, count)
	if e != nil {
		t.Fatal(e)
	}
	p, e := w.Join("private-identity", "Winner")
	if e != nil {
		t.Fatal(e)
	}
	n := 20
	w.GenesisPorts = &n
	for i := 2; i <= 21 && i <= len(w.Ports); i++ {
		w.Ports[i].Owner = p.ID
	}
	return w, p
}
func TestGenesisActualOwnershipAndThresholds(t *testing.T) {
	for _, n := range []int{-1, 0, 19, 20, 21, 300, 301} {
		t.Run(fmt.Sprint(n), func(t *testing.T) {
			w, p := genesisWorld(t, 305)
			w.GenesisPorts = &n
			for _, port := range w.Ports {
				port.Owner = 0
			}
			p.StoredScore = MaxMoney
			for i := 2; i <= 21; i++ {
				w.Ports[i].Owner = p.ID
			}
			_, err := w.PrepareGenesis(p.ID, clock)
			if (err == nil) != (n == 20) {
				t.Fatalf("threshold %d err %v", n, err)
			}
			if (w.Validate() == nil) != (n == 0 || n == 20 || n == 21 || n == 300) {
				t.Fatalf("invalid threshold accepted: %d", n)
			}
		})
	}
	w, p := genesisWorld(t, 305)
	w.GenesisPorts = nil
	for i := 2; i <= 300; i++ {
		w.Ports[i].Owner = p.ID
	}
	if _, err := w.PrepareGenesis(p.ID, clock); err == nil {
		t.Fatal("299 met default 300")
	}
	for _, n := range []int{300, 301} {
		w.Ports[n+1].Owner = p.ID
		e, err := w.PrepareGenesis(p.ID, clock)
		if err != nil || len(e.Ports) != n || e.Threshold != 300 {
			t.Fatal(n, e, err)
		}
	}
	small, _ := genesisWorld(t, 8)
	small.GenesisPorts = nil
	if _, err := small.PrepareGenesis(1, clock); err == nil {
		t.Fatal("unreachable default lowered")
	}
}
func TestGenesisCandidateClearsStateAndBootstrapsOnce(t *testing.T) {
	for _, count := range []int{21, 3000} {
		t.Run(fmt.Sprint(count), func(t *testing.T) {
			w, p := genesisWorld(t, count)
			zero := 0
			w.LotteryDailyLimit = &zero
			p.LotteryDay = day(clock)
			p.LotteryPlays = 5
			p.LotterySequence = 9
			p.WarpSequence = 7
			p.StoredScore = MaxMoney
			// Disabling future play must not erase already valid account history.
			p.LotteryPlays = 5
			_, _ = w.Join("other-private", "Other")
			p.Sector, p.Credits, p.Mines, p.Missiles, p.Plasma, p.Ground = 8, 100000, 10, 20, 1, 30
			p.Cargo = [3]int64{1, 2, 3}
			if err := w.CreateTeam(1, "Old Private Team", "ABCD"); err != nil {
				t.Fatal(err)
			}
			if err := w.CreatePlanet(1, "Old Private Planet", clock); err != nil {
				t.Fatal(err)
			}
			draft, err := w.PrepareRadio(1, RadioAddress{ID: 2, Alias: "Other"}, "old private message", clock)
			if err != nil {
				t.Fatal(err)
			}
			if _, err = w.CommitRadio(draft, clock); err != nil {
				t.Fatal(err)
			}
			if err = w.RecordLogin(1, clock); err != nil {
				t.Fatal(err)
			}
			w.Ports[2].Treasury = 1234
			w.Sectors[9].Minefield = []MineLayer{{Owner: 1, Count: 5}}
			w.Sectors[10].Defense = &SectorDefense{Owner: 1, Fighters: 7}
			w.NextBattleReport = 123
			w.restoreMercenaryBase(clock, func() float64 { return .5 })
			w.restoreXannoron(clock, func() float64 { return .5 })
			w.Xannor.Revenge = &XannorRevengeTarget{Player: 1, Generation: p.ShipGeneration}
			w.Xannor.Reserve = 17
			e, err := w.PrepareGenesis(1, clock)
			if err != nil {
				t.Fatal(err)
			}
			before, _ := json.Marshal(w)
			at := clock.Add(time.Minute)
			next, out, err := w.GenesisCandidate(e, at, 99)
			if err != nil {
				t.Fatal(err)
			}
			after, _ := json.Marshal(w)
			if string(before) != string(after) {
				t.Fatal("candidate mutated original")
			}
			if next.Season != 2 || out.NewSeason != 2 || len(next.Players) != 0 || next.NextPlayer != 1 || len(next.Radio) != 0 || len(next.News) != 0 || next.NextNews != 1 || next.NextRadio != 1 || next.NextBattleReport != 1 || len(next.Teams) != 0 || len(next.Planets) != 2 || next.Xannor == nil || next.Xannor.Revenge != nil || next.Xannor.Reserve != 0 || next.GenerationSeed == nil || *next.GenerationSeed != 99 || next.LotteryDailyLimit == nil || *next.LotteryDailyLimit != 0 || next.GenesisPorts == w.GenesisPorts {
				t.Fatal("reset lost config or retained old state", next)
			}
			if len(next.SeasonResults) != 1 || out.Result.Score == MaxMoney || out.Result.Ports != 20 || out.Result.Winner != "Winner" || out.Result.Season != 1 || out.Result.Player != 1 {
				t.Fatal(out)
			}
			for _, port := range next.Ports {
				if port.Owner != 0 || port.Treasury != 0 || port.Supply != [3]float64{1000, 1000, 1000} {
					t.Fatal("old port retained", port)
				}
			}
			for _, sector := range next.Sectors {
				if len(sector.Minefield) != 0 || sector.Defense != nil {
					t.Fatal("old hazards retained")
				}
			}
			raw, _ := json.Marshal(next)
			next.Maintain(at)
			again, _ := json.Marshal(next)
			if string(raw) != string(again) {
				t.Fatal("bootstrap ran twice")
			}
			q, _ := next.Join("fresh", "Fresh")
			if q.ID != p.ID || q.ShipGeneration != p.ShipGeneration {
				t.Fatal("fixture did not reuse incarnation")
			}
			if err := next.CheckSession(q.ID, q.ShipGeneration, w.Season); err != ErrSeasonChanged {
				t.Fatal("old incarnation accepted", err)
			}
			if err := next.CheckSession(q.ID, q.ShipGeneration, next.Season); err != nil {
				t.Fatal(err)
			}
		})
	}
	for _, count := range []int{8, 3000} {
		w, err := New(clock, 1, count)
		if err != nil || len(w.Sectors) != count {
			t.Fatal(count, err)
		}
	}
}
func TestGenesisStaleQuotesAndBounds(t *testing.T) {
	for _, mode := range []string{"expired", "backward", "location", "turns", "cloak", "maintenance", "ownership", "config", "lottery-config", "score", "alias", "ship", "season", "altered", "history", "exhausted", "invalid"} {
		t.Run(mode, func(t *testing.T) {
			w, _ := genesisWorld(t, 32)
			e, err := w.PrepareGenesis(1, clock)
			if err != nil {
				t.Fatal(err)
			}
			now := clock.Add(time.Second)
			switch mode {
			case "location":
				w.Players[1].Sector = 2
			case "turns":
				w.Players[1].Turns--
			case "cloak":
				w.Players[1].Cloak = .5
			case "maintenance":
				w.LastMaintenance = day(clock.Add(24 * time.Hour))
			case "expired":
				now = e.Expires
			case "backward":
				now = clock.Add(-time.Second)
			case "ownership":
				w.Ports[2].Owner = 0
			case "config":
				n := 21
				w.GenesisPorts = &n
			case "lottery-config":
				n := 0
				w.LotteryDailyLimit = &n
			case "score":
				w.Players[1].Credits++
			case "alias":
				w.Players[1].Alias = "Changed"
			case "ship":
				w.Players[1].ShipGeneration++
			case "season":
				w.Season++
			case "altered":
				e.Ports[0] = 99
			case "history":
				w.SeasonResults = make([]SeasonResult, 128)
			case "exhausted":
				w.Season = math.MaxUint64
				e.Season = w.Season
			case "invalid":
				w.Sectors[1].Warps = []int{1}
			}
			if _, _, err := w.GenesisCandidate(e, now, 1); err == nil {
				t.Fatal("stale or invalid reset accepted")
			}
		})
	}
}
func TestGenesisHistoryContinuityAndNoPrivateFields(t *testing.T) {
	w, _ := genesisWorld(t, 32)
	for season := uint64(1); season <= MaxSeasonResults; season++ {
		if len(w.Players) == 0 {
			_, _ = w.Join("private-id", "Winner")
		}
		for i := 2; i <= 21; i++ {
			w.Ports[i].Owner = 1
		}
		at := clock.Add(time.Duration(season) * time.Minute)
		entry, err := w.PrepareGenesis(1, at)
		if err != nil {
			t.Fatal(season, err)
		}
		w, _, err = w.GenesisCandidate(entry, at, int64(season))
		if err != nil {
			t.Fatal(season, err)
		}
	}
	_, _ = w.Join("private-id", "Winner")
	for i := 2; i <= 21; i++ {
		w.Ports[i].Owner = 1
	}
	if _, err := w.PrepareGenesis(1, clock.Add(200*time.Minute)); err == nil {
		t.Fatal("full archive silently dropped winner")
	}
	raw, _ := json.Marshal(w.SeasonResults)
	var fields []map[string]any
	_ = json.Unmarshal(raw, &fields)
	for _, r := range fields {
		if len(r) != 8 {
			t.Fatal("unexpected archive fields", r)
		}
	}
	for _, mutate := range []func(*World){func(w *World) { w.Season = 0 }, func(w *World) { w.SeasonResults[0].Winner = "\x1bprivate" }, func(w *World) { w.SeasonResults[1].Started = clock }, func(w *World) { w.SeasonResults[0].Ports = 19 }, func(w *World) { w.SeasonResults = w.SeasonResults[:127] }} {
		data, _ := json.Marshal(w)
		var changed World
		_ = json.Unmarshal(data, &changed)
		mutate(&changed)
		if changed.Validate() == nil {
			t.Fatal("corrupt archive accepted")
		}
	}
}
func TestGenesisEpochInvalidatesEveryPreparedValueAndCache(t *testing.T) {
	for _, kind := range []string{"attack", "missile", "radio", "visibility", "spies", "warp", "lottery", "anticloak", "scanner", "mine-entry", "mine-placement", "defense", "bribe"} {
		t.Run(kind, func(t *testing.T) {
			w, p := genesisWorld(t, 32)
			_, _ = w.Join("other", "Other")
			p.Credits = 10000000
			p.Fighters = 100
			p.Mines = 10
			p.Turns = 500
			p.Sector = 8
			w.Players[2].Sector = 8
			w.Players[2].Cloak = 0
			var check func(*World) error
			switch kind {
			case "attack":
				e, err := w.PrepareAttack(1, 2, 1)
				if err != nil {
					t.Fatal(err)
				}
				check = func(w *World) error {
					_, err := w.CommitAttack(e, func() float64 { t.Fatal("stale RNG"); return 0 }, clock)
					return err
				}
			case "missile":
				w.Players[2].Sector = 9
				w.Players[2].Cloak = 0
				p.Missiles = 10
				v, _ := w.NewVisibility(1)
				e, err := w.PrepareMissile(1, 9, 1, v)
				if err != nil {
					t.Fatal(err)
				}
				check = func(w *World) error {
					fresh, _ := w.NewVisibility(1)
					_, err := w.CommitMissile(e, fresh, func() float64 { t.Fatal("stale missile RNG"); return 0 }, clock)
					return err
				}
			case "radio":
				e, err := w.PrepareRadio(1, RadioAddress{ID: 2, Alias: "Other"}, "private", clock)
				if err != nil {
					t.Fatal(err)
				}
				check = func(w *World) error { _, err := w.CommitRadio(e, clock); return err }
			case "visibility":
				v, _ := w.NewVisibility(1)
				check = func(w *World) error { _, err := w.ScanVisible(1, v, nil); return err }
			case "spies":
				n := NewSpyNetwork(1, 0, w.Season)
				n.reports = []SpyReport{{ID: 1, Unread: true}}
				n.next = 2
				check = func(w *World) error { return n.Acknowledge(w, 1) }
			case "warp":
				e, err := w.PrepareWarp(1)
				if err != nil {
					t.Fatal(err)
				}
				check = func(w *World) error {
					_, err := w.CommitWarp(e, func() float64 { t.Fatal("stale warp RNG"); return 0 }, clock)
					return err
				}
			case "lottery", "anticloak":
				p.Sector = 1
				if err := w.Dock(1, clock); err != nil {
					t.Fatal(err)
				}
				if kind == "lottery" {
					e, err := w.PrepareLottery(1, p.DockToken, "111111", clock)
					if err != nil {
						t.Fatal(err)
					}
					check = func(w *World) error {
						_, err := w.CommitLottery(e, func() (int, error) { t.Fatal("stale lottery RNG"); return 0, nil }, clock)
						return err
					}
				} else {
					v, _ := w.NewVisibility(1)
					e, err := w.PrepareAntiCloak(1, p.DockToken, v, clock)
					if err != nil {
						t.Fatal(err)
					}
					check = func(w *World) error { _, err := w.CommitAntiCloak(e, v, clock); return err }
				}
			case "mine-placement":
				e, err := w.PrepareMinePlacement(1, 1)
				if err != nil {
					t.Fatal(err)
				}
				check = func(w *World) error { _, err := w.CommitMinePlacement(e); return err }
			case "mine-entry", "scanner":
				to := w.Sectors[8].Warps[0]
				w.Sectors[to].Minefield = []MineLayer{{Owner: 0, Count: 1}}
				if kind == "mine-entry" {
					e, err := w.PrepareMineEntry(1, to)
					if err != nil {
						t.Fatal(err)
					}
					check = func(w *World) error {
						_, err := w.CommitMineEntry(e, func() float64 { t.Fatal("stale mine RNG"); return 0 }, clock)
						return err
					}
				} else {
					p.DangerScanner = true
					e, err := w.PrepareScannerEntry(1, to)
					if err != nil {
						t.Fatal(err)
					}
					check = func(w *World) error {
						_, err := w.CommitScannerEntry(e, func() float64 { t.Fatal("stale scanner RNG"); return 0 }, clock)
						return err
					}
				}
			case "defense", "bribe":
				w.Sectors[8].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: 10}
				if kind == "defense" {
					e, err := w.PrepareDefenseRetreat(1)
					if err != nil {
						t.Fatal(err)
					}
					check = func(w *World) error {
						_, err := w.CommitDefense(e, func() float64 { t.Fatal("stale defense RNG"); return 0 }, clock)
						return err
					}
				} else {
					e, err := w.PrepareBribe(1, 1, false)
					if err != nil {
						t.Fatal(err)
					}
					check = func(w *World) error {
						_, err := w.CommitBribe(e, false, func() float64 { t.Fatal("stale bribe RNG"); return 0 }, clock)
						return err
					}
				}
			}
			// Identical resources, IDs, generations, tokens and clock: epoch is the only change.
			w.Season++
			before, _ := json.Marshal(w)
			if err := check(w); err == nil {
				t.Fatal("old value accepted")
			}
			after, _ := json.Marshal(w)
			if !reflect.DeepEqual(before, after) {
				t.Fatal("stale value mutated new world")
			}
		})
	}
}

func TestGenesisGenerationBootstrapAndValidationFailureLeaveOldWorld(t *testing.T) {
	for _, mode := range []string{"generation", "nil", "bootstrap", "validation"} {
		t.Run(mode, func(t *testing.T) {
			w, _ := genesisWorld(t, 32)
			e, err := w.PrepareGenesis(1, clock)
			if err != nil {
				t.Fatal(err)
			}
			before, _ := json.Marshal(w)
			generator := func(now time.Time, seed int64, count int) (*World, error) {
				if mode == "generation" {
					return nil, errors.New("injected generator failure")
				}
				if mode == "nil" {
					return nil, nil
				}
				if mode == "bootstrap" {
					count = 8
				}
				candidate, err := New(now, seed, count)
				if err != nil {
					return nil, err
				}
				if mode == "validation" {
					candidate.Ports[1].Treasury = -1
				}
				return candidate, nil
			}
			if _, _, err = w.genesisCandidate(e, clock, 99, generator); err == nil {
				t.Fatal("broken candidate accepted")
			}
			after, _ := json.Marshal(w)
			if string(before) != string(after) {
				t.Fatal("candidate failure mutated old world")
			}
		})
	}
}

func TestGenesisPreservesOptionalConfigurationAndEncounterGuards(t *testing.T) {
	for _, value := range []*int{nil, ptrGenesisInt(0), ptrGenesisInt(7)} {
		w, _ := genesisWorld(t, 32)
		w.LotteryDailyLimit = value
		e, err := w.PrepareGenesis(1, clock)
		if err != nil {
			t.Fatal(err)
		}
		next, _, err := w.GenesisCandidate(e, clock, 1)
		if err != nil {
			t.Fatal(err)
		}
		if !reflect.DeepEqual(next.LotteryDailyLimit, value) || value != nil && next.LotteryDailyLimit == value {
			t.Fatal("config changed or aliased")
		}
	}
	for _, mode := range []string{"dead", "mines", "fighters"} {
		t.Run(mode, func(t *testing.T) {
			w, p := genesisWorld(t, 32)
			p.Sector = 8
			switch mode {
			case "dead":
				p.Death = &Death{At: clock}
			case "mines":
				w.Sectors[8].Minefield = []MineLayer{{Count: 1}}
			case "fighters":
				w.Sectors[8].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: 1}
			}
			if _, err := w.PrepareGenesis(1, clock); err == nil {
				t.Fatal("encounter/dead ship admitted")
			}
		})
	}
}
func ptrGenesisInt(n int) *int { return &n }

func TestGenesisArchivesActualOwnershipAcrossSupportedWorldGeometry(t *testing.T) {
	w, _ := genesisWorld(t, 1100)
	w.GenesisPorts = nil
	// Valid custom worlds can have more ports than New's provisional 1,000-port
	// placement. The archive must not impose that generator limit on real titles.
	for id := 2; id <= 1100; id++ {
		if w.Ports[id] == nil {
			port := *w.Ports[2]
			port.ID = id
			port.Sector = id
			w.Ports[id] = &port
			w.Sectors[id].Port = id
		}
		w.Ports[id].Owner = 1
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
	e, err := w.PrepareGenesis(1, clock)
	if err != nil {
		t.Fatal(err)
	}
	next, out, err := w.GenesisCandidate(e, clock, 99)
	if err != nil || out.Result.Ports != 1099 || len(next.Sectors) != 1100 {
		t.Fatal("actual ownership rejected by generator-specific bound", out, err)
	}
}
