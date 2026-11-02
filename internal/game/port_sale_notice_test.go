package game

import (
	"math"
	"strings"
	"testing"
	"time"
)

func TestPortSaleNoticeSettlementPrivacyAndSnapshots(t *testing.T) {
	for _, scope := range []string{"owned", "team", "unowned", "long"} {
		t.Run(scope, func(t *testing.T) {
			w, buyer, seller := ownedPortWorld(t)
			port := w.Ports[2]
			if scope == "unowned" {
				port.Owner = 0
			}
			if scope == "team" {
				if err := w.CreateTeam(buyer.ID, "Orion", "ABCD"); err != nil {
					t.Fatal(err)
				}
				if err := w.JoinTeam(seller.ID, buyer.Team, "ABCD"); err != nil {
					t.Fatal(err)
				}
			}
			if scope == "long" {
				buyer.Alias = strings.Repeat("B", 41)
				port.Name = strings.Repeat("P", 41)
			}
			q, err := w.QuotePortPurchase(buyer.ID, clock)
			if err != nil {
				t.Fatal(err)
			}
			turns := buyer.Turns
			name, alias := port.Name, buyer.Alias
			if err = w.PurchasePort(buyer.ID, q, clock); err != nil {
				t.Fatal(err)
			}
			if buyer.Credits != 100000-q.Price || buyer.Turns != turns || port.Owner != buyer.ID || len(w.News) != 0 {
				t.Fatal("incorrect action/publication")
			}
			want := 1
			if scope == "unowned" {
				want = 0
				if port.Treasury != 777 || seller.Credits != 2000 {
					t.Fatal("unowned paid seller")
				}
			} else if port.Treasury != 0 || seller.Credits != 2000+q.Price+777 {
				t.Fatal("settlement")
			}
			if len(w.Radio) != want {
				t.Fatal(w.Radio)
			}
			if want == 0 {
				return
			}
			n := w.Radio[0]
			if n.System != "port-sale" || n.From != 0 || n.FromAlias != "The Mercenaries" || n.To != seller.ID || !n.Unread || n.Text != "" || n.PortSale.AskingPrice != q.Price {
				t.Fatal(n)
			}
			before := string(worldJSON(t, w))
			if w.PurchasePort(buyer.ID, q, clock) == nil || string(worldJSON(t, w)) != before {
				t.Fatal("retry settled again")
			}
			buyer.Alias = "Renamed Buyer"
			port.Name = "Renamed Port"
			visitor, _ := w.Join("observer-secret", "Observer")
			for _, id := range []int{buyer.ID, visitor.ID} {
				entries, e := w.RadioHistory(id, 0, 20, false)
				if e != nil || len(entries) != 0 {
					t.Fatal("private notice leaked", entries, e)
				}
			}
			entries, e := w.RadioHistory(seller.ID, 0, 20, true)
			if e != nil || len(entries) != 1 {
				t.Fatal(entries, e)
			}
			expected := (&PortSaleNotice{BuyerAlias: alias, PortName: name, Sector: 2, AskingPrice: q.Price}).message()
			if entries[0].Text != expected || strings.Contains(entries[0].Text, "808") || strings.Contains(entries[0].Text, "Renamed") {
				t.Fatal(entries)
			}
			if scope == "long" && len(entries[0].Text) <= MaxRadioText {
				t.Fatal("long fields truncated")
			}
			if err = w.AcknowledgeRadio(seller.ID, n.ID); err != nil {
				t.Fatal(err)
			}
			unread, _ := w.RadioHistory(seller.ID, 0, 20, true)
			history, _ := w.RadioHistory(seller.ID, 0, 20, false)
			if len(unread) != 0 || len(history) != 1 || history[0].Text != expected {
				t.Fatal("read/history semantics")
			}
			if err = w.Validate(); err != nil {
				t.Fatal(err)
			}
		})
	}
}
func TestPortSaleNoticeRejectsBeforeMutation(t *testing.T) {
	for _, mode := range []string{"full", "sequence", "clock", "name", "generation", "season", "price", "owner", "expiry", "poor", "seller-limit", "tamper-owner", "tamper-price"} {
		t.Run(mode, func(t *testing.T) {
			w, b, s := ownedPortWorld(t)
			q, _ := w.QuotePortPurchase(b.ID, clock)
			at := clock
			switch mode {
			case "full":
				w.Radio = make([]RadioMessage, MaxRadioMessages)
			case "sequence":
				w.NextRadio = math.MaxUint64
			case "clock":
				at = clock.Add(-time.Second)
			case "name":
				w.Ports[2].Name = "Renamed"
			case "generation":
				b.ShipGeneration++
			case "season":
				w.Season++
			case "price":
				w.Ports[2].Production[0] += 100
			case "owner":
				w.Ports[2].Owner = 0
			case "tamper-owner":
				w.Ports[2].Owner = 0
				q.Owner = 0
			case "tamper-price":
				w.Ports[2].Production[0] += 100
				q.Price += 10
			case "expiry":
				at = clock.Add(5 * time.Minute)
			case "poor":
				b.Credits = 0
			case "seller-limit":
				s.Credits = MaxMoney
			}
			before := string(worldJSON(t, w))
			if w.PurchasePort(b.ID, q, at) == nil || string(worldJSON(t, w)) != before {
				t.Fatal("rejection mutated", mode)
			}
		})
	}
	w, b, _ := ownedPortWorld(t)
	w.Ports[2].Owner = 0
	w.Radio = make([]RadioMessage, MaxRadioMessages)
	q, _ := w.QuotePortPurchase(b.ID, clock)
	if err := w.PurchasePort(b.ID, q, clock); err != nil {
		t.Fatal("unowned sale required notice capacity", err)
	}
}
func TestPortSaleNoticeStrictValidationAndMigration(t *testing.T) {
	w, b, _ := ownedPortWorld(t)
	q, _ := w.QuotePortPurchase(b.ID, clock)
	if e := w.PurchasePort(b.ID, q, clock); e != nil {
		t.Fatal(e)
	}
	good := w.Radio[0]
	snapshot := *good.PortSale
	for _, mutate := range []func(*RadioMessage){func(m *RadioMessage) { m.From = 1 }, func(m *RadioMessage) { m.FromAlias = "Buyer" }, func(m *RadioMessage) { m.System = "" }, func(m *RadioMessage) { m.System = "super-planet" }, func(m *RadioMessage) { m.Text = "forged" }, func(m *RadioMessage) { m.PortSale = nil }, func(m *RadioMessage) { m.PortSale.BuyerAlias = "bad\x1b" }, func(m *RadioMessage) { m.PortSale.PortName = "" }, func(m *RadioMessage) { m.PortSale.Sector = 1 }, func(m *RadioMessage) { m.PortSale.Sector = 3001 }, func(m *RadioMessage) { m.PortSale.AskingPrice = 0 }, func(m *RadioMessage) { m.PortSale.AskingPrice = MaxMoney + 1 }} {
		copy := snapshot
		w.Radio[0] = good
		w.Radio[0].PortSale = &copy
		mutate(&w.Radio[0])
		if w.Validate() == nil {
			t.Fatal(w.Radio[0])
		}
	}
	w.Radio[0] = good
	w.Version = 28
	if w.Upgrade() == nil {
		t.Fatal("old schema accepted new notice")
	}
	w.Radio = nil
	price := w.Players[b.ID].Credits
	if err := w.Upgrade(); err != nil || w.Version != WorldVersion || len(w.Radio) != 0 || w.Players[b.ID].Credits != price {
		t.Fatal("migration backfilled", err)
	}
}

