package qbmaint

import (
	"bytes"
	"fmt"
)

// retainedWandererLosses authenticates the bounded model receipt chain before
// admitting its reduced force inventory downstream. It is not native provenance.
func retainedWandererLosses(world []byte, events []WandererEncounter) (int, error) {
	if len(events) == 0 {
		return 0, nil
	}
	if len(world) != WorldRecords*RecordSize || len(events) != 18 {
		return 0, fmt.Errorf("retained groups 2..19 encounter chain required")
	}
	work := append([]byte(nil), world...)
	rec := work[4051*RecordSize : 4052*RecordSize]
	rate := encode(5000)
	for _, o := range []int{45, 49, 53} {
		copy(rec[o:o+4], rate[:])
	}
	clear(rec[73:77])
	lost := 0
	sector := events[0].Inputs.Sector
	for i, event := range events {
		if event.Inputs.Group != i+2 || event.Inputs.Sector != sector {
			return 0, fmt.Errorf("retained shared pursuit order")
		}
		updated, result, e := ReplayWandererAssault(work, event.Inputs)
		if e != nil || result != event.Result {
			return 0, fmt.Errorf("encounter receipt differs from raw arithmetic replay")
		}
		lost += event.Inputs.Force
		work = updated
	}
	if lost <= 0 || lost >= 10000 || !bytes.Equal(work[4051*RecordSize:4052*RecordSize], world[4051*RecordSize:4052*RecordSize]) {
		return 0, fmt.Errorf("encounter aftermath/force inventory differs")
	}
	return lost, nil
}
