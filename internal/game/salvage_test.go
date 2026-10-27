package game

import (
	"encoding/json"
	"math"
	"math/big"
	"os"
	"reflect"
	"testing"
)

func TestSalvageSamplingMoneyIsExact(t *testing.T) {
	for _, n := range []int64{0, 1, 2, 3, 100000001, MaxMoney - 1, MaxMoney} {
		for _, r := range []float64{0, math.SmallestNonzeroFloat64, 1e-200, .1, .2, .5, math.Nextafter(.5, 0), math.Nextafter(.5, 1), math.Nextafter(1, 0)} {
			want := new(big.Rat).Mul(new(big.Rat).SetInt64(n), new(big.Rat).SetFloat64(r))
			expected := new(big.Int).Quo(want.Num(), want.Denom()).Int64()
			got, err := scaledSalvageDraw(n, func() float64 { return r })
			if err != nil || got != expected {
				t.Fatalf("floor(%d * %.18g): %d != %d (%v)", n, r, got, expected, err)
			}
		}
	}
}

func TestRecoveredSalvageModel(t *testing.T) {
	var cases []struct {
		Name        string
		Victim      Player
		WinnerHolds int64
		Draws       []float64
		Expected    Salvage
	}
	b, err := os.ReadFile("testdata/salvage-model.json")
	if err != nil {
		t.Fatal(err)
	}
	if err = json.Unmarshal(b, &cases); err != nil {
		t.Fatal(err)
	}
	for _, c := range cases {
		t.Run(c.Name, func(t *testing.T) {
			i := 0
			result, err := SampleSalvage(c.Victim, c.WinnerHolds, func() float64 { r := c.Draws[i%len(c.Draws)]; i++; return r })
			if err != nil || !reflect.DeepEqual(result, c.Expected) {
				t.Fatal(result, c.Expected, err)
			}
			if result.Cargo[0]+result.Cargo[1]+result.Cargo[2] > result.Holds {
				t.Fatal("cargo exceeds newly recovered holds")
			}
		})
	}
}

func TestSalvageSettlementConservesInventoryAndRevokesAccess(t *testing.T) {
	w, victim, killer := ownedPortWorld(t)
	killer.Sector = 2
	victim.Fighters, victim.Shields = 0, 0
	victim.Holds = 100
	victim.Cargo = [3]int64{11, 23, 37}
	victim.Missiles, victim.Plasma, victim.Ground, victim.Mines = 41, 43, 47, 5
	victim.Credits = 10000
	killer.Credits = 1005
	w.Ports[2].Owner, w.Ports[2].Treasury = victim.ID, 777
	w.Ports[3].Owner, w.Ports[3].Treasury = victim.ID, 333
	other, _ := w.Join("other", "Other")
	other.Sector = 3
	if err := w.Dock(other.ID, clock); err != nil {
		t.Fatal(err)
	}
	w.Planets[2] = &Planet{ID: 2, Sector: 2, Owner: victim.ID, Name: "Home", Updated: clock, Production: [3]float64{1, 1, 1}, Ground: 100, Bank: 1000}
	w.Sectors[2].Planet = 2
	member, _ := w.Join("member", "Member")
	member.Sector = 2
	if err := w.CreateTeam(victim.ID, "Orion", "ABCD"); err != nil {
		t.Fatal(err)
	}
	if err := w.JoinTeam(member.ID, 1, "ABCD"); err != nil {
		t.Fatal(err)
	}
	if err := w.Land(member.ID, clock); err != nil {
		t.Fatal(err)
	}
	token := member.PlanetToken
	w.Sectors[4].Defense = &SectorDefense{Owner: victim.ID, Fighters: 123}
	planet := *w.Planets[2]
	stocks := func(p *Player) [9]int64 {
		return [9]int64{p.Holds, p.Credits, p.Missiles, p.Plasma, p.Ground, p.Mines, p.Cargo[0], p.Cargo[1], p.Cargo[2]}
	}
	v, k := stocks(victim), stocks(killer)
	draws := []float64{.785, .76755, .105, .735, .645, .455, 0, .2, .6, .99}
	i := 0
	ctx := DeathContext{Victim: victim.ID, Sector: 2, Killer: killer.ID, Cause: "combat"}
	result, err := w.SettleShipSalvage(ctx, func() float64 { r := draws[i%len(draws)]; i++; return r }, clock)
	if err != nil {
		t.Fatal(err)
	}
	nowV, nowK := stocks(victim), stocks(killer)
	for j := range v {
		if v[j]+k[j] != nowV[j]+nowK[j] {
			t.Fatal("inventory duplicated/lost", j, v, k, nowV, nowK)
		}
	}
	if result.Holds != 78 || result.Credits != 7675 || victim.Team != 0 || member.PlanetToken != "" || other.DockToken != "" {
		t.Fatal("incomplete settlement", result, victim, member, other)
	}
	if w.Ports[2].Owner != killer.ID || w.Ports[2].Treasury != 777 || w.Ports[3].Owner != killer.ID || w.Ports[3].Treasury != 333 {
		t.Fatal("port title/treasury mismatch")
	}
	if !reflect.DeepEqual(*w.Planets[2], planet) || w.Sectors[4].Defense.Owner != MercenaryOwner || w.Sectors[4].Defense.Fighters != 123 {
		t.Fatal("planet/defense estate mismatch")
	}
	if w.Bank(member.ID, token, 0, clock) == nil {
		t.Fatal("former teammate retained planet access")
	}
	if err = w.Validate(); err != nil {
		t.Fatal(err)
	}
	before, _ := json.Marshal(w)
	if _, err = w.SettleShipSalvage(ctx, func() float64 { t.Fatal("replay consumed randomness"); return 0 }, clock); err == nil {
		t.Fatal("replay succeeded")
	}
	after, _ := json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("replay changed state")
	}
	if err = w.ReplaceShip(victim.ID, clock); err != nil {
		t.Fatal(err)
	}
	if victim.Team != 0 || w.Ports[2].Owner != killer.ID || w.Planets[2].Owner != victim.ID {
		t.Fatal("replacement restored disposed assets")
	}
}

