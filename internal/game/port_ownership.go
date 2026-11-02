package game

import (
	"crypto/rand"
	"encoding/hex"
	"errors"
	"math"
	"sort"
	"time"
)

// PortPurchaseQuote is an in-memory confirmation, never part of a saved world.
type PortPurchaseQuote struct {
	PortID, Sector, Owner int
	Price                 int64
	buyer                 int
	expires, issued       time.Time
	generation, season    uint64
	name, request         string
	port, sector, owner   int
	price                 int64
}

func (w *World) QuotePortPurchase(id int, now time.Time) (PortPurchaseQuote, error) {
	p, err := w.player(id)
	if err != nil {
		return PortPurchaseQuote{}, err
	}
	port := w.Ports[w.Sectors[p.Sector].Port]
	if port == nil {
		return PortPurchaseQuote{}, errors.New("no port here")
	}
	if port.ID == 1 {
		return PortPurchaseQuote{}, errors.New("Earth cannot be owned")
	}
	if port.Owner == id {
		return PortPurchaseQuote{}, errors.New("you already own this port")
	}
	if port.Owner != 0 && w.Players[port.Owner] == nil {
		return PortPurchaseQuote{}, errors.New("port owner no longer exists")
	}
	if now.IsZero() || now.Before(w.Created) {
		return PortPurchaseQuote{}, errors.New("invalid port purchase time")
	}
	// A preview or rejected action must not advance production in the live world.
	updated := *port
	update(&updated, now)
	price := int64(math.Floor((updated.Production[0]+updated.Production[1]+updated.Production[2])/10)) + 1
	var token [16]byte
	if _, err := rand.Read(token[:]); err != nil {
		return PortPurchaseQuote{}, err
	}
	return PortPurchaseQuote{PortID: port.ID, Sector: p.Sector, Owner: port.Owner,
		Price: price, buyer: id, expires: now.Add(5 * time.Minute), issued: now, generation: p.ShipGeneration, season: w.Season, name: port.Name, request: hex.EncodeToString(token[:]), port: port.ID, sector: p.Sector, owner: port.Owner, price: price}, nil
}

// PurchasePort must execute within the store's Update transaction. The seller
// receives both the asking price and their current treasury; no team is paid.
func (w *World) PurchasePort(id int, quote PortPurchaseQuote, now time.Time) error {
	if quote.PortID != quote.port || quote.Sector != quote.sector || quote.Owner != quote.owner || quote.Price != quote.price {
		return errors.New("purchase confirmation changed; request a new quote")
	}
	if quote.buyer != id || now.Before(quote.issued) || !now.Before(quote.expires) {
		return errors.New("port purchase quote expired; request a new quote")
	}
	if err := w.CheckSession(id, quote.generation, quote.season); err != nil {
		return err
	}
	if _, err := hex.DecodeString(quote.request); err != nil || len(quote.request) != 32 {
		return errors.New("invalid purchase confirmation")
	}
	for _, message := range w.Radio {
		if message.From == 0 && message.RequestID == quote.request {
			return errors.New("port purchase already committed; request a new quote")
		}
	}
	fresh, err := w.QuotePortPurchase(id, now)
	if err != nil {
		return err
	}
	if fresh.PortID != quote.PortID || fresh.Sector != quote.Sector || fresh.Owner != quote.Owner || fresh.Price != quote.Price || fresh.name != quote.name {
		return errors.New("port or asking price changed; request a new quote")
	}
	buyer := w.Players[id]
	port := w.Ports[quote.PortID]
	if buyer.Credits < fresh.Price {
		return errors.New("not enough credits to buy this port")
	}
	var seller *Player
	payout := int64(0)
	if port.Owner != 0 {
		seller = w.Players[port.Owner]
		if port.Treasury > MaxMoney-fresh.Price || seller.Credits > MaxMoney-fresh.Price-port.Treasury {
			return errors.New("seller credit limit exceeded")
		}
		payout = fresh.Price + port.Treasury
	}
	var notice RadioMessage
	if seller != nil {
		notice, err = w.preparePortSaleNotice(buyer, seller, port, fresh.Price, quote.request, now)
		if err != nil {
			return err
		}
	}
	// All validation precedes mutation, including both sides' money limits.
	update(port, now)
	buyer.Credits -= fresh.Price
	if seller != nil {
		seller.Credits += payout
		port.Treasury = 0
		w.Radio = append(w.Radio, notice)
		w.NextRadio++
	}
	// A pre-existing unowned balance stays in the account; the ordinary
	// generator and unowned trading never create such a balance.
	port.Owner = id
	for _, p := range w.Players {
		if p.Sector == port.Sector {
			p.DockToken = ""
		}
	}
	return nil
}

type PortAccount struct {
	PortID, Sector int
	Name           string
	Treasury       int64
}

// PortAccounts exposes only the caller's personal port accounts, in stable order.
func (w *World) PortAccounts(id int) ([]PortAccount, error) {
	if _, err := w.player(id); err != nil {
		return nil, err
	}
	accounts := []PortAccount{}
	for _, port := range w.Ports {
		if port.Owner == id {
			accounts = append(accounts, PortAccount{PortID: port.ID, Sector: port.Sector, Name: port.Name, Treasury: port.Treasury})
		}
	}
	sort.Slice(accounts, func(i, j int) bool { return accounts[i].Sector < accounts[j].Sector })
	return accounts, nil
}

// CollectPortTreasury transfers every personally owned balance, or none when
// the ship cannot hold the complete amount. It is free and works from any sector.
func (w *World) CollectPortTreasury(id int) (int64, error) {
	p, err := w.player(id)
	if err != nil {
		return 0, err
	}
	accounts, err := w.PortAccounts(id)
	if err != nil {
		return 0, err
	}
	if len(accounts) == 0 {
		return 0, errors.New("you don't own any ports")
	}
	total := int64(0)
	for _, account := range accounts {
		if account.Treasury > MaxMoney-p.Credits-total {
			return 0, errors.New("not enough credit capacity to collect all port treasuries")
		}
		total += account.Treasury
	}
	for _, account := range accounts {
		w.Ports[account.PortID].Treasury = 0
	}
	p.Credits += total
	return total, nil
}
