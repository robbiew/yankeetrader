package door

import (
	"errors"
	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
	"io"
	"strings"
	"testing"
	"time"
)

func genesisSession(t *testing.T, lines []string) (Session, *scripted) {
	t.Helper()
	at := time.Now().UTC()
	w, err := game.New(at, 36, 32)
	if err != nil {
		t.Fatal(err)
	}
	p, _ := w.Join("winner", "Winner")
	p.LastLogin = at.Format("2006-01-02")
	n := 20
	w.GenesisPorts = &n
	for i := 2; i <= 21; i++ {
		w.Ports[i].Owner = 1
	}
	st := store.Store{Dir: t.TempDir()}
	if err = st.Create(w); err != nil {
		t.Fatal(err)
	}
	term := &scripted{lines: lines}
	return Session{Store: st, Terminal: term, Identity: "winner", Alias: "Winner", Deadline: time.Now().Add(time.Minute), Now: func() time.Time { return at }}, term
}
func TestGenesisBothInterfacesCommitOnceAndEndLogin(t *testing.T) {
	for _, classic := range []bool{false, true} {
		t.Run(map[bool]string{false: "compact", true: "classic"}[classic], func(t *testing.T) {
			s, term := genesisSession(t, []string{"g;GENESIS;q", "GENESIS", "q"})
			s.Classic = classic
			if classic {
				term.lines = append([]string{"", "", ""}, term.lines...)
			}
			if err := s.Run(); err != nil {
				t.Fatal(err, term.output.String())
			}
			w, err := s.Store.View()
			if err != nil {
				t.Fatal(err)
			}
			if w.Season != 2 || len(w.Players) != 0 || len(w.SeasonResults) != 1 || len(term.lines) != 1 || !strings.Contains(term.output.String(), "Genesis saved: Winner won season 1 with 20 ports (required 20)") || strings.Contains(term.output.String(), "Safe travels") {
				t.Fatal("partial commit or login resumed", term.output.String())
			}
			term.lines = []string{"seasons;q"}
			s.Classic = false
			s.Identity = "new"
			s.Alias = "New Person"
			if err = s.Run(); err != nil {
				t.Fatal(err)
			}
			w, err = s.Store.View()
			if err != nil || w.Players[1].Identity != "new" || w.Season != 2 || !strings.Contains(term.output.String(), "Season 1: Winner (#1); 20 ports / 20 required") {
				t.Fatal("new season/history unavailable", err, term.output.String())
			}
		})
	}
}
func TestGenesisLiteralFreshConfirmationAndCancellation(t *testing.T) {
	for _, answer := range []string{"", "n", "y", "genesis", " GENESIS", "GENESIS;q"} {
		t.Run(answer, func(t *testing.T) {
			s, term := genesisSession(t, []string{answer})
			s.Store = s.Store.ForShip(1, 0, 1)
			pending := []string{"GENESIS", "q"}
			before, _ := s.Store.View()
			done, err := s.genesis(nil, &pending)
			after, _ := s.Store.View()
			if err != nil || done || len(pending) != 0 || after.Season != before.Season || strings.Contains(term.output.String(), "Genesis saved:") {
				t.Fatal(done, err, term.output.String())
			}
		})
	}
	s, term := genesisSession(t, nil)
	s.Store = s.Store.ForShip(1, 0, 1)
	if done, err := s.genesis(nil, &[]string{}); done || !errors.Is(err, io.EOF) {
		t.Fatal(done, err)
	}
	if strings.Contains(term.output.String(), "Genesis saved:") {
		t.Fatal("disconnect printed receipt")
	}
	s, term = genesisSession(t, []string{"GENESIS"})
	s.Store = s.Store.ForShip(1, 0, 1)
	if done, err := s.genesis([]string{"GENESIS"}, &[]string{}); done || err == nil {
		t.Fatal("inline argument authorized reset")
	}
}

type genesisFailureTerminal struct {
	scripted
	failure error
}

