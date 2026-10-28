package game

import (
	"crypto/rand"
	"encoding/hex"
	"errors"
	"math"
	"math/big"
	"strings"
	"time"
)

// Nonfinancial production/stocks retain fractions. Spendable credits never use floats.
type Planet struct {
	ID, Sector, Owner                 int
	Name                              string
	Updated                           time.Time
	Production, Cargo                 [3]float64
	Fighters, Missiles, Mines, Plasma float64
	Ground, Bank                      int64
}

func (w *World) Upgrade() error {
	if w.Version == 1 {
		if len(w.Planets) != 0 {
			return errors.New("version-one world unexpectedly contains planets")
		}
		w.Planets = map[int]*Planet{}
		w.Version = 2
	}
	if w.Version == 2 {
		if len(w.Teams) != 0 {
			return errors.New("version-two world unexpectedly contains teams")
		}
		for _, p := range w.Players {
			if p != nil && p.Team != 0 {
				return errors.New("legacy team membership has no team metadata; refusing to invent invitations or captains")
			}
		}
		w.Teams = map[int]*Team{}
		w.Version = 3
	}
	if w.Version == 3 {
		for _, p := range w.Players {
			if p != nil && (p.ShipGeneration != 0 || p.Death != nil) {
				return errors.New("version-three world unexpectedly contains ship lifecycle state")
			}
		}
		w.Version = 4
	}
	if w.Version == 4 {
		for _, s := range w.Sectors {
			if s != nil && s.Defense != nil {
				return errors.New("version-four world unexpectedly contains sector defenses")
			}
		}
		w.Version = 5
	}
	if w.Version == 5 {
		for _, p := range w.Players {
			if p != nil && p.Cloak != 0 {
				return errors.New("version-five world unexpectedly contains cloak energy")
			}
		}
		w.Version = 6
	}
	if w.Version == 6 {
		for _, p := range w.Players {
			if p != nil && ((p.Death != nil && p.Death.Cause == "mines") || (p.Death == nil && p.Holds < 10)) {
				return errors.New("version-six world unexpectedly contains mine lifecycle state")
			}
		}
		for _, s := range w.Sectors {
			if s != nil && len(s.Minefield) > 0 {
				return errors.New("version-six world unexpectedly contains minefields")
			}
		}
		w.Version = 7
	}
	if w.Version == 7 {
		for _, p := range w.Players {
			if p != nil && (p.StoredScore != 0 || (p.Death != nil && p.Death.Cause == "missile")) {
				return errors.New("version-seven world unexpectedly contains missile state")
			}
		}
		w.Version = 8
	}
	if w.Version == 8 {
		w.Version = 9
	}
	return nil
}
func (w *World) validatePlanets() error {
	if len(w.Planets) > 99 {
		return errors.New("too many planets")
	}
	for _, p := range w.Players {
		if p.Team < 0 || p.Team > 50 || p.Missiles < 0 || p.Missiles > MaxQuantity || p.Mines < 0 || p.Mines > MaxQuantity || p.Plasma < 0 || p.Plasma > MaxQuantity {
			return errors.New("invalid player planet inventory")
		}
		if p.PlanetToken != "" {
			planet := w.Planets[p.LandedPlanet]
			_, err := hex.DecodeString(p.PlanetToken)
			if planet == nil || planet.Sector != p.Sector || len(p.PlanetToken) != 32 || err != nil || p.DockToken != "" {
				return errors.New("invalid landing session")
			}
		} else if p.LandedPlanet != 0 {
			return errors.New("landing has no token")
		}
	}
	for _, s := range w.Sectors {
		if s.Planet != 0 {
			p := w.Planets[s.Planet]
			if p == nil || p.Sector != s.ID {
				return errors.New("invalid planet link")
			}
		}
	}
	for id, p := range w.Planets {
		if p == nil || id < 2 || id > 100 || p.ID != id || !clean(p.Name) || p.Updated.IsZero() || w.Sectors[p.Sector] == nil || w.Sectors[p.Sector].Planet != id || p.Owner < 0 || (p.Owner != 0 && w.Players[p.Owner] == nil) || p.Bank < 0 || p.Bank > MaxMoney || p.Ground < 0 || p.Ground > MaxQuantity {
			return errors.New("invalid planet")
		}
		for _, x := range append(append([]float64{}, p.Production[:]...), append(p.Cargo[:], p.Fighters, p.Missiles, p.Mines, p.Plasma)...) {
			if math.IsNaN(x) || math.IsInf(x, 0) || x < 0 || x > float64(MaxQuantity) {
				return errors.New("invalid planet production or inventory")
			}
		}
	}
	return nil
}
func (w *World) CreatePlanet(id int, name string, now time.Time) error {
	p, e := w.player(id)
	if e != nil {
		return e
	}
	name = strings.TrimSpace(name)
	if !clean(name) {
		return errors.New("use a printable planet name of 1 to 41 characters")
	}
	if w.Sectors[p.Sector].Planet != 0 {
		return errors.New("there is already a planet here")
	}
	if p.Credits < 25000 {
		return errors.New("planets cost 25000 credits")
	}
	slot := 2
	for slot <= 100 && w.Planets[slot] != nil {
		slot++
	}
	if slot > 100 {
		return errors.New("all planet slots are occupied")
	}
	planet := &Planet{ID: slot, Sector: p.Sector, Owner: id, Name: name, Updated: now.UTC(), Production: [3]float64{1, 1, 1}, Cargo: [3]float64{10, 10, 10}, Fighters: 30, Ground: 1}
	w.Planets[slot] = planet
	w.Sectors[p.Sector].Planet = slot
	p.Credits -= 25000
	p.DockToken = ""
	p.PlanetToken = ""
	p.LandedPlanet = 0
	return nil
}
func (w *World) allowed(p *Player, planet *Planet) bool {
	if planet.Ground == 0 || planet.Owner == p.ID {
		return true
	}
	owner := w.Players[planet.Owner]
	return owner != nil && p.Team != 0 && w.Teams[p.Team] != nil && p.Team == owner.Team
}
func (w *World) Land(id int, now time.Time) error {
	p, e := w.player(id)
	if e != nil {
		return e
	}
	planet := w.Planets[w.Sectors[p.Sector].Planet]
	if planet == nil {
		return errors.New("no planet here; CREATE <name> costs 25000 credits")
	}
	planet.update(now, true)
	if !w.allowed(p, planet) {
		return errors.New("permission to land is denied by ground defenses")
	}
	token := make([]byte, 16)
	if _, e = rand.Read(token); e != nil {
		return e
	}
	p.PlanetToken = hex.EncodeToString(token)
	p.LandedPlanet = planet.ID
	p.DockToken = ""
	return nil
}
func (w *World) landed(id int, token string, now time.Time) (*Player, *Planet, error) {
	p, e := w.player(id)
	if e != nil {
		return nil, nil, e
	}
	planet := w.Planets[p.LandedPlanet]
	if token == "" || token != p.PlanetToken || planet == nil || planet.Sector != p.Sector || w.Sectors[p.Sector].Planet != planet.ID {
		return nil, nil, errors.New("land again; this landing session is no longer current")
	}
	planet.update(now, true)
	if !w.allowed(p, planet) {
		return nil, nil, errors.New("planet access has changed; landing permission is denied")
	}
	return p, planet, nil
}
func limited(x float64) float64 { return math.Min(float64(MaxQuantity), math.Max(0, x)) }

