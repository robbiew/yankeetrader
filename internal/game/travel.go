package game

import (
	"errors"
	"math"
	"reflect"
	"slices"
	"sort"
	"time"
)

// DangerScannerPrice is the exact one-time Earth installation cost.
const DangerScannerPrice int64 = 250_000

// TravelShip snapshots risk-relevant ship state, including access and incarnation.
type TravelShip struct {
	Player, Sector, Team, MineGrace                                           int
	Generation                                                                uint64
	Season                                                                    uint64
	Credits, Turns, Holds, Fighters, Shields, Ground, Missiles, Mines, Plasma int64
	Cargo                                                                     [3]int64
	Cloak                                                                     float64
	Scanner                                                                   bool
	DockToken, PlanetToken                                                    string
}

func (w *World) travelShip(p *Player) TravelShip {
	return TravelShip{p.ID, p.Sector, p.Team, p.MineGraceSector, p.ShipGeneration, w.Season, p.Credits, p.Turns, p.Holds, p.Fighters, p.Shields, p.Ground, p.Missiles, p.Mines, p.Plasma, p.Cargo, p.Cloak, p.DangerScanner, p.DockToken, p.PlanetToken}
}

// ScannerEntry captures a free warning; it grants no authority to reuse a stale hop.
type ScannerEntry struct {
	Ship          TravelShip
	To, OwnerTeam int
	Defense       *SectorDefense
	Layers        []MineLayer
	Maintenance   string
}

// Dangerous reports the supported hazards that require a scanner decision.
func (e ScannerEntry) Dangerous() bool { return len(e.Layers) > 0 || e.Defense != nil }

func (w *World) PrepareScannerEntry(id, to int) (ScannerEntry, error) {
	p, err := w.player(id)
	if err != nil {
		return ScannerEntry{}, err
	}
	if !p.DangerScanner {
		return ScannerEntry{}, errors.New("danger scanner is not installed")
	}
	if err = w.canMoveBase(p, to); err != nil {
		return ScannerEntry{}, err
	}
	e := ScannerEntry{Ship: w.travelShip(p), To: to, Layers: append([]MineLayer(nil), w.Sectors[to].Minefield...), Maintenance: w.LastMaintenance}
	if w.HostileDefense(id, to) {
		d := *w.Sectors[to].Defense
		e.Defense = &d
		if owner := w.Players[d.Owner]; owner != nil {
			e.OwnerTeam = owner.Team
		}
	}
	return e, nil
}

// CommitScannerEntry enters only after revalidating the complete warning. The
// caller's store transaction also commits mine damage and any resulting death.
func (w *World) CommitScannerEntry(e ScannerEntry, rng func() float64, now time.Time) (MineOutcome, error) {
	fresh, err := w.PrepareScannerEntry(e.Ship.Player, e.To)
	if err != nil {
		return MineOutcome{}, err
	}
	if !reflect.DeepEqual(fresh, e) {
		return MineOutcome{}, errors.New("scanner warning or ship changed; confirm again")
	}
	p := w.Players[e.Ship.Player]
	w.move(p, e.To)
	return w.ResolveMinefield(p.ID, rng, now)
}

// WarpIntent is a warning snapshot. Store adds a login-local single-use nonce;
// Sequence also invalidates other logins' old zero-cost/same-sector warnings.
type WarpIntent struct {
	Ship               TravelShip
	Sequence           uint64
	Maintenance, Nonce string
}

// WarpOutcome distinguishes the random landing and recharge from later aftermath.
type WarpOutcome struct {
	Destination, FinalSector, Heat            int
	RechargeTurns, AftermathTurns, TurnsSpent int64
	Meltdown, HostileDefense                  bool
	Mines                                     MineOutcome
}

