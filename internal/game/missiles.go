package game

import (
	"errors"
	"math"
	"reflect"
	"sort"
	"time"
)

const maxMissileRounds = 1_000_000

type MissileDamage struct{ Spent, Fighters, Shields int64 }
type MissileIntent struct {
	Season           uint64
	Player, From, To int
	Generation       uint64
	Sequence         uint64
	Count            int64
	Route            []int
	Sectors          []MissileRouteSector
}
type MissileRouteSector struct {
	Sector  int
	Mines   []MineLayer
	Defense *SectorDefense
	Ships   []MissileShipTarget
	Planet  *Planet
}
type MissileShipTarget struct {
	Player, Team      int
	Generation        uint64
	Sequence          uint64
	Alias             string
	Fighters, Shields int64
	Cloak             float64
	ReturnRoute       []int
	ReturnSectors     []MissileRouteSector
}
type MissileImpact struct {
	HQRewards                                   []XannorHQReward
	SectorMissiles                              int64
	PlanetID                                    int
	GroundBefore, GroundAfter, PlanetMissiles   int64
	GroundMissiles, ProductionMissiles          int64
	ProductionBefore, ProductionAfter           [3]float64
	CargoBefore, CargoAfter                     [3]float64
	PlanetDestroyed                             bool
	Target                                      int
	Retaliator                                  int
	Launched, MinesDestroyed, Dropped, Disarmed int64
	SectorFightersDestroyed                     int64
	LostEscorts                                 int64
	Damage                                      MissileDamage
	Destroyed                                   bool
	Salvage                                     Salvage
	Interceptions                               []MissileInterception
	ShipImpacts                                 []MissileShipImpact
	PlanetImpacts                               []MissilePlanetImpact
}
type MissileInterception struct {
	Sector                                      int
	Missiles, FightersDestroyed, MinesDestroyed int64
}
type MissileShipImpact struct {
	Sector, Player int
	Alias          string
	Damage         MissileDamage
	Destroyed      bool
	LostEscorts    int64
	Salvage        Salvage
}
type MissilePlanetImpact struct {
	Sector, PlanetID                    int
	GroundBefore, GroundAfter, Missiles int64
	GroundMissiles, ProductionMissiles  int64
	ProductionBefore, ProductionAfter   [3]float64
	CargoBefore, CargoAfter             [3]float64
	Destroyed                           bool
}
type MissileResult struct{ Primary, Counter MissileImpact }

// ResolveMissileShip calculates one ship encounter without changing the world.
// Each missile consumes the recovered scanner-check draw. No scanner is installed
// in this build; that check does not drop mines or grant a new visibility power.
func ResolveMissileShip(missiles, fighters, shields int64, rng func() float64) (MissileDamage, error) {
	budget := maxMissileRounds
	return resolveMissileShip(missiles, fighters, shields, rng, &budget)
}
func resolveMissileShip(missiles, fighters, shields int64, rng func() float64, budget *int) (MissileDamage, error) {
	if missiles < 1 || missiles > MaxQuantity || fighters < 0 || fighters > MaxQuantity || shields < 0 || shields > MaxQuantity || rng == nil {
		return MissileDamage{}, errors.New("invalid missile damage inputs")
	}
	var out MissileDamage
	for out.Spent < missiles {
		if *budget <= 0 {
			return MissileDamage{}, errors.New("missile calculation limit reached")
		}
		*budget -= 1
		if _, err := scaledSalvageDraw(1, rng); err != nil {
			return MissileDamage{}, err
		}
		killed, err := scaledSalvageDraw(4001, rng)
		if err != nil {
			return MissileDamage{}, err
		}
		out.Fighters += killed
		check, err := scaledSalvageDraw(fighters, rng)
		if err != nil {
			return MissileDamage{}, err
		}
		if check < out.Fighters {
			hit, err := scaledSalvageDraw(1001, rng)
			if err != nil {
				return MissileDamage{}, err
			}
			out.Shields += hit
		}
		out.Spent++
		if out.Fighters >= fighters && out.Shields >= shields {
			break
		}
	}
	out.Fighters = min(out.Fighters, fighters)
	out.Shields = min(out.Shields, shields)
	return out, nil
}

