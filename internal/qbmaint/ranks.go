package qbmaint

import "fmt"

// ReplayInactiveRanks applies only the recovered all-inactive rank-cache reset
// and final day watermark to an independently modeled default-layout world.
// finalDay is an explicit source-qualified base-year day, not a host date.
// It does not compute rankings, move NPCs, create reports or select game policy.
// Input storage is readonly; unsupported profiles return no partial world.
func ReplayInactiveRanks(before []byte, finalDay int) ([]byte, error) {
	if len(before) != WorldRecords*RecordSize || finalDay < 1 || finalDay > 732 {
		return nil, fmt.Errorf("inactive ranks: default world and day 1..732 required")
	}
	for off, want := range map[int]int{53: 51, 57: 3051, 61: 4051, 93: 4151} {
		v, ok := integer([4]byte(before[off : off+4]))
		if !ok || v != want {
			return nil, fmt.Errorf("inactive ranks: default geometry required")
		}
	}
	for i := 1; i <= 50; i++ {
		if before[i*RecordSize+85+3] != 0 {
			return nil, fmt.Errorf("inactive ranks: active player outside profile")
		}
	}
	out := append([]byte(nil), before...)
	day := encode(finalDay)
	copy(out[81:85], day[:])
	unset := encode(-1)
	for i := 1; i <= 50; i++ {
		at := i*RecordSize + 109
		copy(out[at:at+4], unset[:])
	}
	return out, nil
}
