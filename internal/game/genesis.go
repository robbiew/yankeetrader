package game

import (
	"errors"
	"fmt"
	"math"
	"math/rand"
	"reflect"
	"sort"
	"time"
)

const MaxSeasonResults = 128
const GenesisQuoteLifetime = 2 * time.Minute

var ErrSeasonChanged = errors.New("this season has ended; reconnect to join the new season")

// SeasonResult archives only public winner fields. IDs are scoped to Season.
type SeasonResult struct {
	Season                   uint64
	Started, Ended           time.Time
	Winner                   string
	Player, Ports, Threshold int
	Score                    int64
}

type GenesisIntent struct {
	Ship                               TravelShip
	Sectors                            int
	Maintenance                        string
	Season, Generation                 uint64
	Player                             int
	Alias                              string
	Ports                              []int
	Threshold                          int
	ExplicitThreshold, ExplicitLottery bool
	LotteryLimit                       int
	Score                              int64
	Started, QuotedAt, Expires         time.Time
	Nonce                              string
}
type GenesisReceipt struct {
	Result    SeasonResult
	NewSeason uint64
	Seed      int64
}

func (w *World) CheckSession(id int, generation, season uint64) error {
	if season == 0 || season != w.Season {
		return ErrSeasonChanged
	}
	return w.CheckShip(id, generation)
}
func (w *World) GenesisThreshold() int {
	if w.GenesisPorts == nil {
		return 300
	}
	return *w.GenesisPorts
}
func (w *World) validateSeasons() error {
	if w.Season == 0 || len(w.SeasonResults) > MaxSeasonResults {
		return errors.New("invalid season archive")
	}
	threshold := w.GenesisThreshold()
	if threshold != 0 && (threshold < 20 || threshold > 300) {
		return errors.New("GenesisPorts must be zero (disabled) or 20 through 300; omitted defaults to 300")
	}
	if w.Season > 1 && len(w.SeasonResults) == 0 {
		return errors.New("missing previous season result")
	}
	var previous SeasonResult
	for i, r := range w.SeasonResults {
		if r.Season != uint64(i+1) || r.Season >= w.Season || r.Started.IsZero() || r.Ended.Before(r.Started) || r.Ended.After(w.Created) || !clean(r.Winner) || r.Player < 1 || r.Player > MaxPlayerIdentities || r.Threshold < 20 || r.Threshold > 300 || r.Ports < r.Threshold || r.Ports > 2999 || r.Score < 0 || r.Score > MaxMoney {
			return errors.New("invalid season result")
		}
		if i > 0 && !r.Started.Equal(previous.Ended) {
			return errors.New("discontinuous season archive")
		}
		previous = r
	}
	if len(w.SeasonResults) > 0 && (previous.Season != w.Season-1 || !previous.Ended.Equal(w.Created)) {
		return errors.New("season archive does not match current world")
	}
	return nil
}

func (w *World) PrepareGenesis(id int, now time.Time) (GenesisIntent, error) {
	p, err := w.player(id)
	if err != nil {
		return GenesisIntent{}, err
	}
	if now.IsZero() || now.Before(w.Created) {
		return GenesisIntent{}, errors.New("invalid Genesis clock")
	}
	if w.HasMineEncounter(id) {
		return GenesisIntent{}, ErrMineEncounter
	}
	if w.HostileDefense(id, p.Sector) {
		return GenesisIntent{}, ErrDefenseEncounter
	}
	threshold := w.GenesisThreshold()
	if threshold == 0 {
		return GenesisIntent{}, errors.New("Genesis is disabled in this universe")
	}
	if threshold < 20 || threshold > 300 {
		return GenesisIntent{}, errors.New("invalid Genesis threshold")
	}
	if w.Season == 0 || w.Season == math.MaxUint64 {
		return GenesisIntent{}, errors.New("season counter exhausted or invalid")
	}
	if len(w.SeasonResults) >= MaxSeasonResults {
		return GenesisIntent{}, errors.New("season history is full; no universe was reset")
	}
	ports := []int{}
	for id, port := range w.Ports {
		if id != 1 && port.Owner == p.ID {
			ports = append(ports, id)
		}
	}
	sort.Ints(ports)
	if len(ports) < threshold {
		return GenesisIntent{}, fmt.Errorf("Genesis requires %d non-Earth ports; you own %d (%d short)", threshold, len(ports), threshold-len(ports))
	}
	score := int64(0)
	for _, row := range w.rankingSnapshot(false).Players {
		if row.ID == id {
			score = row.Score
			break
		}
	}
	return GenesisIntent{Ship: w.travelShip(p), Sectors: len(w.Sectors), Maintenance: w.LastMaintenance, Season: w.Season, Generation: p.ShipGeneration, Player: id, Alias: p.Alias, Ports: ports, Threshold: threshold, ExplicitThreshold: w.GenesisPorts != nil, ExplicitLottery: w.LotteryDailyLimit != nil, LotteryLimit: w.LotteryLimit(), Score: score, Started: w.Created, QuotedAt: now.UTC(), Expires: now.UTC().Add(GenesisQuoteLifetime)}, nil
}

