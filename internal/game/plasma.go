package game

import (
	"crypto/sha256"
	"encoding/json"
	"errors"
	"math"
	"sort"
	"time"
)

// All budgets are shared by an entire accepted launch, including redirects and
// wreck mines. Zero random draws must not turn a command into unbounded work.
const (
	MaxPlasmaBolts     int64 = 64
	MaxPlasmaRounds          = 100_000
	MaxPlasmaDraws           = 200_000
	MaxPlasmaVisits          = 128
	MaxPlasmaRedirects       = 32
)

var ErrPlasmaLimit = errors.New("plasma calculation limit reached; launch aborted without spending resources")

// State seals all saved state because a redirected course can reach any sector.
// The private login hole context is hashed, never returned as coordinates. Nonce
// is issued/consumed by the bound store; the rules layer never samples a preview.
type PlasmaIntent struct {
	Nonce                        string
	Player, From, To             int
	Generation, Season, Sequence uint64
	Count                        int64
	State                        [32]byte
}

// PlasmaResult is an immutable private receipt, not a redeemable award. It omits
// target identities and tracking coordinates, including concealed redirected paths.
type PlasmaResult struct {
	Launched, TurnsSpent, BoltsRemaining, TurnsRemaining   int64
	OwnFightersLost, OwnShieldsLost                        int64
	SectorFighters, MinesDestroyed, Dropped, Disarmed      int64
	ShipsHit, ShipsDestroyed, PlanetsHit, PlanetsDestroyed int
	Redirects, Visits                                      int
	Destroyed, SelfDestroyed, RouteUnavailable             bool
	Salvage                                                Salvage
	Aftermath                                              MineOutcome
	HQRewards                                              []XannorHQReward
}

func (w *World) PreparePlasma(id, to int, count int64) (PlasmaIntent, error) {
	p, err := w.player(id)
	if err != nil {
		return PlasmaIntent{}, err
	}
	if w.HasMineEncounter(id) {
		return PlasmaIntent{}, ErrMineEncounter
	}
	if w.HostileDefense(id, p.Sector) {
		return PlasmaIntent{}, ErrDefenseEncounter
	}
	if w.Disrupted(id, p.Sector) {
		return PlasmaIntent{}, errors.New("resolve the current disruption before acting")
	}
	if w.Sectors[to] == nil {
		return PlasmaIntent{}, errors.New("choose an existing plasma destination")
	}
	if p.Turns < 1 {
		return PlasmaIntent{}, errors.New("no turns left today")
	}
	if count < 1 || count > p.Plasma || count > MaxPlasmaBolts {
		return PlasmaIntent{}, errors.New("choose 1 to 64 available plasma bolts")
	}
	var holes *Disruption
	if w.arrival != nil {
		if err = w.CheckSession(id, w.arrival.state.Generation, w.arrival.state.Season); err != nil || w.arrival.state.Player != id {
			return PlasmaIntent{}, errors.New("plasma login context changed")
		}
		holes = &w.arrival.state
	}
	b, err := json.Marshal(struct {
		World               *World
		Login               *Disruption
		Player, Destination int
		Count               int64
	}{w, holes, id, to, count})
	if err != nil {
		return PlasmaIntent{}, err
	}
	return PlasmaIntent{Player: id, From: p.Sector, To: to, Generation: p.ShipGeneration, Season: w.Season, Sequence: p.WarpSequence, Count: count, State: sha256.Sum256(b)}, nil
}

type plasmaEnergy struct {
	energy, loss float64
	rounds       int
	rng          func() float64
}

