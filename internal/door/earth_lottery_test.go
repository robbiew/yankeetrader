package door

import (
	"errors"
	"io"
	"strings"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
)

func lotterySession(t *testing.T, term *scripted) (Session, int, string) {
	t.Helper()
	s, id, token := portSession(t, true)
	s.Terminal = term
	s.Store = s.Store.ForShip(id, 0, 1)
	return s, id, token
}
func TestPaidLotteryDoorExactSavedReceiptAndFreshConfirmation(t *testing.T) {
	for _, classic := range []bool{false, true} {
		for _, answer := range []string{"y", "Y", "n", "", "y;q"} {
			t.Run(strings.Join([]string{map[bool]string{true: "classic", false: "compact"}[classic], answer}, "/"), func(t *testing.T) {
				term := &scripted{lines: []string{answer}}
				s, id, token := lotterySession(t, term)
				s.Classic = classic
				pending := []string{"y", "q"}
				calls := 0
				err := s.lotteryWithDraw(token, []string{"111111"}, &pending, func() (int, error) { calls++; return 1, nil })
				w, e := s.Store.View()
				if e != nil {
					t.Fatal(e)
				}
				p := w.Players[id]
				out := term.output.String()
				yes := strings.EqualFold(answer, "y")
				if err != nil || len(pending) != 0 {
					t.Fatal(err, pending)
				}
				if !yes {
					if p.Credits != 10000 || p.LotteryPlays != 0 || calls != 0 || strings.Contains(out, "Lottery saved:") {
						t.Fatal("false receipt", out)
					}
					return
				}
				if calls != 6 || p.Credits != 100009995 || p.LotteryPlays != 1 || p.Turns != 499 || !strings.Contains(out, "ticket 111111; drawn 111111; matches 6. Fee: 5. Gross prize: 100000000. Awarded: 100000000. Credit cap reduction: 0. Balance: 100009995. Plays remaining: 4 (UTC).") {
					t.Fatal(out, p)
				}
			})
		}
	}
}
func TestPaidLotteryDoorCancellationFailuresAndCapNews(t *testing.T) {
	for _, mode := range []string{"blank", "invalid", "args", "eof", "poor", "expired", "draw-error"} {
		t.Run(mode, func(t *testing.T) {
			term := &scripted{lines: []string{"y"}}
			s, id, token := lotterySession(t, term)
			args := []string{"111111"}
			switch mode {
			case "blank":
				args = nil
				term.lines = []string{""}
			case "invalid":
				args = []string{"12.456"}
			case "args":
				args = []string{"111111", "y"}
			case "eof":
				term.lines = nil
			case "poor":
				if err := s.Store.Update(func(w *game.World) error { w.Players[id].Credits = 4; return nil }); err != nil {
					t.Fatal(err)
				}
			case "expired":
				at := s.Now()
				n := 0
				s.Deadline = time.Now().Add(20 * time.Millisecond)
				s.Now = func() time.Time {
					n++
					if n == 2 {
						time.Sleep(40 * time.Millisecond)
					}
					return at
				}
			}
			before, _ := s.Store.View()
			cash := before.Players[id].Credits
			err := s.lotteryWithDraw(token, args, &[]string{}, func() (int, error) {
				if mode != "draw-error" {
					t.Error("unexpected draw")
				}
				return 0, errors.New("no entropy")
			})
			if mode != "blank" && err == nil {
				t.Fatal("expected rejection")
			}
			if mode == "eof" && !errors.Is(err, io.EOF) {
				t.Fatal(err)
			}
			after, _ := s.Store.View()
			if after.Players[id].Credits != cash || after.Players[id].LotteryPlays != 0 || strings.Contains(term.output.String(), "Lottery saved:") {
				t.Fatal("false receipt", err, term.output.String())
			}
		})
	}
	term := &scripted{lines: []string{"y"}}
	s, id, token := lotterySession(t, term)
	if err := s.Store.Update(func(w *game.World) error { w.Players[id].Credits = game.MaxMoney; return nil }); err != nil {
		t.Fatal(err)
	}
	if err := s.lotteryWithDraw(token, []string{"111111"}, &[]string{}, func() (int, error) { return 1, nil }); err != nil {
		t.Fatal(err)
	}
	if err := s.newspaper(id, []string{"today"}, &[]string{}); err != nil {
		t.Fatal(err)
	}
	out := term.output.String()
	if !strings.Contains(out, "Awarded: 5. Credit cap reduction: 99999995.") || !strings.Contains(out, "Won 5 credits in the paid lottery (6 matches; gross prize 100000000).") {
		t.Fatal(out)
	}
}
func TestPaidLotteryClassicItemAndCompactDispatch(t *testing.T) {
	term := &scripted{lines: []string{"n", "0"}}
	s, id, token := lotterySession(t, term)
	s.Classic = true
	if err := s.earthShop(id, token, &[]string{"4", "000000", "y", "0"}); err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(term.output.String(), "Ticket 000000 costs 5 credits") || strings.Contains(term.output.String(), "Lottery saved:") {
		t.Fatal(term.output.String())
	}
	term = &scripted{lines: []string{"p;lottery 000000;y;q", "n", "q"}}
	s, id, _ = lotterySession(t, term)
	s.Identity = "port-test"
	s.Alias = "Trader"
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	w, _ := s.Store.View()
	if w.Players[id].Credits != 10000 || w.Players[id].LotteryPlays != 0 || !strings.Contains(term.output.String(), "Ticket 000000 costs 5 credits") {
		t.Fatal(term.output.String())
	}
}

