package game

import (
	"encoding/json"
	"math"
	"reflect"
	"strings"
	"testing"
	"time"
)

func teamRadioWorld(t *testing.T) (*World, *Player, *Player, *Player) {
	t.Helper()
	w, sender, recipient, other := radioWorld(t)
	if err := w.CreateTeam(sender.ID, "Orion", "ABCD"); err != nil {
		t.Fatal(err)
	}
	if err := w.JoinTeam(recipient.ID, sender.Team, "ABCD"); err != nil {
		t.Fatal(err)
	}
	return w, sender, recipient, other
}

func TestTeamRadioCopiesRecipientsAndIndependentReadState(t *testing.T) {
	w, sender, recipient, other := teamRadioWorld(t)
	before, _ := json.Marshal(w.Players)
	address, err := w.FindTeamRadioRecipients(sender.ID)
	if err != nil || len(address.Recipients) != 2 {
		t.Fatal(address, err)
	}
	draft, err := w.PrepareTeamRadio(sender.ID, address, "Team text; literal/", clock)
	if err != nil {
		t.Fatal(err)
	}
	address.Recipients[0].Alias = "tampered"
	ids, err := w.CommitTeamRadio(draft, clock)
	if err != nil || !reflect.DeepEqual(ids, []uint64{1, 2}) {
		t.Fatal(ids, err)
	}
	for _, id := range []int{sender.ID, recipient.ID, other.ID} {
		incoming, err := w.RadioHistory(id, 0, 20, true)
		if err != nil {
			t.Fatal(err)
		}
		want := 1
		if id == other.ID {
			want = 0
		}
		if len(incoming) != want {
			t.Fatal(id, incoming)
		}
	}
	if err := w.AcknowledgeRadio(sender.ID, ids[0]); err != nil {
		t.Fatal(err)
	}
	if !w.Radio[1].Unread || w.Radio[0].Unread {
		t.Fatal("one recipient consumed another's mail")
	}
	if err := w.AcknowledgeRadio(other.ID, ids[1]); err == nil {
		t.Fatal("outsider acknowledged team mail")
	}
	after, _ := json.Marshal(w.Players)
	if string(before) != string(after) {
		t.Fatal("radio charged resources or changed membership")
	}
	// Retries do not recreate read flags, even after the team changes.
	if err := w.LeaveTeam(sender.ID, sender.Team); err != nil {
		t.Fatal(err)
	}
	retry, err := w.CommitTeamRadio(draft, clock.Add(time.Minute))
	if err != nil || !reflect.DeepEqual(ids, retry) || len(w.Radio) != 2 || w.Radio[0].Unread {
		t.Fatal(retry, err)
	}
	// New members cannot read old copies; former members retain their own copy.
	recipient.Team = 0
	other.Team = address.ID
	incoming, err := w.RadioHistory(other.ID, 0, 20, false)
	if err != nil || len(incoming) != 0 {
		t.Fatal("new member inherited old mail", incoming, err)
	}
	incoming, err = w.RadioHistory(recipient.ID, 0, 20, true)
	if err != nil || len(incoming) != 1 {
		t.Fatal("leaving lost mail", incoming, err)
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
}

func TestTeamRadioStaleRosterAndLateFailureAreAtomic(t *testing.T) {
	for _, mode := range []string{"leave", "join", "rename-player", "rename-team", "recreate", "sender-team", "expiry", "generation", "season", "sequence", "capacity", "invalid-text"} {
		t.Run(mode, func(t *testing.T) {
			w, sender, recipient, other := teamRadioWorld(t)
			address, _ := w.FindTeamRadioRecipients(sender.ID)
			draft, err := w.PrepareTeamRadio(sender.ID, address, "Private team text", clock)
			if err != nil {
				t.Fatal(err)
			}
			now := clock
			switch mode {
			case "leave":
				recipient.Team = 0
			case "join":
				other.Team = sender.Team
			case "rename-player":
				recipient.Alias = "Changed"
			case "rename-team":
				w.Teams[sender.Team].Name = "Changed"
			case "recreate":
				hash, err := hashTeamPassword("ABCD")
				if err != nil {
					t.Fatal(err)
				}
				w.Teams[sender.Team].PasswordHash = hash
			case "sender-team":
				sender.Team = 0
			case "expiry":
				now = clock.Add(5 * time.Minute)
			case "generation":
				sender.ShipGeneration++
			case "season":
				w.Season++
			case "sequence":
				w.NextRadio = math.MaxUint64 - 1
			case "capacity":
				w.Radio = make([]RadioMessage, MaxRadioMessages-1)
			case "invalid-text":
				draft.drafts[1].text = "\x1b"
			}
			before, _ := json.Marshal(w)
			if _, err := w.CommitTeamRadio(draft, now); err == nil {
				t.Fatal("stale/invalid batch committed")
			}
			after, _ := json.Marshal(w)
			if string(before) != string(after) {
				t.Fatal("partial team delivery")
			}
		})
	}
}

func TestTeamRadioPreparationRechecksConfirmationAndText(t *testing.T) {
	w, sender, _, other := teamRadioWorld(t)
	if _, err := w.FindTeamRadioRecipients(other.ID); err == nil {
		t.Fatal("outsider selected a team")
	}
	address, _ := w.FindTeamRadioRecipients(sender.ID)
	for _, text := range []string{"", " ", strings.Repeat("x", 75), "line\nbreak", "\x1b[2J"} {
		if _, err := w.PrepareTeamRadio(sender.ID, address, text, clock); err == nil {
			t.Fatal("invalid text accepted")
		}
	}
	other.Team = sender.Team
	if _, err := w.PrepareTeamRadio(sender.ID, address, "text", clock); err == nil {
		t.Fatal("unconfirmed recipient added")
	}
	address, _ = w.FindTeamRadioRecipients(sender.ID)
	w.Radio = make([]RadioMessage, MaxRadioMessages-2)
	if _, err := w.PrepareTeamRadio(sender.ID, address, "text", clock); err == nil {
		t.Fatal("inadequate batch capacity accepted")
	}
}
