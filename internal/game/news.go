package game

import (
	"errors"
	"math"
	"slices"
	"time"
)

const MaxNewsEvents = 1024

type NewsKind string

const (
	NewsPlanetCreated NewsKind = "planet-created"
	NewsBroadcast     NewsKind = "radio-broadcast"
	NewsPlayerPlanet  NewsKind = "player-planet-assault"
	NewsLottery       NewsKind = "paid-lottery"
	NewsXannorHQ      NewsKind = "xannor-hq-victory"
	NewsPortPlague    NewsKind = "port-plague"
	NewsPlanetPlague  NewsKind = "planet-plague"
	NewsCivilWar      NewsKind = "civil-war"
	NewsSuperPlanet   NewsKind = "super-planet"
	NewsRetirement    NewsKind = "retirement"
	NewsXannorPlanet  NewsKind = "xannor-planet-assault"
	NewsLogin         NewsKind = "login"
	NewsXannorDeath   NewsKind = "xannor-death"
	NewsTeamCreated   NewsKind = "team-created"
)

// NewsEvent stores whitelisted public snapshots. Only explicitly public radio
// broadcasts may contain message text; private mail and account secrets are excluded.
type NewsEvent struct {
	BroadcastText                    string `json:",omitempty"`
	GroundCommitted, GroundRemaining int64  `json:",omitempty"`
	LotteryMatches                   int    `json:",omitempty"`
	LotteryPrize                     int64  `json:",omitempty"`
	PortCount                        int    `json:",omitempty"`
	PlanetName                       string `json:",omitempty"`
	Outcome                          string `json:",omitempty"`
	ID                               uint64
	At                               time.Time
	Kind                             NewsKind
	Alias                            string
	Team                             int    `json:",omitempty"`
	TeamName                         string `json:",omitempty"`
}
type Newspaper struct {
	Date    string
	Entries []NewsEvent
}

func planetaryNews(kind NewsKind) bool {
	return kind == NewsPlayerPlanet || kind == NewsXannorPlanet || kind == NewsPlanetPlague || kind == NewsCivilWar
}

func utcDay(t time.Time) time.Time {
	t = t.UTC()
	return time.Date(t.Year(), t.Month(), t.Day(), 0, 0, 0, 0, time.UTC)
}
func (w *World) validateNews() error {
	if w.NextNews == 0 || len(w.News) > MaxNewsEvents {
		return errors.New("invalid newspaper archive")
	}
	var lastID uint64
	var lastAt time.Time
	reference, _ := time.Parse("2006-01-02", w.LastMaintenance)
	if len(w.News) > 0 && w.News[len(w.News)-1].At.After(reference) {
		reference = w.News[len(w.News)-1].At
	}
	cutoff := utcDay(reference).AddDate(0, 0, -1)
	for _, e := range w.News {
		_, offset := e.At.Zone()
		if e.ID <= lastID || e.ID >= w.NextNews || e.At.IsZero() || offset != 0 || e.At.Before(w.Created) || e.At.Before(lastAt) || e.At.Before(cutoff) || (!planetaryNews(e.Kind) && e.Kind != NewsPortPlague && !clean(e.Alias)) {
			return errors.New("invalid newspaper event")
		}
		if !planetaryNews(e.Kind) && e.Kind != NewsPlanetCreated && (e.PlanetName != "" || e.Outcome != "") {
			return errors.New("unrelated news contains planetary details")
		}
		if e.Kind != NewsPortPlague && e.PortCount != 0 {
			return errors.New("unrelated news contains port count")
		}
		if e.Kind != NewsLottery && (e.LotteryMatches != 0 || e.LotteryPrize != 0) {
			return errors.New("unrelated news contains paid lottery details")
		}
		if e.Kind != NewsPlayerPlanet && (e.GroundCommitted != 0 || e.GroundRemaining != 0) {
			return errors.New("unrelated news contains ground assault details")
		}
		if e.Kind != NewsBroadcast && e.BroadcastText != "" {
			return errors.New("private or unrelated news contains radio text")
		}
		switch e.Kind {
		case NewsPlanetCreated:
			if !clean(e.PlanetName) || e.Outcome != "" || e.Team != 0 || e.TeamName != "" {
				return errors.New("invalid planet creation news")
			}
		case NewsBroadcast:
			if !validRadioText(e.BroadcastText) || e.Team != 0 || e.TeamName != "" {
				return errors.New("invalid public broadcast news")
			}

		case NewsPlayerPlanet:
			if !clean(e.Alias) || !clean(e.PlanetName) || e.Team != 0 || e.TeamName != "" || e.GroundCommitted < 0 || e.GroundCommitted > MaxQuantity || e.GroundRemaining < 0 || e.GroundRemaining > MaxQuantity {
				return errors.New("invalid player planetary news")
			}
			switch e.Outcome {
			case "captured", "defended", "unfinished":
				if e.GroundCommitted == 0 {
					return errors.New("missing assault commitment")
				}
			case "adopted":
				if e.GroundCommitted != 0 {
					return errors.New("adoption charged troops")
				}
			default:
				return errors.New("invalid player planetary outcome")
			}

		case NewsLottery:
			if e.Team != 0 || e.TeamName != "" || e.LotteryMatches < 4 || e.LotteryMatches > 6 || e.LotteryPrize < LotteryPrice || e.LotteryPrize > LotteryPrize(e.LotteryMatches) {
				return errors.New("invalid paid lottery news")
			}

		case NewsPortPlague:
			if e.PortCount < 1 || e.PortCount > 3000 || e.Alias != "" || e.Team != 0 || e.TeamName != "" {
				return errors.New("invalid port plague news")
			}
		case NewsPlanetPlague, NewsCivilWar:
			if !clean(e.PlanetName) || e.Outcome != "" || e.Alias != "" || e.Team != 0 || e.TeamName != "" {
				return errors.New("invalid overcrowding news")
			}
		case NewsXannorPlanet:
			if e.Alias != "" || e.Team != 0 || e.TeamName != "" || !clean(e.PlanetName) {
				return errors.New("invalid planetary news snapshot")
			}
			switch e.Outcome {
			case "defended", "damaged", "neutralized", "destroyed", "unfinished":
			default:
				return errors.New("invalid planetary news outcome")
			}
		case NewsLogin, NewsXannorDeath, NewsSuperPlanet, NewsRetirement, NewsXannorHQ:
			if e.Team != 0 || e.TeamName != "" {
				return errors.New("login newspaper event contains team details")
			}
		case NewsTeamCreated:
			if e.Team < 1 || e.Team > 50 || !clean(e.TeamName) || len(e.TeamName) < 3 {
				return errors.New("invalid newspaper team snapshot")
			}
		default:
			return errors.New("unsupported newspaper event")
		}
		lastID, lastAt = e.ID, e.At
	}
	return nil
}
func (w *World) newsTime(now time.Time) error {
	if now.IsZero() || now.Before(w.Created) || day(now) < w.LastMaintenance || (len(w.News) > 0 && now.Before(w.News[len(w.News)-1].At)) {
		return errors.New("newspaper clock predates saved history")
	}
	return nil
}
func (w *World) prepareNews(now time.Time) error {
	if err := w.newsTime(now); err != nil {
		return err
	}
	if w.NextNews == 0 || w.NextNews == math.MaxUint64 {
		return errors.New("newspaper sequence exhausted")
	}
	return nil
}