// Store tests exercise actual post-rename faults. This receipt-boundary injection
// checks the main loop's handling of that same committed-warning type without
// adding a production fault switch to storage or the terminal.
type lotteryWarningTerminal struct {
	scripted
	outputError error
}

func (t *lotteryWarningTerminal) Printf(format string, args ...any) error {
	if err := t.scripted.Printf(format, args...); err != nil {
		return err
	}
	if strings.Contains(format, "Lottery saved:") {
		return errors.Join(&store.DurabilityError{Err: errors.New("simulated committed storage warning")}, t.outputError)
	}
	return nil
}
func TestPaidLotterySessionStopsAfterCommittedWarning(t *testing.T) {
	s, id, _ := portSession(t, true)
	term := &lotteryWarningTerminal{scripted: scripted{lines: []string{"p;lottery 000000", "y", "lottery 000000", "y", "q"}}}
	s.Terminal = term
	s.Identity = "port-test"
	s.Alias = "Trader"
	err := s.Run()
	var committed *store.DurabilityError
	if !errors.As(err, &committed) {
		t.Fatal("continued after committed warning", err, term.output.String())
	}
	w, e := s.Store.View()
	if e != nil {
		t.Fatal(e)
	}
	if w.Players[id].LotterySequence != 1 || w.Players[id].LotteryPlays != 1 || len(term.lines) != 3 || strings.Count(term.output.String(), "Lottery saved:") != 1 {
		t.Fatal("continued or lost committed settlement", term.output.String())
	}
}

type lotteryOutputFailure struct {
	scripted
	failure error
}

func (t *lotteryOutputFailure) Printf(format string, args ...any) error {
	if strings.Contains(format, "Lottery saved:") {
		return t.failure
	}
	return t.scripted.Printf(format, args...)
}
func TestLotteryReceiptWriteRetainsCommittedWarning(t *testing.T) {
	for _, failure := range []error{errors.New("output failed"), io.ErrClosedPipe, io.EOF} {
		terminal := &lotteryOutputFailure{failure: failure}
		warning := &store.DurabilityError{Err: errors.New("sync failed after replacement")}
		err := (Session{Terminal: terminal}).lotteryReceipt(game.LotteryReceipt{Ticket: "000000", Draw: "111111", Fee: 5, Balance: 1000}, warning)
		var committed *store.DurabilityError
		if !errors.As(err, &committed) || committed != warning || !errors.Is(err, failure) {
			t.Fatalf("lost committed/output error: %v", err)
		}
	}
}
func TestLotteryCommittedWarningWithEOFStillEndsAsWarning(t *testing.T) {
	s, id, _ := portSession(t, true)
	terminal := &lotteryWarningTerminal{scripted: scripted{lines: []string{"p;lottery 000000", "y", "lottery 000000", "y", "q"}}, outputError: io.EOF}
	s.Terminal = terminal
	s.Identity = "port-test"
	s.Alias = "Trader"
	err := s.Run()
	var warning *store.DurabilityError
	if !errors.As(err, &warning) || !errors.Is(err, io.EOF) {
		t.Fatal("committed warning swallowed as ordinary disconnect", err)
	}
	w, e := s.Store.View()
	if e != nil {
		t.Fatal(e)
	}
	if w.Players[id].LotterySequence != 1 || len(terminal.lines) != 3 {
		t.Fatal("continued after warning")
	}
}
