package game

import (
	"encoding/json"
	"math"
	"os"
	"reflect"
	"testing"
)

func missileWorld(t *testing.T) (*World, *Player, *Player, *Visibility) {
	t.Helper()
	w, a := setup(t)
	a.Missiles = 10
	a.Sector = 1
	d, err := w.Join("defender", "Defender")
	if err != nil {
		t.Fatal(err)
	}
	d.Sector = 2
	d.Cloak = 0
	d.Fighters, d.Shields = 100000, 100000
	d.Missiles = 0
	w.Sectors[1].Warps = []int{2}
	w.Sectors[2].Warps = []int{1, 3}
	v, _ := w.NewVisibility(a.ID)
	return w, a, d, v
}

func TestMissileKillDropsOnlyUnsampledMinesAndClearsWithRemainingShots(t *testing.T) {
	w, a, d, v := missileWorld(t)
	d.Fighters, d.Shields = 1, 1
	d.Mines = 100
	d.Missiles = 100
	w.Ports[2].Owner = d.ID
	w.Ports[2].Treasury = 777
	intent, err := w.PrepareMissile(a.ID, 2, 3, v)
	if err != nil {
		t.Fatal(err)
	}
	out, err := w.CommitMissile(intent, v, func() float64 { return .5 }, clock)
	if err != nil {
		t.Fatal(err)
	}
	if !out.Primary.Destroyed || out.Primary.Damage.Spent != 1 || out.Primary.MinesDestroyed != 2 || out.Counter.Launched != 0 {
		t.Fatal(out)
	}
	if d.Death.Cause != "missile" || d.Death.Killer != a.ID || a.Missiles != 57 || d.Missiles != 50 || a.Turns != 499 || d.Mines != 0 || a.Mines != 50 {
		t.Fatal(a, d)
	}
	field := w.Sectors[2].Minefield
	if len(field) != 1 || field[0].Owner != d.ID || field[0].Count != 48 {
		t.Fatal(field)
	}
	if w.Ports[2].Owner != a.ID || w.Ports[2].Treasury != 777 {
		t.Fatal("missile estate lost")
	}
	if err = w.Validate(); err != nil {
		t.Fatal(err)
	}
	if _, err = w.CommitMissile(intent, v, func() float64 { t.Fatal("replayed launch RNG"); return 0 }, clock); err == nil {
		t.Fatal("replayed launch")
	}
}

func TestRetaliationHitsCloakAndPreservesActualKiller(t *testing.T) {
	w, a, d, v := missileWorld(t)
	a.StoredScore = 500000
	a.Fighters, a.Shields = 0, 0
	a.Mines = 100
	a.Turns = 37
	d.Fighters, d.Shields = MaxQuantity, MaxQuantity
	d.Missiles = 6
	w.Ports[2].Owner = a.ID
	w.Ports[2].Treasury = 777
	intent, err := w.PrepareMissile(a.ID, 2, 1, v)
	if err != nil {
		t.Fatal(err)
	}
	out, err := w.CommitMissile(intent, v, func() float64 { return .99 }, clock)
	if err != nil {
		t.Fatal(err)
	}
	if out.Primary.Destroyed || out.Counter.Launched != 6 || !out.Counter.Destroyed || a.Death.Cause != "retaliation" || a.Death.Killer != d.ID {
		t.Fatal(out, a.Death)
	}
	if a.Turns != 36 || d.Turns != 500 || a.Mines != 0 || out.Counter.Disarmed != 2 || len(w.Sectors[1].Minefield) != 0 {
		t.Fatal(out, a, d)
	}
	if w.Ports[2].Owner != d.ID || w.Ports[2].Treasury != 777 {
		t.Fatal("counter estate")
	}
	if err = w.ReplaceShip(a.ID, clock); err != nil {
		t.Fatal("false suicide cooldown", err)
	}
	if a.Turns != 36 || a.StoredScore != 500000 {
		t.Fatal("replacement changed budget/score cache")
	}
	if err = w.Validate(); err != nil {
		t.Fatal(err)
	}
}

func TestMissileMineInterceptionPreventsUnhitEnemyCounterfire(t *testing.T) {
	w, a, d, v := missileWorld(t)
	d.Missiles = 100
	w.Sectors[2].Minefield = []MineLayer{{Owner: d.ID, Count: 10}}
	intent, err := w.PrepareMissile(a.ID, 2, 5, v)
	if err != nil {
		t.Fatal(err)
	}
	out, err := w.CommitMissile(intent, v, func() float64 { t.Fatal("intercepted volley consumed RNG"); return 0 }, clock)
	if err != nil || out.Primary.MinesDestroyed != 5 || out.Counter.Launched != 0 || a.Missiles != 5 || d.Missiles != 100 || d.Fighters != 100000 {
		t.Fatal(out, err)
	}
}

