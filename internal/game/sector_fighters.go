package game

import (
	"errors"
	"math"
	"slices"
	"sort"
	"time"
)

var ErrDefenseEncounter = errors.New("hostile sector fighters block normal actions; fight them or flee")

type SectorBattle struct {
	Survivors, Defenders, AttackerLosses, DefenderLosses, Joined int64
	Rounds                                                       int
	SurrenderConsidered                                          bool
}
type DefenseIntent struct {
	Player, From, To         int
	Generation               uint64
	Fighters                 int64
	Defense                  SectorDefense
	Mines                    []MineLayer
	AcceptSurrender, Retreat bool
}
type DefenseOutcome struct {
	Battle  SectorBattle
	Sector  int
	Escaped bool
	Mines   MineOutcome
}

type SectorFighterGroup struct {
	Sector   int
	Fighters int64
}

// OwnSectorFighters lists only the caller's deployed fighter groups.
func (w *World) OwnSectorFighters(id int) ([]SectorFighterGroup, error) {
	if _, err := w.player(id); err != nil {
		return nil, err
	}
	groups := make([]SectorFighterGroup, 0)
	for sectorID, sector := range w.Sectors {
		if sector.Defense != nil && sector.Defense.Owner == id {
			groups = append(groups, SectorFighterGroup{Sector: sectorID, Fighters: sector.Defense.Fighters})
		}
	}
	sort.Slice(groups, func(i, j int) bool { return groups[i].Sector < groups[j].Sector })
	return groups, nil
}

func (w *World) friendlyDefense(id int, d *SectorDefense) bool {
	if d == nil || d.Owner == id {
		return true
	}
	p, owner := w.Players[id], w.Players[d.Owner]
	return p != nil && owner != nil && p.Team != 0 && p.Team == owner.Team
}
func (w *World) HostileDefense(id, sector int) bool {
	s := w.Sectors[sector]
	return s != nil && s.Defense != nil && !w.friendlyDefense(id, s.Defense)
}

// SetSectorFighters chooses a final personally owned defense balance, as F does
// in DOS. Taking a teammate's group is never permitted. Existing legacy groups
// in Union sectors can be recovered, but no new fighters may be deployed there.
func (w *World) SetSectorFighters(id int, target int64) error {
	p, err := w.player(id)
	if err != nil {
		return err
	}
	if target < 0 || target > MaxQuantity {
		return errors.New("choose a defense balance within capacity")
	}
	s := w.Sectors[p.Sector]
	old := int64(0)
	if s.Defense != nil {
		if s.Defense.Owner != id {
			return errors.New("only the owner may recover or rebalance this group")
		}
		old = s.Defense.Fighters
	}
	if target > old && p.Sector < 8 {
		return errors.New("no fighter deployment in the Union (sectors 1-7)")
	}
	delta := target - old
	if delta > p.Fighters || p.Fighters-delta > MaxQuantity {
		return errors.New("not enough fighters or ship capacity exceeded")
	}
	p.Fighters -= delta
	if target == 0 {
		s.Defense = nil
	} else {
		s.Defense = &SectorDefense{Owner: id, Fighters: target}
	}
	return nil
}
func (w *World) ReinforceSector(id int, count int64) error {
	p, err := w.player(id)
	if err != nil {
		return err
	}
	s := w.Sectors[p.Sector]
	if p.Sector < 8 {
		return errors.New("no fighter deployment in the Union (sectors 1-7)")
	}
	if s.Defense == nil || !w.friendlyDefense(id, s.Defense) {
		return errors.New("reinforce only an existing personal or teammate group")
	}
	if count < 1 || count > p.Fighters || count > MaxQuantity-s.Defense.Fighters {
		return errors.New("choose available fighters within defense capacity")
	}
	p.Fighters -= count
	s.Defense.Fighters += count
	return nil
}

func ResolveSectorBattle(committed, defenders int64, cloak float64, owner int, accept bool, rng func() float64) (SectorBattle, error) {
	if committed < 1 || committed > MaxQuantity || defenders < 1 || defenders > MaxQuantity || owner == 0 || owner < MercenaryOwner || owner > 50 || math.IsNaN(cloak) || math.IsInf(cloak, 0) || cloak < 0 || cloak > 1 || rng == nil {
		return SectorBattle{}, errors.New("invalid sector battle inputs")
	}
	out := SectorBattle{Survivors: committed, Defenders: defenders}
	for out.Survivors > 0 && out.Defenders > 0 {
		if !out.SurrenderConsidered && out.Survivors > 10*out.Defenders {
			out.SurrenderConsidered = true
			if owner > 0 && accept {
				out.Joined = out.Defenders
				out.Defenders = 0
				break
			}
		}
		if out.Rounds >= maxDuelRounds {
			return SectorBattle{}, errors.New("sector battle calculation limit reached")
		}
		r := rng()
		if math.IsNaN(r) || math.IsInf(r, 0) || r < 0 || r >= 1 {
			return SectorBattle{}, errors.New("combat RNG must return [0,1)")
		}
		batch := max(int64(1), min(out.Survivors, out.Defenders)/20)
		if r+cloak/10 < .45 {
			out.Survivors -= batch
			out.AttackerLosses += batch
		} else {
			out.Defenders -= batch
			out.DefenderLosses += batch
		}
		out.Rounds++
	}
	return out, nil
}

