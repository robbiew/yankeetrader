package game

import (
	"errors"
	"slices"
	"time"
)

// commitRadioBatch stages ordinary private copies. The caller supplies its
// recipient snapshot check, which is skipped only for a fully committed retry.
func (w *World) commitRadioBatch(drafts []RadioDraft, now time.Time, validate func() error) ([]uint64, error) {
	if len(drafts) < 1 || len(drafts) > MaxActivePlayers {
		return nil, errors.New("invalid radio batch")
	}
	first := drafts[0]
	if err := w.CheckSession(first.from, first.generation, first.season); err != nil {
		return nil, err
	}
	existing := make([]uint64, len(drafts))
	found := 0
	for i, draft := range drafts {
		for _, m := range w.Radio {
			if m.From == draft.from && m.RequestID == draft.request {
				existing[i] = m.ID
				found++
				break
			}
		}
	}
	// A successful retry stays successful after a subsequent roster change.
	if found == len(drafts) {
		return existing, nil
	}
	if found != 0 {
		return nil, errors.New("incomplete radio batch; compose again")
	}
	if err := validate(); err != nil {
		return nil, err
	}
	candidate := *w
	candidate.Radio = slices.Clone(w.Radio)
	ids := make([]uint64, 0, len(drafts))
	for _, draft := range drafts {
		id, err := candidate.CommitRadio(draft, now)
		if err != nil {
			return nil, err
		}
		ids = append(ids, id)
	}
	w.Radio, w.NextRadio = candidate.Radio, candidate.NextRadio
	return ids, nil
}
