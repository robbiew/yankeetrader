package game

import (
	"errors"
	"sort"
)

// SensorReport contains only public, local observations, never account or session data.
type SensorReport struct {
	Sector     int
	Warps      []int
	PortID     int
	PortName   string
	Selling    []string
	PlanetName string
	Ground     int64
	Ships      []SensorShip
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
	if w.Sectors[from] == nil || w.Sectors[to] == nil {
		return nil, errors.New("choose existing start and destination sectors")
	}
	if from == to {
		return nil, errors.New("start and destination are the same sector")
	}
	previous := map[int]int{from: 0}
	queue := []int{from}
	for head := 0; head < len(queue); head++ {
		for _, next := range w.Sectors[queue[head]].Warps {
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
	path, err := w.Path(p.Sector, to)
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
func (w *World) FollowCourse(id, from, to int, remaining int) error {
	p, err := w.player(id)
	if err != nil {
		return err
	}
	if p.Sector != from {
		return errors.New("autopilot stopped: ship position changed; plot a new course")
	}
	if remaining < 1 || int64(remaining) > p.Turns {
		return errors.New("autopilot stopped: not enough turns left")
	}
	return w.Move(id, to)
}
