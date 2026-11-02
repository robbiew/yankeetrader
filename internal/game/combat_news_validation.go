package game

import (
	"errors"
	"math"
	"reflect"
)

func validateCombatNews(e NewsEvent) error {
	c := e.Combat
	if c == nil || c.Amount < 0 || c.Amount > MaxMoney || c.Secondary < 0 || c.Secondary > MaxQuantity || c.Sector < 0 || c.Sector > 3000 {
		return errors.New("invalid combat news")
	}
	if c.Target != "" && !clean(c.Target) {
		return errors.New("invalid combat target snapshot")
	}
	allowed := CombatNews{Operation: c.Operation}
	switch c.Operation {
	case "ship-death":
		allowed.Target = c.Target
	case "ports-captured":
		allowed.Target = c.Target
		allowed.Amount = c.Amount
		if c.Target == "" || c.Amount < 1 || c.Amount > 2999 {
			return errors.New("invalid captured port news")
		}
	case "salvage":
		allowed.Target = c.Target
		allowed.Resource = c.Resource
		allowed.Amount = c.Amount
		if c.Target == "" {
			return errors.New("missing salvage victim")
		}
		switch c.Resource {
		case "summary", "nothing":
			if c.Amount != 0 {
				return errors.New("invalid salvage header")
			}
		case "credits":
			if c.Amount < 1 {
				return errors.New("empty salvage resource")
			}
		case "missiles", "plasma", "ground", "mines", "empty-holds", "ore", "organics", "equipment":
			if c.Amount < 1 || c.Amount > MaxQuantity {
				return errors.New("invalid salvage quantity")
			}
		default:
			return errors.New("invalid salvage resource")
		}
	case "sector-surrender", "sector-destroyed":
		allowed.Target = c.Target
		allowed.Sector = c.Sector
		allowed.Amount = c.Amount
		if c.Target == "" || c.Sector < 1 || c.Amount < 1 || c.Amount > MaxQuantity {
			return errors.New("invalid defense news")
		}
	case "wreck-mines":
		allowed.Sector = c.Sector
		allowed.Amount = c.Amount
		if c.Sector < 1 || c.Amount < 1 || c.Amount > MaxQuantity {
			return errors.New("invalid wreck mine news")
		}
	case "mine-hit":
		allowed.Sector = c.Sector
		allowed.Amount = c.Amount
		if c.Sector < 1 || c.Amount > MaxQuantity {
			return errors.New("invalid mine news")
		}
	case "missile-defense", "plasma-defense":
		allowed.Sector = c.Sector
		allowed.Amount = c.Amount
		if c.Sector < 1 || c.Amount <= 9 || c.Amount > MaxQuantity {
			return errors.New("invalid weapon defense news")
		}
	case "missile-mines", "plasma-mines":
		allowed.Sector = c.Sector
		allowed.Amount = c.Amount
		if c.Sector < 1 || c.Amount < 1 || c.Amount > MaxQuantity {
			return errors.New("invalid weapon mine news")
		}
	case "missile-ship", "plasma-ship":
		allowed.Target = c.Target
		allowed.Sector = c.Sector
		allowed.Amount = c.Amount
		allowed.Secondary = c.Secondary
		if c.Target == "" || c.Sector < 1 || c.Amount > MaxQuantity {
			return errors.New("invalid weapon ship news")
		}
	case "missile-retaliation":
		allowed.Target = c.Target
		allowed.Amount = c.Amount
		if c.Target == "" || c.Amount < 1 || c.Amount > MaxQuantity {
			return errors.New("invalid retaliation news")
		}
	case "missile-planet", "plasma-planet":
		allowed.Target = c.Target
		allowed.Sector = c.Sector
		allowed.Amount = c.Amount
		allowed.ProductionLoss = c.ProductionLoss
		allowed.ProductionRemaining = c.ProductionRemaining
		allowed.GroundLoss = c.GroundLoss
		allowed.GroundRemaining = c.GroundRemaining
		allowed.Destroyed = c.Destroyed
		if c.Target == "" || c.Sector < 1 || c.Amount > MaxQuantity || c.GroundLoss < 0 || c.GroundLoss > MaxQuantity || c.GroundRemaining < 0 || c.GroundRemaining > MaxQuantity || math.IsNaN(c.ProductionLoss) || math.IsInf(c.ProductionLoss, 0) || c.ProductionLoss < 0 || c.ProductionLoss > 3*float64(MaxMoney) || math.IsNaN(c.ProductionRemaining) || math.IsInf(c.ProductionRemaining, 0) || c.ProductionRemaining < 0 || c.ProductionRemaining > 3*float64(MaxMoney) {
			return errors.New("invalid weapon planet news")
		}
	case "mobility-explosion":
		allowed.Target = c.Target
		allowed.Amount = c.Amount
		if c.Target == "" || c.Amount > MaxQuantity {
			return errors.New("invalid mobility news")
		}
	default:
		return errors.New("unsupported combat news operation")
	}
	if !reflect.DeepEqual(*c, allowed) {
		return errors.New("unrelated combat news fields")
	}
	return nil
}