func TestMissileConfirmationRevalidatesBeforeRandomness(t *testing.T) {
	for _, change := range []string{"actor moves", "target moves", "target replaced", "actor replaced", "team changes", "cloak changes", "mines change", "ammo spent", "turns spent", "planet arrives", "fighter defense arrives"} {
		t.Run(change, func(t *testing.T) {
			w, a, d, v := missileWorld(t)
			intent, err := w.PrepareMissile(a.ID, 2, 1, v)
			if err != nil {
				t.Fatal(err)
			}
			switch change {
			case "actor moves":
				a.Sector = 3
			case "target moves":
				d.Sector = 3
			case "target replaced":
				d.ShipGeneration++
			case "actor replaced":
				a.ShipGeneration++
			case "team changes":
				a.Team, d.Team = 1, 1
			case "cloak changes":
				d.Cloak = 1
			case "mines change":
				w.Sectors[2].Minefield = []MineLayer{{Owner: 0, Count: 1}}
			case "ammo spent":
				a.Missiles = 0
			case "turns spent":
				a.Turns = 0
			case "planet arrives":
				w.Sectors[2].Planet = 2
			case "fighter defense arrives":
				w.Sectors[2].Defense = &SectorDefense{Owner: d.ID, Fighters: 1}
			}
			before, _ := json.Marshal(w)
			_, err = w.CommitMissile(intent, v, func() float64 { t.Fatal("stale launch RNG"); return 0 }, clock)
			after, _ := json.Marshal(w)
			if err == nil || string(before) != string(after) {
				t.Fatal("stale launch changed state", err)
			}
		})
	}
}

func TestRetaliationVolleyBoundaries(t *testing.T) {
	for _, c := range []struct {
		score, stock int64
		r            float64
		want         int64
	}{{500000, 100, 0, 6}, {1, 100, 0, 1}, {0, 100, .5, 51}, {-1, 100, 0, 1}, {1000000, 3, .5, 2}, {MaxMoney, MaxQuantity, math.Nextafter(1, 0), MaxQuantity}, {1, 0, 0, 0}} {
		n, err := RetaliationVolley(c.score, c.stock, func() float64 { return c.r })
		if err != nil || n != c.want {
			t.Fatal(c, n, err)
		}
	}
	if _, err := RetaliationVolley(0, 1, func() float64 { return math.NaN() }); err == nil {
		t.Fatal("invalid counter RNG")
	}
}

func TestMissileCalculationErrorsAndBounds(t *testing.T) {
	for _, r := range []float64{math.NaN(), math.Inf(1), -1, 1} {
		if _, err := ResolveMissileShip(1, 1, 1, func() float64 { return r }); err == nil {
			t.Fatal("bad RNG", r)
		}
	}
	budget := 2
	if _, err := resolveMissileShip(100, 100, 100, func() float64 { return 0 }, &budget); err == nil {
		t.Fatal("calculation cap")
	}
}

func TestMissileDamageModel(t *testing.T) {
	var cases []struct {
		Name                        string
		Missiles, Fighters, Shields int64
		Draws                       []float64
		Expected                    MissileDamage
	}
	data, err := os.ReadFile("testdata/missile-model.json")
	if err != nil {
		t.Fatal(err)
	}
	if err = json.Unmarshal(data, &cases); err != nil {
		t.Fatal(err)
	}
	for _, c := range cases {
		t.Run(c.Name, func(t *testing.T) {
			i := 0
			out, err := ResolveMissileShip(c.Missiles, c.Fighters, c.Shields, func() float64 { r := c.Draws[i%len(c.Draws)]; i++; return r })
			if err != nil || !reflect.DeepEqual(out, c.Expected) {
				t.Fatal(out, c.Expected, err)
			}
		})
	}
}

func TestUnsupportedMissileEncountersAreRejectedWithoutSpending(t *testing.T) {
	for _, mode := range []string{"same sector", "longer route", "one way", "planet", "multiple enemies", "no turns", "no stock"} {
		t.Run(mode, func(t *testing.T) {
			w, a, _, v := missileWorld(t)
			to := 2
			switch mode {
			case "same sector":
				to = 1
			case "longer route":
				to = 3
			case "one way":
				w.Sectors[2].Warps = []int{3}
			case "planet":
				w.Sectors[2].Planet = 2
			case "multiple enemies":
				third, _ := w.Join("third", "Third")
				third.Sector = 2
				third.Cloak = 0
			case "no turns":
				a.Turns = 0
			case "no stock":
				a.Missiles = 0
			}
			before, _ := json.Marshal(w)
			if _, err := w.PrepareMissile(a.ID, to, 1, v); err == nil {
				t.Fatal("unsupported launch")
			}
			after, _ := json.Marshal(w)
			if string(before) != string(after) {
				t.Fatal("preparation mutated state")
			}
		})
	}
}

