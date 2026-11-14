package qbmaint

import (
	"bytes"
	"encoding/json"
	"os"
	"testing"
)

type tailCase struct {
	Name             string
	State            uint32
	Timer            *string `json:"candidate_timer"`
	Candidate, Draws int
	Lottery          float32
	Final            uint32 `json:"final_state"`
	Day              int    `json:"final_day"`
	Native           string `json:"native_world_sha256"`
}

func tailFixture(t *testing.T) (fixture, []xannoronCase, []mobileCase, []baseCase, []tailCase) {
	t.Helper()
	p, x, m, b := baseFixture(t)
	raw, e := os.ReadFile("testdata/npc_tail.json")
	if e != nil {
		t.Fatal(e)
	}
	var d struct {
		Format string
		Cases  []tailCase
	}
	if e = json.Unmarshal(raw, &d); e != nil || d.Format != "qb-initial-npc-tail-v1" || len(d.Cases) != 29 {
		t.Fatal("tail fixture", e)
	}
	return p, x, m, b, d.Cases
}
func tailPrefix(t *testing.T, p fixture, x []xannoronCase, m []mobileCase, b []baseCase, c tailCase) ([]byte, TailInputs) {
	t.Helper()
	for _, bc := range b {
		if bc.Name != c.Name {
			continue
		}
		before, in := basePrefix(t, p, x, m, bc)
		out, s, e := ReplayMercenaryBaseBirth(before, in)
		if e != nil || s.FinalState != c.State {
			t.Fatal("base handoff", e)
		}
		ti := TailInputs{State: s.FinalState}
		if c.Timer != nil {
			v := raw4(t, *c.Timer)
			ti.CandidateTimer = &v
		}
		return out, ti
	}
	t.Fatal("missing base predecessor")
	return nil, TailInputs{}
}
func TestNPCTailAndWholeNativeWorld(t *testing.T) {
	p, x, m, b, cases := tailFixture(t)
	selected, skipped := 0, 0
	for _, c := range cases {
		t.Run(c.Name, func(t *testing.T) {
			before, in := tailPrefix(t, p, x, m, b, c)
			saved := append([]byte(nil), before...)
			s, e := ReplayInitialNPCTail(before, in)
			if e != nil {
				t.Fatal(e)
			}
			if s != (TailStats{DesertionDraws: 20, Draws: c.Draws, Candidate: c.Candidate, Lottery: c.Lottery, FinalState: c.Final}) {
				t.Fatal("independent tail model", s, c)
			}
			if !bytes.Equal(before, saved) {
				t.Fatal("tail wrote world")
			}
			if s.Candidate == 0 {
				skipped++
			} else {
				selected++
			}
			// Compose all implemented Go world writers; native bytes never enter inputs.
			var pc *fixtureCase
			for i := range p.Cases {
				if p.Cases[i].Name == c.Name {
					pc = &p.Cases[i]
					break
				}
			}
			if pc == nil {
				t.Fatal("port schedule")
			}
			block, _, e := ReplayCleanPorts(unpack(t, p.Worlds[pc.BeforeSHA]), schedule(t, *pc))
			if e != nil {
				t.Fatal(e)
			}
			world := append([]byte(nil), before...)
			copy(world[PortStart:PortStart+len(block)], block)
			world, e = ReplayInactiveRanks(world, c.Day)
			if e != nil {
				t.Fatal(e)
			}
			if digest(world) != c.Native {
				t.Fatal("complete native YTDATA world mismatch")
			}
		})
	}
	if selected == 0 || skipped == 0 {
		t.Fatal("both lottery branches required")
	}
}
func TestNPCTailAdmission(t *testing.T) {
	p, x, m, b, cases := tailFixture(t)
	before, in := tailPrefix(t, p, x, m, b, cases[0])
	changes := map[string]func([]byte, *TailInputs){"state": func(_ []byte, i *TailInputs) { i.State = 1 << 24 }, "active": func(b []byte, _ *TailInputs) { b[137+88] = 129 }, "funded treasury": func(b []byte, _ *TailInputs) { v := encode(100); copy(b[3051*137+89:], v[:]) }, "human owner": func(b []byte, _ *TailInputs) {
		hq, _ := integer([4]byte(b[117:121]))
		v := encode(2)
		copy(b[(50+hq)*137+85:], v[:])
	}, "base": func(b []byte, _ *TailInputs) { b[4149*137] = 'X' }, "revenge": func(b []byte, _ *TailInputs) { v := encode(3); copy(b[71*137+105:], v[:]) }}
	for n, f := range changes {
		t.Run(n, func(t *testing.T) {
			v := append([]byte(nil), before...)
			i := in
			f(v, &i)
			saved := append([]byte(nil), v...)
			s, e := ReplayInitialNPCTail(v, i)
			if e == nil || s != (TailStats{}) || !bytes.Equal(v, saved) {
				t.Fatal("invalid admission/partial stats")
			}
		})
	}
	if s, e := ReplayInitialNPCTail(before[:2], in); e == nil || s != (TailStats{}) {
		t.Fatal("short world")
	}
	for _, c := range cases {
		v, i := tailPrefix(t, p, x, m, b, c)
		if c.Timer == nil {
			raw := [4]byte{}
			i.CandidateTimer = &raw
		} else {
			i.CandidateTimer = nil
		}
		if s, e := ReplayInitialNPCTail(v, i); e == nil || s != (TailStats{}) {
			t.Fatal("conditional helper inventory", c.Name)
		}
	}
}

func TestNPCTailLotteryHalfBoundary(t *testing.T) {
	p, x, m, b, cases := tailFixture(t)
	before, _ := tailPrefix(t, p, x, m, b, cases[0])
	// Synthetic qbrng inverse states make the 21st draw exactly .5 or one RNG quantum below.
	for _, tc := range []struct {
		state    uint32
		selected bool
	}{{0x740f18, false}, {0xdbae9d, true}} {
		in := TailInputs{State: tc.state}
		if tc.selected {
			timer := [4]byte{}
			in.CandidateTimer = &timer
		}
		s, e := ReplayInitialNPCTail(before, in)
		if e != nil {
			t.Fatal(e)
		}
		if tc.selected && s.Lottery != .5 || !tc.selected && s.Lottery != float32(0x7fffff)/float32(1<<24) {
			t.Fatal("inverse gate state", s)
		}
		if (s.Candidate != 0) != tc.selected {
			t.Fatal("lottery equality gate", s)
		}
	}
}
