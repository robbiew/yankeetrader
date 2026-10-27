package game

import (
	"encoding/json"
	"os"
	"reflect"
	"testing"
	"time"
)

func ownedPortWorld(t *testing.T) (*World, *Player, *Player) {
	t.Helper()
	w, buyer := setup(t)
	seller, err := w.Join("local:seller", "Seller")
	if err != nil {
		t.Fatal(err)
	}
	buyer.Sector, buyer.Credits = 2, 100000
	seller.Credits = 2000
	w.Ports[2].Owner, w.Ports[2].Treasury = seller.ID, 777
	return w, buyer, seller
}

func TestDOSPortOwnershipExamples(t *testing.T) {
	var cases []struct {
		Name                                                                              string
		BuyerBefore, BuyerAfter, SellerBefore, SellerAfter, TreasuryBefore, TreasuryAfter int64
		OwnerBefore, OwnerAfter                                                           int
	}
	b, err := os.ReadFile("testdata/dos-ownership.json")
	if err != nil {
		t.Fatal(err)
	}
	if err = json.Unmarshal(b, &cases); err != nil {
		t.Fatal(err)
	}
	for _, c := range cases {
		t.Run(c.Name, func(t *testing.T) {
			w, buyer, seller := ownedPortWorld(t)
			remap := func(id int) int {
				if id == 2 {
					return buyer.ID
				}
				if id == 3 {
					return seller.ID
				}
				return 0
			}
			buyer.Credits, seller.Credits = c.BuyerBefore, c.SellerBefore
			w.Ports[2].Owner, w.Ports[2].Treasury = remap(c.OwnerBefore), c.TreasuryBefore
			switch c.Name {
			case "ownership-collect":
				buyer.Sector = 1 // Collection is remote, including from Earth.
				_, err = w.CollectPortTreasury(buyer.ID)
			case "ownership-report":
				_, err = w.PortAccounts(buyer.ID)
			default:
				var q PortPurchaseQuote
				q, err = w.QuotePortPurchase(buyer.ID, clock)
				if err == nil && c.Name != "ownership-cancel" && c.Name != "ownership-default" {
					err = w.PurchasePort(buyer.ID, q, clock)
					if err == nil && c.Name == "ownership-buy-collect" {
						_, err = w.CollectPortTreasury(buyer.ID)
					}
				}
			}
			rejected := c.Name == "ownership-poor" || c.Name == "ownership-self"
			if (err != nil) != rejected {
				t.Fatalf("error=%v, rejected=%v", err, rejected)
			}
			if buyer.Credits != c.BuyerAfter || seller.Credits != c.SellerAfter || w.Ports[2].Owner != remap(c.OwnerAfter) || w.Ports[2].Treasury != c.TreasuryAfter || buyer.Turns != 500 {
				t.Fatalf("DOS mismatch: buyer=%d seller=%d port=%+v", buyer.Credits, seller.Credits, w.Ports[2])
			}
			if err = w.Validate(); err != nil {
				t.Fatal(err)
			}
		})
	}
}

func TestPortPurchaseRejectsStaleQuotesWithoutMutation(t *testing.T) {
	for _, mode := range []string{"expired", "owner", "price", "position", "funds", "seller-limit", "treasury-limit", "wrong-buyer"} {
		t.Run(mode, func(t *testing.T) {
			w, buyer, seller := ownedPortWorld(t)
			q, err := w.QuotePortPurchase(buyer.ID, clock)
			if err != nil {
				t.Fatal(err)
			}
			now, caller := clock, buyer.ID
			switch mode {
			case "expired":
				now = clock.Add(5 * time.Minute)
			case "owner":
				other, _ := w.Join("other", "Other")
				w.Ports[2].Owner = other.ID
			case "price":
				w.Ports[2].Production[0] = 200
			case "position":
				if err = w.Move(buyer.ID, 3); err != nil {
					t.Fatal(err)
				}
			case "funds":
				buyer.Credits = 30
			case "seller-limit":
				seller.Credits = MaxMoney - 31
			case "treasury-limit":
				w.Ports[2].Treasury = MaxMoney
			case "wrong-buyer":
				caller = seller.ID
			}
			before, _ := json.Marshal(w)
			if err = w.PurchasePort(caller, q, now); err == nil {
				t.Fatal("stale or invalid purchase accepted")
			}
			after, _ := json.Marshal(w)
			if string(before) != string(after) {
				t.Fatal("rejected purchase mutated world")
			}
		})
	}
}