// RetaliationVolley uses the stored account score, not a freshly invented score.
// When score sizing is absent or exceeds stock, choose a random 1..stock volley.
func RetaliationVolley(score, stock int64, rng func() float64) (int64, error) {
	if stock < 0 || stock > MaxQuantity || score < -MaxMoney || score > MaxMoney {
		return 0, errors.New("invalid retaliation inputs")
	}
	if stock == 0 {
		return 0, nil
	}
	n := int64(0)
	if score > 0 {
		n = score/100000 + 1
	}
	if n == 0 || n > stock {
		if rng == nil {
			return 0, errors.New("retaliation requires randomness")
		}
		draw, err := scaledSalvageDraw(stock, rng)
		if err != nil {
			return 0, err
		}
		n = draw + 1
	}
	return n, nil
}

func (w *World) PrepareMissile(id, to int, count int64, v *Visibility) (MissileIntent, error) {
	if err := w.checkVisibility(id, v); err != nil {
		return MissileIntent{}, err
	}
	a, err := w.player(id)
	if err != nil {
		return MissileIntent{}, err
	}
	if w.HostileDefense(id, a.Sector) {
		return MissileIntent{}, ErrDefenseEncounter
	}
	if w.HasMineEncounter(a.ID) {
		return MissileIntent{}, ErrMineEncounter
	}
	if w.Sectors[to] == nil || to == a.Sector {
		return MissileIntent{}, errors.New("choose a different existing sector")
	}
	if a.Turns < 1 {
		return MissileIntent{}, errors.New("no turns left today")
	}
	if count < 1 || count > a.Missiles {
		return MissileIntent{}, errors.New("choose available missiles to launch")
	}
	route, err := w.path(a.Sector, to, nil)
	if err != nil {
		return MissileIntent{}, errors.New("no warp route reaches that missile target")
	}
	intent := MissileIntent{Season: w.Season, Player: id, From: a.Sector, To: to, Generation: a.ShipGeneration, Sequence: a.WarpSequence, Count: count, Route: route}
	intent.Sectors, err = w.snapshotMissileRoute(id, route, v, true)
	if err != nil {
		return MissileIntent{}, err
	}
	eligible := false
	for _, sector := range intent.Sectors {
		eligible = eligible || len(sector.Mines) > 0 || sector.Defense != nil && !w.friendlyDefense(id, sector.Defense) || len(sector.Ships) > 0 || sector.Planet != nil && !w.friendlyPlanet(id, sector.Planet)
		if sector.Sector == to && sector.Planet != nil && w.friendlyPlanet(id, sector.Planet) {
			return MissileIntent{}, errors.New("cannot target a personal or teammate planet")
		}
	}
	if !eligible {
		return MissileIntent{}, errors.New("no eligible ship, hostile fighter group, minefield or hostile planet lies along that route")
	}
	return intent, nil
}

func (w *World) friendlyPlanet(shooter int, planet *Planet) bool {
	if planet == nil {
		return false
	}
	a := w.Players[shooter]
	owner := w.Players[planet.Owner]
	return planet.Owner == shooter || a != nil && a.Team != 0 && owner != nil && owner.Team == a.Team
}

