package door

import (
	"errors"
	"fmt"
	"strings"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
)

func (s Session) sendRadio(id int, args []string, pending *[]string) error {
	multiline := len(args) > 1 && strings.EqualFold(args[0], "EDIT")
	if multiline {
		args = args[1:]
	}
	query := strings.Join(args, " ")
	if query == "" {
		if err := s.Terminal.Printf("For multiple lines, enter EDIT <alias, player number, TEAM or ALL>.\r\n"); err != nil {
			return err
		}
		var err error
		query, err = s.classicArgument("Send a message to who? (alias search, player number, TEAM or ALL) ", pending)
		if err != nil {
			return err
		}
	}
	if len(query) > 5 && strings.EqualFold(query[:5], "EDIT ") {
		multiline = true
		query = strings.TrimSpace(query[5:])
	}
	if strings.TrimSpace(query) == "" {
		return s.Terminal.Printf("Radio cancelled.\r\n")
	}
	w, err := s.Store.View()
	if err != nil {
		return err
	}
	isTeam := strings.EqualFold(strings.TrimSpace(query), "team")
	isBroadcast := strings.EqualFold(strings.TrimSpace(query), "all")
	var address game.RadioAddress
	var team game.TeamRadioAddress
	var broadcast game.BroadcastRadioAddress
	var label string
	if isBroadcast {
		broadcast, err = w.FindBroadcastRadioRecipients(id)
		label = fmt.Sprintf("ALL %d current active accounts (including you)", len(broadcast.Recipients))
	} else if isTeam {
		team, err = w.FindTeamRadioRecipients(id)
		if err == nil {
			label = fmt.Sprintf("team %s (#%d)", team.Name, team.ID)
		}
	} else {
		address, err = w.FindRadioRecipient(id, query)
		label = fmt.Sprintf("%s (#%d)", address.Alias, address.ID)
	}
	if err != nil {
		return err
	}
	if isTeam {
		if err = s.teamRadioRecipients(team); err != nil {
			return err
		}
	}
	answer, err := s.classicArgument(fmt.Sprintf("Send to %s? [y/N] ", label), pending)
	if err != nil {
		return err
	}
	if !strings.EqualFold(strings.TrimSpace(answer), "y") {
		return s.Terminal.Printf("Radio cancelled.\r\n")
	}
	*pending = nil
	if t, ok := s.Terminal.(interface{ DiscardTypeahead() error }); ok {
		if err := t.DiscardTypeahead(); err != nil {
			return err
		}
	}
	var lines []string
	if multiline {
		lines, err = s.radioEditor()
	} else {
		if err = s.Terminal.Printf("Message (one line, 1-74 ASCII characters; blank cancels): "); err != nil {
			return err
		}
		var line string
		line, err = s.readLiteralLine()
		if strings.TrimSpace(line) != "" {
			lines = []string{line}
		}
	}
	if err != nil {
		return err
	}
	if len(lines) == 0 {
		return s.Terminal.Printf("Radio cancelled.\r\n")
	}
	text := strings.Join(lines, "\r\n")
	w, err = s.Store.View()
	if err != nil {
		return err
	}
	var document game.RadioDocumentDraft
	var draft game.RadioDraft
	var teamDraft game.TeamRadioDraft
	var broadcastDraft game.BroadcastRadioDraft
	if multiline {
		target := game.RadioDocumentTarget{}
		if isBroadcast {
			target.Broadcast = &broadcast
		} else if isTeam {
			target.Team = &team
		} else {
			target.Direct = &address
		}
		document, err = w.PrepareRadioDocument(id, target, lines, s.Now())
	} else if isBroadcast {
		broadcastDraft, err = w.PrepareBroadcastRadio(id, broadcast, text, s.Now())
	} else if isTeam {
		teamDraft, err = w.PrepareTeamRadio(id, team, text, s.Now())
	} else {
		draft, err = w.PrepareRadio(id, address, text, s.Now())
	}
	if err != nil {
		return err
	}
	if t, ok := s.Terminal.(interface{ DiscardTypeahead() error }); ok {
		if err := t.DiscardTypeahead(); err != nil {
			return err
		}
	}
	if err = s.Terminal.Printf("To: %s\r\n", label); err != nil {
		return err
	}
	if isBroadcast {
		if err = s.Terminal.Printf("PUBLIC: This exact text and your alias will also appear in the Galactic Newspaper, visible beyond the current radio recipients.\r\nPublic sender: %s\r\n", w.Players[id].Alias); err != nil {
			return err
		}
	}
	if isTeam {
		if err = s.teamRadioRecipients(team); err != nil {
			return err
		}
	}
	if err = s.Terminal.Printf("%s\r\n[S] Send [A] Abort -=> ", text); err != nil {
		return err
	}
	answer, err = s.readLiteralLine()
	if err != nil {
		return err
	}
	if !strings.EqualFold(strings.TrimSpace(answer), "s") {
		return s.Terminal.Printf("Radio cancelled.\r\n")
	}
	var messageID uint64
	var messageIDs []uint64
	err = s.Store.Update(func(w *game.World) error {
		if !time.Now().Before(s.Deadline) {
			return errors.New("session time expired; radio cancelled")
		}
		var err error
		if multiline {
			messageIDs, err = w.CommitRadioDocument(document, s.Now())
		} else if isBroadcast {
			messageIDs, err = w.CommitBroadcastRadio(broadcastDraft, s.Now())
		} else if isTeam {
			messageIDs, err = w.CommitTeamRadio(teamDraft, s.Now())
		} else {
			messageID, err = w.CommitRadio(draft, s.Now())
		}
		if err == nil && !time.Now().Before(s.Deadline) {
			return errors.New("session time expired; radio cancelled")
		}
		return err
	})
	if multiline {
		var durability *store.DurabilityError
		if err != nil && !errors.As(err, &durability) {
			return err
		}
		public := 0
		if isBroadcast {
			public = len(lines)
		}
		if err != nil {
			return errors.Join(err, s.Terminal.Printf("%d lines saved (%d private copies, %d public entries). %s\r\n", len(lines), len(messageIDs), public, err))
		}
		return s.Terminal.Printf("Transmission successful! %d lines saved (%d private copies, %d public entries).\r\n", len(lines), len(messageIDs), public)
	}
	if err != nil {
		var durability *store.DurabilityError
		if (!isTeam && !isBroadcast) || !errors.As(err, &durability) {
			return err
		}
		if isBroadcast {
			return s.broadcastReceipt(len(messageIDs), err)
		}
		return s.Terminal.Printf("%d radio copies saved. %s\r\n", len(messageIDs), err)
	}
	if isBroadcast {
		return s.broadcastReceipt(len(messageIDs), nil)
	}
	if isTeam {
		return s.Terminal.Printf("Transmission successful! %d team copies saved.\r\n", len(messageIDs))
	}
	return s.Terminal.Printf("Transmission successful! Message #%d saved.\r\n", messageID)
}

