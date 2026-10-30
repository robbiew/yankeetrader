package game

import (
	"crypto/rand"
	"encoding/hex"
	"errors"
	"fmt"
	"math"
	prng "math/rand"
	"strings"
	"time"
)

const MaxMoney int64 = 9_000_000_000_000_000
const MaxQuantity int64 = 1_000_000_000

// WorldVersion is the current persisted schema, independent of the app release.
const WorldVersion = 23

var Goods = [3]string{"ore", "organics", "equipment"}

type Player struct {
	LotteryDay                                       string         `json:",omitempty"`
	LotteryPlays                                     int            `json:",omitempty"`
	LotterySequence                                  uint64         `json:",omitempty"`
	DangerScanner                                    bool           `json:",omitempty"`
	WarpSequence                                     uint64         `json:",omitempty"`
	LastActivity                                     string         `json:",omitempty"`
	RetiredAt                                        time.Time      `json:",omitempty"`
	BattleReports                                    []BattleReport `json:",omitempty"`
	MineGraceSector                                  int            `json:",omitempty"`
	StoredScore                                      int64          `json:",omitempty"`
	Cloak                                            float64        `json:",omitempty"`
	ShipGeneration                                   uint64         `json:",omitempty"`
	Death                                            *Death         `json:",omitempty"`
	ID                                               int
	Identity, Alias                                  string
	Sector                                           int
	Credits, Turns, Holds, Fighters, Shields, Ground int64
	Cargo                                            [3]int64
	DockToken                                        string
	PlanetToken                                      string
	LandedPlanet, Team                               int
	Missiles, Mines, Plasma                          int64
	DockUntil                                        time.Time
	DockPrices                                       [3]int64
	LastLogin                                        string `json:",omitempty"`
	AvoidSectors                                     []int  `json:",omitempty"`
}
type Sector struct {
	Minefield []MineLayer    `json:",omitempty"`
	Defense   *SectorDefense `json:",omitempty"`
	ID        int
	Warps     []int
	Port      int
	Planet    int
}
type Port struct {
	ID, Sector         int
	Name               string
	Owner              int
	Treasury           int64
	Supply, Production [3]float64
	Coefficient        [3]float64
	Updated            time.Time
}
type World struct {
	Season            uint64
	GenerationSeed    *int64         `json:",omitempty"`
	GenesisPorts      *int           `json:",omitempty"`
	SeasonResults     []SeasonResult `json:",omitempty"`
	LotteryDailyLimit *int           `json:",omitempty"`
	NextBattleReport  uint64
	Xannor            *XannorState `json:",omitempty"`
	News              []NewsEvent  `json:",omitempty"`
	NextNews          uint64

	Radio           []RadioMessage `json:",omitempty"`
	NextRadio       uint64
	Version         int
	Created         time.Time
	LastMaintenance string
	NextPlayer      int
	Players         map[int]*Player
	Sectors         map[int]*Sector
	Ports           map[int]*Port
	Planets         map[int]*Planet
	Teams           map[int]*Team
}

