package game

import (
	"encoding/json"
	"fmt"
	"math"
	"reflect"
	"testing"
	"time"
)

func TestBroadcastRadioCurrentAccountsAndIndependentCopies(t *testing.T) {
	w, sender, recipient, other := radioWorld(t)
	address, err := w.FindBroadcastRadioRecipients(sender.ID)
	if err != nil || len(address.Recipients) != 3 {
		t.Fatal(address, err)
	}
	before, _ := json.Marshal(w.Players)
	draft, err := w.PrepareBroadcastRadio(sender.ID, address, "ALL; literal/", clock)
	if err != nil {
		t.Fatal(err)
	}
	address.Recipients[0].Alias = "tampered"
	ids, err := w.CommitBroadcastRadio(draft, clock)
	if err != nil || !reflect.DeepEqual(ids, []uint64{1, 2, 3}) {
		t.Fatal(ids, err)
	}
	for _, p := range []*Player{sender, recipient, other} {
		entries, err := w.RadioHistory(p.ID, 0, 20, true)
		if err != nil || len(entries) != 1 || entries[0].Text != "ALL; literal/" || !entries[0].Incoming {
			t.Fatal(entries, err)
		}
	}
	if err := w.AcknowledgeRadio(recipient.ID, 2); err != nil {
		t.Fatal(err)
	}
	if !w.Radio[0].Unread || w.Radio[1].Unread || !w.Radio[2].Unread {
		t.Fatal("shared acknowledgement")
	}
	after, _ := json.Marshal(w.Players)
	if string(before) != string(after) {
		t.Fatal("broadcast changed account resources")
	}
	later, err := w.Join("later-account", "Later")
	if err != nil {
		t.Fatal(err)
	}
	entries, err := w.RadioHistory(later.ID, 0, 20, false)
	if err != nil || len(entries) != 0 {
		t.Fatal("future account inherited broadcast", entries, err)
	}
	if err := w.AcknowledgeRadio(later.ID, 2); err == nil {
		t.Fatal("future account acknowledged another copy")
	}
	again, err := w.CommitBroadcastRadio(draft, clock.Add(time.Minute))
	if err != nil || !reflect.DeepEqual(ids, again) || len(w.Radio) != 3 || w.Radio[1].Unread {
		t.Fatal("retry duplicated delivery", again, err)
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
}

func TestBroadcastRadioStaleRecipientsAndAtomicFailures(t *testing.T) {
	for _, mode := range []string{"join", "retire", "rename", "generation", "season", "expiry", "capacity", "sequence", "late-text", "partial", "news-sequence", "news-clock"} {
		t.Run(mode, func(t *testing.T) {
			w, sender, recipient, _ := radioWorld(t)
			address, _ := w.FindBroadcastRadioRecipients(sender.ID)
			draft, err := w.PrepareBroadcastRadio(sender.ID, address, "broadcast", clock)
			if err != nil {
				t.Fatal(err)
			}
			now := clock
			switch mode {
			case "join":
				_, _ = w.Join("new", "New")
			case "retire":
				recipient.RetiredAt = clock
			case "rename":
				recipient.Alias = "Renamed"
			case "generation":
				sender.ShipGeneration++
			case "season":
				w.Season++
			case "expiry":
				now = clock.Add(5 * time.Minute)
			case "capacity":
				w.Radio = make([]RadioMessage, MaxRadioMessages-2)
			case "sequence":
				w.NextRadio = math.MaxUint64 - 2
			case "late-text":
				draft.drafts[2].text = "\x1b"
			case "news-sequence":
				w.NextNews = math.MaxUint64
			case "news-clock":
				w.appendNews(NewsEvent{At: clock.Add(time.Minute), Kind: NewsLogin, Alias: sender.Alias})
			case "partial":
				if _, err := w.CommitRadio(draft.drafts[0], clock); err != nil {
					t.Fatal(err)
				}
			}
			before, _ := json.Marshal(w)
			if _, err := w.CommitBroadcastRadio(draft, now); err == nil {
				t.Fatal("invalid/stale batch committed")
			}
			after, _ := json.Marshal(w)
			if string(before) != string(after) {
				t.Fatal("partial broadcast publication")
			}
		})
	}
}

func TestBroadcastRadioFullActiveRosterAndRetirement(t *testing.T) {
	w, sender, recipient, _ := radioWorld(t)
	if err := w.RecordDeath(DeathContext{Victim: recipient.ID, Generation: recipient.ShipGeneration, Sector: recipient.Sector, Cause: "mines"}, clock); err != nil {
		t.Fatal(err)
	}
	address, err := w.FindBroadcastRadioRecipients(sender.ID)
	if err != nil || len(address.Recipients) != 3 {
		t.Fatal("dead account lost mail eligibility", address, err)
	}
	now := clock.AddDate(0, 0, InactiveRetirementDays+1)
	w.retireInactivePlayers(now)
	address, err = w.FindBroadcastRadioRecipients(sender.ID)
	if err != nil || len(address.Recipients) != 2 {
		t.Fatal("retired account still selected", address, err)
	}
	if _, err := w.PrepareBroadcastRadio(sender.ID, BroadcastRadioAddress{}, "text", clock); err == nil {
		t.Fatal("unconfirmed roster accepted")
	}
	for w.activePlayers() < MaxActivePlayers {
		n := w.NextPlayer
		if _, err := w.Join(fmt.Sprint("identity", n), fmt.Sprint("Pilot", n)); err != nil {
			t.Fatal(err)
		}
	}
	address, err = w.FindBroadcastRadioRecipients(sender.ID)
	if err != nil || len(address.Recipients) != MaxActivePlayers {
		t.Fatal(address, err)
	}
	draft, err := w.PrepareBroadcastRadio(sender.ID, address, "full roster", now)
	if err != nil {
		t.Fatal(err)
	}
	ids, err := w.CommitBroadcastRadio(draft, now)
	if err != nil || len(ids) != MaxActivePlayers {
		t.Fatal(ids, err)
	}
}
