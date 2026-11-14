package qbmaint

import (
	"bytes"
	"reflect"
	"testing"
)

func initialInput(t *testing.T, d auxFixtureData, c auxCase) (map[string][]byte, InitialRecipe, tailCase) {
	t.Helper()
	before, _, aux := auxPrefix(t, d, c)
	p, x, m, b, tcases := tailFixture(t)
	var recipe InitialRecipe
	recipe.Aux = aux
	var tc tailCase
	for _, v := range p.Cases {
		if v.Name == c.Name {
			recipe.Ports = schedule(t, v)
			break
		}
	}
	for _, v := range x {
		if v.Name == c.Name {
			recipe.WandererDay = v.WandererDay
			recipe.XannoronDay = v.Day
			recipe.InitialState = v.InitialState
			recipe.XannoronTimer = raw4(t, v.Timer)
			recipe.HelperOne = append(recipe.HelperOne, raw4(t, v.WandererTimer))
			break
		}
	}
	for _, v := range m {
		if v.Name == c.Name {
			for _, s := range v.One {
				recipe.HelperOne = append(recipe.HelperOne, raw4(t, s))
			}
			for _, s := range v.Two {
				recipe.HelperTwo = append(recipe.HelperTwo, raw4(t, s))
			}
			break
		}
	}
	for _, v := range b {
		if v.Name == c.Name {
			recipe.BaseDay = v.Day
			recipe.HelperOne = append(recipe.HelperOne, raw4(t, v.Timer))
			break
		}
	}
	for _, v := range tcases {
		if v.Name == c.Name {
			tc = v
			recipe.FinalDay = v.Day
			if v.Timer != nil {
				recipe.HelperOne = append(recipe.HelperOne, raw4(t, *v.Timer))
			}
			break
		}
	}
	return before, recipe, tc
}
func cloneRecipe(r InitialRecipe) InitialRecipe {
	r.Ports.Days = append([]int(nil), r.Ports.Days...)
	r.Ports.TimerMinutes = append([][4]byte(nil), r.Ports.TimerMinutes...)
	r.HelperOne = append([][4]byte(nil), r.HelperOne...)
	r.HelperTwo = append([][4]byte(nil), r.HelperTwo...)
	return r
}
func copyFiles(b map[string][]byte) map[string][]byte {
	c := map[string][]byte{}
	for n, v := range b {
		if v == nil {
			c[n] = nil
		} else {
			c[n] = append([]byte{}, v...)
		}
	}
	return c
}
func TestInitialMaintenanceSixNativeFiles(t *testing.T) {
	d := auxFixture(t)
	for _, c := range d.Cases {
		t.Run(c.Name, func(t *testing.T) {
			before, r, tc := initialInput(t, d, c)
			saved := copyFiles(before)
			recipe := cloneRecipe(r)
			out, s, e := ReplayInitialMaintenance(before, r)
			if e != nil {
				t.Fatal(e)
			}
			if len(out) != 6 {
				t.Fatal("six-file inventory")
			}
			for n, h := range c.Native {
				if digest(out[n]) != h {
					t.Fatal("whole native file mismatch", n)
				}
			}
			if s.FinalState != tc.Final || s.Tail.Candidate != tc.Candidate || s.Draws != s.Wanderer.Draws+s.Xannoron.Draws+s.Mobile.Draws+s.Base.Draws+s.Tail.Draws || s.Draws <= 0 {
				t.Fatal("phase continuation/count")
			}
			if !reflect.DeepEqual(before, saved) || !reflect.DeepEqual(r, recipe) {
				t.Fatal("mutated inputs/recipe")
			}
			for _, v := range out {
				if len(v) > 0 {
					v[0] ^= 255
				}
			}
			if !reflect.DeepEqual(before, saved) {
				t.Fatal("output aliases before files")
			}
		})
	}
}
func TestInitialMaintenanceAtomicPhaseFailures(t *testing.T) {
	d := auxFixture(t)
	before, recipe, _ := initialInput(t, d, d.Cases[0])
	changes := map[string]func(map[string][]byte, *InitialRecipe){"missing file": func(b map[string][]byte, _ *InitialRecipe) { delete(b, "YTNAME.DAT") }, "extra file": func(b map[string][]byte, _ *InitialRecipe) { b["YTRMSG.DAT"] = []byte{} }, "short world": func(b map[string][]byte, _ *InitialRecipe) { b["YTDATA.DAT"] = b["YTDATA.DAT"][:2] }, "ports": func(_ map[string][]byte, r *InitialRecipe) { r.Ports.Days = nil }, "helper one short": func(_ map[string][]byte, r *InitialRecipe) { r.HelperOne = r.HelperOne[:40] }, "helper two short": func(_ map[string][]byte, r *InitialRecipe) { r.HelperTwo = r.HelperTwo[:18] }, "Wanderer day": func(_ map[string][]byte, r *InitialRecipe) { r.WandererDay = 0 }, "Xannoron TIMER": func(_ map[string][]byte, r *InitialRecipe) { r.XannoronTimer = [4]byte{} }, "base day": func(_ map[string][]byte, r *InitialRecipe) { r.BaseDay = 0 }, "rank day": func(_ map[string][]byte, r *InitialRecipe) { r.FinalDay = 0 }, "auxiliary clock": func(_ map[string][]byte, r *InitialRecipe) { r.Aux.ScoreClock = "24:00:01" }}
	for n, f := range changes {
		t.Run(n, func(t *testing.T) {
			b := copyFiles(before)
			r := cloneRecipe(recipe)
			f(b, &r)
			saved := copyFiles(b)
			rc := cloneRecipe(r)
			out, s, e := ReplayInitialMaintenance(b, r)
			if e == nil || out != nil || s != (InitialStats{}) || !reflect.DeepEqual(b, saved) || !reflect.DeepEqual(r, rc) {
				t.Fatal("invalid phase/partial output or input mutation")
			}
		})
	}
	// Invalid late clocks must not expose earlier synthesized world bytes.
	b := copyFiles(before)
	r := cloneRecipe(recipe)
	r.Aux.NewsDate = "2026-02-30"
	if out, s, e := ReplayInitialMaintenance(b, r); e == nil || out != nil || s != (InitialStats{}) || !bytes.Equal(b["YTDATA.DAT"], before["YTDATA.DAT"]) {
		t.Fatal("late auxiliary error leaked partial world")
	}
}