func New(now time.Time, seed int64, count int) (*World, error) {
	if count < 8 || count > 3000 {
		return nil, errors.New("sector count must be between 8 and 3000")
	}
	w := &World{Season: 1, GenerationSeed: &seed, Version: WorldVersion, NextBattleReport: 1, NextNews: 1, NextRadio: 1, Teams: map[int]*Team{}, Planets: map[int]*Planet{}, Created: now.UTC(), LastMaintenance: day(now), NextPlayer: 1, Players: map[int]*Player{}, Sectors: map[int]*Sector{}, Ports: map[int]*Port{}}
	rng := prng.New(prng.NewSource(seed))
	for i := 1; i <= count; i++ {
		prev, next := (i+count-2)%count+1, i%count+1
		s := &Sector{ID: i, Warps: []int{prev, next}}
		w.Sectors[i] = s
		// Finite partial shuffle: four distinct extra destinations without rejection sampling.
		choices := make([]int, 0, count-3)
		for n := 1; n <= count; n++ {
			if n != i && n != prev && n != next {
				choices = append(choices, n)
			}
		}
		for j := 0; j < 4; j++ {
			k := j + rng.Intn(len(choices)-j)
			choices[j], choices[k] = choices[k], choices[j]
			s.Warps = append(s.Warps, choices[j])
		}
		if i <= 1000 {
			s.Port = i
			p := &Port{ID: i, Sector: i, Name: fmt.Sprintf("Port %d", i), Updated: now.UTC(), Supply: [3]float64{1000, 1000, 1000}, Production: [3]float64{100, 100, 100}, Coefficient: [3]float64{-50, -50, -50}}
			p.Coefficient[(i+1)%3] = 50
			w.Ports[i] = p
		}
	}
	w.Ports[1].Name = "Earth"
	return w, w.Validate()
}
func contains(xs []int, n int) bool {
	for _, x := range xs {
		if x == n {
			return true
		}
	}
	return false
}
func day(t time.Time) string { return t.UTC().Format("2006-01-02") }
func clean(s string) bool {
	if len(s) < 1 || len(s) > 41 {
		return false
	}
	for _, r := range s {
		if r < 32 || r > 126 {
			return false
		}
	}
	return true
}
func (w *World) Validate() error {
	if w.Players == nil || w.Sectors == nil || w.Ports == nil || w.Planets == nil || w.Version != WorldVersion || len(w.Sectors) < 8 || len(w.Players) > MaxPlayerIdentities || w.activePlayers() > MaxActivePlayers || w.NextPlayer < 1 || w.NextPlayer > MaxPlayerIdentities+1 || len(w.Sectors) > 3000 || w.Sectors[1] == nil || w.Ports[1] == nil || w.Ports[1].Sector != 1 || w.Created.IsZero() {
		return errors.New("invalid world header")
	}
	if _, err := time.Parse("2006-01-02", w.LastMaintenance); err != nil {
		return errors.New("invalid maintenance date")
	}
	if err := w.validateSeasons(); err != nil {
		return err
	}
	if err := w.validateLottery(); err != nil {
		return err
	}
	if err := w.validateLifecycle(); err != nil {
		return err
	}
	ids := map[string]bool{}
	for id, p := range w.Players {
		if p == nil || p.ID != id || id < 1 || id >= w.NextPlayer || !clean(p.Alias) || p.Identity == "" || len(p.Identity) > 256 || ids[p.Identity] || (p.Death == nil && w.Sectors[p.Sector] == nil) {
			return errors.New("invalid player identity or position")
		}
		ids[p.Identity] = true
		if p.LastActivity != "" {
			if _, err := time.Parse("2006-01-02", p.LastActivity); err != nil {
				return errors.New("invalid last activity date")
			}
		}
		if p.LastLogin != "" {
			if _, err := time.Parse("2006-01-02", p.LastLogin); err != nil {
				return errors.New("invalid last login date")
			}
		}

		if len(p.AvoidSectors) > 30 {
			return errors.New("too many sectors to avoid")
		}
		for _, sector := range p.AvoidSectors {
			if sector != 0 && w.Sectors[sector] == nil {
				return errors.New("invalid sector to avoid")
			}
		}

		if p.StoredScore < -MaxMoney || p.StoredScore > MaxMoney {
			return errors.New("invalid stored score")
		}
		if math.IsNaN(p.Cloak) || math.IsInf(p.Cloak, 0) || p.Cloak < 0 || p.Cloak > 1 {
			return errors.New("invalid cloak energy")
		}
		if p.Credits < 0 || p.Credits > MaxMoney || p.Turns < 0 || p.Turns > 500 || (p.Holds < 1 && p.Death == nil) || p.Holds < 0 || p.Holds > 1000 || p.Fighters < 0 || p.Fighters > MaxQuantity || p.Shields < 0 || p.Shields > MaxQuantity || p.Ground < 0 || p.Ground > MaxQuantity {
			return errors.New("invalid player assets")
		}
		if p.DockToken != "" {
			if _, err := hex.DecodeString(p.DockToken); err != nil || len(p.DockToken) != 32 || p.DockUntil.IsZero() || w.Ports[w.Sectors[p.Sector].Port] == nil {
				return errors.New("invalid docking session")
			}
			for _, price := range p.DockPrices {
				if price < 1 || price > 1_000_000 {
					return errors.New("invalid docking price")
				}
			}
		}
		used := int64(0)
		for _, q := range p.Cargo {
			if q < 0 || q > 1000 {
				return errors.New("invalid cargo")
			}
			used += q
		}
		if used > p.Holds {
			return errors.New("cargo exceeds holds")
		}
	}
	for id, s := range w.Sectors {
		if s == nil || s.ID != id || id < 1 {
			return errors.New("invalid sector")
		}
		for _, to := range s.Warps {
			if to == id || w.Sectors[to] == nil {
				return errors.New("invalid warp")
			}
		}
		if s.Port != 0 {
			p := w.Ports[s.Port]
			if p == nil || p.Sector != id {
				return errors.New("invalid port link")
			}
		}
	}
	for id, p := range w.Ports {
		if p == nil || p.ID != id || w.Sectors[p.Sector] == nil || w.Sectors[p.Sector].Port != id || !clean(p.Name) || p.Updated.IsZero() || p.Treasury < 0 || p.Treasury > MaxMoney || p.Owner < 0 || (p.Owner != 0 && (w.Players[p.Owner] == nil || !w.Players[p.Owner].RetiredAt.IsZero())) {
			return errors.New("invalid port")
		}
		if id == 1 && p.Owner != 0 {
			return errors.New("Earth cannot be owned")
		}
		for i := 0; i < 3; i++ {
			for _, v := range []float64{p.Supply[i], p.Production[i], p.Coefficient[i]} {
				if math.IsNaN(v) || math.IsInf(v, 0) {
					return errors.New("non-finite economy")
				}
			}
			if p.Supply[i] < 0 || p.Supply[i] > 1e12 || p.Production[i] < 1 || p.Supply[i] > p.Production[i]*10*(1+1e-12) || p.Production[i] > 1e12 || math.Abs(p.Coefficient[i]) > 100 || p.Coefficient[i] == 0 {
				return errors.New("invalid port economy")
			}
		}
	}
	if err := w.validateXannor(); err != nil {
		return err
	}
	if err := w.validateMines(); err != nil {
		return err
	}
	if err := w.validateDefenses(); err != nil {
		return err
	}
	if err := w.validateTeams(); err != nil {
		return err
	}
	if err := w.validatePlanets(); err != nil {
		return err
	}
	if err := w.validateRadio(); err != nil {
		return err
	}
	if err := w.validateBattleReports(); err != nil {
		return err
	}
	return w.validateNews()
}
func (w *World) Join(identity, alias string) (*Player, error) {
	alias = strings.TrimSpace(alias)
	if identity == "" || !clean(alias) {
		return nil, errors.New("use a printable name of 1 to 41 characters")
	}
	for _, p := range w.Players {
		if p.Identity == identity {
			p.Alias = alias
			return p, nil
		}
	}
	if w.activePlayers() >= MaxActivePlayers {
		return nil, errors.New("all player slots are occupied")
	}
	if w.NextPlayer > MaxPlayerIdentities {
		return nil, errors.New("player identity archive is full; identities are never reassigned")
	}
	p := &Player{Cloak: 1, ID: w.NextPlayer, Identity: identity, Alias: alias, Sector: 1, Credits: 1005, Turns: 500, Holds: 10, Fighters: 25}
	w.NextPlayer++
	w.Players[p.ID] = p
	return p, nil
}
func (w *World) player(id int) (*Player, error) {
	p := w.Players[id]
	if p == nil {
		return nil, errors.New("player no longer exists")
	}
	if p.Death != nil {
		return nil, ErrShipDestroyed
	}
	return p, nil
}
func (w *World) Move(id, to int) error {
	p, err := w.player(id)
	if err != nil {
		return err
	}
	if err = w.canMove(p, to); err != nil {
		return err
	}
	if len(w.Sectors[to].Minefield) > 0 {
		return errors.New("minefield ahead; confirm entry manually")
	}
	w.move(p, to)
	return nil
}
func (w *World) canMoveBase(p *Player, to int) error {
	if w.HostileDefense(p.ID, p.Sector) {
		return ErrDefenseEncounter
	}
	if w.HasMineEncounter(p.ID) {
		return ErrMineEncounter
	}
	if !contains(w.Sectors[p.Sector].Warps, to) {
		return errors.New("that sector is not an adjacent warp")
	}
	if p.Turns < 1 {
		return errors.New("no turns left today")
	}
	return nil
}
func (w *World) canMove(p *Player, to int) error {
	if err := w.canMoveBase(p, to); err != nil {
		return err
	}
	if defense := w.Sectors[to].Defense; defense != nil && defense.Owner != p.ID {
		owner := w.Players[defense.Owner]
		if owner == nil || p.Team == 0 || owner.Team != p.Team {
			return errors.New("hostile sector fighters block this warp; use BRIBE <sector> <credits> or BREACH")
		}
	}
	return nil
}
func (w *World) move(p *Player, to int) {
	p.MineGraceSector = 0
	p.Sector = to
	p.spendTurn()
	p.DockToken = ""
	p.PlanetToken = ""
	p.LandedPlanet = 0
}