func TestPortSaleOldConfirmationCannotReplayAfterResale(t *testing.T) {
	w, b, s := ownedPortWorld(t)
	old, _ := w.QuotePortPurchase(b.ID, clock)
	if err := w.PurchasePort(b.ID, old, clock); err != nil {
		t.Fatal(err)
	}
	s.Sector = 2
	back, _ := w.QuotePortPurchase(s.ID, clock)
	if err := w.PurchasePort(s.ID, back, clock); err != nil {
		t.Fatal(err)
	}
	before := string(worldJSON(t, w))
	if w.PurchasePort(b.ID, old, clock) == nil || string(worldJSON(t, w)) != before {
		t.Fatal("old confirmation replayed after resale")
	}
	fresh, _ := w.QuotePortPurchase(b.ID, clock)
	if err := w.PurchasePort(b.ID, fresh, clock); err != nil {
		t.Fatal("fresh repurchase refused", err)
	}
	if len(w.Radio) != 3 {
		t.Fatal(w.Radio)
	}
}

func TestPortSalePaysCurrentTreasuryButNoticesAskingPrice(t *testing.T) {
	w, b, s := ownedPortWorld(t)
	q, _ := w.QuotePortPurchase(b.ID, clock)
	w.Ports[2].Treasury = 999
	if err := w.PurchasePort(b.ID, q, clock); err != nil {
		t.Fatal(err)
	}
	if s.Credits != 3030 || w.Radio[0].PortSale.AskingPrice != 31 {
		t.Fatal(s, w.Radio)
	}
}
