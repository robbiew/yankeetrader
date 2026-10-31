package game

import (
	"errors"
	"math"
	"reflect"
	"time"
)

const PlanetActionLifetime = 2 * time.Minute
const MaxGroundRounds = 4096

func (w *World) allocatePlanetGeneration() (uint64, error) {
	if w.NextPlanetGeneration < 101 || w.NextPlanetGeneration == math.MaxUint64 {
		return 0, errors.New("planet identity allocator exhausted")
	}
	n := w.NextPlanetGeneration
	w.NextPlanetGeneration++
	return n, nil
}

type PlanetRouteSector struct {
	Sector           Sector
	PlanetGeneration uint64
	DefenseTeam      int
}

// PlanetIntent keeps persisted state separate from its lazy economic projection.
// Store seals the complete snapshot to one live login and consumes it once.
type PlanetIntent struct {
	WandererCandidates []int
	Kind, Nonce        string
	Ship               TravelShip
	Planet             Planet
	OwnerTeam          int
	OwnerDead          bool
	Maintenance        string
	Path               []int
	Route              []PlanetRouteSector
	Quantity           int64
	QuotedAt           time.Time
}

type PlanetReceipt struct {
	Vanished                                                           bool
	LandingToken                                                       string
	Retreated                                                          int64
	Kind, Stop, Name                                                   string
	PlanetID, From, Destination, FinalSector, PlanetSector             int
	Destroyed, Captured, Adopted, Interrupted, HostileDefense          bool
	Hops, Rounds                                                       int
	TurnsSpent, TransportTurns, AftermathTurns, TurnsRemaining         int64
	FightersLost, FightersRemaining                                    int64
	Committed, AttackersLost, DefendersLost, Garrison, GroundRemaining int64
	Mines                                                              MineOutcome
}

func (w *World) vacantGovernor(planet *Planet) bool {
	if planet.Owner == 0 {
		return true
	}
	owner := w.Players[planet.Owner]
	return owner != nil && owner.Death != nil
}

func (w *World) PreparePlanetAction(id int, kind, token string, destination int, quantity int64, now time.Time) (PlanetIntent, error) {
	p, err := w.player(id)
	if err != nil {
		return PlanetIntent{}, err
	}
	if now.IsZero() || now.Before(w.Created) {
		return PlanetIntent{}, errors.New("invalid planet action clock")
	}
	if w.HasMineEncounter(id) {
		return PlanetIntent{}, ErrMineEncounter
	}
	if w.HostileDefense(id, p.Sector) {
		return PlanetIntent{}, ErrDefenseEncounter
	}
	planet := w.Planets[w.Sectors[p.Sector].Planet]
	if planet == nil || planet.Generation == 0 {
		return PlanetIntent{}, errors.New("no current planet here")
	}
	if now.Before(planet.Updated) {
		return PlanetIntent{}, errors.New("planet clock is ahead of this action")
	}
	projected := *planet
	projected.update(now, true)
	e := PlanetIntent{Kind: kind, Ship: w.travelShip(p), Planet: *planet, Maintenance: w.LastMaintenance, Quantity: quantity, QuotedAt: now.UTC()}
	if owner := w.Players[planet.Owner]; owner != nil {
		e.OwnerTeam = owner.Team
		e.OwnerDead = owner.Death != nil
	}
	switch kind {
	case "thrusters":
		if quantity != 0 || token == "" || token != p.PlanetToken || p.LandedPlanet != planet.ID || !w.allowed(p, &projected) {
			return PlanetIntent{}, errors.New("land again before using planetary thrusters")
		}
		// Both captured homes retain their independent restoration/HQ identity.
		if planet.FactionHome != "" {
			return PlanetIntent{}, errors.New("faction home planets cannot use thrusters, including after capture")
		}
		path, err := w.PlayerPath(id, p.Sector, destination)
		if err != nil {
			return PlanetIntent{}, err
		}
		if int64(len(path)-1) > p.Turns/10 {
			return PlanetIntent{}, errors.New("not enough turns: planetary thrusters cost 10 turns per hop")
		}
		e.Path = path
		if planet.Wanderer {
			e.WandererCandidates = w.wandererCandidates(planet.Sector)
		}
		// Include every outgoing edge of the chosen route and every reached hazard.
		// A new shorter path also changes the fresh path comparison at commit.
		for _, sid := range path {
			s := *w.Sectors[sid]
			s.Warps = append([]int(nil), s.Warps...)
			s.Minefield = append([]MineLayer(nil), s.Minefield...)
			team := 0
			if s.Defense != nil {
				d := *s.Defense
				s.Defense = &d
				if owner := w.Players[d.Owner]; owner != nil {
					team = owner.Team
				}
			}
			g := uint64(0)
			if other := w.Planets[s.Planet]; other != nil {
				g = other.Generation
			}
			e.Route = append(e.Route, PlanetRouteSector{s, g, team})
		}
	case "assault":
		if token != "" || destination != 0 || w.allowed(p, &projected) {
			return PlanetIntent{}, errors.New("ordinary landing is available; no assault is needed")
		}
		if w.vacantGovernor(planet) {
			if quantity != 0 {
				return PlanetIntent{}, errors.New("vacant government requires adoption, not a troop commitment")
			}
		} else if quantity < 1 || quantity > p.Ground || quantity > MaxQuantity {
			return PlanetIntent{}, errors.New("commit a positive whole ground force no greater than your stock")
		}
		if err := w.prepareNews(now); err != nil {
			return PlanetIntent{}, err
		}
	default:
		return PlanetIntent{}, errors.New("unknown planet action")
	}
	return e, nil
}