func TestSalvageRejectionsDoNotPartlySettle(t *testing.T) {
	for _, mode := range []string{"cash", "missiles", "plasma", "ground", "mines", "rng", "cargo-rng", "stale", "defended"} {
		t.Run(mode, func(t *testing.T) {
			w, victim, killer := ownedPortWorld(t)
			killer.Sector = 2
			victim.Fighters, victim.Shields = 0, 0
			victim.Missiles, victim.Plasma, victim.Ground, victim.Mines = 100, 100, 100, 100
			switch mode {
			case "cash":
				killer.Credits = MaxMoney
			case "missiles":
				killer.Missiles = MaxQuantity
			case "plasma":
				killer.Plasma = MaxQuantity
			case "ground":
				killer.Ground = MaxQuantity
			case "mines":
				killer.Mines = MaxQuantity
			case "stale":
				victim.ShipGeneration = 1
			case "defended":
				victim.Shields = 1
			}
			before, _ := json.Marshal(w)
			i := 0
			_, err := w.SettleShipSalvage(DeathContext{Victim: victim.ID, Sector: 2, Killer: killer.ID, Cause: "combat"}, func() float64 {
				i++
				if mode == "rng" || (mode == "cargo-rng" && i == 7) {
					return math.NaN()
				}
				return .9
			}, clock)
			if err == nil {
				t.Fatal("invalid settlement accepted")
			}
			after, _ := json.Marshal(w)
			if string(before) != string(after) {
				t.Fatal("failed settlement changed world")
			}
		})
	}
}

func TestDeathEstateReleaseAndProtectedDefenses(t *testing.T) {
	for _, cause := range []string{"self", "hazard"} {
		t.Run(cause, func(t *testing.T) {
			w, p := setup(t)
			w.Ports[2].Owner, w.Ports[2].Treasury = p.ID, 777
			if err := w.CreateTeam(p.ID, "Orion", "ABCD"); err != nil {
				t.Fatal(err)
			}
			w.Sectors[2].Defense = &SectorDefense{Owner: p.ID, Fighters: 123}
			actor := p.ID
			if cause == "hazard" {
				actor = 0
			}
			if err := w.RecordDeath(DeathContext{Victim: p.ID, Sector: p.Sector, Killer: actor, Cause: cause}, clock); err != nil {
				t.Fatal(err)
			}
			if w.Ports[2].Owner != 0 || w.Ports[2].Treasury != 0 || len(w.Teams) != 0 || w.Sectors[2].Defense.Owner != MercenaryOwner || w.Sectors[1].Defense != nil {
				t.Fatal("estate release failed")
			}
			if err := w.Validate(); err != nil {
				t.Fatal(err)
			}
		})
	}
	w, p := setup(t)
	w.Sectors[2].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: 123}
	if w.Move(p.ID, 2) == nil {
		t.Fatal("hostile defense silently bypassed")
	}
	w.Sectors[1].Defense = &SectorDefense{Owner: p.ID, Fighters: 1}
	if w.Validate() == nil {
		t.Fatal("Earth defense accepted")
	}
}

