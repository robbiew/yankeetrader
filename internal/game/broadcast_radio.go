package game

import (
	"errors"
	"slices"
	"sort"
	"time"
)

type BroadcastRadioAddress struct{ Recipients []RadioAddress }
type BroadcastRadioDraft struct {
	address BroadcastRadioAddress
	drafts  []RadioDraft
}

// Broadcasts are explicit copies for the current active account roster. Dead
// accounts can receive private mail for their next ship; retired accounts cannot.
func (w *World) FindBroadcastRadioRecipients(id int) (BroadcastRadioAddress, error) {
	if _, err := w.player(id); err != nil {
		return BroadcastRadioAddress{}, err
	}
	var ids []int
	for id, p := range w.Players {
		if p != nil && p.RetiredAt.IsZero() {
			ids = append(ids, id)
		}
	}
	sort.Ints(ids)
	if len(ids) < 1 || len(ids) > MaxActivePlayers {
		return BroadcastRadioAddress{}, errors.New("invalid broadcast roster")
	}
	address := BroadcastRadioAddress{}
	for _, id := range ids {
		address.Recipients = append(address.Recipients, RadioAddress{ID: id, Alias: w.Players[id].Alias})
	}
	return address, nil
}

func (w *World) PrepareBroadcastRadio(id int, address BroadcastRadioAddress, text string, now time.Time) (BroadcastRadioDraft, error) {
	current, err := w.FindBroadcastRadioRecipients(id)
	if err != nil {
		return BroadcastRadioDraft{}, err
	}
	if !slices.Equal(current.Recipients, address.Recipients) {
		return BroadcastRadioDraft{}, errors.New("broadcast recipients changed; choose and confirm again")
	}
	if err := w.prepareNews(now); err != nil {
		return BroadcastRadioDraft{}, err
	}
	if len(w.Radio) > MaxRadioMessages-len(address.Recipients) {
		return BroadcastRadioDraft{}, errors.New("radio archive has no room for the whole broadcast; no message was sent")
	}
	address.Recipients = slices.Clone(address.Recipients)
	draft := BroadcastRadioDraft{address: address}
	for _, recipient := range address.Recipients {
		d, err := w.PrepareRadio(id, recipient, text, now)
		if err != nil {
			return BroadcastRadioDraft{}, err
		}
		draft.drafts = append(draft.drafts, d)
	}
	return draft, nil
}

func (w *World) CommitBroadcastRadio(d BroadcastRadioDraft, now time.Time) ([]uint64, error) {
	if len(d.drafts) < 1 || len(d.drafts) > MaxActivePlayers || len(d.drafts) != len(d.address.Recipients) {
		return nil, errors.New("invalid broadcast draft")
	}
	// A fully committed retry must not append news again, even after pruning.
	already := false
	for _, m := range w.Radio {
		if m.From == d.drafts[0].from && m.RequestID == d.drafts[0].request {
			already = true
			break
		}
	}
	candidate := *w
	candidate.Radio = slices.Clone(w.Radio)
	candidate.News = slices.Clone(w.News)
	if !already {
		if err := candidate.prepareNews(now); err != nil {
			return nil, err
		}
	}
	ids, err := candidate.commitRadioBatch(d.drafts, now, func() error {
		current, err := w.FindBroadcastRadioRecipients(d.drafts[0].from)
		if err != nil {
			return err
		}
		if !slices.Equal(current.Recipients, d.address.Recipients) {
			return errors.New("broadcast recipients changed; compose again")
		}
		return nil
	})
	if err != nil {
		return nil, err
	}
	if !already {
		first := d.drafts[0]
		candidate.appendNews(NewsEvent{At: now.UTC(), Kind: NewsBroadcast, Alias: w.Players[first.from].Alias, BroadcastText: first.text})
	}
	w.Radio, w.NextRadio = candidate.Radio, candidate.NextRadio
	w.News, w.NextNews = candidate.News, candidate.NextNews
	return ids, nil
}