func (w *World) snapshotMissileRoute(shooter int, route []int, visibility *Visibility, includeShips bool) ([]MissileRouteSector, error) {
	if len(route) < 2 {
		return nil, errors.New("missile course has no destination")
	}
	out := make([]MissileRouteSector, 0, len(route)-1)
	for _, sectorID := range route[1:] {
		sector := w.Sectors[sectorID]
		if sector == nil {
			return nil, errors.New("missile course changed; confirm again")
		}
		snapshot := MissileRouteSector{Sector: sectorID, Mines: append([]MineLayer(nil), sector.Minefield...)}
		if sector.Defense != nil {
			defense := *sector.Defense
			snapshot.Defense = &defense
		}
		if sector.Planet != 0 {
			planet := w.Planets[sector.Planet]
			if planet == nil {
				return nil, errors.New("planet record is missing")
			}
			copy := *planet
			snapshot.Planet = &copy
		}
		if includeShips {
			ids := make([]int, 0, len(w.Players))
			for playerID := range w.Players {
				ids = append(ids, playerID)
			}
			sort.Ints(ids)
			for _, playerID := range ids {
				p, actor := w.Players[playerID], w.Players[shooter]
				if p.ID == shooter || p.Death != nil || p.Sector != sectorID || actor.Team != 0 && actor.Team == p.Team || !visibility.sees(p) {
					continue
				}
				target := MissileShipTarget{Player: p.ID, Team: p.Team, Generation: p.ShipGeneration, Sequence: p.WarpSequence, Alias: p.Alias, Fighters: p.Fighters, Shields: p.Shields, Cloak: p.Cloak}
				if back, err := w.path(sectorID, route[0], nil); err == nil {
					target.ReturnRoute = back
					target.ReturnSectors, err = w.snapshotMissileRoute(p.ID, back, nil, false)
					if err != nil {
						return nil, err
					}
				}
				snapshot.Ships = append(snapshot.Ships, target)
			}
		}
		out = append(out, snapshot)
	}
	return out, nil
}

// CommitMissile saves both volleys and every consequence in the caller's single
// store Update. A surviving target may fire once; that response cannot recurse.
func (w *World) CommitMissile(intent MissileIntent, v *Visibility, rng func() float64, now time.Time) (MissileResult, error) {
	if err := w.CheckSession(intent.Player, intent.Generation, intent.Season); err != nil {
		return MissileResult{}, err
	}
	fresh, err := w.PrepareMissile(intent.Player, intent.To, intent.Count, v)
	if err != nil {
		return MissileResult{}, err
	}
	if !reflect.DeepEqual(fresh, intent) {
		return MissileResult{}, errors.New("missile target or mine warning changed; confirm again")
	}
	if rng == nil || now.IsZero() || now.Before(w.Created) {
		return MissileResult{}, errors.New("invalid missile launch inputs")
	}
	a := w.Players[intent.Player]
	a.Missiles -= intent.Count
	a.spendTurn()
	budget := maxMissileRounds
	primary, err := w.missileImpact(a.ID, intent.Route, intent.Sectors, 0, intent.Count, "missile", rng, now, &budget)
	if err != nil {
		return MissileResult{}, err
	}
	result := MissileResult{Primary: primary}
	if primary.Retaliator == 0 {
		return result, nil
	}
	d := w.Players[primary.Retaliator]
	if d == nil || d.Death != nil || d.Missiles == 0 {
		return result, nil
	}
	var target *MissileShipTarget
	for si := range intent.Sectors {
		for ti := range intent.Sectors[si].Ships {
			if intent.Sectors[si].Ships[ti].Player == d.ID {
				target = &intent.Sectors[si].Ships[ti]
				break
			}
		}
	}
	if target == nil || len(target.ReturnRoute) < 2 {
		return result, nil
	}
	// The same locked encounter supplies the explicit original attacker target,
	// including its cloak. No other hidden ship is revealed or damaged.
	n, err := RetaliationVolley(a.StoredScore, d.Missiles, rng)
	if err != nil {
		return MissileResult{}, err
	}
	d.Missiles -= n
	result.Counter, err = w.missileImpact(d.ID, target.ReturnRoute, target.ReturnSectors, a.ID, n, "retaliation", rng, now, &budget)
	if err != nil {
		return MissileResult{}, err
	}
	return result, nil
}