func (w *World) PrepareDefenseFight(id, to int, count int64, accept bool) (DefenseIntent, error) {
	p, err := w.player(id)
	if err != nil {
		return DefenseIntent{}, err
	}
	if len(w.Sectors[p.Sector].Minefield) > 0 {
		return DefenseIntent{}, ErrMineEncounter
	}
	if to != p.Sector {
		if w.HostileDefense(id, p.Sector) {
			return DefenseIntent{}, ErrDefenseEncounter
		}
		if !contains(w.Sectors[p.Sector].Warps, to) {
			return DefenseIntent{}, errors.New("choose the current or an adjacent defended sector")
		}
		if p.Turns < 1 {
			return DefenseIntent{}, errors.New("no turns left today")
		}
	}
	if !w.HostileDefense(id, to) {
		return DefenseIntent{}, errors.New("no hostile sector fighter group there")
	}
	if count < 1 || count > p.Fighters {
		return DefenseIntent{}, errors.New("choose available fighters to commit")
	}
	return DefenseIntent{Player: id, From: p.Sector, To: to, Generation: p.ShipGeneration, Fighters: count, Defense: *w.Sectors[to].Defense, Mines: append([]MineLayer(nil), w.Sectors[to].Minefield...), AcceptSurrender: accept}, nil
}
func (w *World) PrepareDefenseRetreat(id int) (DefenseIntent, error) {
	p, err := w.player(id)
	if err != nil {
		return DefenseIntent{}, err
	}
	if !w.HostileDefense(id, p.Sector) {
		return DefenseIntent{}, errors.New("no hostile defense requires escape here")
	}
	if len(w.Sectors[p.Sector].Minefield) > 0 {
		return DefenseIntent{}, ErrMineEncounter
	}
	return DefenseIntent{Player: id, From: p.Sector, To: p.Sector, Generation: p.ShipGeneration, Defense: *w.Sectors[p.Sector].Defense, Retreat: true}, nil
}
func (w *World) CommitDefense(entry DefenseIntent, rng func() float64, now time.Time) (DefenseOutcome, error) {
	if err := w.CheckShip(entry.Player, entry.Generation); err != nil {
		return DefenseOutcome{}, err
	}
	p := w.Players[entry.Player]
	var fresh DefenseIntent
	var err error
	if entry.Retreat {
		fresh, err = w.PrepareDefenseRetreat(entry.Player)
	} else {
		fresh, err = w.PrepareDefenseFight(entry.Player, entry.To, entry.Fighters, entry.AcceptSurrender)
	}
	if err != nil {
		return DefenseOutcome{}, err
	}
	if fresh.From != entry.From || fresh.To != entry.To || fresh.Defense != entry.Defense || !slices.Equal(fresh.Mines, entry.Mines) {
		return DefenseOutcome{}, errors.New("defense warning or ship changed; confirm again")
	}
	if rng == nil || now.IsZero() || now.Before(w.Created) {
		return DefenseOutcome{}, errors.New("invalid defense encounter inputs")
	}
	out := DefenseOutcome{Sector: p.Sector}
	if entry.Retreat {
		if err = w.escapeMines(p, rng); err != nil {
			return DefenseOutcome{}, err
		}
		out.Escaped = true
		out.Sector = p.Sector
		return out, nil
	}
	// Entering spends a turn before combat, including its cloak decay. Calculate
	// using a copy so invalid RNG or a capacity refusal leaves this model intact.
	combatShip := *p
	if entry.To != entry.From {
		combatShip.spendTurn()
	}
	out.Battle, err = ResolveSectorBattle(entry.Fighters, entry.Defense.Fighters, combatShip.Cloak, entry.Defense.Owner, entry.AcceptSurrender, rng)
	if err != nil {
		return DefenseOutcome{}, err
	}
	if out.Battle.Joined > MaxQuantity-(p.Fighters-out.Battle.AttackerLosses) {
		return DefenseOutcome{}, errors.New("surrender exceeds ship fighter capacity")
	}
	if entry.To != entry.From {
		w.move(p, entry.To)
	}
	p.Fighters = p.Fighters - out.Battle.AttackerLosses + out.Battle.Joined
	s := w.Sectors[entry.To]
	if out.Battle.Defenders == 0 {
		s.Defense = nil
	} else {
		s.Defense.Fighters = out.Battle.Defenders
	}
	if out.Battle.Survivors == 0 {
		if err = w.escapeMines(p, rng); err != nil {
			return DefenseOutcome{}, err
		}
		out.Escaped = true
		out.Sector = p.Sector
		return out, nil
	}
	out.Mines, err = w.ResolveMinefield(p.ID, rng, now)
	if err != nil {
		return DefenseOutcome{}, err
	}
	out.Sector = p.Sector
	return out, nil
}
