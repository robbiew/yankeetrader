package game

import (
	"errors"
	"math"
	"slices"
	"time"
)

const maxMissileRounds = 1_000_000

type MissileDamage struct{ Spent, Fighters, Shields int64 }
type MissileIntent struct {
	Player, From, To, Target     int
	Generation, TargetGeneration uint64
	Count                        int64
	Mines                        []MineLayer
	Defense                      SectorDefense
	Planet                       *Planet
}
type MissileImpact struct {
	SectorMissiles                              int64
	PlanetID                                    int
	GroundBefore, GroundAfter, PlanetMissiles   int64
	GroundMissiles, ProductionMissiles          int64
	ProductionBefore, ProductionAfter           [3]float64
	CargoBefore, CargoAfter                     [3]float64
	PlanetDestroyed                             bool
	Target                                      int
	Launched, MinesDestroyed, Dropped, Disarmed int64
	SectorFightersDestroyed                     int64
	LostEscorts                                 int64
	Damage                                      MissileDamage
	Destroyed                                   bool
	Salvage                                     Salvage
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
	if len(w.Sectors[a.Sector].Minefield) > 0 {
		return MissileIntent{}, ErrMineEncounter
	}
	// Return fire reaches this sector too. Until its interception rules are
	// supported, refuse the whole exchange before charging ammo or turns.
	origin := w.Sectors[a.Sector]
	if origin.Planet != 0 {
		return MissileIntent{}, errors.New("missile return path through planets is not available yet")
	}
	target := w.Sectors[to]
	if target == nil || to == a.Sector || !contains(w.Sectors[a.Sector].Warps, to) || !contains(target.Warps, a.Sector) {
		return MissileIntent{}, errors.New("choose a different sector linked in both directions by one warp")
	}
	if a.Turns < 1 {
		return MissileIntent{}, errors.New("no turns left today")
	}
	if count < 1 || count > a.Missiles {
		return MissileIntent{}, errors.New("choose available missiles to launch")
	}
	intent := MissileIntent{Player: id, From: a.Sector, To: to, Generation: a.ShipGeneration, Count: count, Mines: append([]MineLayer(nil), target.Minefield...)}
	if target.Defense != nil {
		intent.Defense = *target.Defense
	}
	for _, p := range w.Players {
		if p.ID == id || p.Death != nil || p.Sector != to || (a.Team != 0 && a.Team == p.Team) || !v.sees(p) {
			continue
		}
		if intent.Target != 0 {
			return MissileIntent{}, errors.New("multiple visible enemies require sector-wide missile combat, which is not available yet")
		}
		intent.Target = p.ID
		intent.TargetGeneration = p.ShipGeneration
	}
	if target.Planet != 0 {
		planet := w.Planets[target.Planet]
		if planet == nil {
			return MissileIntent{}, errors.New("planet record is missing")
		}
		if intent.Target != 0 {
			return MissileIntent{}, errors.New("mixed ship/planet missile encounters are not available yet")
		}
		owner := w.Players[planet.Owner]
		if planet.Owner == id || (a.Team != 0 && owner != nil && owner.Team == a.Team) {
			return MissileIntent{}, errors.New("cannot bombard a personal or teammate planet")
		}
		snapshot := *planet
		intent.Planet = &snapshot
	}
	if intent.Planet == nil && intent.Target == 0 && len(intent.Mines) == 0 && !w.HostileDefense(id, to) {
		return MissileIntent{}, errors.New("no eligible ship, hostile fighter group, minefield or supported planet in that sector")
	}
	return intent, nil
}