// Exact integer interest: floor(bank * elapsedNanoseconds / (100 * dayNanoseconds)).
func interest(bank int64, elapsed time.Duration) int64 {
	n := new(big.Int).Mul(big.NewInt(bank), big.NewInt(int64(elapsed)))
	n.Quo(n, big.NewInt(int64(100*24*time.Hour)))
	return n.Int64()
}
func (p *Planet) update(now time.Time, lazy bool) {
	if now.Before(p.Updated) || (!lazy && !now.After(p.Updated)) {
		return
	}
	elapsed := now.Sub(p.Updated)
	if elapsed > 10*24*time.Hour {
		elapsed = 10 * 24 * time.Hour
	}
	d := float64(elapsed) / float64(24*time.Hour)
	old := p.Production
	bank := p.Bank
	total := old[0] + old[1] + old[2]
	bonuses := [3]float64{float64(bank) / 10000, float64(bank) / 20000, float64(bank) / 30000}
	for i := 0; i < 3; i++ {
		base := old[i]
		if lazy {
			base *= 1 + .01*d
		}
		rate := base + bonuses[i]
		p.Cargo[i] = limited(p.Cargo[i] + rate*d)
		if lazy {
			if p.Cargo[i] > 10*rate {
				base = p.Cargo[i] / 10
			}
		} else {
			base = math.Max(base, p.Cargo[i]/10) * (1 + .01*d)
		}
		p.Production[i] = limited(base)
	}
	p.Fighters = limited(p.Fighters + (math.Floor(total)+float64(bank)/500)*d)
	p.Missiles = limited(p.Missiles + (math.Floor(total/2500)+float64(bank)/100000)*d)
	p.Mines = limited(p.Mines + (math.Floor(total/25000)+float64(bank)/250000)*d)
	p.Plasma = limited(p.Plasma + (math.Floor(total/100000)+float64(bank)/25000000)*d)
	p.Ground = int64(limited(math.Floor(float64(p.Ground)*(1+.01*d) + float64(bank)/10000*d)))
	earned := interest(bank, elapsed)
	if earned > MaxMoney-bank {
		earned = MaxMoney - bank
	}
	p.Bank += earned
	p.Updated = now.UTC()
}
func (w *World) Bank(id int, token string, target int64, now time.Time) error {
	p, planet, e := w.landed(id, token, now)
	if e != nil {
		return e
	}
	if target < 0 || target > MaxMoney {
		return errors.New("bank target must be between zero and the account limit")
	}
	total := p.Credits + planet.Bank
	if target > total {
		return errors.New("not enough credits for that account balance")
	}
	cash := total - target
	if cash > MaxMoney {
		return errors.New("ship credit limit exceeded")
	}
	p.Credits = cash
	planet.Bank = target
	// The DOS planet menu immediately reevaluates bank-dependent surplus rates.
	planet.update(now, true)
	return nil
}
func (w *World) Invest(id int, token string, amount int64, now time.Time) error {
	p, planet, e := w.landed(id, token, now)
	if e != nil {
		return e
	}
	if amount < 1 || amount > p.Credits {
		return errors.New("enter a positive expenditure within your credits")
	}
	delta := float64(amount) / 250
	for _, x := range planet.Production {
		if x+delta > float64(MaxQuantity) {
			return errors.New("production limit exceeded")
		}
	}
	for i := 0; i < 3; i++ {
		planet.Production[i] += delta
	}
	p.Credits -= amount
	return nil
}
func (w *World) Take(id int, token, kind string, qty int64, now time.Time) error {
	p, planet, e := w.landed(id, token, now)
	if e != nil {
		return e
	}
	if qty < 1 || qty > MaxQuantity {
		return errors.New("enter a positive whole quantity")
	}
	i := -1
	for j, n := range Goods {
		if n == kind {
			i = j
		}
	}
	if i >= 0 {
		free := p.Holds - p.Cargo[0] - p.Cargo[1] - p.Cargo[2]
		if qty > free || float64(qty) > math.Floor(planet.Cargo[i]) {
			return errors.New("not enough cargo or free holds")
		}
		p.Cargo[i] += qty
		planet.Cargo[i] -= float64(qty)
		return nil
	}
	ship, stock := resource(p, planet, kind)
	if ship == nil {
		return errors.New("unknown planet item")
	}
	if qty > MaxQuantity-*ship || float64(qty) > math.Floor(*stock) {
		return errors.New("not enough stock or ship capacity")
	}
	*ship += qty
	*stock -= float64(qty)
	return nil
}
func resource(p *Player, planet *Planet, kind string) (*int64, *float64) {
	switch kind {
	case "fighters":
		return &p.Fighters, &planet.Fighters
	case "missiles":
		return &p.Missiles, &planet.Missiles
	case "mines":
		return &p.Mines, &planet.Mines
	case "plasma":
		return &p.Plasma, &planet.Plasma
	}
	return nil, nil
}
func (w *World) TakeAll(id int, token string, now time.Time) error {
	p, planet, e := w.landed(id, token, now)
	if e != nil {
		return e
	}
	for _, kind := range []string{"fighters", "missiles", "mines", "plasma"} {
		ship, stock := resource(p, planet, kind)
		q := int64(math.Floor(*stock))
		if q > MaxQuantity-*ship {
			q = MaxQuantity - *ship
		}
		*ship += q
		*stock -= float64(q)
	}
	free := p.Holds - p.Cargo[0] - p.Cargo[1] - p.Cargo[2]
	for _, i := range []int{2, 1, 0} {
		q := int64(math.Floor(planet.Cargo[i]))
		if q > free {
			q = free
		}
		p.Cargo[i] += q
		planet.Cargo[i] -= float64(q)
		free -= q
	}
	return nil
}
func (w *World) Transfer(id int, token, kind string, qty int64, now time.Time) error {
	p, planet, e := w.landed(id, token, now)
	if e != nil {
		return e
	}
	if kind == "cargo" {
		if p.Cargo[0]+p.Cargo[1]+p.Cargo[2] == 0 {
			return errors.New("no cargo aboard")
		}
		for i := 0; i < 3; i++ {
			if planet.Cargo[i]+float64(p.Cargo[i]) > float64(MaxQuantity) {
				return errors.New("planet warehouse is full")
			}
		}
		for i := 0; i < 3; i++ {
			combined := planet.Cargo[i] + float64(p.Cargo[i])
			if combined > 10*planet.Production[i] {
				planet.Production[i] = math.Floor(combined)/10 + 1
			}
			planet.Cargo[i] = combined
			p.Cargo[i] = 0
		}
		return nil
	}
	ship, stock := resource(p, planet, kind)
	if ship == nil {
		return errors.New("unknown planet item")
	}
	if qty == 0 {
		qty = *ship
	}
	if qty < 1 || qty > *ship {
		return errors.New("not enough carried items")
	}
	if *stock+float64(qty) > float64(MaxQuantity) {
		return errors.New("planet warehouse is full")
	}
	*ship -= qty
	*stock += float64(qty)
	return nil
}
func (w *World) Garrison(id int, token string, target int64, now time.Time) error {
	p, planet, e := w.landed(id, token, now)
	if e != nil {
		return e
	}
	total := p.Ground + planet.Ground
	if target < 0 || target > MaxQuantity || target > total || total-target > MaxQuantity {
		return errors.New("invalid target garrison")
	}
	p.Ground = total - target
	planet.Ground = target
	if target == 0 {
		planet.Owner = 0
	} else {
		planet.Owner = id
	}
	return nil
}

func (w *World) PlanetStatus(id int, token string, now time.Time) (Planet, error) {
	_, planet, e := w.landed(id, token, now)
	if e != nil {
		return Planet{}, e
	}
	return *planet, nil
}
