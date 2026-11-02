package game

import (
	"errors"
	"slices"
	"time"
)

const MaxRadioLines = 20

type RadioDocumentTarget struct {
	Direct    *RadioAddress
	Team      *TeamRadioAddress
	Broadcast *BroadcastRadioAddress
}

type RadioDocumentDraft struct {
	direct    []RadioDraft
	team      []TeamRadioDraft
	broadcast []BroadcastRadioDraft
}

func (d RadioDocumentDraft) requests() []RadioDraft {
	var all []RadioDraft
	all = append(all, d.direct...)
	for _, line := range d.team {
		all = append(all, line.drafts...)
	}
	for _, line := range d.broadcast {
		all = append(all, line.drafts...)
	}
	return all
}

func (w *World) PrepareRadioDocument(id int, target RadioDocumentTarget, lines []string, now time.Time) (RadioDocumentDraft, error) {
	kinds := 0
	for _, set := range []bool{target.Direct != nil, target.Team != nil, target.Broadcast != nil} {
		if set {
			kinds++
		}
	}
	if kinds != 1 || len(lines) < 1 || len(lines) > MaxRadioLines {
		return RadioDocumentDraft{}, errors.New("choose one recipient scope and 1 to 20 lines")
	}
	for _, line := range lines {
		if !validRadioText(line) {
			return RadioDocumentDraft{}, errors.New("each line must contain 1 to 74 printable ASCII characters")
		}
	}
	view := *w
	view.News = slices.Clone(w.News)
	view.Radio = slices.Clone(w.Radio)
	d := RadioDocumentDraft{}
	for _, line := range lines {
		switch {
		case target.Direct != nil:
			draft, err := view.PrepareRadio(id, *target.Direct, line, now)
			if err != nil {
				return RadioDocumentDraft{}, err
			}
			d.direct = append(d.direct, draft)
		case target.Team != nil:
			draft, err := view.PrepareTeamRadio(id, *target.Team, line, now)
			if err != nil {
				return RadioDocumentDraft{}, err
			}
			d.team = append(d.team, draft)
		case target.Broadcast != nil:
			draft, err := view.PrepareBroadcastRadio(id, *target.Broadcast, line, now)
			if err != nil {
				return RadioDocumentDraft{}, err
			}
			d.broadcast = append(d.broadcast, draft)
		}
	}
	if len(w.Radio) > MaxRadioMessages-len(d.requests()) {
		return RadioDocumentDraft{}, errors.New("radio archive has no room for every line and recipient")
	}
	return d, nil
}

func (w *World) CommitRadioDocument(d RadioDocumentDraft, now time.Time) ([]uint64, error) {
	kinds, lines := 0, 0
	for _, n := range []int{len(d.direct), len(d.team), len(d.broadcast)} {
		if n > 0 {
			kinds++
			lines = n
		}
	}
	requests := d.requests()
	if kinds != 1 || lines < 1 || lines > MaxRadioLines || len(requests) < 1 || len(requests) > MaxRadioLines*MaxActivePlayers {
		return nil, errors.New("invalid radio document")
	}
	first := requests[0]
	if err := w.CheckSession(first.from, first.generation, first.season); err != nil {
		return nil, err
	}
	found := 0
	existing := make([]uint64, len(requests))
	for i, r := range requests {
		for _, m := range w.Radio {
			if m.From == r.from && m.RequestID == r.request {
				found++
				existing[i] = m.ID
				break
			}
		}
	}
	if found == len(requests) {
		return existing, nil
	}
	if found != 0 {
		return nil, errors.New("incomplete radio document; no additional lines sent")
	}
	candidate := *w
	candidate.Radio = slices.Clone(w.Radio)
	candidate.News = slices.Clone(w.News)
	var ids []uint64
	for _, line := range d.direct {
		id, err := candidate.CommitRadio(line, now)
		if err != nil {
			return nil, err
		}
		ids = append(ids, id)
	}
	for _, line := range d.team {
		batch, err := candidate.CommitTeamRadio(line, now)
		if err != nil {
			return nil, err
		}
		ids = append(ids, batch...)
	}
	for _, line := range d.broadcast {
		batch, err := candidate.CommitBroadcastRadio(line, now)
		if err != nil {
			return nil, err
		}
		ids = append(ids, batch...)
	}
	w.Radio, w.NextRadio = candidate.Radio, candidate.NextRadio
	w.News, w.NextNews = candidate.News, candidate.NextNews
	return ids, nil
}