func (w *World) interceptMines(sector int, missiles int64) int64 {
	s := w.Sectors[sector]
	spent := int64(0)
	for missiles > 0 && len(s.Minefield) > 0 {
		used := min(missiles, s.Minefield[0].Count)
		spent += used
		missiles -= used
		s.Minefield[0].Count -= used
		if s.Minefield[0].Count == 0 {
			s.Minefield = s.Minefield[1:]
			if len(s.Minefield) == 0 {
				s.Minefield = nil
			}
		}
	}
	return spent
}
func (w *World) missileImpact(shooter int, route []int, routeSectors []MissileRouteSector, explicitTarget int, count int64, cause string, rng func() float64, now time.Time, budget *int) (MissileImpact, error) {
	out := MissileImpact{Launched: count}
	remaining := count
	for i, snap := range routeSectors {
		sectorID := snap.Sector
		sector := w.Sectors[sectorID]
		if sector == nil || i+1 >= len(route) || route[i+1] != sectorID {
			return MissileImpact{}, errors.New("missile course changed")
		}
		var intercepted MissileInterception
		intercepted.Sector = sectorID
		if sector.Defense != nil && !w.friendlyDefense(shooter, sector.Defense) {
			spent, killed := int64(0), int64(0)
			for spent < remaining && killed < sector.Defense.Fighters {
				if *budget <= 0 {
					return MissileImpact{}, errors.New("missile calculation limit reached")
				}
				(*budget)--
				hit, err := scaledSalvageDraw(5000, rng)
				if err != nil {
					return MissileImpact{}, err
				}
				killed += hit
				spent++
			}
			intercepted.Missiles = spent
			intercepted.FightersDestroyed = min(killed, sector.Defense.Fighters)
			out.SectorMissiles += spent
			out.SectorFightersDestroyed += intercepted.FightersDestroyed
			prior := *sector.Defense
			sector.Defense.Fighters -= intercepted.FightersDestroyed
			if sector.Defense.Fighters == 0 {
				sector.Defense = nil
				reward, err := w.awardXannorHQ(shooter, sectorID, prior, now)
				if err != nil {
					return MissileImpact{}, err
				}
				if reward != nil {
					out.HQRewards = append(out.HQRewards, *reward)
				}
			}
			remaining -= spent
		}
		if remaining > 0 {
			intercepted.MinesDestroyed = w.interceptMines(sectorID, remaining)
			out.MinesDestroyed += intercepted.MinesDestroyed
			remaining -= intercepted.MinesDestroyed
		}
		if intercepted.Missiles > 0 || intercepted.MinesDestroyed > 0 {
			out.Interceptions = append(out.Interceptions, intercepted)
		}
		if remaining == 0 {
			break
		}

		var targets []int
		if explicitTarget != 0 {
			if i == len(routeSectors)-1 {
				targets = []int{explicitTarget}
			}
		} else {
			for _, target := range snap.Ships {
				targets = append(targets, target.Player)
			}
		}
		for _, targetID := range targets {
			if remaining == 0 {
				break
			}
			d := w.Players[targetID]
			actor := w.Players[shooter]
			if d == nil || d.Death != nil || d.Sector != sectorID || d.ID == shooter || actor.Team != 0 && actor.Team == d.Team {
				continue
			}
			damage, err := resolveMissileShip(remaining, d.Fighters, d.Shields, rng, budget)
			if err != nil {
				return MissileImpact{}, err
			}
			remaining -= damage.Spent
			out.Target = d.ID
			out.Damage.Spent += damage.Spent
			out.Damage.Fighters += damage.Fighters
			out.Damage.Shields += damage.Shields
			d.Fighters -= damage.Fighters
			d.Shields -= damage.Shields
			shipImpact := MissileShipImpact{Sector: sectorID, Player: d.ID, Alias: d.Alias, Damage: damage}
			if d.Shields != 0 {
				if cause == "missile" {
					out.Retaliator = d.ID
				}
				out.ShipImpacts = append(out.ShipImpacts, shipImpact)
				continue
			}
			shipImpact.Destroyed = true
			out.Destroyed = true
			shipImpact.LostEscorts = d.Fighters
			out.LostEscorts += d.Fighters
			d.Fighters = 0 // The ship and surviving escorts are lost when shields are exhausted.
			var deathRoute []int
			if cause == "missile" {
				deathRoute = append([]int(nil), route[:i+2]...)
			}
			shipImpact.Salvage, err = w.SettleShipSalvage(DeathContext{Victim: d.ID, Generation: d.ShipGeneration, Sector: sectorID, Killer: shooter, Cause: cause, MissileRoute: deathRoute}, rng, now)
			if err != nil {
				return MissileImpact{}, err
			}
			addSalvage(&out.Salvage, shipImpact.Salvage)
			if sectorID == 1 {
				out.Disarmed += d.Mines
				d.Mines = 0
			} else {
				out.Dropped += d.Mines
				if err = w.dropMines(sectorID, d.ID, d.Mines); err != nil {
					return MissileImpact{}, err
				}
				d.Mines = 0
				if remaining > 0 {
					destroyedMines := w.interceptMines(sectorID, remaining)
					out.MinesDestroyed += destroyedMines
					remaining -= destroyedMines
					if destroyedMines > 0 {
						out.Interceptions = append(out.Interceptions, MissileInterception{Sector: sectorID, MinesDestroyed: destroyedMines})
					}
				}
			}
			out.ShipImpacts = append(out.ShipImpacts, shipImpact)
		}
		if remaining == 0 {
			break
		}

		if sector.Planet != 0 {
			planet := w.Planets[sector.Planet]
			if planet == nil {
				return MissileImpact{}, errors.New("planet record is missing")
			}
			if w.friendlyPlanet(shooter, planet) {
				continue
			}
			planetImpact := MissilePlanetImpact{Sector: sectorID, PlanetID: planet.ID, Missiles: remaining}
			if now.Before(planet.Updated) {
				return MissileImpact{}, errors.New("planet update is ahead of launch time")
			}
			planet.update(now, true)
			planetImpact.GroundBefore = planet.Ground
			planetImpact.ProductionBefore = planet.Production
			planetImpact.CargoBefore = planet.Cargo
			left, groundAfter, err := resolveMissileGroundPhase(remaining, float64(planet.Ground), rng, budget)
			if err != nil {
				return MissileImpact{}, err
			}
			planetImpact.GroundMissiles = remaining - left
			planet.Ground = groundAfter
			planetImpact.GroundAfter = groundAfter
			used, rates, cargo, destroyed := int64(0), planet.Production, planet.Cargo, false
			if left > 0 {
				used, rates, cargo, destroyed, err = resolveMissileProduction(left, rates, cargo, rng, budget)
				if err != nil {
					return MissileImpact{}, err
				}
			}
			planetImpact.ProductionMissiles = used
			planetImpact.ProductionAfter, planetImpact.CargoAfter = rates, cargo
			planetImpact.Destroyed = destroyed
			planet.Production, planet.Cargo = rates, cargo
			remaining = left - used
			out.PlanetID = planet.ID
			out.GroundBefore, out.GroundAfter = planetImpact.GroundBefore, planetImpact.GroundAfter
			out.PlanetMissiles += planetImpact.Missiles
			out.GroundMissiles += planetImpact.GroundMissiles
			out.ProductionMissiles += planetImpact.ProductionMissiles
			out.ProductionBefore, out.ProductionAfter = planetImpact.ProductionBefore, planetImpact.ProductionAfter
			out.CargoBefore, out.CargoAfter = planetImpact.CargoBefore, planetImpact.CargoAfter
			out.PlanetDestroyed = out.PlanetDestroyed || planetImpact.Destroyed
			if destroyed {
				w.destroyPlanet(planet)
			}
			out.PlanetImpacts = append(out.PlanetImpacts, planetImpact)
		}
		if remaining == 0 {
			break
		}
	}
	return out, nil
}

