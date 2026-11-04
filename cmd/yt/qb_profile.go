package main

import (
	"errors"
	"github.com/robbiew/yankeetrader/internal/game"
	"strconv"
	"strings"
)

func validateQBFlags(init bool, profile, raw, date string, sectors int, explicit map[string]bool) (uint32, error) {
	selected := explicit["generation-profile"] || explicit["qb-state"] || explicit["qb-date"]
	if !selected {
		return 0, nil
	}
	if !init {
		return 0, errors.New("QB generation flags require -init")
	}
	if profile != game.QB36Profile {
		return 0, errors.New("QB flags require -generation-profile qb36-v1")
	}
	if !explicit["qb-state"] || !explicit["qb-date"] || date == "" {
		return 0, errors.New("qb36-v1 requires explicit -qb-state and -qb-date")
	}
	for _, name := range []string{"seed", "dos-ports", "dos-warps"} {
		if explicit[name] {
			return 0, errors.New("qb36-v1 conflicts with explicit -" + name)
		}
	}
	if sectors != 3000 {
		return 0, errors.New("qb36-v1 requires 3000 sectors")
	}
	base := 10
	digits := raw
	if strings.HasPrefix(raw, "0x") {
		base = 16
		digits = raw[2:]
	}
	if digits == "" {
		return 0, errors.New("invalid QB state")
	}
	for _, c := range digits {
		if !(c >= '0' && c <= '9') && !(base == 16 && (c >= 'a' && c <= 'f' || c >= 'A' && c <= 'F')) {
			return 0, errors.New("QB state must be unsigned decimal or 0x hexadecimal")
		}
	}
	n, err := strconv.ParseUint(digits, base, 24)
	if err != nil {
		return 0, errors.New("QB state must fit 24 bits")
	}
	return uint32(n), nil
}