func (w *World) PrepareWarp(id int) (WarpIntent, error) {
	p, err := w.player(id)
	if err != nil {
		return WarpIntent{}, err
	}
	if w.HasMineEncounter(id) {
		return WarpIntent{}, ErrMineEncounter
	}
	if p.Turns < 1 {
		return WarpIntent{}, errors.New("no turns left for emergency warp")
	}
	if p.WarpSequence == math.MaxUint64 {
		return WarpIntent{}, errors.New("emergency warp sequence exhausted")
	}
	return WarpIntent{Ship: w.travelShip(p), Sequence: p.WarpSequence, Maintenance: w.LastMaintenance}, nil
}

// CommitWarp must run in one store Update. Work is bounded to 139 heat steps;
// original graph, avoid and current-sector filtering are intentionally absent.
func (w *World) CommitWarp(e WarpIntent, rng func() float64, now time.Time) (WarpOutcome, error) {
	fresh, err := w.PrepareWarp(e.Ship.Player)
	if err != nil {
		return WarpOutcome{}, err
	}
	fresh.Nonce = e.Nonce
	if !reflect.DeepEqual(fresh, e) {
		return WarpOutcome{}, errors.New("emergency warp warning or ship changed; confirm again")
	}
	if rng == nil || now.IsZero() || now.Before(w.Created) {
		return WarpOutcome{}, errors.New("invalid emergency warp inputs")
	}
	draw := func() (float64, error) {
		r := rng()
		if math.IsNaN(r) || math.IsInf(r, 0) || r < 0 || r >= 1 {
			return 0, errors.New("invalid emergency warp RNG")
		}
		return r, nil
	}
	r, err := draw()
	if err != nil {
		return WarpOutcome{}, err
	}
	r2, err := draw()
	if err != nil {
		return WarpOutcome{}, err
	}
	budget := min(139, int(math.Floor(70*(r+r2))))
	heat := 0
	for i := 0; i < budget; i++ {
		r, err = draw()
		if err != nil {
			return WarpOutcome{}, err
		}
		if r > .75 {
			heat++
		}
		if heat == 31 {
			break
		}
	}
	sectors := make([]int, 0, len(w.Sectors))
	for id := range w.Sectors {
		sectors = append(sectors, id)
	}
	sort.Ints(sectors)
	if len(sectors) == 0 || len(sectors) > 3000 {
		return WarpOutcome{}, errors.New("invalid emergency destinations")
	}
	r, err = draw()
	if err != nil {
		return WarpOutcome{}, err
	}
	destination := sectors[min(len(sectors)-1, int(r*float64(len(sectors))))]
	if _, err = draw(); err != nil {
		return WarpOutcome{}, err
	} // Recovered overwritten draw.
	r, err = draw()
	if err != nil {
		return WarpOutcome{}, err
	}
	p := w.Players[e.Ship.Player]
	before := p.Turns
	cost := min(before, int64(4*heat)+int64(4*r))
	if heat == 31 {
		cost = before
	}
	for i := int64(0); i < cost; i++ {
		p.spendTurn()
	}
	p.Sector = destination
	p.MineGraceSector = 0
	p.DockToken = ""
	p.PlanetToken = ""
	p.LandedPlanet = 0
	p.WarpSequence++
	out := WarpOutcome{Destination: destination, Heat: heat, RechargeTurns: cost, Meltdown: heat == 31}
	out.Mines, err = w.ResolveMinefield(p.ID, rng, now)
	if err != nil {
		return WarpOutcome{}, err
	}
	out.FinalSector = p.Sector
	out.TurnsSpent = before - p.Turns
	out.AftermathTurns = out.TurnsSpent - cost
	out.HostileDefense = p.Death == nil && w.HostileDefense(p.ID, p.Sector)
	return out, nil
}

// CheckCourse checks a remaining route without spending a hop or authorizing a
// scanner decision. FollowCourse and scanner commits share these stale guards.
func (w *World) CheckCourse(id int, course []int) error {
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
		if slices.Contains(p.AvoidSectors, sector) {
			return errors.New("autopilot stopped: course now crosses your avoid list; plot a new course")
		}
		if w.Sectors[sector] == nil || i > 0 && !slices.Contains(w.Sectors[course[i-1]].Warps, sector) {
			return errors.New("autopilot stopped: warp route changed; plot a new course")
		}
	}
	return nil
}