func addSalvage(total *Salvage, add Salvage) {
	total.Holds += add.Holds
	total.Credits += add.Credits
	total.Missiles += add.Missiles
	total.Plasma += add.Plasma
	total.Ground += add.Ground
	total.Mines += add.Mines
	for i := range total.Cargo {
		total.Cargo[i] += add.Cargo[i]
	}
}

// ResolveMissileGround is the bounded ground-only calculation retained for
// fixtures and callers that explicitly need that isolated phase. Full attacks
// use resolveMissileGroundPhase and continue into production.
func ResolveMissileGround(missiles, ground int64, rng func() float64) (int64, error) {
	budget := maxMissileRounds
	return resolveMissileGround(missiles, ground, rng, &budget)
}
func resolveMissileGround(missiles, ground int64, rng func() float64, budget *int) (int64, error) {
	if missiles < 1 || ground < 1 || ground > MaxQuantity || missiles > ground/25 || rng == nil {
		return 0, errors.New("unsupported ground bombardment inputs")
	}
	remaining := float64(ground)
	for i := int64(0); i < missiles; i++ {
		if *budget <= 0 {
			return 0, errors.New("missile calculation limit reached")
		}
		*budget -= 1
		r := rng()
		if math.IsNaN(r) || math.IsInf(r, 0) || r < 0 || r >= 1 {
			return 0, errors.New("combat RNG must return [0,1)")
		}
		remaining -= r * 25
	}
	return int64(math.Floor(remaining)), nil
}