// pruneNews runs only with a successful forward maintenance/append. Reads never
// rewrite the journal. A gap of two calendar days naturally yields empty history.
func (w *World) pruneNews(now time.Time) {
	if len(w.News) > 0 && now.Before(w.News[len(w.News)-1].At) {
		now = w.News[len(w.News)-1].At
	}
	cutoff := utcDay(now).AddDate(0, 0, -1)
	first := 0
	for first < len(w.News) && w.News[first].At.Before(cutoff) {
		first++
	}
	if first > 0 {
		w.News = slices.Clone(w.News[first:])
	}
}
func (w *World) appendNews(e NewsEvent) {
	w.pruneNews(e.At)
	e.ID = w.NextNews
	w.NextNews++
	w.News = append(w.News, e)
	if len(w.News) > MaxNewsEvents {
		w.News = slices.Clone(w.News[len(w.News)-MaxNewsEvents:])
	}
}

// RecordLogin is called inside the successful authenticated login transaction,
// after replacement eligibility and alias selection, before that world saves.
func (w *World) RecordLogin(id int, now time.Time) error {
	p, err := w.player(id)
	if err != nil {
		return err
	}
	if err = w.prepareNews(now); err != nil {
		return err
	}
	w.appendNews(NewsEvent{At: now.UTC(), Kind: NewsLogin, Alias: p.Alias})
	p.LastActivity = day(now)
	return nil
}

// CreateTeamWithNews validates journal metadata before changing the team, then
// records its public snapshot without any further fallible action.
func (w *World) CreateTeamWithNews(id int, name, password string, now time.Time) error {
	if err := w.prepareNews(now); err != nil {
		return err
	}
	if err := w.CreateTeam(id, name, password); err != nil {
		return err
	}
	p := w.Players[id]
	team := w.Teams[p.Team]
	w.appendNews(NewsEvent{At: now.UTC(), Kind: NewsTeamCreated, Alias: p.Alias, Team: team.ID, TeamName: team.Name})
	return nil
}
func (w *World) ReadNewspaper(id int, now time.Time, yesterday bool) (Newspaper, error) {
	if _, err := w.player(id); err != nil {
		return Newspaper{}, err
	}
	if err := w.newsTime(now); err != nil {
		return Newspaper{}, err
	}
	date := utcDay(now)
	if yesterday {
		date = date.AddDate(0, 0, -1)
	}
	report := Newspaper{Date: day(date)}
	for _, e := range w.News {
		if day(e.At) == report.Date {
			report.Entries = append(report.Entries, e)
		}
	}
	return report, nil
}
