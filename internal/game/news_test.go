package game

import (
	"encoding/json"
	"math"
	"strings"
	"testing"
	"time"
)

func newsWorld(t *testing.T) (*World, *Player) {
	t.Helper()
	now := time.Date(2026, 10, 24, 23, 59, 0, 0, time.UTC)
	w, err := New(now, 36, 8)
	if err != nil {
		t.Fatal(err)
	}
	p, err := w.Join("private-account-key", "Q")
	if err != nil {
		t.Fatal(err)
	}
	return w, p
}
func TestNewspaperUTCSelectionSnapshotsAndPrivacy(t *testing.T) {
	w, p := newsWorld(t)
	at := w.Created
	if err := w.RecordLogin(p.ID, at); err != nil {
		t.Fatal(err)
	}
	if err := w.CreateTeamWithNews(p.ID, "News Team", "ABCD", at.Add(30*time.Second)); err != nil {
		t.Fatal(err)
	}
	now := at.Add(61 * time.Second)
	if err := w.RecordLogin(p.ID, now.In(time.FixedZone("caller", -7*3600))); err != nil {
		t.Fatal(err)
	}
	p.Alias = "Renamed"
	w.Teams[1].Name = "Renamed Team"
	other, _ := w.Join("other-private-key", "Other")
	before, _ := json.Marshal(w)
	today, err := w.ReadNewspaper(other.ID, now, false)
	if err != nil || today.Date != "2026-10-25" || len(today.Entries) != 1 || today.Entries[0].Kind != NewsLogin || today.Entries[0].Alias != "Q" {
		t.Fatal(today, err)
	}
	yesterday, err := w.ReadNewspaper(p.ID, now, true)
	if err != nil || yesterday.Date != "2026-10-24" || len(yesterday.Entries) != 2 || yesterday.Entries[1].Kind != NewsTeamCreated || yesterday.Entries[1].Team != 1 || yesterday.Entries[1].TeamName != "News Team" {
		t.Fatal(yesterday, err)
	}
	encoded, _ := json.Marshal(append(today.Entries, yesterday.Entries...))
	for _, secret := range []string{"private-account-key", "other-private-key", "ABCD", "PasswordHash", "Identity", "Credits", "DockToken"} {
		if strings.Contains(string(encoded), secret) {
			t.Fatal("private fields leaked", string(encoded))
		}
	}
	after, _ := json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("newspaper read changed world")
	}
	today.Entries[0].Alias = "tampered"
	again, _ := w.ReadNewspaper(p.ID, now, false)
	if again.Entries[0].Alias != "Q" {
		t.Fatal("newspaper aliases world")
	}
	if err = w.Validate(); err != nil {
		t.Fatal(err)
	}
}
func TestNewspaperRetentionAndIdempotentMaintenance(t *testing.T) {
	w, p := newsWorld(t)
	if err := w.RecordLogin(p.ID, w.Created); err != nil {
		t.Fatal(err)
	}
	// Isolate expiration from random maintenance events that legitimately add news.
	maintain := func(at time.Time) bool { return w.MaintainWithRandom(at, func() float64 { return 0 }) }
	nextDay := w.Created.Add(2 * time.Minute)
	if !maintain(nextDay) {
		t.Fatal("forward maintenance skipped")
	}
	before, _ := json.Marshal(w)
	if maintain(nextDay.Add(time.Hour)) || maintain(w.Created) {
		t.Fatal("same-day/rollback maintenance ran")
	}
	after, _ := json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("repeated maintenance rotated history")
	}
	for i := 0; i < MaxNewsEvents+3; i++ {
		if err := w.RecordLogin(p.ID, nextDay); err != nil {
			t.Fatal(err)
		}
	}
	if len(w.News) != MaxNewsEvents || w.News[0].ID != 5 || w.NextNews != MaxNewsEvents+5 {
		t.Fatal("history cap or IDs", len(w.News), w.News[0].ID, w.NextNews)
	}
	lastID := w.NextNews
	future := nextDay.AddDate(0, 0, 3)
	if !maintain(future) || len(w.News) != 0 || w.NextNews != lastID {
		t.Fatal("maintenance did not expire old history")
	}
	if err := w.RecordLogin(p.ID, nextDay); err == nil {
		t.Fatal("clock rollback repopulated expired history")
	}
	report, err := w.ReadNewspaper(p.ID, future, true)
	if err != nil || len(report.Entries) != 0 || report.Date != "2026-10-27" {
		t.Fatal("gap invented history", report, err)
	}
	if err = w.RecordLogin(p.ID, future); err != nil || w.News[0].ID != lastID {
		t.Fatal("expired IDs reused", err)
	}
}
func TestNewspaperRejectedActionsDoNotRecordEvents(t *testing.T) {
	for _, mode := range []string{"name", "password", "player", "clock", "sequence", "membership"} {
		t.Run(mode, func(t *testing.T) {
			w, p := newsWorld(t)
			at := w.Created
			id := p.ID
			name, password := "News Team", "ABCD"
			switch mode {
			case "name":
				name = "x"
			case "password":
				password = "bad"
			case "player":
				id = 999
			case "clock":
				at = at.Add(-time.Second)
			case "sequence":
				w.NextNews = math.MaxUint64
			case "membership":
				if err := w.CreateTeam(p.ID, "Other", "ABCD"); err != nil {
					t.Fatal(err)
				}
			}
			before, _ := json.Marshal(w)
			if err := w.CreateTeamWithNews(id, name, password, at); err == nil {
				t.Fatal("invalid team creation accepted")
			}
			after, _ := json.Marshal(w)
			if string(before) != string(after) {
				t.Fatal("rejected team creation changed world")
			}
		})
	}
	w, p := newsWorld(t)
	if err := w.RecordLogin(p.ID, w.Created.Add(time.Second)); err != nil {
		t.Fatal(err)
	}
	before, _ := json.Marshal(w)
	if err := w.RecordLogin(p.ID, w.Created); err == nil {
		t.Fatal("backdated event accepted")
	}
	if _, err := w.ReadNewspaper(p.ID, w.Created, false); err == nil {
		t.Fatal("clock rollback silently relabeled history")
	}
	after, _ := json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("clock rejection changed journal")
	}
}
func TestNewspaperArchiveRejectsMalformedEvents(t *testing.T) {
	for _, mode := range []string{"duplicate", "sequence", "kind", "alias", "time", "offset", "order", "login-team", "team-name", "team-id", "old-day", "over-cap", "maintenance-horizon"} {
		t.Run(mode, func(t *testing.T) {
			w, p := newsWorld(t)
			if err := w.RecordLogin(p.ID, w.Created); err != nil {
				t.Fatal(err)
			}
			if err := w.CreateTeamWithNews(p.ID, "News Team", "ABCD", w.Created.Add(time.Second)); err != nil {
				t.Fatal(err)
			}
			switch mode {
			case "duplicate":
				w.News[1].ID = w.News[0].ID
			case "sequence":
				w.NextNews = w.News[1].ID
			case "kind":
				w.News[0].Kind = "arbitrary"
			case "alias":
				w.News[0].Alias = "\x1b[2J"
			case "time":
				w.News[0].At = time.Time{}
			case "offset":
				w.News[0].At = w.News[0].At.In(time.FixedZone("local", 3600))
			case "order":
				w.News[0].At = w.News[1].At.Add(time.Second)
			case "login-team":
				w.News[0].TeamName = "private"
			case "team-name":
				w.News[1].TeamName = "\x00"
			case "team-id":
				w.News[1].Team = 51
			case "old-day":
				w.News[1].At = w.News[0].At.AddDate(0, 0, 3)
			case "maintenance-horizon":
				w.LastMaintenance = day(w.Created.AddDate(0, 0, 4))
			case "over-cap":
				w.News = append(w.News, make([]NewsEvent, MaxNewsEvents)...)
			}
			if err := w.Validate(); err == nil {
				t.Fatal("invalid newspaper accepted", mode)
			}
		})
	}
	w, p := newsWorld(t)
	p.Death = &Death{}
	if _, err := w.ReadNewspaper(p.ID, w.Created, false); err == nil {
		t.Fatal("dead account read newspaper")
	}
}
