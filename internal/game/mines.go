package game

import (
	"errors"
	"math"
	"slices"
	"sort"
	"time"
)

var ErrMineEncounter = errors.New("resolve the current minefield before acting")

// MineLayer preserves account attribution, even after its owner dies. Layers
// resolve FIFO; quantities from the same account merge without changing order.
type MineLayer struct {
	Owner int
	Count int64
}
type MineOutcome struct {
	ScannerLost        bool
	Bursts             int
	Spent, Dropped     int64
	Destroyed, Escaped bool
	Killer, Sector     int
}
type MineEntry struct {
	Player, From, To int
	Generation       uint64
	Layers           []MineLayer
}
type MinePlacement struct {
	Player, Sector int
	Generation     uint64
	Stock, Count   int64
	Layers         []MineLayer
}

// HasMineEncounter distinguishes entry/wreck hazards from a voluntary field
// deployed around a ship that has not left its current sector yet.
func (w *World) HasMineEncounter(id int) bool {
	p := w.Players[id]
	if p == nil || p.Death != nil {
		return false
	}
	s := w.Sectors[p.Sector]
	return s != nil && len(s.Minefield) > 0 && p.MineGraceSector != p.Sector
}

func (w *World) validateMines() error {
	for _, p := range w.Players {
		if p.MineGraceSector != 0 && (p.Death != nil || p.MineGraceSector <= 7 || p.MineGraceSector != p.Sector) {
			return errors.New("invalid mine departure grace")
		}
	}
	for _, s := range w.Sectors {
		total := int64(0)
		owners := map[int]bool{}
		if s.ID == 1 && len(s.Minefield) > 0 {
			return errors.New("Earth cannot contain mines")
		}
		if len(s.Minefield) > 51 {
			return errors.New("too many mine sources")
		}
		for _, layer := range s.Minefield {
			if layer.Owner < 0 || (layer.Owner > 0 && (w.Players[layer.Owner] == nil || !w.Players[layer.Owner].RetiredAt.IsZero())) || layer.Count < 1 || layer.Count > MaxQuantity || owners[layer.Owner] {
				return errors.New("invalid minefield")
			}
			total += layer.Count
			owners[layer.Owner] = true
		}
		if total > MaxQuantity {
			return errors.New("minefield capacity exceeded")
		}
	}
	return nil
}

func (w *World) dropMines(sector, owner int, count int64) error {
	if count == 0 || sector == 1 {
		return nil
	}
	s := w.Sectors[sector]
	total := count
	for _, layer := range s.Minefield {
		total += layer.Count
	}
	if count < 0 || total > MaxQuantity {
		return errors.New("minefield capacity exceeded")
	}
	// Wreck mines retain their immediate aftermath behavior, even in a field
	// where voluntary deployment previously granted departure grace.
	for _, p := range w.Players {
		if p.MineGraceSector == sector {
			p.MineGraceSector = 0
		}
	}
	for i := range s.Minefield {
		if s.Minefield[i].Owner == owner {
			s.Minefield[i].Count += count
			return nil
		}
	}
	s.Minefield = append(s.Minefield, MineLayer{Owner: owner, Count: count})
	return nil
}

func (w *World) PrepareMinePlacement(id int, count int64) (MinePlacement, error) {
	p, err := w.player(id)
	if err != nil {
		return MinePlacement{}, err
	}
	if w.HasMineEncounter(id) {
		return MinePlacement{}, ErrMineEncounter
	}
	if p.Sector <= 7 {
		return MinePlacement{}, errors.New("the home seven sectors are protected from mine placement")
	}
	if count < 1 || count > p.Mines || count > MaxQuantity {
		return MinePlacement{}, errors.New("choose a positive mine quantity no greater than your stock")
	}
	s := w.Sectors[p.Sector]
	if s == nil {
		return MinePlacement{}, errors.New("current sector does not exist")
	}
	return MinePlacement{Player: id, Sector: p.Sector, Generation: p.ShipGeneration,
		Stock: p.Mines, Count: count, Layers: append([]MineLayer(nil), s.Minefield...)}, nil
}