func TestSurvivingMissileExchangeDoesNotRecurse(t *testing.T) {
	w, a, d, v := missileWorld(t)
	d.Shields = 100
	a.Shields = 100
	d.Missiles = 1
	a.StoredScore = 0
	intent, err := w.PrepareMissile(a.ID, 2, 1, v)
	if err != nil {
		t.Fatal(err)
	}
	draws := 0
	out, err := w.CommitMissile(intent, v, func() float64 { draws++; return 0 }, clock)
	if err != nil || out.Primary.Destroyed || out.Counter.Destroyed || out.Counter.Launched != 1 || a.Death != nil || d.Death != nil || a.Missiles != 9 || d.Missiles != 0 || draws != 7 {
		t.Fatal(out, a, d, draws, err)
	}
}

func TestRetaliationOverrideDoesNotRevealOrHitOtherCloakedShips(t *testing.T) {
	w, a, d, v := missileWorld(t)
	d.Missiles = 1
	a.StoredScore = 1
	hidden, _ := w.Join("hidden", "Hidden")
	hidden.Sector = 1
	hidden.Fighters, hidden.Shields = 100, 100
	hidden.Cloak = 1
	intent, err := w.PrepareMissile(a.ID, 2, 1, v)
	if err != nil {
		t.Fatal(err)
	}
	out, err := w.CommitMissile(intent, v, func() float64 { return .5 }, clock)
	if err != nil || !out.Counter.Destroyed || hidden.Fighters != 100 || hidden.Shields != 100 || hidden.Cloak != 1 {
		t.Fatal(out, hidden, err)
	}
}

func TestAutomaticRetaliationDoesNotNeedDefendersTurns(t *testing.T) {
	w, a, d, v := missileWorld(t)
	a.Turns = 1
	a.StoredScore = 1
	d.Turns = 0
	d.Missiles = 1
	intent, err := w.PrepareMissile(a.ID, 2, 1, v)
	if err != nil {
		t.Fatal(err)
	}
	out, err := w.CommitMissile(intent, v, func() float64 { return 0 }, clock)
	if err != nil || out.Counter.Launched != 1 || a.Turns != 0 || d.Turns != 0 || a.Cloak != .99 {
		t.Fatal(out, a, d, err)
	}
}

func TestShieldExhaustionDestroysShipEvenWithEscortsRemaining(t *testing.T) {
	w, a, d, v := missileWorld(t)
	d.Shields = 0
	d.Missiles = 1
	intent, err := w.PrepareMissile(a.ID, 2, 1, v)
	if err != nil {
		t.Fatal(err)
	}
	out, err := w.CommitMissile(intent, v, func() float64 { return 0 }, clock)
	if err != nil || !out.Primary.Destroyed || out.Primary.LostEscorts != 100000 || out.Primary.Damage.Fighters != 0 || d.Fighters != 0 || out.Counter.Launched != 0 {
		t.Fatal(out, d, err)
	}
	if err = w.Validate(); err != nil {
		t.Fatal(err)
	}
}

func TestRetaliationUsesOriginalAttackersStoredScore(t *testing.T) {
	w, a, d, v := missileWorld(t)
	a.StoredScore = 500000
	a.Fighters, a.Shields = MaxQuantity, MaxQuantity
	d.StoredScore = 0
	d.Missiles = 100
	intent, err := w.PrepareMissile(a.ID, 2, 1, v)
	if err != nil {
		t.Fatal(err)
	}
	out, err := w.CommitMissile(intent, v, func() float64 { return .5 }, clock)
	if err != nil || out.Counter.Launched != 6 || d.Missiles != 94 || a.Missiles != 9 || a.Death != nil {
		t.Fatal(out, a, d, err)
	}
	if len(v.revealed) != 0 {
		t.Fatal("return fire changed observation cache")
	}
}

func TestMissileReturnPathUnsupportedDefensesRejectedBeforeSpending(t *testing.T) {
	for _, mode := range []string{"planet", "fighters"} {
		t.Run(mode, func(t *testing.T) {
			w, a, _, v := missileWorld(t)
			if mode == "planet" {
				w.Sectors[a.Sector].Planet = 2
			} else {
				w.Sectors[a.Sector].Defense = &SectorDefense{Owner: a.ID, Fighters: 100}
			}
			before, _ := json.Marshal(w)
			if _, err := w.PrepareMissile(a.ID, 2, 1, v); err == nil {
				t.Fatal("unsupported return path")
			}
			after, _ := json.Marshal(w)
			if string(before) != string(after) {
				t.Fatal("return-path rejection spent resources")
			}
		})
	}
}