func (e *plasmaEnergy) spend() error {
	if e.rounds >= MaxPlasmaRounds {
		return ErrPlasmaLimit
	}
	e.rounds++
	if e.rng == nil {
		return errors.New("plasma requires randomness")
	}
	r := e.rng()
	if math.IsNaN(r) || math.IsInf(r, 0) || r < 0 || r >= 1 {
		return errors.New("plasma RNG must return a finite value in [0,1)")
	}
	e.energy = math.Max(0, e.energy-r*25000)
	return nil
}
func (e *plasmaEnergy) absorb(stock int64, divisor float64) (int64, error) {
	lost := int64(0)
	for lost < stock && e.energy > 0 {
		n := min(stock-lost, int64(math.Floor(e.energy/divisor))+1)
		if err := e.spend(); err != nil {
			return 0, err
		}
		lost += n
	}
	return lost, nil
}
func (w *World) plasmaMines(sector int, e *plasmaEnergy) (int64, error) {
	s := w.Sectors[sector]
	total := int64(0)
	for len(s.Minefield) > 0 && e.energy > 0 {
		n, err := e.absorb(s.Minefield[0].Count, 1_000_000)
		if err != nil {
			return 0, err
		}
		total += n
		s.Minefield[0].Count -= n
		if s.Minefield[0].Count == 0 {
			s.Minefield = s.Minefield[1:]
		}
	}
	if len(s.Minefield) == 0 {
		s.Minefield = nil
	}
	return total, nil
}
func (w *World) plasmaPlanet(p *Planet, e *plasmaEnergy, now time.Time) (bool, error) {
	if now.Before(p.Updated) {
		return false, errors.New("planet update is ahead of plasma launch")
	}
	p.update(now, true)
	cachedOre := p.Production[0]
	rates := p.Production
	ground := float64(p.Ground)
	for e.energy > 0 && (cachedOre > 0 || rates[1] > 0 || rates[2] > 0) {
		damage := e.energy * .000004
		if err := e.spend(); err != nil {
			return false, err
		}
		ground -= damage
		for i := range rates {
			rates[i] -= damage
		}
	}
	p.Ground = int64(math.Floor(math.Max(0, ground)))
	if p.Ground == 0 {
		p.Owner = 0
		w.invalidatePlanetLandings(p.ID)
	}
	for i := range rates {
		p.Production[i] = math.Max(0, rates[i])
		p.Cargo[i] = math.Min(p.Cargo[i], 10*p.Production[i])
	}
	destroyed := p.Production == [3]float64{}
	if destroyed {
		w.destroyPlanet(p)
	}
	return destroyed, nil
}

// plasmaDeath permits self, teammate and posthumous blame without treating those
// as an enemy-only missile death. Only a different living source receives loot
// and ports. Residual ship assets are discarded; deposits on surviving planets
// remain the account's. Wreck mines are handled by the caller at the impact site.
func (w *World) plasmaDeath(source int, victim *Player, rng func() float64, now time.Time) (Salvage, error) {
	context := DeathContext{Victim: victim.ID, Generation: victim.ShipGeneration, Sector: victim.Sector, Killer: source, Cause: "plasma"}
	if _, err := w.deathTarget(context, now); err != nil {
		return Salvage{}, err
	}
	var loot Salvage
	killer := w.Players[source]
	if source != victim.ID && killer != nil && killer.Death == nil {
		var err error
		// Wreck mines are not simultaneously salvaged and deployed.
		sample := *victim
		sample.Mines = 0
		loot, err = SampleSalvage(sample, killer.Holds, rng)
		if err != nil {
			return Salvage{}, err
		}
		if loot.Credits > MaxMoney-killer.Credits || loot.Missiles > MaxQuantity-killer.Missiles || loot.Plasma > MaxQuantity-killer.Plasma || loot.Ground > MaxQuantity-killer.Ground {
			return Salvage{}, errors.New("plasma salvage exceeds recipient capacity")
		}
		killer.Holds += loot.Holds
		killer.Credits += loot.Credits
		killer.Missiles += loot.Missiles
		killer.Plasma += loot.Plasma
		killer.Ground += loot.Ground
		for i, n := range loot.Cargo {
			killer.Cargo[i] += n
		}
	}
	w.recordDeath(victim, context, now)
	return loot, nil
}