func TestDefensesReportRealOwnersAndAllowOnlyFriendlyPassage(t *testing.T) {
	w, p := setup(t)
	other, _ := w.Join("other", "Other")
	if err := w.CreateTeam(p.ID, "Orion", "ABCD"); err != nil {
		t.Fatal(err)
	}
	if err := w.JoinTeam(other.ID, 1, "ABCD"); err != nil {
		t.Fatal(err)
	}
	w.Sectors[2].Defense = &SectorDefense{Owner: other.ID, Fighters: 123}
	reports, err := w.Scan(p.ID)
	if err != nil {
		t.Fatal(err)
	}
	found := false
	for _, r := range reports {
		if r.Sector == 2 {
			found = true
			if r.DefenseFighters != 123 || r.DefenseOwner != "Other" {
				t.Fatal("wrong defense report", r)
			}
		}
	}
	if !found {
		t.Fatal("fixture target is not adjacent")
	}
	if err = w.Move(p.ID, 2); err != nil {
		t.Fatal("teammate defense blocked", err)
	}
	p.Sector = 1
	if err = w.LeaveTeam(other.ID, 1); err != nil {
		t.Fatal(err)
	}
	if w.Move(p.ID, 2) == nil {
		t.Fatal("former teammate defense allowed passage")
	}
	for _, d := range []*SectorDefense{{Owner: 0, Fighters: 1}, {Owner: -3, Fighters: 1}, {Owner: 99, Fighters: 1}, {Owner: 1, Fighters: 0}, {Owner: 1, Fighters: MaxQuantity + 1}} {
		w.Sectors[2].Defense = d
		if w.Validate() == nil {
			t.Fatal("invalid defense accepted", d)
		}
	}
}

func TestSalvagedHoldsCanLeaveSmallFrozenInventory(t *testing.T) {
	w, victim, killer := ownedPortWorld(t)
	killer.Sector = 2
	victim.Fighters, victim.Shields = 0, 0
	victim.Holds = 10
	victim.Cargo = [3]int64{10, 0, 0}
	result, err := w.SettleShipSalvage(DeathContext{Victim: victim.ID, Sector: 2, Killer: killer.ID, Cause: "combat"}, func() float64 { return .999999 }, clock)
	if err != nil || result.Holds != 9 || victim.Holds != 1 || victim.Cargo[0] != 1 || killer.Cargo[0] != 9 {
		t.Fatal("small frozen inventory lost", result, victim, killer, err)
	}
	if err = w.Validate(); err != nil {
		t.Fatal(err)
	}
	victim.Death = nil
	victim.Sector = 1
	if w.Validate() == nil {
		t.Fatal("live ship with fewer than ten holds accepted")
	}
}

func TestSalvageRejectsMalformedInputsAndRandomDraws(t *testing.T) {
	for _, r := range []float64{-1, 1, math.NaN(), math.Inf(1)} {
		if result, err := SampleSalvage(Player{Holds: 10}, 10, func() float64 { return r }); err == nil || result != (Salvage{}) {
			t.Fatal("invalid draw returned partial award", result, err)
		}
	}
	for _, v := range []Player{{Holds: -1}, {Holds: 1001}, {Holds: 10, Credits: -1}, {Holds: 10, Credits: MaxMoney + 1}, {Holds: 10, Missiles: -1}, {Holds: 10, Ground: MaxQuantity + 1}, {Holds: 10, Cargo: [3]int64{11, 0, 0}}, {Holds: 10, Cargo: [3]int64{-1, 0, 0}}} {
		if _, err := SampleSalvage(v, 10, func() float64 { t.Fatal("invalid inventory consumed randomness"); return 0 }); err == nil {
			t.Fatal("malformed inventory accepted", v)
		}
	}
	if _, err := SampleSalvage(Player{Holds: 10}, 10, nil); err == nil {
		t.Fatal("nil RNG accepted")
	}
}