func (w *World) CommitMinePlacement(placement MinePlacement) (int64, error) {
	p, err := w.player(placement.Player)
	if err != nil {
		return 0, err
	}
	s := w.Sectors[placement.Sector]
	if s == nil || p.Sector != placement.Sector || p.ShipGeneration != placement.Generation ||
		p.Mines != placement.Stock || !slices.Equal(placement.Layers, s.Minefield) {
		return 0, errors.New("mine placement warning or ship changed; confirm again")
	}
	if placement.Sector <= 7 || placement.Count < 1 || placement.Count > p.Mines || placement.Count > MaxQuantity {
		return 0, errors.New("mine placement is no longer valid")
	}
	if w.HasMineEncounter(p.ID) {
		return 0, ErrMineEncounter
	}
	var occupants []*Player
	for _, occupant := range w.Players {
		if occupant.Death == nil && occupant.Sector == p.Sector && !w.HasMineEncounter(occupant.ID) {
			occupants = append(occupants, occupant)
		}
	}
	if err = w.dropMines(placement.Sector, p.ID, placement.Count); err != nil {
		return 0, err
	}
	for _, occupant := range occupants {
		occupant.MineGraceSector = placement.Sector
	}
	p.Mines -= placement.Count
	var total int64
	for _, layer := range s.Minefield {
		total += layer.Count
	}
	return total, nil
}

// nestedMineDraw is the recovered helper's three successively smaller integer
// draws, each floor(RND * previous)+1, not a sum of three independent rolls.
func nestedMineDraw(limit int64, rng func() float64) (int64, error) {
	for i := 0; i < 3; i++ {
		n, err := scaledSalvageDraw(limit, rng)
		if err != nil {
			return 0, err
		}
		limit = n + 1
	}
	return limit, nil
}

func mineBurst(p *Player, burst int64, rng func() float64) error {
	if p.Shields > 0 {
		damage, err := scaledSalvageDraw(1001, rng)
		if err != nil {
			return err
		}
		p.Shields = max(0, p.Shields-damage*burst)
		if p.DangerScanner && p.Shields > 0 {
			r, err := scaledSalvageDraw(1<<53, rng)
			if err != nil {
				return err
			}
			if float64(r)/(1<<53) > .95 {
				p.DangerScanner = false
			}
		}
		return nil
	}
	p.DangerScanner = false
	if p.Fighters > 0 {
		loss, err := nestedMineDraw(40000*burst, rng)
		if err != nil {
			return err
		}
		p.Fighters -= min(p.Fighters, loss)
	}
	if p.Cloak > 0 {
		loss, err := scaledSalvageDraw(burst*100, rng)
		if err != nil {
			return err
		}
		p.Cloak = math.Max(0, p.Cloak-float64(loss)/100)
	}
	for _, stock := range []*int64{&p.Missiles, &p.Mines, &p.Cargo[0], &p.Cargo[1], &p.Cargo[2]} {
		if *stock == 0 {
			continue
		}
		loss, err := nestedMineDraw(*stock*burst, rng)
		if err != nil {
			return err
		}
		*stock -= min(*stock, loss)
	}
	empty := p.Holds - p.Cargo[0] - p.Cargo[1] - p.Cargo[2]
	if empty > 0 {
		loss, err := nestedMineDraw(empty, rng)
		if err != nil {
			return err
		}
		p.Holds -= min(empty, loss*burst)
	}
	return nil
}

// ResolveMinefield must run inside one store Update. Every error must abort
// that callback so damage, depleted fields, escape and death all roll back.
func (w *World) ResolveMinefield(id int, rng func() float64, now time.Time) (MineOutcome, error) {
	p, err := w.player(id)
	if err != nil {
		return MineOutcome{}, err
	}
	out := MineOutcome{Sector: p.Sector}
	s := w.Sectors[p.Sector]
	if !w.HasMineEncounter(id) {
		return out, nil
	}
	if rng == nil || now.IsZero() || now.Before(w.Created) {
		return MineOutcome{}, errors.New("invalid mine encounter inputs")
	}
	for len(s.Minefield) > 0 {
		if out.Bursts >= 16000 {
			return MineOutcome{}, errors.New("mine encounter calculation limit reached")
		}
		layer := s.Minefield[0]
		burst := int64(1)
		if layer.Count > 19 {
			burst = layer.Count / 10
		}
		s.Minefield[0].Count -= burst
		if s.Minefield[0].Count == 0 {
			s.Minefield = s.Minefield[1:]
			if len(s.Minefield) == 0 {
				s.Minefield = nil
			}
		}
		out.Bursts++
		out.Spent += burst
		hadScanner := p.DangerScanner
		if err = mineBurst(p, burst, rng); err != nil {
			return MineOutcome{}, err
		}
		out.ScannerLost = out.ScannerLost || hadScanner && !p.DangerScanner
		if p.Holds == 0 {
			source := p.Sector
			out.Destroyed = true
			out.Killer = layer.Owner
			out.Dropped = p.Mines
			if err = w.dropMines(source, p.ID, p.Mines); err != nil {
				return MineOutcome{}, err
			}
			p.Mines = 0
			// No remote inventory award is created for a hazard kill. Record the actual
			// mine source, including a dead source, independently from estate eligibility.
			if err = w.RecordDeath(DeathContext{Victim: p.ID, Generation: p.ShipGeneration, Sector: source, Killer: layer.Owner, Cause: "mines"}, now); err != nil {
				return MineOutcome{}, err
			}
			return out, nil
		}
		escape, err := scaledSalvageDraw(1<<53, rng)
		if err != nil {
			return MineOutcome{}, err
		}
		if p.Holds < 10 && float64(escape)/(1<<53) > .8 {
			if err = w.escapeMines(p, rng); err != nil {
				return MineOutcome{}, err
			}
			out.Escaped = true
			out.Sector = p.Sector
			return out, nil
		}
	}
	return out, nil
}

