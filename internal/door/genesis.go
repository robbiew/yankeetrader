package door

import (
	"errors"
	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
)

// genesis returns done on a committed reset, including failed receipt output or
// directory-sync warning. No old-session view or logout publication may follow.
func (s Session) genesis(args []string, pending *[]string) (done bool, err error) {
	if len(args) != 0 {
		return false, errors.New("use GENESIS with no arguments; confirmation must be entered separately")
	}
	entry, err := s.Store.PrepareGenesis(s.Now, s.Deadline)
	if err != nil {
		return false, err
	}
	defer s.Store.CancelGenesis(entry)
	*pending = nil
	if terminal, ok := s.Terminal.(interface{ DiscardTypeahead() error }); ok {
		if err = terminal.DiscardTypeahead(); err != nil {
			return false, err
		}
	}
	if err = s.Terminal.Printf("GENESIS ends season %d and replaces the ENTIRE universe. All players, teams, assets and messages will be removed. Your public winner result will be saved (%d ports; required %d). Reconnect to join the new season.\r\nType GENESIS to confirm this reset (blank cancels): ", entry.Season, len(entry.Ports), entry.Threshold); err != nil {
		return false, err
	}
	answer, err := s.readLiteralLine()
	if err != nil {
		return false, err
	}
	if answer != "GENESIS" {
		return false, s.Terminal.Printf("Genesis cancelled; universe unchanged.\r\n")
	}
	out, err := s.Store.ResetSeason(entry, s.Now, s.Deadline)
	var committed *store.DurabilityError
	if err != nil && !errors.As(err, &committed) {
		return false, err
	}
	return true, s.genesisReceipt(out, err)
}
func (s Session) genesisReceipt(out game.GenesisReceipt, err error) error {
	var committed *store.DurabilityError
	if err != nil && !errors.As(err, &committed) {
		return err
	}
	e := s.Terminal.Printf("Genesis saved: %s won season %d with %d ports (required %d), score %d. Season %d is ready. This login has ended; reconnect to join.\r\n", out.Result.Winner, out.Result.Season, out.Result.Ports, out.Result.Threshold, out.Result.Score, out.NewSeason)
	return errors.Join(err, e)
}
func (s Session) seasonHistory(args []string) error {
	if len(args) != 0 {
		return errors.New("use SEASONS with no arguments")
	}
	w, err := s.Store.View()
	if err != nil {
		return err
	}
	if err = s.Terminal.Printf("Current season: %d. Genesis requirement: %d non-Earth ports (0 = disabled).\r\n", w.Season, w.GenesisThreshold()); err != nil {
		return err
	}
	if len(w.SeasonResults) == 0 {
		return s.Terminal.Printf("No completed seasons.\r\n")
	}
	// Bounded 128 rows, paginate without holding a world lock, then revalidate the
	// session on every page so a concurrent reset cannot resume an obsolete login.
	for i, r := range w.SeasonResults {
		if i > 0 && i%20 == 0 {
			if err = s.Terminal.Printf("[Enter for more season results] "); err != nil {
				return err
			}
			if _, err = s.readLiteralLine(); err != nil {
				return err
			}
			// The initial View validates page one; only a paging pause needs a
			// new live check. Rows within a page share the immutable snapshot.
			if _, err = s.Store.View(); err != nil {
				return err
			}
		}
		if err = s.Terminal.Printf("Season %d: %s (#%d); %d ports / %d required; score %d; %s to %s UTC.\r\n", r.Season, r.Winner, r.Player, r.Ports, r.Threshold, r.Score, r.Started.UTC().Format("2006-01-02 15:04:05"), r.Ended.UTC().Format("2006-01-02 15:04:05")); err != nil {
			return err
		}
	}
	return nil
}