func update(p *Port, now time.Time) {
	if !now.After(p.Updated) {
		return
	}
	elapsed := math.Min(now.Sub(p.Updated).Hours()/24, 10)
	for i := 0; i < 3; i++ {
		p.Supply[i] = math.Min(1e12, p.Supply[i]+p.Production[i]*elapsed)
		p.Production[i] = math.Max(p.Production[i], p.Supply[i]/10)
	}
	p.Updated = now.UTC()
}
func Price(p *Port, i int) int64 {
	base := [3]float64{20, 30, 40}
	return int64(math.Max(1, math.Floor(base[i]*(1-p.Coefficient[i]*p.Supply[i]/(p.Production[i]*1000))+.5)))
}
func (w *World) Dock(id int, now time.Time) error {
	p, e := w.player(id)
	if e != nil {
		return e
	}
	port := w.Ports[w.Sectors[p.Sector].Port]
	if port == nil {
		return errors.New("no port here")
	}
	if p.Turns < 1 {
		return errors.New("no turns left today")
	}
	token := make([]byte, 16)
	if _, e = rand.Read(token); e != nil {
		return e
	}
	update(port, now)
	p.spendTurn()
	p.PlanetToken = ""
	p.LandedPlanet = 0
	p.DockToken = hex.EncodeToString(token)
	p.DockUntil = now.Add(5 * time.Minute).UTC()
	for i := 0; i < 3; i++ {
		p.DockPrices[i] = Price(port, i)
	}
	return nil
}
func (w *World) docked(id int, token string, now time.Time) (*Player, *Port, error) {
	p, e := w.player(id)
	if e != nil {
		return nil, nil, e
	}
	if token == "" || p.DockToken != token || !now.Before(p.DockUntil) {
		return nil, nil, errors.New("dock again; this docking session is no longer current")
	}
	port := w.Ports[w.Sectors[p.Sector].Port]
	if port == nil {
		return nil, nil, errors.New("no port here")
	}
	return p, port, nil
}
func (w *World) Trade(id int, token string, buy bool, i int, q int64, now time.Time) error {
	p, port, e := w.docked(id, token, now)
	if e != nil {
		return e
	}
	if port.ID == 1 {
		return errors.New("Earth sells ship equipment; trade cargo at other ports")
	}
	if i < 0 || i > 2 || q < 1 || q > MaxQuantity {
		return errors.New("enter a positive whole quantity")
	}
	if (port.Coefficient[i] > 0) != buy {
		return errors.New("this port does not trade that commodity in that direction")
	}
	if float64(q) > port.Supply[i] {
		return errors.New("port supply or demand is exhausted")
	}
	price := p.DockPrices[i]
	if price < 1 || price > 1_000_000 {
		return errors.New("invalid price; dock again")
	}
	cost := q * price
	if buy {
		if q > p.Holds-p.Cargo[0]-p.Cargo[1]-p.Cargo[2] {
			return errors.New("not enough cargo holds")
		}
		if cost > p.Credits {
			return errors.New("not enough credits")
		}
		commission := int64(0)
		if port.Owner != 0 {
			commission = cost
			if port.Owner == id {
				commission = cost / 100
			}
		}
		if port.Treasury > MaxMoney-commission {
			return errors.New("port account is full")
		}
		p.Credits -= cost
		p.Cargo[i] += q
		port.Treasury += commission
	} else {
		if q > p.Cargo[i] {
			return errors.New("not enough cargo")
		}
		if p.Credits > MaxMoney-cost {
			return errors.New("credit limit exceeded")
		}
		p.Credits += cost
		p.Cargo[i] -= q
	}
	port.Supply[i] -= float64(q)
	return nil
}
func (w *World) Equip(id int, token, item string, q int64, now time.Time) error {
	p, port, e := w.docked(id, token, now)
	if e != nil {
		return e
	}
	if port.ID != 1 {
		return errors.New("ship equipment is sold at Earth")
	}
	if q < 1 || q > MaxQuantity {
		return errors.New("enter a positive whole quantity")
	}
	if item == "cloak" {
		if now.IsZero() || now.Before(w.Created) {
			return errors.New("invalid cloak purchase clock")
		}
		if q > cloakCapacity(p) {
			return ErrCloakCapacity
		}
		cost := q * CloakPointPrice
		if p.Credits < cost {
			return errors.New("not enough credits for cloak energy")
		}
		p.Credits -= cost
		p.Cloak = math.Min(1, p.Cloak+float64(q)/100)
		return nil
	}
	if item == "scanner" {
		if q != 1 {
			return errors.New("buy one danger scanner")
		}
		if p.DangerScanner {
			return errors.New("danger scanner is already installed")
		}
		if p.Credits < DangerScannerPrice {
			return errors.New("not enough credits for danger scanner")
		}
		p.Credits -= DangerScannerPrice
		p.DangerScanner = true
		return nil
	}
	var asset *int64
	var price, limit int64
	switch item {
	case "holds":
		asset = &p.Holds
		price = 500
		limit = 1000
	case "fighters":
		asset = &p.Fighters
		price = 100
		limit = MaxQuantity
	case "shields":
		asset = &p.Shields
		price = 50
		limit = MaxQuantity
	case "forces":
		asset = &p.Ground
		price = 750
		limit = MaxQuantity
	default:
		return errors.New("choose holds, fighters, shields, forces, scanner, or cloak")
	}
	if q > limit-*asset {
		return errors.New("equipment limit exceeded")
	}
	cost := q * price
	if cost > p.Credits {
		return errors.New("not enough credits")
	}
	p.Credits -= cost
	*asset += q
	// Earth equipment expenditure is always a sink; never recycled to a port owner.
	return nil
}
func (w *World) Maintain(now time.Time) bool {
	return w.maintain(now, prng.Float64)
}

