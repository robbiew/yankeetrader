package game

import (
	"encoding/json"
	"math"
	"strings"
	"testing"
	"time"
)

func TestRegistrationNewsOnlyForNewIdentity(t *testing.T) {
	w, _ := newsWorld(t)
	at := w.Created
	p, err := w.JoinWithNews("new-private-identity", "Original", at)
	if err != nil {
		t.Fatal(err)
	}
	if len(w.News) != 1 || w.News[0].Kind != NewsRegistration || w.News[0].Alias != "Original" || p.LastActivity != day(at) {
		t.Fatal(w.News)
	}
	if _, err = w.JoinWithNews(p.Identity, "Renamed", at); err != nil {
		t.Fatal(err)
	}
	if len(w.News) != 1 || w.News[0].Alias != "Original" {
		t.Fatal("reconnect duplicated or rewrote registration", w.News)
	}
	if err = w.RecordDeath(DeathContext{Victim: p.ID, Generation: p.ShipGeneration, Sector: p.Sector, Cause: "self", Killer: p.ID}, at); err != nil {
		t.Fatal(err)
	}
	next := at.AddDate(0, 0, 1)
	if _, err = w.JoinWithNews(p.Identity, "Renamed", next); err != nil {
		t.Fatal(err)
	}
	if err = w.LoginShip(p.ID, next); err != nil {
		t.Fatal(err)
	}
	registrations := 0
	for _, event := range w.News {
		if event.Kind == NewsRegistration {
			registrations++
		}
	}
	if registrations != 1 {
		t.Fatal("replacement duplicated registration", w.News)
	}
	encoded, _ := json.Marshal(w.News)
	if strings.Contains(string(encoded), p.Identity) {
		t.Fatal("identity leaked", string(encoded))
	}
	if err = w.Validate(); err != nil {
		t.Fatal(err)
	}
}

func TestRegistrationNewsPreflightAndFailedJoin(t *testing.T) {
	for _, mode := range []string{"clock", "sequence", "alias", "identity", "capacity", "identity-capacity"} {
		t.Run(mode, func(t *testing.T) {
			w, _ := newsWorld(t)
			at := w.Created
			alias := "New"
			identity := "new"
			switch mode {
			case "clock":
				at = at.Add(-time.Second)
			case "sequence":
				w.NextNews = math.MaxUint64
			case "alias":
				alias = "\x1b"
			case "identity":
				identity = ""
			case "capacity":
				for i := len(w.Players); i < MaxActivePlayers; i++ {
					if _, err := w.Join(string(rune(1000+i)), "Other"); err != nil {
						t.Fatal(err)
					}
				}
			case "identity-capacity":
				w.NextPlayer = MaxPlayerIdentities + 1
			}
			before, _ := json.Marshal(w)
			if _, err := w.JoinWithNews(identity, alias, at); err == nil {
				t.Fatal("failed join accepted")
			}
			after, _ := json.Marshal(w)
			if string(before) != string(after) {
				t.Fatal("failed registration mutated world")
			}
		})
	}
}

func TestTeamJoinNewsSnapshotsAndRejections(t *testing.T) {
	w, captain := newsWorld(t)
	if err := w.CreateTeam(captain.ID, "Secret Team", "ABCD"); err != nil {
		t.Fatal(err)
	}
	member, err := w.Join("member-private", "Member")
	if err != nil {
		t.Fatal(err)
	}
	if err = w.JoinTeamWithNews(member.ID, captain.Team, "bad!", w.Created); err == nil {
		t.Fatal("wrong password accepted")
	}
	if len(w.News) != 0 || member.Team != 0 {
		t.Fatal("failed join published")
	}
	w.NextNews = math.MaxUint64
	if err = w.JoinTeamWithNews(member.ID, captain.Team, "ABCD", w.Created); err == nil || member.Team != 0 {
		t.Fatal("journal exhaustion mutated membership")
	}
	w.NextNews = 1
	if err = w.JoinTeamWithNews(member.ID, captain.Team, "ABCD", w.Created.Add(-time.Second)); err == nil || member.Team != 0 {
		t.Fatal("invalid clock mutated membership")
	}
	if err = w.JoinTeamWithNews(member.ID, captain.Team, "ABCD", w.Created); err != nil {
		t.Fatal(err)
	}
	if len(w.News) != 1 || w.News[0].Kind != NewsTeamJoined || w.News[0].Alias != "Member" || w.News[0].Team != captain.Team || w.News[0].TeamName != "" {
		t.Fatal(w.News)
	}
	if err = w.JoinTeamWithNews(member.ID, captain.Team, "ABCD", w.Created); err == nil || len(w.News) != 1 {
		t.Fatal("repeat published")
	}
	member.Alias = "Changed"
	w.Teams[captain.Team].Name = "Changed"
	encoded, _ := json.Marshal(w.News)
	for _, secret := range []string{"member-private", "ABCD", "Secret Team", "Changed", w.Teams[captain.Team].PasswordHash} {
		if strings.Contains(string(encoded), secret) {
			t.Fatal("private or live data leaked", string(encoded))
		}
	}
	if err = w.Validate(); err != nil {
		t.Fatal(err)
	}
}
