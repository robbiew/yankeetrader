package game

import (
	"encoding/json"
	"errors"
	"math"
	"os"
	"testing"
)

func TestSectorTransferOwnershipUnionAndCapacity(t *testing.T) {
	w, p := setup(t)
	p.Sector = 8
	p.Fighters = 1000
	if err := w.SetSectorFighters(p.ID, 100); err != nil {
		t.Fatal(err)
	}
	if p.Fighters != 900 || w.Sectors[8].Defense.Fighters != 100 {
		t.Fatal(p)
	}
	if err := w.SetSectorFighters(p.ID, 0); err != nil || p.Fighters != 1000 || w.Sectors[8].Defense != nil {
		t.Fatal(err, p)
	}
	p.Sector = 7
	if err := w.SetSectorFighters(p.ID, 1); err == nil {
		t.Fatal("Union deployment")
	}
	w.Sectors[7].Defense = &SectorDefense{Owner: p.ID, Fighters: 100}
	if err := w.SetSectorFighters(p.ID, 0); err != nil || p.Fighters != 1100 {
		t.Fatal(err)
	}
	p.Sector = 8
	owner, _ := w.Join("owner", "Owner")
	p.Team = 1
	owner.Team = 1
	w.Sectors[8].Defense = &SectorDefense{Owner: owner.ID, Fighters: 100}
	if err := w.ReinforceSector(p.ID, 123); err != nil {
		t.Fatal(err)
	}
	if p.Fighters != 977 || w.Sectors[8].Defense.Fighters != 223 || w.Sectors[8].Defense.Owner != owner.ID {
		t.Fatal("transfer changed title or balances")
	}
	if err := w.SetSectorFighters(p.ID, 0); err == nil {
		t.Fatal("teammate withdrawal")
	}
	owner.Team = 0
	if err := w.ReinforceSector(p.ID, 1); err == nil {
		t.Fatal("foreign donation")
	}
	w.Sectors[8].Defense = &SectorDefense{Owner: p.ID, Fighters: 1}
	p.Fighters = MaxQuantity
	if err := w.SetSectorFighters(p.ID, 0); err == nil || w.Sectors[8].Defense == nil {
		t.Fatal("recovery overflow")
	}
}

func TestSectorSurrenderStrictThresholdAndNPCRefusal(t *testing.T) {
	out, err := ResolveSectorBattle(10001, 1000, 0, 2, true, func() float64 { t.Fatal("immediate surrender used RNG"); return 0 })
	if err != nil || out.Joined != 1000 || out.AttackerLosses != 0 || out.Rounds != 0 {
		t.Fatal(out, err)
	}
	out, err = ResolveSectorBattle(10000, 1000, 0, 2, true, func() float64 { return .5 })
	if err != nil || out.Rounds != 1 || out.DefenderLosses != 50 || out.Joined != 950 {
		t.Fatal(out, err)
	}
	for _, owner := range []int{2, MercenaryOwner, XannorOwner} {
		out, err = ResolveSectorBattle(10001, 1, 0, owner, false, func() float64 { return .5 })
		if err != nil || out.Joined != 0 || out.DefenderLosses != 1 {
			t.Fatal(out, err)
		}
	}
	out, err = ResolveSectorBattle(10001, 1, 0, MercenaryOwner, true, func() float64 { return .5 })
	if err != nil || out.Joined != 0 || out.DefenderLosses != 1 {
		t.Fatal(out, err)
	}
	if _, err = ResolveSectorBattle(1, 1, 0, 2, true, func() float64 { return math.NaN() }); err == nil {
		t.Fatal("invalid RNG")
	}
}

