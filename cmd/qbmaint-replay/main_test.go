package main

import (
	"bytes"
	"testing"
)

func TestUsageAndArgumentErrors(t *testing.T) {
	for _, args := range [][]string{nil, {"unexpected"}, {"-unknown"}} {
		var out, err bytes.Buffer
		if e := run(args, &out, &err); e == nil {
			t.Fatal("missing/invalid args admitted", args)
		}
	}
	var out, err bytes.Buffer
	if e := run([]string{"-help"}, &out, &err); e != nil || !bytes.Contains(err.Bytes(), []byte("source-root")) {
		t.Fatal("help", e)
	}
}
