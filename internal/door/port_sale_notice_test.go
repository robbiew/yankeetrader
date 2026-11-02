package door

import (
	"errors"
	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
	"io"
	"strings"
	"testing"
)

func TestPortSaleNoticeReceiptPreservesWarning(t *testing.T) {
	s, _ := ownershipSession(t, nil)
	s.Terminal = &failedCreationReceipt{scripted: &scripted{}}
	warning := &store.DurabilityError{Err: errors.New("sync failed")}
	err := s.portPurchaseReceipt(warning, true)
	var got *store.DurabilityError
	if !errors.As(err, &got) || !errors.Is(err, io.EOF) {
		t.Fatal(err)
	}
}
func TestPortSaleNoticeUsesSellerHistoryOnly(t *testing.T) {
	s, term := ownershipSession(t, []string{"acquire;y;messages;q"})
	if e := s.Run(); e != nil {
		t.Fatal(e)
	}
	if strings.Contains(term.output.String(), "bought your port") {
		t.Fatal("buyer saw seller-only notice")
	}
	w, _ := s.Store.View()
	if len(w.Radio) != 1 || w.Radio[0].System != "port-sale" {
		t.Fatal(w.Radio)
	}
	s.Identity = "seller"
	s.Alias = "Seller"
	s.Terminal = &scripted{lines: []string{"messages;q"}}
	// Use an unbound administrative view as the login entry point, never the old buyer binding.
	s.Store = store.Store{Dir: s.Store.Dir}
	if e := s.Run(); e != nil {
		t.Fatal(e)
	}
	text := s.Terminal.(*scripted).output.String()
	if !strings.Contains(text, "The Mercenaries") || !strings.Contains(text, `Buyer bought your port "Port 2" in 2 for 31 credits`) {
		t.Fatal(text)
	}
	w, _ = s.Store.View()
	if w.Radio[0].Unread || w.Players[2].Credits != 2808 {
		t.Fatal("notice read settled again")
	}
	for _, n := range w.News {
		if n.Kind != game.NewsLogin {
			t.Fatal("private buyout published news", n)
		}
	}
}
