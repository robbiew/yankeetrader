package main

import (
	"os"
	"path/filepath"
	"testing"
)

func TestDoor32StableRecord(t *testing.T) {
	d := t.TempDir()
	p := filepath.Join(d, "DOOR32.SYS")
	if e := os.WriteFile(p, []byte("0\n0\n38400\nTest BBS\n42\nReal Name\nAlias\n10\n60\n0\n1\n"), 0600); e != nil {
		t.Fatal(e)
	}
	n, e := recordNumber(d)
	if e != nil || n != 42 {
		t.Fatalf("record=%d error=%v", n, e)
	}
	_ = os.WriteFile(p, []byte("0\n0\n0\nbbs\n-1\n"), 0600)
	if _, e = recordNumber(d); e == nil {
		t.Fatal("negative record accepted")
	}
}
