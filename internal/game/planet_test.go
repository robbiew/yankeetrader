package game

import (
	"encoding/json"
	"math"
	"os"
	"testing"
	"time"
)

// Decode explicitly so evidence keeps the source's player_after name.
type planetCase struct {
	Name, Source  string
	Now           time.Time
	Player, Other Player
	PlayerAfter   Player `json:"player_after"`
	Before, After Planet
}

func loadPlanets(t *testing.T) []planetCase {
	t.Helper()
	b, e := os.ReadFile("testdata/dos-planets.json")
	if e != nil {
		t.Fatal(e)
	}
	var cases []planetCase
	if e = json.Unmarshal(b, &cases); e != nil {
		t.Fatal(e)
	}
	return cases
}
func fixturePlanet(t *testing.T, c planetCase) *World {
	t.Helper()
	w, e := New(clock, 36, 128)
	if e != nil {
		t.Fatal(e)
	}
	w.Players = map[int]*Player{2: &c.Player, 3: &c.Other}
	w.NextPlayer = 4
	p := c.Before
	if c.Name == "create" || c.Name == "poor" || c.Name == "full" {
		p.Sector = 101
	} else {
		w.Sectors[100].Planet = 2
	}
	w.Planets[2] = &p
	w.Sectors[p.Sector].Planet = 2
	if c.Name == "full" {
		w.Planets = map[int]*Planet{}
		w.Sectors[101].Planet = 0
		for id := 2; id <= 100; id++ {
			v := p
			v.ID = id
			v.Sector = id - 1
			w.Planets[id] = &v
			w.Sectors[v.Sector].Planet = id
		}
		w.Players[2].Sector = 128
	}
	if e = w.Validate(); e != nil {
		t.Fatal(e)
	}
	return w
}
func closeFloat(t *testing.T, n string, got, want, tolerance float64) {
	t.Helper()
	if math.Abs(got-want) > tolerance {
		t.Fatalf("%s: got %.9f, DOS %.9f (tol %.4g)", n, got, want, tolerance)
	}
}
func TestDOSPlanetGoldenActions(t *testing.T) {
	for _, c := range loadPlanets(t) {
		t.Run(c.Name, func(t *testing.T) {
			w := fixturePlanet(t, c)
			var e error
			rejected := false
			switch c.Name {
			case "create", "poor", "full":
				e = w.CreatePlanet(2, "New Eden", c.Now)
				rejected = c.Name != "create"
			default:
				e = w.Land(2, c.Now)
				if c.Name == "foreign" {
					rejected = true
					break
				}
				if e != nil {
					t.Fatal(e)
				}
				token := w.Players[2].PlanetToken
				switch c.Name {
				case "takeall":
					e = w.TakeAll(2, token, c.Now)
				case "transfer-cargo":
					e = w.Transfer(2, token, "cargo", 0, c.Now)
				case "transfer-weapons":
					for _, item := range []string{"plasma", "missiles", "mines"} {
						if e = w.Transfer(2, token, item, 0, c.Now); e != nil {
							t.Fatal(e)
						}
					}
					e = w.Transfer(2, token, "fighters", 123, c.Now)
				case "invest1":
					e = w.Invest(2, token, 1, c.Now)
				case "invest251":
					e = w.Invest(2, token, 251, c.Now)
				case "bank-deposit":
					e = w.Bank(2, token, 15000, c.Now)
				case "bank-negative":
					e = w.Bank(2, token, -1, c.Now)
					rejected = true
				case "bank-over":
					e = w.Bank(2, token, 110001, c.Now)
					rejected = true
				case "bank-large":
					e = w.Bank(2, token, 1, c.Now)
				case "bank-large-relogin":
					e = w.Bank(2, token, 2, c.Now)
				case "bank-withdraw", "bank-halfday", "team-bank", "unguarded-bank":
					e = w.Bank(2, token, 0, c.Now)
				}
			}
			if rejected {
				if e == nil {
					t.Fatal("DOS rejection accepted")
				}
				if w.Players[2].Credits != c.Player.Credits {
					t.Fatal("rejection changed ship credits")
				}
				return
			}
			if e != nil {
				t.Fatal(e)
			}
			p := w.Players[2]
			want := c.PlayerAfter
			if c.Name == "bank-large" || c.Name == "bank-large-relogin" { // Intentional departure: DOS lost the one-credit debit.
				want.Credits = c.Player.Credits - 1
			}
			if p.Credits != want.Credits || p.Cargo != want.Cargo || p.Fighters != want.Fighters || p.Missiles != want.Missiles || p.Mines != want.Mines || p.Plasma != want.Plasma {
				t.Fatalf("ship mismatch %s: got %+v want %+v", c.Source, p, want)
			}
			planet := w.Planets[c.After.ID]
			if c.Name == "create" {
				planet = w.Planets[3]
			}
			if planet.Bank != c.After.Bank || planet.Ground != c.After.Ground || planet.Owner != c.After.Owner {
				t.Fatalf("planet ownership/bank/ground mismatch: %+v want %+v", planet, c.After)
			}
			for i := 0; i < 3; i++ {
				closeFloat(t, "production", planet.Production[i], c.After.Production[i], .03)
				closeFloat(t, "cargo", planet.Cargo[i], c.After.Cargo[i], .03)
			}
			closeFloat(t, "fighters", planet.Fighters, c.After.Fighters, .05)
			closeFloat(t, "missiles", planet.Missiles, c.After.Missiles, .01)
			closeFloat(t, "mines", planet.Mines, c.After.Mines, .01)
			closeFloat(t, "plasma", planet.Plasma, c.After.Plasma, .01)
			if e = w.Validate(); e != nil {
				t.Fatal(e)
			}
		})
	}
}
func TestPlanetMaintenanceOrderAndRollback(t *testing.T) {
	p := Planet{Updated: clock, Production: [3]float64{1000, 2000, 3000}, Bank: 1000000, Ground: 100}
	copy := p
	now := clock.Add(12 * time.Hour)
	p.update(now, true)
	copy.update(now, false)
	closeFloat(t, "lazy ore", p.Cargo[0], 552.5, .0001)
	closeFloat(t, "maintenance ore", copy.Cargo[0], 550, .0001)
	if p.Bank != 1005000 || copy.Bank != 1005000 {
		t.Fatal("interest")
	}
	snapshot, _ := json.Marshal(p)
	p.update(clock, true)
	p.update(now, true)
	after, _ := json.Marshal(p)
	if string(snapshot) != string(after) {
		t.Fatal("rollback or repeated update changed planet")
	}
	if interest(MaxMoney, 24*time.Hour) != 90000000000000 {
		t.Fatal("large exact-money interest")
	}
}
func TestPlanetAccessTokensAndConservation(t *testing.T) {
	w, p := setup(t)
	p.Credits = 100000000
	if e := w.CreatePlanet(p.ID, "Home", clock); e != nil {
		t.Fatal(e)
	}
	if e := w.Land(p.ID, clock); e != nil {
		t.Fatal(e)
	}
	token := p.PlanetToken
	planet := w.Planets[2]
	for _, target := range []int64{1, 2, 0, 1000000, 0} {
		before := p.Credits + planet.Bank
		if e := w.Bank(p.ID, token, target, clock); e != nil {
			t.Fatal(e)
		}
		if p.Credits+planet.Bank != before {
			t.Fatal("money minted")
		}
	}
	other, _ := w.Join("other", "Other")
	planet.Owner = other.ID
	if w.Bank(p.ID, token, 0, clock) == nil {
		t.Fatal("stale access after ownership change")
	}
	p.Team = 1
	other.Team = 1
	if e := w.Bank(p.ID, token, 0, clock); e != nil {
		t.Fatal(e)
	}
	if e := w.Land(p.ID, clock); e != nil {
		t.Fatal(e)
	}
	if w.TakeAll(p.ID, token, clock) == nil {
		t.Fatal("stale token after reland")
	}
	token = p.PlanetToken
	if e := w.Move(p.ID, 2); e != nil {
		t.Fatal(e)
	}
	if w.Bank(p.ID, token, 0, clock) == nil {
		t.Fatal("access after movement")
	}
}
