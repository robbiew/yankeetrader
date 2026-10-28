package game

import (
	"errors"
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
}
type MissileImpact struct {
	Target                                      int
	Launched, MinesDestroyed, Dropped, Disarmed int64
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
	if len(w.Sectors[a.Sector].Minefield) > 0 {
		return MissileIntent{}, ErrMineEncounter
	}
	// Return fire reaches this sector too. Until its interception rules are
	// supported, refuse the whole exchange before charging ammo or turns.
	origin := w.Sectors[a.Sector]
	if origin.Planet != 0 || origin.Defense != nil {
		return MissileIntent{}, errors.New("missile return path through planets or sector fighters is not available yet")
	}
	target := w.Sectors[to]
	if target == nil || to == a.Sector || !contains(w.Sectors[a.Sector].Warps, to) || !contains(target.Warps, a.Sector) {
		return MissileIntent{}, errors.New("choose a different sector linked in both directions by one warp")
	}
	if target.Defense != nil || target.Planet != 0 {
		return MissileIntent{}, errors.New("sector fighter interception and planet bombardment are not available yet")
	}
	if a.Turns < 1 {
		return MissileIntent{}, errors.New("no turns left today")
	}
	if count < 1 || count > a.Missiles {
		return MissileIntent{}, errors.New("choose available missiles to launch")
	}
	intent := MissileIntent{Player: id, From: a.Sector, To: to, Generation: a.ShipGeneration, Count: count, Mines: append([]MineLayer(nil), target.Minefield...)}
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
	if intent.Target == 0 && len(intent.Mines) == 0 {
		return MissileIntent{}, errors.New("no visible enemy ship or minefield in that sector")
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
	if fresh.From != intent.From || fresh.Target != intent.Target || fresh.TargetGeneration != intent.TargetGeneration || !slices.Equal(fresh.Mines, intent.Mines) {
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
	out.MinesDestroyed = w.interceptMines(sector, count)
	remaining := count - out.MinesDestroyed
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