// MaintainWithRandom permits reproducible simulations of all daily phases.
// Like Maintain, call inside the locked store transaction. Draws must be in [0,1).
func (w *World) MaintainWithRandom(now time.Time, rng func() float64) bool {
	if rng == nil {
		return false
	}
	return w.maintain(now, rng)
}

// maintain shares a random source between economic and faction phases. Keeping
// it injectable internally permits exact threshold and phase-order tests.
func (w *World) maintain(now time.Time, rng func() float64) bool {
	today := day(now)
	if today <= w.LastMaintenance {
		return false
	}
	w.retireInactivePlayers(now)
	w.overcrowding(now, rng)
	var taxes int64
	for _, p := range w.Ports {
		if p.ID != 1 {
			tax := p.Treasury / 10
			p.Treasury -= tax
			taxes += tax
		}
	}
	// Deserted groups join this day's stable route snapshot; fresh hires first
	// act on the following day.
	w.desertHumanDefenses(rng)
	w.mercenaryActions(rng)
	w.hireMercenaries(taxes)
	// Restore after Mercenary routes; the following Xannor phases see the new homes.
	w.restoreMercenaryBase(now, rng)
	w.maintainXannor(now, rng)
	w.xannorActions(now, rng)
	w.superPlanetLottery(now, rng)
	for _, p := range w.Players {
		if !p.RetiredAt.IsZero() {
			continue
		}
		p.Turns = 500
		p.DockToken = ""
		p.PlanetToken = ""
		p.LandedPlanet = 0
	}
	w.publishRankings(w.rankingSnapshot(false))
	w.pruneNews(now)
	w.LastMaintenance = today
	return true
}

// ClassicAlias validates a new DOS-style in-game alias without creating a player.
func ClassicAlias(w *World, alias string) error {
	if !clean(alias) {
		return errors.New("use a printable alias of 1 to 41 characters")
	}
	for _, reserved := range []string{"Sysop", "Xannor", "Mercenaries"} {
		if strings.EqualFold(alias, reserved) {
			return errors.New("That ALIAS is NOT allowed. Please choose another.")
		}
	}
	for _, p := range w.Players {
		if strings.EqualFold(strings.TrimSpace(p.Alias), alias) {
			return errors.New("I'm sorry, but that Alias is already in use.")
		}
	}
	return nil
}