func resolveMissileGroundPhase(missiles int64, ground float64, rng func() float64, budget *int) (int64, int64, error) {
	if missiles < 1 || missiles > MaxQuantity || ground < 0 || ground > float64(MaxQuantity) || math.IsNaN(ground) || rng == nil {
		return 0, 0, errors.New("invalid ground bombardment inputs")
	}
	used := int64(0)
	for used < missiles && ground > 0 {
		if *budget <= 0 {
			return 0, 0, errors.New("missile calculation limit reached")
		}
		(*budget)--
		r := rng()
		if math.IsNaN(r) || math.IsInf(r, 0) || r < 0 || r >= 1 {
			return 0, 0, errors.New("combat RNG must return [0,1)")
		}
		ground -= r * 25
		used++
	}
	return missiles - used, int64(math.Max(0, math.Floor(ground))), nil
}

// resolveMissileProduction follows the recovered YT 3.6 loop: the cached ore
// rate at entry controls loop eligibility while all three live rates take
// independent damage draws. A single round consumes one missile and budget.
func resolveMissileProduction(missiles int64, production, cargo [3]float64, rng func() float64, budget *int) (int64, [3]float64, [3]float64, bool, error) {
	if missiles < 0 || rng == nil {
		return 0, production, cargo, false, errors.New("invalid production bombardment inputs")
	}
	cachedOre := production[0]
	used := int64(0)
	for used < missiles && (cachedOre > 0 || production[1] > 0 || production[2] > 0) {
		if *budget <= 0 {
			return 0, production, cargo, false, errors.New("missile calculation limit reached")
		}
		(*budget)--
		for i := range production {
			r := rng()
			if math.IsNaN(r) || math.IsInf(r, 0) || r < 0 || r >= 1 {
				return 0, production, cargo, false, errors.New("combat RNG must return [0,1)")
			}
			production[i] -= r * 2000
		}
		used++
	}
	for i := range production {
		production[i] = limited(production[i])
		cargo[i] = math.Min(cargo[i], 10*production[i])
	}
	destroyed := production == [3]float64{}
	return used, production, cargo, destroyed, nil
}
