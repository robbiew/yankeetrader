package main

import "testing"

func TestQBFlags(t *testing.T) {
	for _, raw := range []string{"0", "51205", "0xc805", "0xC805", "16777215"} {
		if _, err := validateQBFlags(true, "qb36-v1", raw, "2027-01-01", 3000, map[string]bool{"generation-profile": true, "qb-state": true, "qb-date": true}); err != nil {
			t.Fatal(raw, err)
		}
	}
	for _, raw := range []string{"", "-1", "+1", "0Xc805", "0x", "0x1000000", "16777216", "1x", " 0", "1_0", "1.0"} {
		if _, err := validateQBFlags(true, "qb36-v1", raw, "2027-01-01", 3000, map[string]bool{"generation-profile": true, "qb-state": true, "qb-date": true}); err == nil {
			t.Fatal("invalid state", raw)
		}
	}
	for _, name := range []string{"seed", "dos-ports", "dos-warps"} {
		if _, err := validateQBFlags(true, "qb36-v1", "0xc805", "2027-01-01", 3000, map[string]bool{"generation-profile": true, "qb-state": true, "qb-date": true, name: true}); err == nil {
			t.Fatal("conflict", name)
		}
	}
	for _, tc := range []struct {
		init    bool
		profile string
		n       int
		flags   map[string]bool
	}{
		{false, "qb36-v1", 3000, map[string]bool{"generation-profile": true}},
		{true, "unknown", 3000, map[string]bool{"generation-profile": true}},
		{true, "", 3000, map[string]bool{"qb-state": true}},
		{true, "qb36-v1", 32, map[string]bool{"generation-profile": true, "qb-state": true, "qb-date": true}},
		{true, "qb36-v1", 3000, map[string]bool{"generation-profile": true, "qb-date": true}},
	} {
		if _, err := validateQBFlags(tc.init, tc.profile, "0xc805", "2027-01-01", tc.n, tc.flags); err == nil {
			t.Fatal(tc)
		}
	}
}
