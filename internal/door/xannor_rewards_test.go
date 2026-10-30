package door

import (
	"strings"
	"testing"

	"github.com/robbiew/yankeetrader/internal/game"
)

func TestHQRewardReceiptsMatchActualCreditAndPublicPrivacy(t *testing.T) {
	for _, classic := range []bool{false, true} {
		for _, missiles := range []bool{false, true} {
			for _, mode := range []string{"full-bonus", "one-credit", "at-limit", "cancel", "metadata"} {
				lines := []string{"y", "y"}
				if missiles {
					lines = []string{"y"}
				}
				if mode == "cancel" {
					if missiles {
						lines = []string{"n"}
					} else {
						lines = []string{"y", "n"}
					}
				}
				term := &scripted{lines: lines}
				s, st := navigationSession(t, term)
				s.Classic = classic
				balance := int64(1005)
				want := game.XannorHQBonus
				if mode == "one-credit" {
					balance = game.MaxMoney - 1
					want = 1
				}
				if mode == "at-limit" {
					balance = game.MaxMoney
					want = 0
				}
				if err := st.Update(func(w *game.World) error {
					p, err := w.Join("nav", "Navigator")
					if err != nil {
						return err
					}
					p.Sector = 7
					p.Credits = balance
					p.Fighters = 10000
					p.Missiles = 3
					w.Xannor = &game.XannorState{HQ: 8}
					w.Sectors[7].Warps = []int{8}
					w.Sectors[8].Defense = &game.SectorDefense{Owner: game.XannorOwner, Fighters: 1}
					if mode == "metadata" {
						w.NextNews = ^uint64(0)
					}
					return nil
				}); err != nil {
					t.Fatal(err)
				}
				s.Store = st.ForShip(1, 0)
				var err error
				if missiles {
					v, _ := func() (*game.Visibility, error) {
						w, e := st.View()
						if e != nil {
							return nil, e
						}
						return w.NewVisibility(1)
					}()
					err = s.launchMissiles(1, []string{"8", "3"}, &[]string{}, v)
				} else {
					err = s.defenseEncounter(1, []string{"8", "10000"}, &[]string{}, false)
				}
				w, _ := st.View()
				text := term.output.String()
				if mode == "metadata" || mode == "cancel" {
					if w.Players[1].Credits != balance || w.Sectors[8].Defense == nil || strings.Contains(text, "Credits added:") {
						t.Fatal("unsaved/cancelled reward receipt", mode, err, text)
					}
					if mode == "metadata" && err == nil {
						t.Fatal("metadata error suppressed")
					}
					continue
				}
				if err != nil || w.Players[1].Credits != balance+want {
					t.Fatal(mode, err, text)
				}
				expected := "Credits added: 1000000."
				if want == 1 {
					expected = "Credits added: 1."
				}
				if want == 0 {
					expected = "Credits added: 0."
				}
				if strings.Count(text, expected) != 1 || (want < game.XannorHQBonus) != strings.Contains(text, "Ship credit limit capped this bonus.") {
					t.Fatal("inaccurate receipt", mode, text)
				}
				term.output.Reset()
				if err = s.newspaper(1, []string{"today"}, &[]string{}); err != nil {
					t.Fatal(err)
				}
				text = term.output.String()
				if !strings.Contains(text, "Navigator  Defeated the Xannor HQ!") || strings.Contains(text, "Credits added") || strings.Contains(text, "1000000") || strings.Contains(text, "9000000000000000") {
					t.Fatal("public payout leak/missing victory", text)
				}
			}
		}
	}
}