func TestDefenseEntryLossEscapeAndStaleWarning(t *testing.T) {
	w, p := setup(t)
	p.Sector = 7
	p.Fighters = 10002
	p.Turns = 26
	p.Cloak = 1
	w.Sectors[7].Warps = []int{8}
	w.Sectors[8].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: 1}
	intent, err := w.PrepareDefenseFight(p.ID, 8, 1, true)
	if err != nil {
		t.Fatal(err)
	}
	w.Sectors[8].Defense.Fighters++
	if _, err = w.CommitDefense(intent, func() float64 { t.Fatal("stale RNG"); return 0 }, clock); err == nil || p.Sector != 7 {
		t.Fatal("stale warning accepted")
	}
	w.Sectors[8].Defense.Fighters--
	// At 25 turns cloak decays to .99: .3505+.099 < .45, so committed force loses.
	draws := 0
	out, err := w.CommitDefense(intent, func() float64 {
		draws++
		if draws == 1 {
			return .3505
		}
		return 0
	}, clock)
	if err != nil || !out.Escaped || p.Sector == 8 || p.Fighters != 10001 || p.Turns != 25 || p.Cloak != .99 || w.Sectors[8].Defense.Fighters != 1 {
		t.Fatal(out, p, err)
	}
	p.Sector = 8
	if err = w.Move(p.ID, 7); !errors.Is(err, ErrDefenseEncounter) {
		t.Fatal(err)
	}
}

func TestSectorVictoryResolvesDestinationMines(t *testing.T) {
	w, p := setup(t)
	p.Sector = 7
	p.Fighters = 10001
	p.Shields = 10000
	owner, _ := w.Join("owner", "Owner")
	w.Sectors[7].Warps = []int{8}
	w.Sectors[8].Defense = &SectorDefense{Owner: owner.ID, Fighters: 1000}
	w.Sectors[8].Minefield = []MineLayer{{Owner: owner.ID, Count: 1}}
	intent, err := w.PrepareDefenseFight(p.ID, 8, 10001, true)
	if err != nil {
		t.Fatal(err)
	}
	out, err := w.CommitDefense(intent, func() float64 { return .5 }, clock)
	if err != nil || out.Battle.Joined != 1000 || w.Sectors[8].Defense != nil || out.Mines.Spent != 1 || len(w.Sectors[8].Minefield) != 0 {
		t.Fatal(out, err)
	}
	if err = w.Validate(); err != nil {
		t.Fatal(err)
	}
}

func TestMissileSectorInterceptionPrecedesMinesAndShip(t *testing.T) {
	w, a, d, v := missileWorld(t)
	w.Sectors[2].Defense = &SectorDefense{Owner: d.ID, Fighters: 3000}
	w.Sectors[2].Minefield = []MineLayer{{Owner: d.ID, Count: 1}}
	intent, err := w.PrepareMissile(a.ID, 2, 4, v)
	if err != nil {
		t.Fatal(err)
	}
	out, err := w.CommitMissile(intent, v, func() float64 { return .5 }, clock)
	if err != nil || out.Primary.SectorMissiles != 2 || out.Primary.SectorFightersDestroyed != 3000 || out.Primary.MinesDestroyed != 1 || out.Primary.Damage.Spent != 1 || w.Sectors[2].Defense != nil {
		t.Fatal(out, err)
	}
	if a.Missiles != 6 || a.Turns != 499 {
		t.Fatal(a)
	}
}
func TestSectorInterceptionPreventsRetaliationWithoutShipHit(t *testing.T) {
	w, a, d, v := missileWorld(t)
	d.Missiles = 10
	w.Sectors[2].Defense = &SectorDefense{Owner: d.ID, Fighters: 10000}
	intent, err := w.PrepareMissile(a.ID, 2, 1, v)
	if err != nil {
		t.Fatal(err)
	}
	out, err := w.CommitMissile(intent, v, func() float64 { return .5 }, clock)
	if err != nil || out.Primary.Damage.Spent != 0 || out.Counter.Launched != 0 || d.Missiles != 10 || w.Sectors[2].Defense.Fighters != 7500 {
		t.Fatal(out, err)
	}
}

func TestSectorBattleResearchFixtures(t *testing.T) {
	var rows []struct {
		Name                 string
		Attackers, Defenders int64
		Cloak, Draw          float64
		OriginalOwner        int
		Accept               bool
		Expected             struct {
			Lost, Killed, Joined int64
			Offered              bool
		}
	}
	data, err := os.ReadFile("testdata/sector-battles.json")
	if err != nil {
		t.Fatal(err)
	}
	if err = json.Unmarshal(data, &rows); err != nil {
		t.Fatal(err)
	}
	for _, row := range rows {
		t.Run(row.Name, func(t *testing.T) {
			owner := row.OriginalOwner
			if owner > 1 {
				owner = 1
			}
			out, err := ResolveSectorBattle(row.Attackers, row.Defenders, row.Cloak, owner, row.Accept, func() float64 { return row.Draw })
			if err != nil || out.AttackerLosses != row.Expected.Lost || out.DefenderLosses != row.Expected.Killed || out.Joined != row.Expected.Joined || out.SurrenderConsidered != row.Expected.Offered {
				t.Fatal(out, row.Expected, err)
			}
		})
	}
}