// CommitMissile saves both volleys and every consequence in the caller's single
// store Update. A surviving target may fire once; that response cannot recurse.
func (w *World) CommitMissile(intent MissileIntent, v *Visibility, rng func() float64, now time.Time) (MissileResult, error) {
	if err := w.CheckShip(intent.Player, intent.Generation); err != nil {
		return MissileResult{}, err
	}
	fresh, err := w.PrepareMissile(intent.Player, intent.To, intent.Count, v)
	if err != nil {
		return MissileResult{}, err
	}
	if !sameMissilePlanet(fresh.Planet, intent.Planet) || fresh.Defense != intent.Defense || fresh.From != intent.From || fresh.Target != intent.Target || fresh.TargetGeneration != intent.TargetGeneration || !slices.Equal(fresh.Mines, intent.Mines) {
		return MissileResult{}, errors.New("missile target or mine warning changed; confirm again")
	}
	if rng == nil || now.IsZero() || now.Before(w.Created) {
		return MissileResult{}, errors.New("invalid missile launch inputs")
	}
	a := w.Players[intent.Player]
	a.Missiles -= intent.Count
	a.spendTurn()
	budget := maxMissileRounds
	primary, err := w.missileImpact(a.ID, intent.Target, intent.To, intent.Count, "missile", rng, now, &budget)
	if err != nil {
		return MissileResult{}, err
	}
	result := MissileResult{Primary: primary}
	d := w.Players[intent.Target]
	if primary.Damage.Spent == 0 || primary.Destroyed || d == nil || d.Death != nil || d.Missiles == 0 {
		return result, nil
	}
	// The same locked encounter supplies the explicit original attacker target,
	// including its cloak. No other hidden ship is revealed or damaged.
	n, err := RetaliationVolley(a.StoredScore, d.Missiles, rng)
	if err != nil {
		return MissileResult{}, err
	}
	d.Missiles -= n
	result.Counter, err = w.missileImpact(d.ID, a.ID, intent.From, n, "retaliation", rng, now, &budget)
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
func (w *World) missileImpact(shooter, target, sector int, count int64, cause string, rng func() float64, now time.Time, budget *int) (MissileImpact, error) {
	out := MissileImpact{Target: target, Launched: count}
	remaining := count
	if s := w.Sectors[sector]; s.Defense != nil && !w.friendlyDefense(shooter, s.Defense) {
		spent := int64(0)
		killed := int64(0)
		for spent < remaining && killed < s.Defense.Fighters {
			if *budget <= 0 {
				return MissileImpact{}, errors.New("missile calculation limit reached")
			}
			*budget -= 1
			hit, err := scaledSalvageDraw(5000, rng)
			if err != nil {
				return MissileImpact{}, err
			}
			killed += hit
			spent++
		}
		out.SectorMissiles = spent
		out.SectorFightersDestroyed = min(killed, s.Defense.Fighters)
		s.Defense.Fighters -= out.SectorFightersDestroyed
		if s.Defense.Fighters == 0 {
			s.Defense = nil
		}
		remaining -= spent
	}
	out.MinesDestroyed = w.interceptMines(sector, remaining)
	remaining -= out.MinesDestroyed
	if remaining > 0 && target == 0 && w.Sectors[sector].Planet != 0 {
		reachedPlanet := remaining
		planet := w.Planets[w.Sectors[sector].Planet]
		if now.Before(planet.Updated) {
			return MissileImpact{}, errors.New("planet update is ahead of launch time")
		}
		planet.update(now, true)
		out.PlanetID = planet.ID
		out.GroundBefore = planet.Ground
		out.ProductionBefore = planet.Production
		out.CargoBefore = planet.Cargo
		left := remaining
		groundAfter := planet.Ground
		var err error
		if left > 0 {
			left, groundAfter, err = resolveMissileGroundPhase(left, float64(planet.Ground), rng, budget)
			if err != nil {
				return MissileImpact{}, err
			}
		}
		out.GroundMissiles = remaining - left
		remaining = left
		planet.Ground = groundAfter
		out.GroundAfter = groundAfter
		used, rates, cargo, destroyed := int64(0), planet.Production, planet.Cargo, false
		if remaining > 0 {
			used, rates, cargo, destroyed, err = resolveMissileProduction(remaining, rates, cargo, rng, budget)
			if err != nil {
				return MissileImpact{}, err
			}
		}
		out.ProductionMissiles = used
		remaining -= used
		planet.Production, planet.Cargo = rates, cargo
		out.ProductionAfter, out.CargoAfter = rates, cargo
		out.PlanetDestroyed = destroyed
		if destroyed {
			delete(w.Planets, planet.ID)
			w.Sectors[sector].Planet = 0
			for _, player := range w.Players {
				if player.LandedPlanet == planet.ID {
					player.PlanetToken = ""
					player.LandedPlanet = 0
				}
			}
		}
		out.PlanetMissiles = reachedPlanet
	}
	if remaining == 0 || target == 0 {
		return out, nil
	}
	d, err := w.player(target)
	if err != nil {
		return MissileImpact{}, err
	}
	if d.Sector != sector {
		return MissileImpact{}, errors.New("missile target moved")
	}
	out.Damage, err = resolveMissileShip(remaining, d.Fighters, d.Shields, rng, budget)
	if err != nil {
		return MissileImpact{}, err
	}
	d.Fighters -= out.Damage.Fighters
	d.Shields -= out.Damage.Shields
	if d.Shields != 0 {
		return out, nil
	}
	out.Destroyed = true
	out.LostEscorts = d.Fighters
	d.Fighters = 0 // The ship and surviving escorts are lost when shields are exhausted.
	out.Salvage, err = w.SettleShipSalvage(DeathContext{Victim: d.ID, Generation: d.ShipGeneration, Sector: sector, Killer: shooter, Cause: cause}, rng, now)
	if err != nil {
		return MissileImpact{}, err
	}
	if sector == 1 {
		out.Disarmed = d.Mines
		d.Mines = 0
		return out, nil
	}
	out.Dropped = d.Mines
	if err = w.dropMines(sector, d.ID, d.Mines); err != nil {
		return MissileImpact{}, err
	}
	d.Mines = 0
	out.MinesDestroyed += w.interceptMines(sector, remaining-out.Damage.Spent)
	return out, nil
}

func sameMissilePlanet(a, b *Planet) bool {
	if a == nil || b == nil {
		return a == nil && b == nil
	}
	return *a == *b
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