func (t *genesisFailureTerminal) Printf(format string, args ...any) error {
	if strings.Contains(format, "Genesis saved:") {
		return t.failure
	}
	return t.scripted.Printf(format, args...)
}
func TestGenesisReceiptPreservesCommittedAndOutputErrors(t *testing.T) {
	for _, output := range []error{io.EOF, io.ErrClosedPipe, errors.New("terminal failed"), errors.Join(&store.DurabilityError{Err: errors.New("storage warning")}, io.EOF)} {
		warning := &store.DurabilityError{Err: errors.New("committed sync failure")}
		term := &genesisFailureTerminal{failure: output}
		err := (Session{Terminal: term}).genesisReceipt(game.GenesisReceipt{}, warning)
		var committed *store.DurabilityError
		if !errors.As(err, &committed) || committed != warning || !errors.Is(err, output) {
			t.Fatal("lost committed warning", err)
		}
		s, _ := genesisSession(t, nil)
		term.scripted.lines = []string{"g", "GENESIS", "q"}
		s.Terminal = term
		err = s.Run()
		var sessionWarning *store.DurabilityError
		if errors.As(output, &sessionWarning) && !errors.As(err, &sessionWarning) {
			t.Fatal("warning swallowed as EOF", err)
		}
		if !errors.Is(err, output) && !errors.Is(output, io.EOF) {
			t.Fatal(err)
		}
		w, e := s.Store.View()
		if e != nil || w.Season != 2 || len(term.lines) != 1 {
			t.Fatal("receipt failure resumed old login", e)
		}
	}
}
func TestGenesisChangedOwnershipDuringConfirmationRefuses(t *testing.T) {
	s, term := genesisSession(t, []string{"GENESIS"})
	s.Store = s.Store.ForShip(1, 0, 1)
	admin := store.Store{Dir: s.Store.Dir}
	s.Terminal = &ownershipChanged{term, func() {
		if err := admin.Update(func(w *game.World) error { w.Ports[2].Owner = 0; return nil }); err != nil {
			t.Fatal(err)
		}
	}}
	done, err := s.genesis(nil, &[]string{})
	w, e := admin.View()
	if err == nil || done || e != nil || w.Season != 1 || len(w.SeasonResults) != 0 || strings.Contains(term.output.String(), "Genesis saved:") {
		t.Fatal(done, err, e, term.output.String())
	}
}

func TestClassicGenesisResetBetweenScreenLookupAndAuthentication(t *testing.T) {
	s, _ := genesisSession(t, nil)
	old, err := s.Store.View()
	if err != nil {
		t.Fatal(err)
	}
	// Startup saw this authenticated BBS identity at old player number one.
	oldID := old.Players[1].ID
	oldEpoch := old.Season
	bound := s.Store.ForShip(oldID, 0, oldEpoch)
	entry, err := bound.PrepareGenesis(s.Now, s.Deadline)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = bound.ResetSeason(entry, s.Now, s.Deadline); err != nil {
		t.Fatal(err)
	}
	var id int
	var epoch, generation uint64
	if err = s.Store.Update(func(live *game.World) error {
		stranger, e := live.Join("different-bbs-identity", "Stranger")
		if e != nil {
			return e
		}
		if stranger.ID != oldID {
			t.Fatal("slot not reused")
		}
		stranger.Credits = 123456
		// Execute the actual classic startup identity decision against the new world.
		p, e := classicLoginPlayer(live, s.Identity, old.Players[oldID].Alias)
		if e != nil {
			return e
		}
		id, epoch, generation = p.ID, live.Season, p.ShipGeneration
		if p.Identity != s.Identity || p.ID == oldID {
			t.Fatal("stale screen lookup authenticated another player")
		}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	live, err := s.Store.ForShip(id, generation, epoch).View()
	if err != nil || live.Players[oldID].Credits != 123456 || live.Players[oldID].Identity != "different-bbs-identity" || live.Players[id].Identity != s.Identity || epoch == oldEpoch {
		t.Fatal("wrong authenticated incarnation", err)
	}
}
