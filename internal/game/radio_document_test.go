package game

import (
	"encoding/json"
	"math"
	"reflect"
	"testing"
	"time"
)

func documentFixture(t *testing.T, scope string) (*World, *Player, RadioDocumentTarget) {
	t.Helper()
	w, p, q, _ := radioWorld(t)
	target := RadioDocumentTarget{}
	switch scope {
	case "direct":
		a, _ := w.FindRadioRecipient(p.ID, q.Alias)
		target.Direct = &a
	case "team":
		if err := w.CreateTeam(p.ID, "Orion", "ABCD"); err != nil {
			t.Fatal(err)
		}
		if err := w.JoinTeam(q.ID, p.Team, "ABCD"); err != nil {
			t.Fatal(err)
		}
		a, _ := w.FindTeamRadioRecipients(p.ID)
		target.Team = &a
	case "all":
		a, _ := w.FindBroadcastRadioRecipients(p.ID)
		target.Broadcast = &a
	}
	return w, p, target
}
func TestRadioDocumentAtomicScopesAndRetry(t *testing.T) {
	for _, scope := range []string{"direct", "team", "all"} {
		t.Run(scope, func(t *testing.T) {
			w, p, target := documentFixture(t, scope)
			before, _ := json.Marshal(w.Players)
			lines := []string{"FIRST; literal/", "SECOND"}
			d, err := w.PrepareRadioDocument(p.ID, target, lines, clock)
			if err != nil {
				t.Fatal(err)
			}
			lines[0] = "tampered"
			ids, err := w.CommitRadioDocument(d, clock)
			if err != nil {
				t.Fatal(err)
			}
			recipients := 1
			if scope == "team" {
				recipients = 2
			}
			if scope == "all" {
				recipients = 3
			}
			if len(ids) != recipients*2 || len(w.Radio) != len(ids) {
				t.Fatal(ids)
			}
			for i, m := range w.Radio {
				want := "FIRST; literal/"
				if i >= recipients {
					want = "SECOND"
				}
				if m.Text != want {
					t.Fatal(w.Radio)
				}
			}
			news := 0
			for _, n := range w.News {
				if n.Kind == NewsBroadcast {
					news++
				}
			}
			if (scope == "all" && news != 2) || (scope != "all" && news != 0) {
				t.Fatal(w.News)
			}
			if err := w.AcknowledgeRadio(w.Radio[0].To, ids[0]); err != nil {
				t.Fatal(err)
			}
			beforeRetry, _ := json.Marshal(w)
			retry, err := w.CommitRadioDocument(d, clock.Add(time.Minute))
			if err != nil || !reflect.DeepEqual(ids, retry) {
				t.Fatal(retry, err)
			}
			afterRetry, _ := json.Marshal(w)
			if string(beforeRetry) != string(afterRetry) {
				t.Fatal("retry changed archives/read flags")
			}
			after, _ := json.Marshal(w.Players)
			if string(before) != string(after) {
				t.Fatal("document spent assets")
			}
			if err := w.Validate(); err != nil {
				t.Fatal(err)
			}
		})
	}
}
func TestRadioDocumentRejectsLateFailureWithoutPublishing(t *testing.T) {
	for _, scope := range []string{"direct", "team", "all"} {
		for _, mode := range []string{"expiry", "generation", "capacity", "sequence", "partial", "bad-last-line", "news-sequence"} {
			t.Run(scope+"/"+mode, func(t *testing.T) {
				w, p, target := documentFixture(t, scope)
				d, err := w.PrepareRadioDocument(p.ID, target, []string{"FIRST", "SECOND"}, clock)
				if err != nil {
					t.Fatal(err)
				}
				now := clock
				switch mode {
				case "expiry":
					now = clock.Add(5 * time.Minute)
				case "generation":
					p.ShipGeneration++
				case "capacity":
					w.Radio = make([]RadioMessage, MaxRadioMessages-1)
				case "sequence":
					w.NextRadio = math.MaxUint64 - 1
				case "news-sequence":
					if scope != "all" {
						return
					}
					w.NextNews = math.MaxUint64 - 1
				case "partial":
					requests := d.requests()
					if _, err := w.CommitRadio(requests[0], clock); err != nil {
						t.Fatal(err)
					}
				case "bad-last-line":
					switch scope {
					case "direct":
						d.direct[1].text = "\x1b"
					case "team":
						d.team[1].drafts[0].text = "\x1b"
					case "all":
						d.broadcast[1].drafts[0].text = "\x1b"
					}
				}
				before, _ := json.Marshal(w)
				if _, err := w.CommitRadioDocument(d, now); err == nil {
					t.Fatal("invalid document accepted")
				}
				after, _ := json.Marshal(w)
				if string(before) != string(after) {
					t.Fatal("partial document published")
				}
			})
		}
	}
}
func TestRadioDocumentBoundsAndEmptyDraft(t *testing.T) {
	w, p, target := documentFixture(t, "direct")
	for _, lines := range [][]string{nil, {""}, {"\n"}, {"\x1b"}, make([]string, 21)} {
		if _, err := w.PrepareRadioDocument(p.ID, target, lines, clock); err == nil {
			t.Fatal(lines)
		}
	}
	lines := make([]string, 20)
	for i := range lines {
		lines[i] = "valid"
	}
	d, err := w.PrepareRadioDocument(p.ID, target, lines, clock)
	if err != nil {
		t.Fatal(err)
	}
	if ids, err := w.CommitRadioDocument(d, clock); err != nil || len(ids) != 20 {
		t.Fatal(ids, err)
	}
	if _, err := w.CommitRadioDocument(RadioDocumentDraft{}, clock); err == nil {
		t.Fatal("empty document accepted")
	}
}
