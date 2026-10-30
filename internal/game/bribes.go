package game

import (
	"errors"
	"math"
	"slices"
	"time"
)

// BribeIntent is a warning snapshot, not authority to reuse an old offer.
// The store adds a login-local, single-use Nonce before showing confirmation.
type BribeIntent struct {
	Season                       uint64
	Player, From, Sector, Planet int
	Generation                   uint64
	Nonce                        string
	Defense                      SectorDefense
	Credits, Fighters            int64
	Turns                        int64
	Cloak                        float64
	Offer                        int64
	Hostile                      bool
	Mines                        []MineLayer
}

type BribeOutcome struct {
	Reason       string
	Paid, Joined int64
	Combat       bool
	Defense      DefenseOutcome
}

func (w *World) PrepareBribe(id int, offer int64, hostile bool) (BribeIntent, error) {
	return w.PrepareBribeAt(id, 0, offer, hostile)
}

func (w *World) PrepareBribeAt(id, to int, offer int64, hostile bool) (BribeIntent, error) {
	p, err := w.player(id)
	if err != nil {
		return BribeIntent{}, err
	}
	if w.HasMineEncounter(id) {
		return BribeIntent{}, ErrMineEncounter
	}
	if to == 0 {
		to = p.Sector
	}
	if to != p.Sector {
		if w.HostileDefense(id, p.Sector) {
			return BribeIntent{}, ErrDefenseEncounter
		}
		if !contains(w.Sectors[p.Sector].Warps, to) {
			return BribeIntent{}, errors.New("choose the current or an adjacent defended sector")
		}
		if p.Turns < 1 {
			return BribeIntent{}, errors.New("no turns left today")
		}
	}
	s := w.Sectors[to]
	if !w.HostileDefense(id, to) {
		return BribeIntent{}, errors.New("no hostile sector fighter group here")
	}
	if offer < 0 || offer > p.Credits {
		return BribeIntent{}, errors.New("offer must be whole credits within your available balance")
	}
	if s.Defense.Owner == MercenaryOwner && s.Planet == 0 {
		if offer == 0 {
			return BribeIntent{}, errors.New("choose a positive offer; blank cancels")
		}
		if s.Defense.Fighters > MaxQuantity-p.Fighters {
			return BribeIntent{}, errors.New("recruitment would exceed ship fighter capacity")
		}
	}
	return BribeIntent{Season: w.Season, Player: id, From: p.Sector, Sector: to, Planet: s.Planet, Generation: p.ShipGeneration, Defense: *s.Defense, Credits: p.Credits, Fighters: p.Fighters, Turns: p.Turns, Cloak: p.Cloak, Offer: offer, Hostile: hostile, Mines: append([]MineLayer(nil), s.Minefield...)}, nil
}

// ResolveBribeDecision follows the recovered eager draw order. It intentionally
// uses modern [0,1) randomness and integer money rather than QuickBASIC MBF/RNG.
func ResolveBribeDecision(owner int, defenders, fighters, offer int64, planet, hostile bool, rng func() float64) (reason string, combat bool, err error) {
	if owner == 0 || owner < MercenaryOwner || owner > MaxPlayerIdentities || defenders < 1 || defenders > MaxQuantity || fighters < 0 || fighters > MaxQuantity || offer < 0 || offer > MaxMoney {
		return "", false, errors.New("invalid bribe inputs")
	}
	draw := func() (float64, error) {
		if rng == nil {
			return 0, errors.New("bribery requires randomness")
		}
		r := rng()
		if math.IsNaN(r) || math.IsInf(r, 0) || r < 0 || r >= 1 {
			return 0, errors.New("bribe RNG must return [0,1)")
		}
		return r, nil
	}
	if owner != MercenaryOwner {
		r, e := draw()
		if e != nil {
			return "", false, e
		}
		return "faction refusal", owner == XannorOwner || (defenders > fighters && r < .33), nil
	}
	if planet {
		return "planet guard refusal", false, nil
	}
	r1, e := draw()
	if e != nil {
		return "", false, e
	}
	r2, e := draw()
	if e != nil {
		return "", false, e
	}
	if hostile || r1 < .05 || (defenders > fighters && r2 > .9) {
		return "hostile refusal", true, nil
	}
	r, e := draw()
	if e != nil {
		return "", false, e
	}
	if float64(offer) < float64(defenders)*(1+2*r) {
		return "insulting offer", true, nil
	}
	return "accepted", false, nil
}

func (w *World) CommitBribe(entry BribeIntent, hostile bool, rng func() float64, now time.Time) (BribeOutcome, error) {
	if err := w.CheckSession(entry.Player, entry.Generation, entry.Season); err != nil {
		return BribeOutcome{}, err
	}
	if w.Players[entry.Player].Sector != entry.From {
		return BribeOutcome{}, errors.New("bribe warning or ship changed; confirm again")
	}
	fresh, err := w.PrepareBribeAt(entry.Player, entry.Sector, entry.Offer, hostile)
	if err != nil {
		return BribeOutcome{}, err
	}
	if fresh.From != entry.From || fresh.Sector != entry.Sector || fresh.Planet != entry.Planet || fresh.Defense != entry.Defense || fresh.Credits != entry.Credits || fresh.Fighters != entry.Fighters || fresh.Turns != entry.Turns || fresh.Cloak != entry.Cloak || fresh.Hostile != entry.Hostile || !slices.Equal(fresh.Mines, entry.Mines) {
		return BribeOutcome{}, errors.New("bribe warning or ship changed; confirm again")
	}
	if now.IsZero() || now.Before(w.Created) {
		return BribeOutcome{}, errors.New("invalid bribe time")
	}
	reason, combat, err := ResolveBribeDecision(entry.Defense.Owner, entry.Defense.Fighters, entry.Fighters, entry.Offer, entry.Planet != 0, hostile, rng)
	if err != nil {
		return BribeOutcome{}, err
	}
	out := BribeOutcome{Reason: reason, Combat: combat}
	if combat {
		var battle DefenseIntent
		if entry.Fighters == 0 {
			p := w.Players[entry.Player]
			if entry.From != entry.Sector {
				w.move(p, entry.Sector)
			}
			if err = w.escapeMines(p, rng); err != nil {
				return BribeOutcome{}, err
			}
			out.Defense = DefenseOutcome{Escaped: true, Sector: p.Sector}
			return out, nil
		}
		battle, err = w.PrepareDefenseFight(entry.Player, entry.Sector, entry.Fighters, false)
		if err != nil {
			return BribeOutcome{}, err
		}
		out.Defense, err = w.CommitDefense(battle, rng, now)
		return out, err
	}
	p := w.Players[entry.Player]
	if entry.From != entry.Sector {
		w.move(p, entry.Sector)
	}
	if reason == "accepted" {
		p.Credits -= entry.Offer
		p.Fighters += entry.Defense.Fighters
		w.Sectors[entry.Sector].Defense = nil
		out.Paid = entry.Offer
		out.Joined = entry.Defense.Fighters
	}
	out.Defense.Mines, err = w.ResolveMinefield(entry.Player, rng, now)
	out.Defense.Sector = p.Sector
	return out, err
}
