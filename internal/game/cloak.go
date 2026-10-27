package game

import (
	"errors"
	"math"
)

// Visibility belongs to one live caller session, never the saved world.
// Detection grants are bound to both observer and target ship incarnations.
type Visibility struct {
	observer   int
	generation uint64
	revealed   map[int]uint64
}

func (w *World) NewVisibility(id int) (*Visibility, error) {
	p, err := w.player(id)
	if err != nil {
		return nil, err
	}
	return &Visibility{observer: id, generation: p.ShipGeneration, revealed: map[int]uint64{}}, nil
}
func (w *World) checkVisibility(id int, v *Visibility) error {
	if v == nil || v.observer != id || v.revealed == nil {
		return errors.New("visibility belongs to another session")
	}
	return w.CheckShip(id, v.generation)
}
func (v *Visibility) sees(p *Player) bool {
	generation, ok := v.revealed[p.ID]
	return p.Cloak == 0 || (ok && generation == p.ShipGeneration)
}

// Scan is a conservative stateless observation: cloaked ships remain hidden.
func (w *World) Scan(id int) ([]SensorReport, error) { return w.ScanVisible(id, nil, nil) }

// ScanVisible uses RND > cloak, strictly, and retains successful detections for
// this session. Invalid randomness changes neither the cache nor the world.
// A nil visibility performs no detection and only shows uncloaked ships.
func (w *World) ScanVisible(id int, v *Visibility, rng func() float64) ([]SensorReport, error) {
	if v != nil {
		if err := w.checkVisibility(id, v); err != nil {
			return nil, err
		}
	}
	reports, err := w.scanRaw(id)
	if err != nil {
		return nil, err
	}
	pending := map[int]uint64{}
	for i := range reports {
		ships := reports[i].Ships[:0]
		for _, ship := range reports[i].Ships {
			p := w.Players[ship.ID]
			visible := p.Cloak == 0
			if v != nil {
				visible = v.sees(p)
				if !visible && rng != nil {
					r := rng()
					if math.IsNaN(r) || math.IsInf(r, 0) || r < 0 || r >= 1 {
						return nil, errors.New("visibility RNG must return a finite value in [0,1)")
					}
					if r > p.Cloak {
						visible = true
						pending[p.ID] = p.ShipGeneration
						ship.Revealed = true
					}
				}
			}
			if visible {
				ships = append(ships, ship)
			}
		}
		reports[i].Ships = ships
	}
	if v != nil {
		for id, generation := range pending {
			v.revealed[id] = generation
		}
	}
	return reports, nil
}

func (w *World) VisibleAttackCandidates(id int, v *Visibility) ([]SensorShip, error) {
	if err := w.checkVisibility(id, v); err != nil {
		return nil, err
	}
	candidates, err := w.AttackCandidates(id)
	if err != nil {
		return nil, err
	}
	result := candidates[:0]
	for _, ship := range candidates {
		if v.sees(w.Players[ship.ID]) {
			result = append(result, ship)
		}
	}
	return result, nil
}

func (w *World) PrepareVisibleAttack(id, target int, fighters int64, v *Visibility) (AttackIntent, error) {
	if err := w.checkVisibility(id, v); err != nil {
		return AttackIntent{}, err
	}
	intent, err := w.PrepareAttack(id, target, fighters)
	if err != nil {
		return AttackIntent{}, err
	}
	if !v.sees(w.Players[target]) {
		return AttackIntent{}, errors.New("target ship is cloaked")
	}
	return intent, nil
}

func (p *Player) spendTurn() {
	p.Turns--
	if p.Turns%25 == 0 {
		p.Cloak = math.Max(0, p.Cloak-.01)
	}
}
