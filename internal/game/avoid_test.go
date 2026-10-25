package game

import (
	"encoding/json"
	"os"
	"reflect"
	"testing"
)

func TestAvoidRoutesManualMovementAndPrivateLists(t *testing.T) {
	w, p := navigationWorld(t)
	other, _ := w.Join("other", "Other")
	other.Sector = 100
	if err := w.SetAvoid(p.ID, 1, 101); err != nil {
		t.Fatal(err)
	}
	path, err := w.PlayerPath(p.ID, 100, 110)
	if err != nil || !reflect.DeepEqual(path, []int{100, 102, 108, 109, 110}) {
		t.Fatalf("route %v, %v", path, err)
	}
	path, err = w.PlayerPath(other.ID, 100, 110)
	if err != nil || !reflect.DeepEqual(path, []int{100, 101, 107, 109, 110}) {
		t.Fatal("another player inherited routing preferences")
	}
	if err := w.SetAvoid(p.ID, 30, 102); err != nil {
		t.Fatal(err)
	}
	if _, err = w.Course(p.ID, 110); err == nil {
		t.Fatal("ignored avoid slot 30")
	}
	if err = w.Move(p.ID, 101); err != nil {
		t.Fatal("manual movement must ignore avoid list", err)
	}
	if p.Turns != 499 {
		t.Fatal("avoid edit or pathfinding charged turns")
	}
	if err = w.SetAvoid(p.ID, 1, 0); err != nil {
		t.Fatal(err)
	}
	if p.AvoidSectors[0] != 0 || other.AvoidSectors != nil {
		t.Fatal("slot clear affected another player")
	}
}

func TestAvoidEndpointsAndStaleAutopilot(t *testing.T) {
	for _, target := range []int{100, 110} {
		w, p := navigationWorld(t)
		if err := w.SetAvoid(p.ID, 1, target); err != nil {
			t.Fatal(err)
		}
		if _, err := w.PlayerPath(p.ID, 100, 110); err == nil {
			t.Fatal("avoided endpoint accepted")
		}
	}
	w, p := navigationWorld(t)
	course, err := w.Course(p.ID, 110)
	if err != nil {
		t.Fatal(err)
	}
	if err = w.FollowCourse(p.ID, course); err != nil {
		t.Fatal(err)
	}
	if err = w.SetAvoid(p.ID, 1, 109); err != nil {
		t.Fatal(err)
	}
	if err = w.FollowCourse(p.ID, course[1:]); err == nil {
		t.Fatal("stale course crossed newly avoided future sector")
	}
	if p.Sector != 101 || p.Turns != 499 {
		t.Fatal("stale course moved or refunded completed hop")
	}
}

func TestAvoidValidationAndRejectedEditRollback(t *testing.T) {
	w, p := navigationWorld(t)
	for _, tc := range [][2]int{{0, 101}, {31, 101}, {1, -1}, {1, 112}} {
		before, _ := json.Marshal(w)
		if err := w.SetAvoid(p.ID, tc[0], tc[1]); err == nil {
			t.Fatalf("accepted edit %v", tc)
		}
		after, _ := json.Marshal(w)
		if string(before) != string(after) {
			t.Fatal("rejected edit mutated world")
		}
	}
	if err := w.SetAvoid(999, 1, 101); err == nil {
		t.Fatal("missing player accepted")
	}
	// Duplicates are legal in distinct numbered slots, as in the original editor.
	for slot := 1; slot <= 30; slot++ {
		if err := w.SetAvoid(p.ID, slot, 101); err != nil {
			t.Fatal(err)
		}
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
	p.AvoidSectors = append(p.AvoidSectors, 0)
	if err := w.Validate(); err == nil {
		t.Fatal("oversized saved avoid list accepted")
	}
	p.AvoidSectors = []int{-1}
	if err := w.Validate(); err == nil {
		t.Fatal("invalid saved sector accepted")
	}
	p.AvoidSectors = nil
	if err := w.Validate(); err != nil {
		t.Fatal("existing world without avoid list rejected", err)
	}
}

func TestDOSAvoidGolden(t *testing.T) {
	var fixture struct {
		Scenarios []struct {
			Name        string
			Edits       [][2]int
			Route       []int
			SectorAfter int   `json:"sector_after"`
			TurnsAfter  int64 `json:"turns_after"`
		}
	}
	data, err := os.ReadFile("testdata/dos-avoid.json")
	if err != nil {
		t.Fatal(err)
	}
	if err = json.Unmarshal(data, &fixture); err != nil {
		t.Fatal(err)
	}
	if len(fixture.Scenarios) != 10 {
		t.Fatal("incomplete avoid fixture")
	}
	for _, tc := range fixture.Scenarios {
		t.Run(tc.Name, func(t *testing.T) {
			w, p := navigationWorld(t)
			for _, edit := range tc.Edits {
				err := w.SetAvoid(p.ID, edit[0], edit[1])
				invalid := edit[0] < 1 || edit[0] > 30 || edit[1] > 111
				if (err != nil) != invalid {
					t.Fatalf("edit %v: %v", edit, err)
				}
			}
			if tc.Name == "avoid-manual" {
				err = w.Move(p.ID, 101)
			} else {
				var route []int
				route, err = w.PlayerPath(p.ID, 100, 110)
				if len(tc.Route) > 0 && (err != nil || !reflect.DeepEqual(route, tc.Route)) {
					t.Fatalf("Go %v, DOS %v, %v", route, tc.Route, err)
				}
				if len(tc.Route) == 0 && err == nil {
					t.Fatal("DOS blocked route accepted")
				}
			}
			if p.Sector != tc.SectorAfter || p.Turns != tc.TurnsAfter {
				t.Fatalf("Go %+v disagrees with DOS sector %d/turns %d", p, tc.SectorAfter, tc.TurnsAfter)
			}
		})
	}
}
