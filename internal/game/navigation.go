package game

import (
	"errors"
	"sort"
)

// SensorReport contains only public, local observations, never account or session data.
type SensorReport struct {
	Sector          int
	Warps           []int
	PortID          int
	PortName        string
	Selling         []string
	PlanetName      string
	Ground          int64
	DefenseFighters int64
	DefenseOwner    string
	Ships           []SensorShip
}

type SensorShip struct {
	ID, Team          int
	Alias             string
	Fighters, Shields int64
}

// Scan observes outgoing adjacent sectors in warp order without spending a turn.
func (w *World) Scan(id int) ([]SensorReport, error) {
	p, err := w.player(id)
	if err != nil {
		return nil, err
	}
	var reports []SensorReport
	for _, target := range w.Sectors[p.Sector].Warps {
		s := w.Sectors[target]
		r := SensorReport{Sector: target, Warps: append([]int(nil), s.Warps...)}
		if port := w.Ports[s.Port]; port != nil {
			r.PortID, r.PortName = port.ID, port.Name
			for i, coefficient := range port.Coefficient {
				if coefficient > 0 {
					r.Selling = append(r.Selling, Goods[i])
				}
			}
		}
		if planet := w.Planets[s.Planet]; planet != nil {
			r.PlanetName, r.Ground = planet.Name, planet.Ground
		}
		if d := s.Defense; d != nil {
			r.DefenseFighters = d.Fighters
			switch d.Owner {
			case MercenaryOwner:
				r.DefenseOwner = "Mercenaries"
			case XannorOwner:
				r.DefenseOwner = "Xannor"
			default:
				if owner := w.Players[d.Owner]; owner != nil {
					r.DefenseOwner = owner.Alias
				}
			}
		}
		for _, other := range w.Players {
			if other.ID != id && other.Sector == target {
				r.Ships = append(r.Ships, SensorShip{ID: other.ID, Team: other.Team, Alias: other.Alias, Fighters: other.Fighters, Shields: other.Shields})
			}
		}
		sort.Slice(r.Ships, func(i, j int) bool { return r.Ships[i].ID < r.Ships[j].ID })
		reports = append(reports, r)
	}
	return reports, nil
}

// Path finds a shortest directed route, including both endpoints. Equal-length
// routes follow stored warp order. It does not change the world or spend turns.
func (w *World) Path(from, to int) ([]int, error) {
	return w.path(from, to, nil)
}

// PlayerPath applies this player's routing preferences to both endpoints and all intermediate sectors.
func (w *World) PlayerPath(id, from, to int) ([]int, error) {
	p, err := w.player(id)
	if err != nil {
		return nil, err
	}
	return w.path(from, to, p.AvoidSectors)
}

func (w *World) path(from, to int, avoid []int) ([]int, error) {
	if w.Sectors[from] == nil || w.Sectors[to] == nil {
		return nil, errors.New("choose existing start and destination sectors")
	}
	if from == to {
		return nil, errors.New("start and destination are the same sector")
	}
	if contains(avoid, from) || contains(avoid, to) {
		return nil, errors.New("start or destination is in your avoid list")
	}
	previous := map[int]int{from: 0}
	queue := []int{from}
	for head := 0; head < len(queue); head++ {
		for _, next := range w.Sectors[queue[head]].Warps {
			if contains(avoid, next) {
				continue
			}
			if _, seen := previous[next]; seen {
				continue
			}
			previous[next] = queue[head]
			if next == to {
				path := []int{to}
				for current := to; current != from; {
					current = previous[current]
					path = append(path, current)
				}
				for i, j := 0, len(path)-1; i < j; i, j = i+1, j-1 {
					path[i], path[j] = path[j], path[i]
				}
				return path, nil
			}
			queue = append(queue, next)
		}
	}
	return nil, errors.New("no warp route reaches that destination")
}

// Course checks the complete turn budget before autopilot starts.
func (w *World) Course(id, to int) ([]int, error) {
	p, err := w.player(id)
	if err != nil {
		return nil, err
	}
	path, err := w.PlayerPath(id, p.Sector, to)
	if err != nil {
		return nil, err
	}
	if int64(len(path)-1) > p.Turns {
		return nil, errors.New("not enough turns left to autopilot this course")
	}
	return path, nil
}

// FollowCourse revalidates each hop against authoritative state. A stale course
// must stop, rather than resume from another session's new position.
func (w *World) FollowCourse(id int, course []int) error {
	p, err := w.player(id)
	if err != nil {
		return err
	}
	if len(course) < 2 {
		return errors.New("autopilot stopped: no next hop")
	}
	if p.Sector != course[0] {
		return errors.New("autopilot stopped: ship position changed; plot a new course")
	}
	if int64(len(course)-1) > p.Turns {
		return errors.New("autopilot stopped: not enough turns left")
	}
	for i, sector := range course {
		if contains(p.AvoidSectors, sector) {
			return errors.New("autopilot stopped: course now crosses your avoid list; plot a new course")
		}
		if w.Sectors[sector] == nil || (i > 0 && !contains(w.Sectors[course[i-1]].Warps, sector)) {
			return errors.New("autopilot stopped: warp route changed; plot a new course")
		}
	}
	return w.Move(id, course[1])
}

// SetAvoid updates one of 30 private route-planning slots. Zero clears the slot.
// Manual movement deliberately ignores these preferences, as in the DOS game.
func (w *World) SetAvoid(id, slot, sector int) error {
	p, err := w.player(id)
	if err != nil {
		return err
	}
	if slot < 1 || slot > 30 {
		return errors.New("choose an avoid slot from 1 to 30")
	}
	if sector != 0 && w.Sectors[sector] == nil {
		return errors.New("choose an existing sector, or 0 to clear the slot")
	}
	slots := make([]int, 30)
	copy(slots, p.AvoidSectors)
	slots[slot-1] = sector
	p.AvoidSectors = slots
	return nil
}