// CommitPlanetAction composes in one Store.Update. Physical collision and bounded
// battle exhaustion are saved outcomes. Invalid inputs/RNG abort the whole action.
func (w *World) CommitPlanetAction(e PlanetIntent, rng func() float64, now time.Time) (PlanetReceipt, error) {
	var out PlanetReceipt
	if now.Before(e.QuotedAt) || !now.Before(e.QuotedAt.Add(PlanetActionLifetime)) {
		return out, errors.New("planet confirmation expired; confirm again")
	}
	dest := 0
	if len(e.Path) > 0 {
		dest = e.Path[len(e.Path)-1]
	}
	fresh, err := w.PreparePlanetAction(e.Ship.Player, e.Kind, e.Ship.PlanetToken, dest, e.Quantity, e.QuotedAt)
	// Assault has no landing token, even if an obsolete grant remains on the ship.
	if e.Kind == "assault" {
		fresh, err = w.PreparePlanetAction(e.Ship.Player, e.Kind, "", 0, e.Quantity, e.QuotedAt)
	}
	if err != nil {
		return out, err
	}
	fresh.Nonce = e.Nonce
	if !reflect.DeepEqual(fresh, e) {
		return out, errors.New("planet, ship, permission or route changed; confirm again")
	}
	p := w.Players[e.Ship.Player]
	planet := w.Planets[e.Planet.ID]
	draw := func() (float64, error) {
		if rng == nil {
			return 0, errors.New("missing planetary RNG")
		}
		r := rng()
		if math.IsNaN(r) || math.IsInf(r, 0) || r < 0 || r >= 1 {
			return 0, errors.New("invalid planetary RNG")
		}
		return r, nil
	}
	out = PlanetReceipt{Stop: "destination", Kind: e.Kind, Name: planet.Name, PlanetID: planet.ID, From: p.Sector, FinalSector: p.Sector, PlanetSector: planet.Sector, Destination: dest}
	beforeTurns, beforeFighters := p.Turns, p.Fighters
	if e.Kind == "thrusters" {
		for _, to := range e.Path[1:] {
			r, err := draw()
			if err != nil {
				return PlanetReceipt{}, err
			}
			if w.Sectors[to].Planet != 0 || r > .995 {
				out.Destroyed = true
				out.Stop = "stress"
				if w.Sectors[to].Planet != 0 {
					out.Stop = "collision"
				}
				if p.Fighters > 0 {
					loss := p.Fighters
					for i := 0; i < 2; i++ {
						r, err = draw()
						if err != nil {
							return PlanetReceipt{}, err
						}
						loss = int64(r*float64(loss)) + 1
					}
					p.Fighters -= min(p.Fighters, loss)
				}
				w.destroyPlanet(planet)
				out.PlanetSector = 0
				break
			}
			planetTo := to
			if planet.Wanderer {
				planetTo, err = chooseWanderer(e.WandererCandidates, rng)
				if err != nil {
					return PlanetReceipt{}, err
				}
				out.Vanished = true
			}
			w.invalidatePlanetLandings(planet.ID)
			w.Sectors[planet.Sector].Planet = 0
			planet.Sector = planetTo
			w.Sectors[planetTo].Planet = planet.ID
			p.Sector = to
			p.DockToken = ""
			p.MineGraceSector = 0
			// Thruster turns do not invoke ordinary travel's cloak threshold.
			p.Turns -= 10
			out.TransportTurns += 10
			out.Hops++
			out.PlanetSector = planetTo
			if len(w.Sectors[to].Minefield) > 0 || w.HostileDefense(p.ID, to) {
				out.Stop = "defenses"
				out.Mines, err = w.ResolveMinefield(p.ID, rng, now)
				if err != nil {
					return PlanetReceipt{}, err
				}
				break
			}
			if planet.Wanderer {
				out.Stop = "wanderer"
				break
			}
		}
		// The mover and all other landed callers return to their sector interfaces.
		w.invalidatePlanetLandings(planet.ID)
	} else {
		if err := w.prepareNews(now); err != nil {
			return PlanetReceipt{}, err
		}
		projected := *planet
		projected.update(now, true)
		quoted := e.Planet
		quoted.update(e.QuotedAt, true)
		if projected.Ground != quoted.Ground {
			return PlanetReceipt{}, errors.New("planetary defenses changed with growth; confirm again")
		}
		*planet = projected
		oldGround := planet.Ground
		if w.vacantGovernor(planet) {
			a, err := draw()
			if err != nil {
				return PlanetReceipt{}, err
			}
			b, err := draw()
			if err != nil {
				return PlanetReceipt{}, err
			}
			planet.Ground = int64(float64(planet.Ground) * a * b)
			planet.Owner = p.ID
			out.DefendersLost = oldGround - planet.Ground
			out.Adopted = true
			out.Captured = true
		} else {
			attack, defense := e.Quantity, planet.Ground
			p.Ground -= attack
			out.Committed = attack
			for attack > 0 && defense > 0 && out.Rounds < MaxGroundRounds {
				selector, err := draw()
				if err != nil {
					return PlanetReceipt{}, err
				}
				magnitude, err := draw()
				if err != nil {
					return PlanetReceipt{}, err
				}
				if selector > .4 {
					attack = max(0, int64(math.Floor(float64(attack)-magnitude*float64(defense))))
				} else {
					defense = max(0, int64(math.Floor(float64(defense)-magnitude*float64(attack))))
				}
				out.Rounds++
			}
			out.AttackersLost = e.Quantity - attack
			out.Interrupted = attack > 0 && defense > 0
			if out.Interrupted {
				out.Retreated = attack
			}
			if defense == 0 && attack > 0 {
				planet.Ground = attack
				planet.Owner = p.ID
				out.Captured = true
			} else {
				planet.Ground = defense
			}
			// At the finite round limit surviving committed attackers retreat off-world;
			// they remain spent, not refunded or mislabeled as casualties.
			out.DefendersLost = oldGround - defense
		}
		w.invalidatePlanetLandings(planet.ID)
		out.Garrison = planet.Ground
		outcome := "defended"
		if out.Captured {
			outcome = "captured"
		}
		if out.Adopted {
			outcome = "adopted"
		}
		if out.Interrupted {
			outcome = "unfinished"
		}
		w.appendNews(NewsEvent{At: now.UTC(), Kind: NewsPlayerPlanet, Alias: p.Alias, PlanetName: planet.Name, Outcome: outcome, GroundCommitted: out.Committed, GroundRemaining: out.Garrison})
		if out.Captured {
			if err := w.Land(p.ID, now); err != nil {
				return PlanetReceipt{}, err
			}
			out.LandingToken = p.PlanetToken
		}
	}
	if e.Kind == "thrusters" && p.Death == nil {
		extra, err := w.ResolveMinefield(p.ID, rng, now)
		if err != nil {
			return PlanetReceipt{}, err
		}
		out.Mines = mergeMines(out.Mines, extra)
	}
	out.FinalSector = p.Sector
	out.TurnsSpent = beforeTurns - p.Turns
	out.AftermathTurns = out.TurnsSpent - out.TransportTurns
	out.TurnsRemaining = p.Turns
	out.FightersLost = beforeFighters - p.Fighters
	out.FightersRemaining = p.Fighters
	out.GroundRemaining = p.Ground
	out.HostileDefense = p.Death == nil && w.HostileDefense(p.ID, p.Sector)
	return out, nil
}

// LandingTarget projects access defenses for the denied-LAND prompt without saving.
func (w *World) LandingTarget(id int, now time.Time) (Planet, bool, error) {
	p, err := w.player(id)
	if err != nil {
		return Planet{}, false, err
	}
	planet := w.Planets[w.Sectors[p.Sector].Planet]
	if planet == nil {
		return Planet{}, false, errors.New("no planet here")
	}
	projected := *planet
	projected.update(now, true)
	return projected, w.vacantGovernor(planet), nil
}

// CheckLandingPreview binds troop selection to the identity and defenses the
// caller saw before answering consent/quantity prompts. Project only the new
// sealed snapshot, so elapsed economic growth is checked without saving it.
func (e PlanetIntent) CheckLandingPreview(target Planet, adopt bool) error {
	current := e.Planet
	current.update(e.QuotedAt, true)
	if e.Kind != "assault" || current.ID != target.ID || current.Generation != target.Generation || current.Sector != target.Sector || current.Name != target.Name || current.Owner != target.Owner || current.Ground != target.Ground || (current.Owner == 0 || e.OwnerDead) != adopt {
		return errors.New("planet or defenses changed while choosing troops; land again and reconsider your commitment")
	}
	return nil
}
