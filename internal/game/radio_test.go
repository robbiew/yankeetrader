package game

import (
	"encoding/json"
	"errors"
	"math"
	"strings"
	"testing"
	"time"
)

func radioWorld(t *testing.T) (*World, *Player, *Player, *Player) {
	t.Helper()
	w, sender := setup(t)
	recipient, _ := w.Join("recipient-secret", "Enemy")
	other, _ := w.Join("third-party-secret", "Visitor")
	return w, sender, recipient, other
}

func TestRadioDirectDeliveryHistoryAndRecipientPrivacy(t *testing.T) {
	w, sender, recipient, other := radioWorld(t)
	before, _ := json.Marshal(w.Players)
	address, err := w.FindRadioRecipient(sender.ID, "ene")
	if err != nil || address.ID != recipient.ID {
		t.Fatal(address, err)
	}
	draft, err := w.PrepareRadio(sender.ID, address, "YT RADIO PROBE; literal/", clock)
	if err != nil {
		t.Fatal(err)
	}
	id, err := w.CommitRadio(draft, clock)
	if err != nil || id != 1 {
		t.Fatal(id, err)
	}
	for _, actor := range []int{sender.ID, recipient.ID, other.ID} {
		history, err := w.RadioHistory(actor, 0, 20, false)
		if err != nil {
			t.Fatal(err)
		}
		if actor == other.ID {
			if len(history) != 0 {
				t.Fatal("third party read message")
			}
			continue
		}
		if len(history) != 1 || history[0].Text != "YT RADIO PROBE; literal/" || history[0].Unread != (actor == recipient.ID) {
			t.Fatal("wrong participant view/read receipt", history)
		}
		data, _ := json.Marshal(history)
		if strings.Contains(string(data), "secret") || strings.Contains(string(data), "RequestID") {
			t.Fatal("private transport/account data disclosed")
		}
	}
	if err := w.AcknowledgeRadio(other.ID, id); err == nil {
		t.Fatal("third party acknowledged message")
	}
	if err := w.AcknowledgeRadio(sender.ID, id); err == nil {
		t.Fatal("sender acknowledged another recipient's message")
	}
	if err := w.AcknowledgeRadio(recipient.ID, id); err != nil {
		t.Fatal(err)
	}
	if got, err := w.CommitRadio(draft, clock.Add(time.Minute)); err != nil || got != id || len(w.Radio) != 1 || w.Radio[0].Unread {
		t.Fatal("retry duplicated or reset a delivered message", got, err)
	}
	if unread, err := w.RadioHistory(recipient.ID, 0, 20, true); err != nil || len(unread) != 0 {
		t.Fatal(unread, err)
	}
	if history, err := w.RadioHistory(recipient.ID, 0, 20, false); err != nil || len(history) != 1 {
		t.Fatal("read removed history", history, err)
	}
	after, _ := json.Marshal(w.Players)
	if string(before) != string(after) {
		t.Fatal("free radio changed ship resources/session state")
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
}

func TestRadioRejectsUnsafeTextStaleDraftAndCapacity(t *testing.T) {
	w, sender, recipient, _ := radioWorld(t)
	address := RadioAddress{ID: recipient.ID, Alias: recipient.Alias}
	for _, text := range []string{"", " ", "line\nbreak", "\x1b[31m", "caf\u00e9", strings.Repeat("x", 75)} {
		if _, err := w.PrepareRadio(sender.ID, address, text, clock); err == nil {
			t.Fatal("unsafe/oversized text accepted", text)
		}
	}
	for _, mode := range []string{"rename", "generation", "expiry", "sequence", "capacity"} {
		t.Run(mode, func(t *testing.T) {
			w, sender, recipient, _ := radioWorld(t)
			draft, _ := w.PrepareRadio(sender.ID, RadioAddress{ID: recipient.ID, Alias: recipient.Alias}, "text", clock)
			now := clock
			switch mode {
			case "rename":
				recipient.Alias = "Renamed"
			case "generation":
				sender.ShipGeneration++
			case "expiry":
				now = clock.Add(5 * time.Minute)
			case "sequence":
				w.NextRadio = math.MaxUint64
			case "capacity":
				w.Radio = make([]RadioMessage, MaxRadioMessages)
			}
			before, _ := json.Marshal(w)
			if _, err := w.CommitRadio(draft, now); err == nil {
				t.Fatal("invalid draft accepted")
			}
			after, _ := json.Marshal(w)
			if string(before) != string(after) {
				t.Fatal("failed send changed saved state")
			}
		})
	}
}

func TestRadioSearchAmbiguityDeadRecipientAndHistoryCursor(t *testing.T) {
	w, sender, recipient, _ := radioWorld(t)
	_, _ = w.Join("similar", "Enemy Two")
	if address, err := w.FindRadioRecipient(sender.ID, "Enemy"); err != nil || address.ID != recipient.ID {
		t.Fatal("exact match lost to substring ambiguity", address, err)
	}
	for _, query := range []string{"En", "all", "team", "999", ""} {
		if _, err := w.FindRadioRecipient(sender.ID, query); err == nil {
			t.Fatal("ambiguous/unsupported recipient accepted", query)
		}
	}
	if err := w.RecordDeath(DeathContext{Victim: recipient.ID, Generation: recipient.ShipGeneration, Sector: recipient.Sector, Cause: "mines"}, clock); err != nil {
		t.Fatal(err)
	}
	for i := 0; i < 2; i++ {
		address, _ := w.FindRadioRecipient(sender.ID, "2")
		draft, err := w.PrepareRadio(sender.ID, address, "After death", clock)
		if err != nil {
			t.Fatal(err)
		}
		if _, err := w.CommitRadio(draft, clock); err != nil {
			t.Fatal(err)
		}
	}
	if _, err := w.RadioHistory(recipient.ID, 0, 20, false); !errors.Is(err, ErrShipDestroyed) {
		t.Fatal("dead ship read history", err)
	}
	if err := w.ReplaceShip(recipient.ID, clock); err != nil {
		t.Fatal(err)
	}
	history, err := w.RadioHistory(recipient.ID, 1, 1, true)
	if err != nil || len(history) != 1 || history[0].ID != 2 {
		t.Fatal("account history did not survive replacement/cursor", history, err)
	}
}

func TestRadioArchiveValidation(t *testing.T) {
	for _, mode := range []string{"duplicate-id", "duplicate-request", "sequence", "token", "text", "alias", "recipient", "time"} {
		t.Run(mode, func(t *testing.T) {
			w, sender, recipient, _ := radioWorld(t)
			address := RadioAddress{ID: recipient.ID, Alias: recipient.Alias}
			for i := 0; i < 2; i++ {
				d, _ := w.PrepareRadio(sender.ID, address, "safe", clock)
				if _, err := w.CommitRadio(d, clock); err != nil {
					t.Fatal(err)
				}
			}
			switch mode {
			case "duplicate-id":
				w.Radio[1].ID = w.Radio[0].ID
			case "duplicate-request":
				w.Radio[1].RequestID = w.Radio[0].RequestID
			case "sequence":
				w.NextRadio = w.Radio[1].ID
			case "token":
				w.Radio[0].RequestID = strings.Repeat("z", 32)
			case "text":
				w.Radio[0].Text = "\x1b[2J"
			case "alias":
				w.Radio[0].FromAlias = "\x00"
			case "recipient":
				w.Radio[0].To = 999
			case "time":
				w.Radio[0].Sent = w.Created.Add(-time.Second)
			}
			if err := w.Validate(); err == nil {
				t.Fatal("malformed archive accepted")
			}
		})
	}
}

func TestRadioDuplicateExactAliasesRequirePlayerNumber(t *testing.T) {
	w, sender, recipient, _ := radioWorld(t)
	_, err := w.Join("duplicate-alias-account", "enemy")
	if err != nil {
		t.Fatal(err)
	}
	_, err = w.Join("substring-account", "Enemy Two")
	if err != nil {
		t.Fatal(err)
	}
	for i := 0; i < 30; i++ {
		if address, err := w.FindRadioRecipient(sender.ID, "Enemy"); err == nil {
			t.Fatal("ambiguous exact alias selected an account", address)
		}
	}
	address, err := w.FindRadioRecipient(sender.ID, "2")
	if err != nil || address.ID != recipient.ID {
		t.Fatal("numeric disambiguation failed", address, err)
	}
	address, err = w.FindRadioRecipient(sender.ID, "Enemy Two")
	if err != nil || address.Alias != "Enemy Two" {
		t.Fatal("unique exact match lost", address, err)
	}
}
