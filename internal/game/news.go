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
	NewsLogin       NewsKind = "login"
	NewsXannorDeath NewsKind = "xannor-death"
	NewsTeamCreated NewsKind = "team-created"
)

// NewsEvent stores only whitelisted public snapshots, never arbitrary message
// text, authentication identities, account balances or invitation secrets.
type NewsEvent struct {
	ID       uint64
	At       time.Time
	Kind     NewsKind
	Alias    string
	Team     int    `json:",omitempty"`
	TeamName string `json:",omitempty"`
}
type Newspaper struct {
	Date    string
	Entries []NewsEvent
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
		if e.ID <= lastID || e.ID >= w.NextNews || e.At.IsZero() || offset != 0 || e.At.Before(w.Created) || e.At.Before(lastAt) || e.At.Before(cutoff) || !clean(e.Alias) {
			return errors.New("invalid newspaper event")
		}
		switch e.Kind {
		case NewsLogin, NewsXannorDeath:
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
