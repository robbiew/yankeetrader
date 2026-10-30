package game

import (
	"crypto/rand"
	"encoding/hex"
	"errors"
	"math"
	"strconv"
	"strings"
	"time"
)

const MaxRadioMessages = 4096
const MaxRadioText = 74

type RadioMessage struct {
	System                   string `json:",omitempty"`
	ID                       uint64
	RequestID                string
	From, To                 int
	FromAlias, ToAlias, Text string
	Sent                     time.Time
	Unread                   bool
}

// RadioEntry exposes only a participant's history, without read receipts for
// senders or account identity/session fields.
type RadioEntry struct {
	ID                       uint64
	FromAlias, ToAlias, Text string
	Sent                     time.Time
	Incoming, Unread         bool
}

type RadioAddress struct {
	ID    int
	Alias string
}

type RadioDraft struct {
	from, to             int
	generation           uint64
	season               uint64
	alias, text, request string
	expires              time.Time
}

func validRadioText(text string) bool {
	if len(text) == 0 || len(text) > MaxRadioText || strings.TrimSpace(text) == "" {
		return false
	}
	for _, c := range []byte(text) {
		if c < 32 || c > 126 {
			return false
		}
	}
	return true
}

func (w *World) validateRadio() error {
	if w.NextRadio == 0 || len(w.Radio) > MaxRadioMessages {
		return errors.New("invalid radio archive")
	}
	last := uint64(0)
	requests := map[string]bool{}
	for _, m := range w.Radio {
		system := m.System == "super-planet"
		if (m.System != "" && !system) || (system && (m.From != 0 || m.FromAlias != "Super Lottery")) || (!system && m.From == 0) {
			return errors.New("invalid system radio")
		}
		_, err := hex.DecodeString(m.RequestID)
		key := strconv.Itoa(m.From) + ":" + m.RequestID
		if m.ID <= last || m.ID >= w.NextRadio || err != nil || len(m.RequestID) != 32 || requests[key] || (!system && w.Players[m.From] == nil) || w.Players[m.To] == nil || !clean(m.FromAlias) || !clean(m.ToAlias) || !validRadioText(m.Text) || m.Sent.IsZero() || m.Sent.Before(w.Created) {
			return errors.New("invalid radio message")
		}
		requests[key] = true
		last = m.ID
	}
	return nil
}

func (w *World) FindRadioRecipient(id int, query string) (RadioAddress, error) {
	p, err := w.player(id)
	if err != nil {
		return RadioAddress{}, err
	}
	query = strings.TrimSpace(query)
	if strings.EqualFold(query, "team") && p.Team == 0 {
		return RadioAddress{}, errors.New("you don't belong to a team")
	}
	if strings.EqualFold(query, "all") || strings.EqualFold(query, "team") {
		return RadioAddress{}, errors.New("broadcast and team radio are not available yet; choose one player")
	}
	if n, err := strconv.Atoi(query); err == nil {
		if target := w.Players[n]; target != nil && target.RetiredAt.IsZero() {
			return RadioAddress{ID: n, Alias: target.Alias}, nil
		}
		return RadioAddress{}, errors.New("radio recipient not found")
	}
	if query == "" {
		return RadioAddress{}, errors.New("choose a recipient alias or player number")
	}
	var matches, exact []RadioAddress
	for _, target := range w.Players {
		if !target.RetiredAt.IsZero() {
			continue
		}
		if strings.EqualFold(query, target.Alias) {
			exact = append(exact, RadioAddress{ID: target.ID, Alias: target.Alias})
		}
		if strings.Contains(strings.ToLower(target.Alias), strings.ToLower(query)) {
			matches = append(matches, RadioAddress{ID: target.ID, Alias: target.Alias})
		}
	}
	if len(exact) > 1 {
		return RadioAddress{}, errors.New("more than one player has that exact alias; enter a player number")
	}
	if len(exact) > 0 {
		matches = exact
	}
	if len(matches) != 1 {
		return RadioAddress{}, errors.New("recipient search needs one match; enter an exact alias or player number")
	}
	return matches[0], nil
}

func (w *World) PrepareRadio(id int, address RadioAddress, text string, now time.Time) (RadioDraft, error) {
	p, err := w.player(id)
	if err != nil {
		return RadioDraft{}, err
	}
	to := w.Players[address.ID]
	if to == nil || !to.RetiredAt.IsZero() || to.Alias != address.Alias {
		return RadioDraft{}, errors.New("recipient changed; choose and confirm again")
	}
	if !validRadioText(text) {
		return RadioDraft{}, errors.New("use one printable ASCII line of 1 to 74 characters")
	}
	if now.IsZero() || now.Before(w.Created) {
		return RadioDraft{}, errors.New("invalid radio time")
	}
	if len(w.Radio) >= MaxRadioMessages {
		return RadioDraft{}, errors.New("radio archive is full; no message was sent")
	}
	var token [16]byte
	if _, err := rand.Read(token[:]); err != nil {
		return RadioDraft{}, err
	}
	return RadioDraft{from: id, to: to.ID, season: w.Season, generation: p.ShipGeneration, alias: to.Alias, text: text, request: hex.EncodeToString(token[:]), expires: now.Add(5 * time.Minute)}, nil
}

// CommitRadio is idempotent for one prepared draft. It must run in Store.Update.
func (w *World) CommitRadio(d RadioDraft, now time.Time) (uint64, error) {
	if err := w.CheckSession(d.from, d.generation, d.season); err != nil {
		return 0, err
	}
	for _, m := range w.Radio {
		if m.From == d.from && m.RequestID == d.request {
			return m.ID, nil
		}
	}
	to := w.Players[d.to]
	if to == nil || !to.RetiredAt.IsZero() || to.Alias != d.alias || now.IsZero() || now.Before(w.Created) || !now.Before(d.expires) || !validRadioText(d.text) || len(d.request) != 32 {
		return 0, errors.New("radio draft expired or recipient changed; compose again")
	}
	if len(w.Radio) >= MaxRadioMessages || w.NextRadio == 0 || w.NextRadio == math.MaxUint64 {
		return 0, errors.New("radio archive is full; no message was sent")
	}
	messageID := w.NextRadio
	w.Radio = append(w.Radio, RadioMessage{ID: messageID, RequestID: d.request, From: d.from, To: d.to, FromAlias: w.Players[d.from].Alias, ToAlias: to.Alias, Text: d.text, Sent: now.UTC(), Unread: true})
	w.NextRadio++
	return messageID, nil
}

func (w *World) RadioHistory(id int, after uint64, limit int, unreadOnly bool) ([]RadioEntry, error) {
	if _, err := w.player(id); err != nil {
		return nil, err
	}
	if limit < 1 || limit > 20 {
		return nil, errors.New("radio history page must contain 1 to 20 messages")
	}
	var entries []RadioEntry
	for _, m := range w.Radio {
		if m.ID <= after || m.From != id && m.To != id || unreadOnly && (m.To != id || !m.Unread) {
			continue
		}
		entries = append(entries, RadioEntry{ID: m.ID, FromAlias: m.FromAlias, ToAlias: m.ToAlias, Text: m.Text, Sent: m.Sent, Incoming: m.To == id, Unread: m.To == id && m.Unread})
		if len(entries) == limit {
			break
		}
	}
	return entries, nil
}

func (w *World) AcknowledgeRadio(id int, messageID uint64) error {
	if _, err := w.player(id); err != nil {
		return err
	}
	for i := range w.Radio {
		if w.Radio[i].ID == messageID && w.Radio[i].To == id {
			w.Radio[i].Unread = false
			return nil
		}
	}
	return errors.New("received radio message not found")
}
