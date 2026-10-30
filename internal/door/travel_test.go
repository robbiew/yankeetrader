package door

import (
	"fmt"
	"math"
	"strings"
	"testing"

	"github.com/robbiew/yankeetrader/internal/game"
)

func TestTravelScannerPurchaseActualReceipts(t *testing.T) {
	for _, classic := range []bool{false, true} {
		for _, cash := range []int64{249999, 250000, 250001} {
			term := &scripted{}
			s, id, token := portSession(t, true)
			s.Classic = classic
			s.Terminal = term
			if err := s.Store.Update(func(w *game.World) error { w.Players[id].Credits = cash; return nil }); err != nil {
				t.Fatal(err)
			}
			var err error
			if classic {
				err = s.earthShop(id, token, &[]string{"5", "5", "0"})
			} else {
				err = s.buyScanner(id, token, 1)
			}
			w, e := s.Store.View()
			if e != nil {
				t.Fatal(e)
			}
			text := term.output.String()
			if cash < game.DangerScannerPrice {
				if w.Players[id].DangerScanner || w.Players[id].Credits != cash || strings.Contains(text, "installed and saved") {
					t.Fatal(err, text)
				}
				if !classic && err == nil {
					t.Fatal("poor purchase accepted")
				}
			} else {
				if err != nil || !w.Players[id].DangerScanner || w.Players[id].Credits != cash-game.DangerScannerPrice || strings.Count(text, fmt.Sprintf("Credits spent: 250000. Balance: %d.", cash-game.DangerScannerPrice)) != 1 {
					t.Fatal(err, text)
				}
				if classic && !strings.Contains(text, "already installed") {
					t.Fatal("duplicate shop purchase", text)
				}
			}
		}
	}
}
func TestTravelManualWarpReceiptsConfirmationsAndErrors(t *testing.T) {
	for _, classic := range []bool{false, true} {
		for _, mode := range []string{"zero-cost", "three-turns", "meltdown", "cancel", "bad-rng", "stacked"} {
			t.Run(fmt.Sprintf("classic=%v/%s", classic, mode), func(t *testing.T) {
				answer := "y"
				if mode == "cancel" {
					answer = "n"
				}
				if mode == "stacked" {
					answer = "y;q"
				}
				term := &scripted{lines: []string{answer}}
				s, st := navigationSession(t, term)
				s.Classic = classic
				if err := st.Update(func(w *game.World) error { _, e := w.Join("nav", "Navigator"); return e }); err != nil {
					t.Fatal(err)
				}
				s.Store = st.ForShip(1, 0)
				i := 0
				rng := func() float64 {
					i++
					if mode == "bad-rng" {
						return math.NaN()
					}
					if mode == "meltdown" {
						return .99
					}
					if mode == "three-turns" && i == 5 {
						return .99
					}
					return 0
				}
				err := s.warpWithRandom(1, nil, &[]string{"y", "q"}, rng)
				w, _ := st.View()
				p := w.Players[1]
				text := term.output.String()
				if mode == "cancel" || mode == "stacked" || mode == "bad-rng" {
					if p.WarpSequence != 0 || p.Turns != 500 || strings.Contains(text, "Emergency warp saved:") {
						t.Fatal("unsaved warp receipt", err, text)
					}
					if mode == "bad-rng" && err == nil {
						t.Fatal("bad RNG accepted")
					}
					return
				}
				cost := int64(0)
				if mode == "three-turns" {
					cost = 3
				}
				if mode == "meltdown" {
					cost = 500
				}
				if err != nil || p.Turns != 500-cost || p.WarpSequence != 1 || !strings.Contains(text, fmt.Sprintf("recharge %d turns; aftermath 0 turns; total spent %d.", cost, cost)) {
					t.Fatal("wrong warp receipt", err, p, text)
				}
				if strings.Contains(text, "Engine meltdown consumed") != (mode == "meltdown") {
					t.Fatal("wrong meltdown receipt", text)
				}
			})
		}
	}
}
func TestTravelScannerAutopilotStopsAtWarningAndKeepsCompletedHops(t *testing.T) {
	for _, tc := range []struct {
		name, answer string
		mine, want   int
		turns        int64
	}{{"first-accept", "y", 2, 2, 499}, {"second-decline", "n", 3, 2, 499}, {"second-accept", "y", 3, 3, 498}, {"stacked-confirm", "y;q", 2, 1, 500}} {
		t.Run(tc.name, func(t *testing.T) {
			term := &scripted{lines: []string{"auto 4;y", tc.answer, "q"}}
			s, st := navigationSession(t, term)
			if err := st.Update(func(w *game.World) error {
				p, e := w.Join("nav", "Navigator")
				if e != nil {
					return e
				}
				p.DangerScanner = true
				p.Shields = 100000
				w.Sectors[tc.mine].Minefield = []game.MineLayer{{Owner: 0, Count: 1}}
				return nil
			}); err != nil {
				t.Fatal(err)
			}
			if err := s.Run(); err != nil {
				t.Fatal(err)
			}
			w, _ := st.View()
			p := w.Players[1]
			text := term.output.String()
			if p.Sector != tc.want || p.Turns != tc.turns || strings.Count(text, "Danger scanner has detected") != 1 || strings.Contains(text, "Moved to sector 4.") {
				t.Fatal("continued queued course", p, text)
			}
			if tc.answer == "y" && len(w.Sectors[tc.mine].Minefield) != 0 {
				t.Fatal("accepted warning skipped mines")
			}
		})
	}
}
func TestTravelScannerHostileArrivalAndWarpCommandDispatcher(t *testing.T) {
	// Fresh scanner confirmation permits entry, never automatic fighter defeat.
	term := &scripted{lines: []string{"move 2", "y", "q"}}
	s, st := navigationSession(t, term)
	if err := st.Update(func(w *game.World) error {
		p, e := w.Join("nav", "Navigator")
		if e != nil {
			return e
		}
		p.DangerScanner = true
		w.Sectors[2].Defense = &game.SectorDefense{Owner: game.XannorOwner, Fighters: 100}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	w, _ := st.View()
	if w.Players[1].Sector != 2 || w.Players[1].Turns != 499 || w.Sectors[2].Defense.Fighters != 100 || !strings.Contains(term.output.String(), "The Xannor") || !strings.Contains(term.output.String(), "Hostile sector fighters block") {
		t.Fatal(term.output.String())
	}
	for _, cmd := range []string{"w;y", "warp;y"} {
		term := &scripted{lines: []string{cmd, "n", "q"}}
		s, st := navigationSession(t, term)
		if err := s.Run(); err != nil {
			t.Fatal(err)
		}
		w, _ := st.View()
		if w.Players[1].WarpSequence != 0 || !strings.Contains(term.output.String(), "Emergency warp cancelled.") {
			t.Fatal("queued warp confirmation accepted", term.output.String())
		}
	}
}

func TestTravelWarpReceiptIncludesAutomaticMineEscape(t *testing.T) {
	term := &scripted{lines: []string{"y"}}
	s, st := navigationSession(t, term)
	if e := st.Update(func(w *game.World) error {
		p, e := w.Join("nav", "Navigator")
		if e != nil {
			return e
		}
		p.Holds = 9
		p.Shields = 100000
		p.Cloak = 0
		w.Sectors[2].Minefield = []game.MineLayer{{Owner: 0, Count: 1}}
		return nil
	}); e != nil {
		t.Fatal(e)
	}
	s.Store = st.ForShip(1, 0)
	draws := []float64{0, 0, .2, 0, .99, 0, .9, 0, 0, 0, 0, .99}
	i := 0
	e := s.warpWithRandom(1, nil, &[]string{}, func() float64 {
		if i >= len(draws) {
			t.Fatal("extra draw")
			return 0
		}
		r := draws[i]
		i++
		return r
	})
	w, _ := st.View()
	text := term.output.String()
	if e != nil || w.Players[1].Sector != 1 || w.Players[1].Turns != 494 || !strings.Contains(text, "landed in sector 2;") || !strings.Contains(text, "recharge 3 turns; aftermath 3 turns; total spent 6.") || !strings.Contains(text, "Emergency warp escaped to safe sector 1.") {
		t.Fatal("aftermath receipt", e, text)
	}
}

func TestTravelDisconnectedConfirmationHasNoReceipt(t *testing.T) {
	for _, scanner := range []bool{false, true} {
		command := "warp"
		if scanner {
			command = "auto 4;y"
		}
		term := &scripted{lines: []string{command}}
		s, st := navigationSession(t, term)
		if scanner {
			if e := st.Update(func(w *game.World) error {
				p, e := w.Join("nav", "Navigator")
				if e != nil {
					return e
				}
				p.DangerScanner = true
				w.Sectors[2].Minefield = []game.MineLayer{{Owner: 0, Count: 1}}
				return nil
			}); e != nil {
				t.Fatal(e)
			}
		}
		if e := s.Run(); e != nil {
			t.Fatal(e)
		}
		w, _ := st.View()
		text := term.output.String()
		if w.Players[1].Turns != 500 || w.Players[1].Sector != 1 || w.Players[1].WarpSequence != 0 || strings.Contains(text, "EOF") || strings.Contains(text, "warp saved:") || strings.Contains(text, "entry saved") {
			t.Fatal("disconnect completed or fabricated action", text)
		}
	}
}
