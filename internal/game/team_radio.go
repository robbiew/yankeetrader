package game

import (
	"errors"
	"slices"
	"time"
)

// TeamRadioAddress is a confirmation snapshot, not a live distribution list.
// Private metadata prevents a deleted/recreated team from inheriting a draft.
type TeamRadioAddress struct {
	ID         int
	Name       string
	Recipients []RadioAddress
	team       Team
}

type TeamRadioDraft struct {
	address TeamRadioAddress
	drafts  []RadioDraft
}

func (w *World) FindTeamRadioRecipients(id int) (TeamRadioAddress, error) {
	p, err := w.player(id)
	if err != nil {
		return TeamRadioAddress{}, err
	}
	team := w.Teams[p.Team]
	if p.Team == 0 || team == nil {
		return TeamRadioAddress{}, errors.New("you don't belong to a team")
	}
	address := TeamRadioAddress{ID: team.ID, Name: team.Name, team: *team}
	for _, member := range w.teamMembers(team.ID) {
		target := w.Players[member]
		if !target.RetiredAt.IsZero() {
			continue
		}
		address.Recipients = append(address.Recipients, RadioAddress{ID: member, Alias: target.Alias})
	}
	if len(address.Recipients) < 1 || len(address.Recipients) > 4 {
		return TeamRadioAddress{}, errors.New("invalid team radio roster")
	}
	return address, nil
}

func sameTeamRadioAddress(a, b TeamRadioAddress) bool {
	return a.ID == b.ID && a.Name == b.Name && a.team == b.team && slices.Equal(a.Recipients, b.Recipients)
}

func (w *World) PrepareTeamRadio(id int, address TeamRadioAddress, text string, now time.Time) (TeamRadioDraft, error) {
	current, err := w.FindTeamRadioRecipients(id)
	if err != nil {
		return TeamRadioDraft{}, err
	}
	if !sameTeamRadioAddress(current, address) {
		return TeamRadioDraft{}, errors.New("team or recipients changed; choose and confirm again")
	}
	if len(w.Radio) > MaxRadioMessages-len(address.Recipients) {
		return TeamRadioDraft{}, errors.New("radio archive has no room for the whole team; no message was sent")
	}
	address.Recipients = slices.Clone(address.Recipients)
	draft := TeamRadioDraft{address: address}
	for _, recipient := range address.Recipients {
		d, err := w.PrepareRadio(id, recipient, text, now)
		if err != nil {
			return TeamRadioDraft{}, err
		}
		draft.drafts = append(draft.drafts, d)
	}
	return draft, nil
}

// CommitTeamRadio stages ordinary private messages and publishes the entire
// batch or none. Existing mailbox validation and independent read flags apply.
// No group membership or shared read receipt is persisted in the radio archive.
func (w *World) CommitTeamRadio(d TeamRadioDraft, now time.Time) ([]uint64, error) {
	if len(d.drafts) < 1 || len(d.drafts) > 4 || len(d.drafts) != len(d.address.Recipients) {
		return nil, errors.New("invalid team radio draft")
	}
	return w.commitRadioBatch(d.drafts, now, func() error {
		current, err := w.FindTeamRadioRecipients(d.drafts[0].from)
		if err != nil {
			return err
		}
		if !sameTeamRadioAddress(current, d.address) {
			return errors.New("team or recipients changed; compose again")
		}
		return nil
	})
}
