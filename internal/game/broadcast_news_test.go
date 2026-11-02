package game

import (
	"encoding/json"
	"math"
	"strings"
	"testing"
	"time"
)

func TestBroadcastNewspaperPublicationAndReplay(t *testing.T) {
	w, sender, _, _ := radioWorld(t)
	address, _ := w.FindBroadcastRadioRecipients(sender.ID)
	draft, err := w.PrepareBroadcastRadio(sender.ID, address, "ALL; literal/", clock)
	if err != nil {
		t.Fatal(err)
	}
	ids, err := w.CommitBroadcastRadio(draft, clock)
	if err != nil || len(ids) != 3 {
		t.Fatal(ids, err)
	}
	if len(w.News) != 1 || w.NextNews != 2 || w.News[0].Kind != NewsBroadcast || w.News[0].Alias != sender.Alias || w.News[0].BroadcastText != "ALL; literal/" {
		t.Fatal(w.News)
	}
	later, err := w.Join("later", "Later")
	if err != nil {
		t.Fatal(err)
	}
	report, err := w.ReadNewspaper(later.ID, clock, false)
	if err != nil || len(report.Entries) != 1 || report.Entries[0].BroadcastText != "ALL; literal/" {
		t.Fatal(report, err)
	}
	if history, err := w.RadioHistory(later.ID, 0, 20, false); err != nil || len(history) != 0 {
		t.Fatal(history, err)
	}
	alias := w.News[0].Alias
	sender.Alias = "Renamed"
	if w.News[0].Alias != alias {
		t.Fatal("public snapshot changed after rename")
	}
	// A retry after the public entry is pruned must not publish it again. News
	// exhaustion and elapsed draft lifetime cannot turn a saved send into a new one.
	w.pruneNews(clock.AddDate(0, 0, 3))
	w.NextNews = math.MaxUint64
	before, _ := json.Marshal(w)
	again, err := w.CommitBroadcastRadio(draft, clock.AddDate(0, 0, 3))
	after, _ := json.Marshal(w)
	if err != nil || len(again) != 3 || string(before) != string(after) {
		t.Fatal(again, err, "replayed publication")
	}
}

func TestBroadcastNewsBoundsMigrationAndValidation(t *testing.T) {
	for _, mode := range []string{"sequence", "clock"} {
		t.Run(mode, func(t *testing.T) {
			w, sender, _, _ := radioWorld(t)
			address, _ := w.FindBroadcastRadioRecipients(sender.ID)
			now := clock
			if mode == "sequence" {
				w.NextNews = math.MaxUint64
			} else {
				now = clock.Add(-time.Second)
			}
			before, _ := json.Marshal(w)
			if _, err := w.PrepareBroadcastRadio(sender.ID, address, "text", now); err == nil {
				t.Fatal("invalid news metadata accepted")
			}
			after, _ := json.Marshal(w)
			if string(before) != string(after) {
				t.Fatal("prepare mutated world")
			}
		})
	}
	w, sender, _, _ := radioWorld(t)
	for i := 0; i < MaxNewsEvents; i++ {
		w.appendNews(NewsEvent{At: clock, Kind: NewsLogin, Alias: sender.Alias})
	}
	address, _ := w.FindBroadcastRadioRecipients(sender.ID)
	draft, err := w.PrepareBroadcastRadio(sender.ID, address, "bounded", clock)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = w.CommitBroadcastRadio(draft, clock); err != nil {
		t.Fatal(err)
	}
	if len(w.News) != MaxNewsEvents || w.News[0].ID != 2 || w.News[len(w.News)-1].Kind != NewsBroadcast {
		t.Fatal("journal did not roll at its bound")
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
	for _, change := range []func(*NewsEvent){
		func(e *NewsEvent) { e.BroadcastText = "" }, func(e *NewsEvent) { e.BroadcastText = "\x1b" },
		func(e *NewsEvent) { e.BroadcastText = strings.Repeat("a", 75) }, func(e *NewsEvent) { e.Team = 1 },
		func(e *NewsEvent) { e.Kind = NewsLogin }, func(e *NewsEvent) { e.PlanetName = "Secret" },
	} {
		copyWorld := *w
		copyWorld.News = append([]NewsEvent(nil), w.News...)
		change(&copyWorld.News[len(copyWorld.News)-1])
		if err := copyWorld.Validate(); err == nil {
			t.Fatal("invalid public text metadata accepted")
		}
	}
	// Version 26 private mail is retained without inventing historical public text.
	w.News = nil
	w.NextNews = 1
	w.Version = 26
	if err := w.Upgrade(); err != nil {
		t.Fatal(err)
	}
	if w.Version != WorldVersion || len(w.News) != 0 || len(w.Radio) != 3 {
		t.Fatal("migration backfilled public mail")
	}
	w.Version = 26
	w.News = []NewsEvent{{ID: 1, At: clock, Kind: NewsBroadcast, Alias: sender.Alias, BroadcastText: "forged legacy"}}
	w.NextNews = 2
	if err := w.Upgrade(); err == nil {
		t.Fatal("legacy broadcast kind accepted")
	}
	w.News[0].Kind = NewsLogin
	if err := w.Upgrade(); err == nil {
		t.Fatal("legacy broadcast text accepted")
	}
}

func TestDirectAndTeamRadioNeverPublishNewspaperText(t *testing.T) {
	w, sender, recipient, _ := teamRadioWorld(t)
	before, _ := json.Marshal(w.News)
	direct, err := w.PrepareRadio(sender.ID, RadioAddress{ID: recipient.ID, Alias: recipient.Alias}, "DIRECT SECRET", clock)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = w.CommitRadio(direct, clock); err != nil {
		t.Fatal(err)
	}
	address, err := w.FindTeamRadioRecipients(sender.ID)
	if err != nil {
		t.Fatal(err)
	}
	team, err := w.PrepareTeamRadio(sender.ID, address, "TEAM SECRET", clock)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = w.CommitTeamRadio(team, clock); err != nil {
		t.Fatal(err)
	}
	after, _ := json.Marshal(w.News)
	if string(before) != string(after) {
		t.Fatal("private mail changed public news")
	}
}

func TestBroadcastPublicSendWithNoTurnsAndTeamMembership(t *testing.T) {
	w, sender, _, _ := teamRadioWorld(t)
	sender.Turns = 0
	before, _ := json.Marshal(w.Players)
	address, err := w.FindBroadcastRadioRecipients(sender.ID)
	if err != nil {
		t.Fatal(err)
	}
	draft, err := w.PrepareBroadcastRadio(sender.ID, address, "team member public notice", clock)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = w.CommitBroadcastRadio(draft, clock); err != nil {
		t.Fatal(err)
	}
	after, _ := json.Marshal(w.Players)
	if string(before) != string(after) || len(w.Radio) != 3 || len(w.News) != 1 {
		t.Fatal("public send charged assets or excluded outsiders")
	}
}