func TestRetaliationInterceptedByLaunchersDefense(t *testing.T) {
	w, a, d, v := missileWorld(t)
	// Earth never permits defenses; put the launcher in sector 3 instead.
	a.Sector = 3
	w.Sectors[3].Warps = []int{2}
	w.Sectors[2].Warps = []int{3}
	w.Sectors[3].Defense = &SectorDefense{Owner: a.ID, Fighters: 10000}
	d.Missiles = 1
	a.StoredScore = 1
	intent, err := w.PrepareMissile(a.ID, 2, 1, v)
	if err != nil {
		t.Fatal(err)
	}
	out, err := w.CommitMissile(intent, v, func() float64 { return .5 }, clock)
	if err != nil || out.Counter.SectorMissiles != 1 || out.Counter.SectorFightersDestroyed != 2500 || out.Counter.Damage.Spent != 0 || d.Missiles != 0 || w.Sectors[3].Defense.Fighters != 7500 {
		t.Fatal(out, err)
	}
	if err = w.Validate(); err != nil {
		t.Fatal(err)
	}
}
func TestFriendlyDefenseBypassAndDefenseOnlyTarget(t *testing.T) {
	w, a, d, v := missileWorld(t)
	w.Sectors[2].Defense = &SectorDefense{Owner: a.ID, Fighters: 10000}
	intent, err := w.PrepareMissile(a.ID, 2, 1, v)
	if err != nil {
		t.Fatal(err)
	}
	out, err := w.CommitMissile(intent, v, func() float64 { return .5 }, clock)
	if err != nil || out.Primary.SectorMissiles != 0 || out.Primary.Damage.Spent != 1 || w.Sectors[2].Defense.Fighters != 10000 {
		t.Fatal(out, err)
	}
	d.Sector = 3
	w.Sectors[2].Defense.Owner = d.ID
	intent, err = w.PrepareMissile(a.ID, 2, 1, v)
	if err != nil || len(intent.Sectors[0].Ships) != 0 {
		t.Fatal(intent, err)
	}
	out, err = w.CommitMissile(intent, v, func() float64 { return .5 }, clock)
	if err != nil || out.Primary.SectorMissiles != 1 || out.Primary.Target != 0 {
		t.Fatal(out, err)
	}
}

func TestOwnSectorFightersFiltersOrdersAndHandlesEmpty(t *testing.T) {
	w, p := setup(t)
	ally, _ := w.Join("finder-ally", "Teammate")
	enemy, _ := w.Join("finder-enemy", "Enemy")
	empty, _ := w.Join("finder-empty", "No Groups")
	p.Team, ally.Team = 1, 1
	w.Sectors[7].Defense = &SectorDefense{Owner: p.ID, Fighters: 789}
	w.Sectors[3].Defense = &SectorDefense{Owner: p.ID, Fighters: 123}
	w.Sectors[2].Defense = &SectorDefense{Owner: ally.ID, Fighters: 234}
	w.Sectors[4].Defense = &SectorDefense{Owner: enemy.ID, Fighters: 456}
	// NPC ownership is unsupported for deployment, but must never match a
	// personal query if such a source is present in an internal fixture.
	w.Sectors[5].Defense = &SectorDefense{Owner: -1, Fighters: 999}
	before, _ := json.Marshal(w)
	for i := 0; i < 20; i++ {
		groups, err := w.OwnSectorFighters(p.ID)
		if err != nil || len(groups) != 2 || groups[0] != (SectorFighterGroup{Sector: 3, Fighters: 123}) || groups[1] != (SectorFighterGroup{Sector: 7, Fighters: 789}) {
			t.Fatal("wrong personal groups/order", groups, err)
		}
	}
	groups, err := w.OwnSectorFighters(empty.ID)
	if err != nil || len(groups) != 0 {
		t.Fatal("empty finder", groups, err)
	}
	if _, err := w.OwnSectorFighters(999); err == nil {
		t.Fatal("missing caller accepted")
	}
	after, _ := json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("finder mutated world")
	}
}
