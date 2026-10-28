package door

import (
	"errors"
	"fmt"
	"strings"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func (s Session) sendRadio(id int, args []string, pending *[]string) error {
	query := strings.Join(args, " ")
	if query == "" {
		var err error
		query, err = s.classicArgument("Send a message to who? (alias search or player number) ", pending)
		if err != nil {
			return err
		}
	}
	if strings.TrimSpace(query) == "" {
		return s.Terminal.Printf("Radio cancelled.\r\n")
	}
	w, err := s.Store.View()
	if err != nil {
		return err
	}
	address, err := w.FindRadioRecipient(id, query)
	if err != nil {
		return err
	}
	answer, err := s.classicArgument(fmt.Sprintf("Send to %s (#%d)? [y/N] ", address.Alias, address.ID), pending)
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
	if err = s.Terminal.Printf("Message (one line, 1-74 ASCII characters; blank cancels): "); err != nil {
		return err
	}
	text, err := s.readLiteralLine()
	if err != nil {
		return err
	}
	if strings.TrimSpace(text) == "" {
		return s.Terminal.Printf("Radio cancelled.\r\n")
	}
	w, err = s.Store.View()
	if err != nil {
		return err
	}
	draft, err := w.PrepareRadio(id, address, text, s.Now())
	if err != nil {
		return err
	}
	if t, ok := s.Terminal.(interface{ DiscardTypeahead() error }); ok {
		if err := t.DiscardTypeahead(); err != nil {
			return err
		}
	}
	if err = s.Terminal.Printf("To: %s (#%d)\r\n%s\r\n[S] Send [A] Abort -=> ", address.Alias, address.ID, text); err != nil {
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
	err = s.Store.Update(func(w *game.World) error {
		if !time.Now().Before(s.Deadline) {
			return errors.New("session time expired; radio cancelled")
		}
		var err error
		messageID, err = w.CommitRadio(draft, s.Now())
		if err == nil && !time.Now().Before(s.Deadline) {
			return errors.New("session time expired; radio cancelled")
		}
		return err
	})
	if err != nil {
		return err
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