func (s Session) displayRadio(entry game.RadioEntry) error {
	label := ""
	if entry.Unread {
		label = " [NEW]"
	}
	if err := s.Terminal.Printf("\r\nRadio #%d%s | %s\r\nMessage to: %s * From: %s\r\n%s\r\n", entry.ID, label, entry.Sent.UTC().Format("2006-01-02 15:04 UTC"), entry.ToAlias, entry.FromAlias, entry.Text); err != nil {
		return err
	}
	if entry.Incoming && entry.Unread {
		return s.Store.AcknowledgeRadio(entry.ID)
	}
	return nil
}

func (s Session) deliverRadio(id int) error {
	w, err := s.Store.View()
	if err != nil {
		return err
	}
	entries, err := w.RadioHistory(id, 0, 6, true)
	if err != nil || len(entries) == 0 {
		return err
	}
	if err = s.Terminal.Printf("\r\nNew radio messages:\r\n"); err != nil {
		return err
	}
	for _, entry := range entries[:min(5, len(entries))] {
		if err := s.displayRadio(entry); err != nil {
			return err
		}
	}
	if len(entries) > 5 {
		return s.Terminal.Printf("More unread messages remain. Use INBOX to read them.\r\n")
	}
	return nil
}

func (s Session) radioHistory(id int, args []string, unreadOnly bool) error {
	if len(args) != 0 {
		return errors.New("use MESSAGES or INBOX without arguments")
	}
	for after := uint64(0); ; {
		w, err := s.Store.View()
		if err != nil {
			return err
		}
		entries, err := w.RadioHistory(id, after, 6, unreadOnly)
		if err != nil {
			return err
		}
		if len(entries) == 0 {
			return s.Terminal.Printf("No matching radio messages.\r\n")
		}
		for _, entry := range entries[:min(5, len(entries))] {
			if err := s.displayRadio(entry); err != nil {
				return err
			}
			after = entry.ID
		}
		if len(entries) <= 5 {
			return nil
		}
		if err := s.Terminal.Printf("More messages? [Enter=more, Q=stop] "); err != nil {
			return err
		}
		answer, err := s.readLiteralLine()
		if err != nil {
			return err
		}
		if strings.TrimSpace(answer) != "" && !strings.EqualFold(strings.TrimSpace(answer), "y") {
			return nil
		}
	}
}

func (s Session) teamRadioRecipients(team game.TeamRadioAddress) error {
	if err := s.Terminal.Printf("Recipients (including you):\r\n"); err != nil {
		return err
	}
	for _, recipient := range team.Recipients {
		if err := s.Terminal.Printf("  %s (#%d)\r\n", recipient.Alias, recipient.ID); err != nil {
			return err
		}
	}
	return nil
}

// Preserve a committed storage warning even if writing its receipt also fails.
func (s Session) broadcastReceipt(copies int, committed error) error {
	if committed != nil {
		return errors.Join(committed, s.Terminal.Printf("%d broadcast copies and public newspaper entry saved with a committed storage warning. %s\r\n", copies, committed))
	}
	return s.Terminal.Printf("Transmission successful! %d broadcast copies saved. Public newspaper entry saved.\r\n", copies)
}
