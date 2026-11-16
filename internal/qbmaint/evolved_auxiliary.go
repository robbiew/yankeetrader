package qbmaint

import (
	"bytes"
	"fmt"
	"time"
)

// EvolvedAuxInputs preserves the source's separate news/score text clocks and
// explicit final day. Created is source ordered: Wanderer, Xannoron, Base.
type EvolvedAuxInputs struct {
	AuxInputs
	FinalDay int
	Created  [3]bool
}

// ReplayEvolvedAux finalizes only the retained convergence profile: final
// watermark/inactive ranks and five auxiliary files. It takes original before
// files and an independently modeled pre-final world, never a target or host
// clock. Errors return no six-file result; all input storage is readonly.
func ReplayEvolvedAux(before map[string][]byte, world []byte, in EvolvedAuxInputs) (map[string][]byte, error) {
	fail := func(s string) (map[string][]byte, error) { return nil, fmt.Errorf("evolved auxiliary replay: %s", s) }
	names := []string{"YTDATA.DAT", "YTNAME.DAT", "YTNEWS.DAT", "YTYNEWS.DAT", "YTRMSG.DAT", "YTSCORE.ASC"}
	if len(before) != 3 && len(before) != 6 {
		return fail("exact three initial or six evolved input files")
	}
	for i, n := range names {
		_, ok := before[n]
		if (i < 3 || len(before) == 6) && !ok {
			return fail("missing before file")
		}
	}
	if len(before["YTRMSG.DAT"]) != 0 {
		return fail("private-message compression outside profile")
	}
	if in.FinalDay < 306 || in.FinalDay > 308 {
		return fail("convergence final day 306..308 required")
	}
	all := [3]bool{true, true, true}
	none := [3]bool{}
	if in.Created != all && in.Created != none {
		return fail("only complete creation or existing-home mask")
	}
	bootstrap := in.Created == all
	if bootstrap != (len(before) == 3) || bootstrap != (in.FinalDay == 306) {
		return fail("creation/file inventory/day context")
	}
	expectedDate := time.Date(2026, 1, in.FinalDay, 0, 0, 0, 0, time.UTC).Format("2006-01-02")
	if in.NewsDate != expectedDate || in.ScoreDate != expectedDate {
		return fail("independent text dates must match explicit convergence day")
	}
	old := before["YTDATA.DAT"]
	if len(old) != WorldRecords*RecordSize || len(world) != len(old) {
		return fail("complete default worlds required")
	}
	raw := func(b []byte, r, o int) [4]byte { a := (r-1)*RecordSize + o; return [4]byte(b[a : a+4]) }
	get := func(b []byte, r, o int) int {
		n, ok := integer(raw(b, r, o))
		if !ok {
			return -999999
		}
		return n
	}
	for _, b := range [][]byte{old, world} {
		for o, n := range map[int]int{53: 51, 57: 3051, 61: 4051, 93: 4151} {
			if get(b, 1, o) != n {
				return fail("default geometry")
			}
		}
		if get(b, 1, 41) != 11 || string(b[:11]) != "YTSCORE.ASC" {
			return fail("fixed unaliased scoreboard path")
		}
		if get(b, 1, 45) != 26 || get(b, 1, 81) != in.FinalDay-1 {
			return fail("saved base year and pre-final watermark")
		}
		for r := 3052; r <= 4051; r++ {
			if get(b, r, 89) != 0 {
				return fail("tax-funded hiring/news")
			}
		}
		total := 0
		for s := 1; s <= 3000; s++ {
			force, owner := get(b, 51+s, 81), get(b, 51+s, 85)
			if force < 0 || force > 10000 || owner != 0 && owner != -1 && owner != -2 || force > 0 && owner != -1 {
				return fail("bounded physical Xannor deployments")
			}
			total += force
		}
		if total != 10000 {
			return fail("physical force conservation")
		}
	}
	for r := 2; r <= 51; r++ {
		a := (r - 1) * RecordSize
		if !bytes.Equal(old[a:a+RecordSize], world[a:a+RecordSize]) {
			return fail("pre-final human records changed")
		}
		for o := 41; o < 137; o += 4 {
			v := get(old, r, o)
			if v != 0 && (o != 109 || v != -1) {
				return fail("only inactive humans/empty assets")
			}
		}
	}
	links := func(b []byte) (map[int][]int, bool) {
		m := map[int][]int{}
		for s := 1; s <= 3000; s++ {
			v := get(b, 51+s, 93)
			if v < 0 || v != 0 && v != 1 && v != 2 && v != 99 && v != 100 {
				return nil, false
			}
			if v > 0 {
				m[v] = append(m[v], s)
			}
		}
		return m, true
	}
	oldLinks, ok := links(old)
	if !ok {
		return fail("before planet references")
	}
	newLinks, ok := links(world)
	if !ok {
		return fail("modeled planet references")
	}
	homes := []struct {
		slot  int
		name  string
		owner int
	}{{1, "The Wanderer", 0}, {100, "Xannoron", -1}, {99, "Mercenary Base", -2}}
	named := func(b []byte, r int, name string, owner int) bool {
		a := (r - 1) * RecordSize
		return get(b, r, 85) == len(name) && get(b, r, 73) == owner && bytes.Equal(b[a:a+41], append([]byte(name), bytes.Repeat([]byte{' '}, 41-len(name))...))
	}
	for i, h := range homes {
		r := 4051 + h.slot
		active := get(old, r, 85) != 0
		if active {
			if in.Created[i] || !named(old, r, h.name, h.owner) || len(oldLinks[h.slot]) != 1 {
				return fail("existing before home identity/link")
			}
		} else if !in.Created[i] || len(oldLinks[h.slot]) != 0 {
			return fail("missing before home/creation mismatch")
		}
		if !named(world, r, h.name, h.owner) || len(newLinks[h.slot]) != 1 {
			return fail("modeled home identity/link")
		}
	}
	for index, b := range [][]byte{old, world} {
		m := oldLinks
		if index == 1 {
			m = newLinks
		}
		if !named(b, 4053, "Convergence Haven", -1) || len(m[2]) != 1 {
			return fail("friendly Convergence Haven required")
		}
		for slot := 1; slot <= 100; slot++ {
			if slot != 1 && slot != 2 && slot != 99 && slot != 100 && get(b, 4051+slot, 85) != 0 {
				return fail("additional active planet")
			}
		}
	}
	final, e := ReplayInactiveRanks(world, in.FinalDay)
	if e != nil {
		return fail(e.Error())
	}
	news, board, e := formatAuxReports(in.AuxInputs, 1000000, in.Created, nil)
	if e != nil {
		return fail(e.Error())
	}
	return map[string][]byte{"YTDATA.DAT": final, "YTNAME.DAT": bytes.Clone(before["YTNAME.DAT"]), "YTYNEWS.DAT": bytes.Clone(before["YTNEWS.DAT"]), "YTRMSG.DAT": {}, "YTNEWS.DAT": news, "YTSCORE.ASC": board}, nil
}