// Unlike the DOS repeated-hazard loop, emergency warp selects only safe sectors.
// Earth is always eligible, so a valid non-Earth world has a safe escape.
func (w *World) escapeMines(p *Player, rng func() float64) error {
	draw := func() (float64, error) {
		r := rng()
		if math.IsNaN(r) || math.IsInf(r, 0) || r < 0 || r >= 1 {
			return 0, errors.New("invalid escape RNG")
		}
		return r, nil
	}
	r, err := draw()
	if err != nil {
		return err
	}
	r2, err := draw()
	if err != nil {
		return err
	}
	heat := 0
	for i := 0; i < int(math.Floor(70*(r+r2))); i++ {
		r, err = draw()
		if err != nil {
			return err
		}
		if r > .75 {
			heat++
		}
		if heat >= 31 {
			break
		}
	}
	var safe []int
	for id, s := range w.Sectors {
		if id == p.Sector || len(s.Minefield) > 0 {
			continue
		}
		if d := s.Defense; d != nil && d.Owner != p.ID {
			owner := w.Players[d.Owner]
			if owner == nil || p.Team == 0 || owner.Team != p.Team {
				continue
			}
		}
		safe = append(safe, id)
	}
	sort.Ints(safe)
	if len(safe) == 0 {
		return errors.New("no safe emergency destination")
	}
	r, err = draw()
	if err != nil {
		return err
	}
	destination := safe[int(r*float64(len(safe)))]
	if _, err = draw(); err != nil {
		return err
	} // Preserve the recovered overwritten draw.
	r, err = draw()
	if err != nil {
		return err
	}
	cost := min(p.Turns, int64(4*heat)+int64(4*r))
	if heat >= 31 {
		cost = p.Turns
	}
	for i := int64(0); i < cost; i++ {
		p.spendTurn()
	}
	p.MineGraceSector = 0
	p.Sector = destination
	p.DockToken = ""
	p.PlanetToken = ""
	p.LandedPlanet = 0
	return nil
}

func (w *World) PrepareMineEntry(id, to int) (MineEntry, error) {
	p, err := w.player(id)
	if err != nil {
		return MineEntry{}, err
	}
	if err = w.canMove(p, to); err != nil {
		return MineEntry{}, err
	}
	return MineEntry{Player: id, From: p.Sector, To: to, Generation: p.ShipGeneration, Layers: append([]MineLayer(nil), w.Sectors[to].Minefield...)}, nil
}
func (w *World) CommitMineEntry(entry MineEntry, rng func() float64, now time.Time) (MineOutcome, error) {
	p, err := w.player(entry.Player)
	if err != nil {
		return MineOutcome{}, err
	}
	if p.Sector != entry.From || p.ShipGeneration != entry.Generation || w.Sectors[entry.To] == nil || !slices.Equal(entry.Layers, w.Sectors[entry.To].Minefield) {
		return MineOutcome{}, errors.New("mine warning or ship changed; confirm again")
	}
	if err = w.canMove(p, entry.To); err != nil {
		return MineOutcome{}, err
	}
	w.move(p, entry.To)
	return w.ResolveMinefield(p.ID, rng, now)
}
