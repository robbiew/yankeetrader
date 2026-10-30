package game

import (
	"errors"
	"math"
	"reflect"
	"sort"
	"time"
)

const CloakPointPrice int64 = 1000
const AntiCloakPrice int64 = 500000

var ErrCloakCapacity = errors.New("cloak energy cannot exceed 100 percent")

// cloakCapacity buys only whole points. Normalize sub-nanopoint floating drift
// from existing fractional turn consumption; nonintegral capacity is floored.
func cloakCapacity(p *Player) int64 {
	missing := 100 - p.Cloak*100
	if rounded := math.Round(missing); math.Abs(missing-rounded) < 1e-9 {
		missing = rounded
	}
	return max(0, min(100, int64(math.Floor(missing))))
}
func (w *World) CloakPurchaseLimit(id int, token string, now time.Time) (int64, error) {
	if now.IsZero() || now.Before(w.Created) {
		return 0, errors.New("invalid cloak purchase clock")
	}
	p, port, err := w.docked(id, token, now)
	if err != nil {
		return 0, err
	}
	if port.ID != 1 {
		return 0, errors.New("cloak energy is sold at Earth")
	}
	return min(cloakCapacity(p), p.Credits/CloakPointPrice), nil
}

type CloakReceipt struct {
	Points, Spent, Balance int64
	Before, After          float64
}

type AntiCloakIntent struct {
	Ship               TravelShip
	DockUntil          time.Time
	Maintenance, Nonce string
	Activation         uint64
}
type AntiCloakTarget struct {
	ID    int
	Alias string
}
type AntiCloakReceipt struct {
	Spent, Balance int64
	Revealed       []AntiCloakTarget
}

func (w *World) PrepareAntiCloak(id int, token string, v *Visibility, now time.Time) (AntiCloakIntent, error) {
	if now.IsZero() || now.Before(w.Created) {
		return AntiCloakIntent{}, errors.New("invalid anti-cloak clock")
	}
	p, port, err := w.docked(id, token, now)
	if err != nil {
		return AntiCloakIntent{}, err
	}
	if port.ID != 1 {
		return AntiCloakIntent{}, errors.New("anti-cloak activation is sold at Earth")
	}
	if err = w.checkVisibility(id, v); err != nil {
		return AntiCloakIntent{}, err
	}
	if p.Credits < AntiCloakPrice {
		return AntiCloakIntent{}, errors.New("not enough credits for anti-cloak activation")
	}
	count := v.AntiCloakActivations()
	if count == math.MaxUint64 {
		return AntiCloakIntent{}, errors.New("anti-cloak activation counter exhausted")
	}
	return AntiCloakIntent{Ship: w.travelShip(p), DockUntil: p.DockUntil, Maintenance: w.LastMaintenance, Activation: count}, nil
}

// CommitAntiCloak runs against a staged login cache in the same transaction as
// the debit. It reveals existing living incarnations, never future replacements.
func (w *World) CommitAntiCloak(e AntiCloakIntent, v *Visibility, now time.Time) (AntiCloakReceipt, error) {
	fresh, err := w.PrepareAntiCloak(e.Ship.Player, e.Ship.DockToken, v, now)
	if err != nil {
		return AntiCloakReceipt{}, err
	}
	fresh.Nonce = e.Nonce
	if !reflect.DeepEqual(fresh, e) {
		return AntiCloakReceipt{}, errors.New("anti-cloak quote or ship changed; confirm again")
	}
	v.mu.Lock()
	defer v.mu.Unlock()
	if v.antiActivations != e.Activation {
		return AntiCloakReceipt{}, errors.New("anti-cloak confirmation already used")
	}
	if len(w.Players) > 50 {
		return AntiCloakReceipt{}, errors.New("too many anti-cloak targets")
	}
	ids := make([]int, 0, len(w.Players))
	for id := range w.Players {
		ids = append(ids, id)
	}
	sort.Ints(ids)
	out := AntiCloakReceipt{Spent: AntiCloakPrice}
	for _, id := range ids {
		p := w.Players[id]
		if p.ID == e.Ship.Player || p.Death != nil || !p.RetiredAt.IsZero() || p.Cloak <= 0 {
			continue
		}
		if !v.seesLocked(p) {
			out.Revealed = append(out.Revealed, AntiCloakTarget{p.ID, p.Alias})
		}
		v.revealed[p.ID] = p.ShipGeneration
	}
	p := w.Players[e.Ship.Player]
	p.Credits -= AntiCloakPrice
	out.Balance = p.Credits
	v.antiActivations++
	return out, nil
}

// StageAntiCloak holds the live cache until finish. Store calls this only after
// acquiring the world lock (the same lock order used by attack visibility reads).
// The private clone can change freely; ordinary rollback publishes nothing.
func (v *Visibility) StageAntiCloak() (*Visibility, func(bool)) {
	v.mu.Lock()
	staged := &Visibility{observer: v.observer, generation: v.generation, season: v.season, revealed: make(map[int]uint64, len(v.revealed)), antiActivations: v.antiActivations}
	for id, generation := range v.revealed {
		staged.revealed[id] = generation
	}
	return staged, func(commit bool) {
		if commit {
			v.revealed = staged.revealed
			v.antiActivations = staged.antiActivations
		}
		v.mu.Unlock()
	}
}
func (v *Visibility) AntiCloakActivations() uint64 {
	if v == nil {
		return 0
	}
	v.mu.Lock()
	defer v.mu.Unlock()
	return v.antiActivations
}