func TestPortPurchasePreviewReplayAndDockInvalidation(t *testing.T) {
	w, buyer, seller := ownedPortWorld(t)
	before, _ := json.Marshal(w)
	q, err := w.QuotePortPurchase(buyer.ID, clock.Add(24*time.Hour))
	if err != nil || q.Price != 34 {
		t.Fatalf("production-adjusted quote: %+v %v", q, err)
	}
	after, _ := json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("preview advanced production")
	}
	seller.Sector = 2
	if err = w.Dock(seller.ID, clock); err != nil {
		t.Fatal(err)
	}
	token := seller.DockToken
	q, _ = w.QuotePortPurchase(buyer.ID, clock)
	if err = w.PurchasePort(buyer.ID, q, clock); err != nil {
		t.Fatal(err)
	}
	if seller.DockToken != "" {
		t.Fatal("seller's old dock agreement survived ownership change")
	}
	if err = w.Trade(seller.ID, token, true, 0, 1, clock); err == nil {
		t.Fatal("stale trade accepted")
	}
	before, _ = json.Marshal(w)
	if err = w.PurchasePort(buyer.ID, q, clock); err == nil {
		t.Fatal("purchase replay accepted")
	}
	after, _ = json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("replay spent credits")
	}
	if buyer.Credits != 99969 || seller.Credits != 2808 {
		t.Fatal("incorrect buyout transfer")
	}
	buyer.Sector = 1
	if _, err = w.QuotePortPurchase(buyer.ID, clock); err == nil {
		t.Fatal("Earth offered for sale")
	}
}

func TestPersonalPortCollectionConservationAndOverflow(t *testing.T) {
	w, buyer, seller := ownedPortWorld(t)
	buyer.Team, seller.Team = 7, 7
	hash, _ := hashTeamPassword("ABCD")
	w.Teams[7] = &Team{ID: 7, Name: "Team", Captain: buyer.ID, PasswordHash: hash}
	w.Ports[2].Owner = buyer.ID
	w.Ports[3].Owner, w.Ports[3].Treasury = buyer.ID, 333
	w.Ports[4].Owner, w.Ports[4].Treasury = seller.ID, 999
	accounts, err := w.PortAccounts(buyer.ID)
	if err != nil || len(accounts) != 2 || accounts[0].PortID != 2 || accounts[1].PortID != 3 {
		t.Fatal(accounts, err)
	}
	before, _ := json.Marshal(w)
	buyer.Credits = MaxMoney - 1000
	full, _ := json.Marshal(w)
	if _, err = w.CollectPortTreasury(buyer.ID); err == nil {
		t.Fatal("overflow accepted")
	}
	after, _ := json.Marshal(w)
	if string(full) != string(after) {
		t.Fatal("overflow partially cleared accounts")
	}
	if err = json.Unmarshal(before, w); err != nil {
		t.Fatal(err)
	}
	amount, err := w.CollectPortTreasury(buyer.ID)
	if err != nil || amount != 1110 || w.Players[buyer.ID].Credits != 101110 || w.Ports[2].Treasury != 0 || w.Ports[3].Treasury != 0 || w.Ports[4].Treasury != 999 {
		t.Fatal("collection lost or leaked money", amount, err)
	}
	if amount, err = w.CollectPortTreasury(buyer.ID); err != nil || amount != 0 {
		t.Fatal("collection duplicated funds", amount, err)
	}
	if !reflect.DeepEqual(accounts[0], PortAccount{PortID: 2, Sector: 2, Name: w.Ports[2].Name, Treasury: 777}) {
		t.Fatal(accounts)
	}
}