// GenesisCandidate builds an unpublished, fully validated replacement. The caller
// saves this one world under the existing world lock; the old world is untouched.
func (w *World) GenesisCandidate(e GenesisIntent, now time.Time, seed int64) (*World, GenesisReceipt, error) {
	return w.genesisCandidate(e, now, seed, New)
}

func (w *World) genesisCandidate(e GenesisIntent, now time.Time, seed int64, generate func(time.Time, int64, int) (*World, error)) (*World, GenesisReceipt, error) {
	var out GenesisReceipt
	if err := w.CheckSession(e.Player, e.Generation, e.Season); err != nil {
		return nil, out, err
	}
	if now.IsZero() || now.Before(e.QuotedAt) || !now.Before(e.Expires) || e.Expires != e.QuotedAt.Add(GenesisQuoteLifetime) {
		return nil, out, errors.New("Genesis confirmation expired; confirm again")
	}
	fresh, err := w.PrepareGenesis(e.Player, e.QuotedAt)
	if err != nil {
		return nil, out, err
	}
	fresh.Nonce = e.Nonce
	if !reflect.DeepEqual(fresh, e) {
		return nil, out, errors.New("Genesis ownership, settings or winner changed; confirm again")
	}
	if err = w.Validate(); err != nil {
		return nil, out, err
	}
	candidate, err := generate(now, seed, len(w.Sectors))
	if err != nil {
		return nil, out, err
	}
	if candidate == nil {
		return nil, out, errors.New("new season generation returned no candidate")
	}
	candidate.Season = w.Season + 1
	if w.GenesisPorts != nil {
		n := *w.GenesisPorts
		candidate.GenesisPorts = &n
	}
	if w.LotteryDailyLimit != nil {
		n := *w.LotteryDailyLimit
		candidate.LotteryDailyLimit = &n
	}
	result := SeasonResult{Season: w.Season, Started: w.Created, Ended: now.UTC(), Winner: e.Alias, Player: e.Player, Ports: len(e.Ports), Threshold: e.Threshold, Score: e.Score}
	candidate.SeasonResults = append(append([]SeasonResult(nil), w.SeasonResults...), result)
	// New already stocks the economy. Bootstrap supported homes explicitly because
	// same-day Maintain deliberately does nothing; never rerun all daily events.
	rng := rand.New(rand.NewSource(seed))
	candidate.restoreMercenaryBase(now, rng.Float64)
	candidate.restoreXannoron(now, rng.Float64)
	if candidate.Xannor == nil || candidate.xannorHome() == nil {
		return nil, out, errors.New("new season has no room for required faction homes")
	}
	mercenary := false
	for _, p := range candidate.Planets {
		if p.FactionHome == MercenaryHome {
			mercenary = true
		}
	}
	if !mercenary {
		return nil, out, errors.New("new season has no Mercenary base")
	}
	if _, err = candidate.BootstrapWanderer(now, rng.Float64); err != nil {
		return nil, out, err
	}
	if candidate.wanderer() == nil {
		return nil, out, errors.New("new season has no room for The Wanderer")
	}
	if err = candidate.Validate(); err != nil {
		return nil, out, err
	}
	return candidate, GenesisReceipt{Result: result, NewSeason: candidate.Season, Seed: seed}, nil
}
