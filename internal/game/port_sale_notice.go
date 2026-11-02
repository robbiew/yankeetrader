package game

import (
	"errors"
	"fmt"
	"math"
	"time"
)

// PortSaleNotice captures only the former owner's private sale receipt. The
// asking price excludes the separately returned treasury. It is not public news.
type PortSaleNotice struct {
	BuyerAlias  string
	PortName    string
	Sector      int
	AskingPrice int64
}

func validPortSaleNotice(n *PortSaleNotice) bool {
	return n != nil && clean(n.BuyerAlias) && clean(n.PortName) && n.Sector >= 2 && n.Sector <= 3000 && n.AskingPrice >= 1 && n.AskingPrice <= MaxMoney
}
func (n PortSaleNotice) message() string {
	return fmt.Sprintf("%s bought your port \"%s\" in %d for %d credits", n.BuyerAlias, n.PortName, n.Sector, n.AskingPrice)
}
func (w *World) preparePortSaleNotice(buyer, seller *Player, port *Port, price int64, request string, now time.Time) (RadioMessage, error) {
	n := &PortSaleNotice{BuyerAlias: buyer.Alias, PortName: port.Name, Sector: port.Sector, AskingPrice: price}
	if !validPortSaleNotice(n) || !clean(seller.Alias) || now.IsZero() || now.Before(w.Created) {
		return RadioMessage{}, errors.New("invalid port-sale notice")
	}
	if len(w.Radio) >= MaxRadioMessages || w.NextRadio == 0 || w.NextRadio == math.MaxUint64 {
		return RadioMessage{}, errors.New("radio archive has no room for the seller notice; purchase cancelled")
	}
	return RadioMessage{System: "port-sale", PortSale: n, ID: w.NextRadio, RequestID: request, To: seller.ID, FromAlias: "The Mercenaries", ToAlias: seller.Alias, Sent: now.UTC(), Unread: true}, nil
}