// CommitPlasma must run in a store transaction whose callback returns every
// error. Like CommitMissile, intermediate rules mutations are not a saved result.
func (w *World) CommitPlasma(intent PlasmaIntent, rng func() float64, now time.Time) (result PlasmaResult, resultErr error) {
	if err := w.CheckSession(intent.Player, intent.Generation, intent.Season); err != nil {
		return PlasmaResult{}, err
	}
	fresh, err := w.PreparePlasma(intent.Player, intent.To, intent.Count)
	if err != nil {
		return PlasmaResult{}, err
	}
	comparison := intent
	comparison.Nonce = ""
	if comparison != fresh {
		return PlasmaResult{}, errors.New("plasma confirmation changed; reconsider the launch")
	}
	if rng == nil || now.IsZero() || now.Before(w.Created) {
		return PlasmaResult{}, errors.New("invalid plasma launch inputs")
	}
	drawCount, limited := 0, false
	originalRandom := rng
	rng = func() float64 {
		if drawCount >= MaxPlasmaDraws {
			limited = true
			return math.NaN()
		}
		drawCount++
		return originalRandom()
	}
	defer func() {
		if limited {
			result = PlasmaResult{}
			resultErr = ErrPlasmaLimit
		}
	}()
	a := w.Players[intent.Player]
	initialTurns := a.Turns
	beforeF, beforeS := a.Fighters, a.Shields
	a.Plasma -= intent.Count
	a.spendTurn()
	out := PlasmaResult{Launched: intent.Count, TurnsSpent: 1}
	energy := plasmaEnergy{energy: float64(intent.Count) * 2500000, loss: float64(intent.Count) * 50000, rng: rng}
	sectors := make([]int, 0, len(w.Sectors))
	players := make([]int, 0, len(w.Players))
	for id := range w.Sectors {
		sectors = append(sectors, id)
	}
	sort.Ints(sectors)
	for id := range w.Players {
		players = append(players, id)
	}
	sort.Ints(players)
	var holes [2]int
	if w.arrival != nil {
		holes = w.arrival.state.Locations
	}
	from, to := intent.From, intent.To
	for energy.energy >= 1 {
		var path []int
		if from == to {
			path = []int{from, to}
		} else {
			path, err = w.path(from, to, nil)
			if err != nil {
				out.RouteUnavailable = true
				break
			}
		}
		redirected := false
		for i, sectorID := range path[1:] {
			if i > 0 {
				energy.energy -= energy.loss
			}
			if energy.energy < 1 {
				break
			}
			if out.Visits >= MaxPlasmaVisits {
				return PlasmaResult{}, ErrPlasmaLimit
			}
			out.Visits++
			if sectorID == holes[0] || sectorID == holes[1] {
				if out.Redirects >= MaxPlasmaRedirects {
					return PlasmaResult{}, ErrPlasmaLimit
				}
				r, e := warpDraw(rng)
				if e != nil {
					return PlasmaResult{}, e
				}
				out.Redirects++
				from, to = sectorID, sectors[int(r*float64(len(sectors)))]
				redirected = true
				break
			}
			s := w.Sectors[sectorID]
			if d := s.Defense; d != nil {
				killed, e := energy.absorb(d.Fighters, 5000)
				if e != nil {
					return PlasmaResult{}, e
				}
				prior := *d
				d.Fighters -= killed
				out.SectorFighters += killed
				if d.Fighters == 0 {
					s.Defense = nil
					reward, e := w.awardXannorHQ(a.ID, sectorID, prior, now)
					if e != nil {
						return PlasmaResult{}, e
					}
					if reward != nil {
						out.HQRewards = append(out.HQRewards, *reward)
					}
				}
			}
			n, e := w.plasmaMines(sectorID, &energy)
			if e != nil {
				return PlasmaResult{}, e
			}
			out.MinesDestroyed += n
			for _, id := range players {
				p := w.Players[id]
				if energy.energy <= 0 {
					break
				}
				if p.Death != nil || p.Sector != sectorID {
					continue
				}
				out.ShipsHit++
				n, e = energy.absorb(p.Fighters, 5000)
				if e != nil {
					return PlasmaResult{}, e
				}
				p.Fighters -= n
				n, e = energy.absorb(p.Shields, 10000)
				if e != nil {
					return PlasmaResult{}, e
				}
				p.Shields -= n
				if p.Shields > 0 {
					continue
				}
				out.ShipsDestroyed++
				mines := p.Mines
				loot, e := w.plasmaDeath(a.ID, p, rng, now)
				if e != nil {
					return PlasmaResult{}, e
				}
				addSalvage(&out.Salvage, loot)
				if sectorID == 1 {
					out.Disarmed += mines
				} else {
					if e = w.dropMines(sectorID, p.ID, mines); e != nil {
						return PlasmaResult{}, e
					}
					out.Dropped += mines
					n, e = w.plasmaMines(sectorID, &energy)
					if e != nil {
						return PlasmaResult{}, e
					}
					out.MinesDestroyed += n
				}
			}
			if energy.energy > 0 && s.Planet != 0 {
				p := w.Planets[s.Planet]
				if p == nil {
					return PlasmaResult{}, errors.New("plasma planet record missing")
				}
				out.PlanetsHit++
				destroyed, e := w.plasmaPlanet(p, &energy, now)
				if e != nil {
					return PlasmaResult{}, e
				}
				if destroyed {
					out.PlanetsDestroyed++
				}
			}
		}
		if !redirected {
			break
		}
	}
	if a.Death == nil && w.HasMineEncounter(a.ID) {
		out.Aftermath, err = w.ResolveMinefield(a.ID, rng, now)
		if err != nil {
			return PlasmaResult{}, err
		}
	}
	out.TurnsSpent = initialTurns - a.Turns
	out.BoltsRemaining, out.TurnsRemaining = a.Plasma, a.Turns
	out.Destroyed = a.Death != nil
	out.SelfDestroyed = out.Destroyed && a.Death.Cause == "plasma" && a.Death.Killer == a.ID
	out.OwnFightersLost, out.OwnShieldsLost = beforeF-a.Fighters, beforeS-a.Shields
	return out, nil
}
