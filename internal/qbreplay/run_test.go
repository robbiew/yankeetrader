package qbreplay

import (
	"bytes"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
)

func TestPublishCompleteBundleAndRefuseExisting(t *testing.T) {
	parent := t.TempDir()
	out := filepath.Join(parent, "out")
	files := map[string][]byte{}
	for _, n := range outputNames {
		files[n] = []byte(n)
	}
	receipt := []byte("receipt\n")
	if e := publish(parent, out, files, receipt); e != nil {
		t.Fatal(e)
	}
	entries, e := os.ReadDir(filepath.Join(out, "replay"))
	if e != nil || len(entries) != 7 {
		t.Fatal("bundle inventory", e)
	}
	for n, b := range files {
		got, e := os.ReadFile(filepath.Join(out, "replay", n))
		if e != nil || !bytes.Equal(got, b) {
			t.Fatal("published bytes", n, e)
		}
	}
	if e := publish(parent, out, files, []byte("replacement")); e == nil {
		t.Fatal("existing directory reused")
	}
	r, _ := os.ReadFile(filepath.Join(out, "replay", "receipt.json"))
	if !bytes.Equal(r, receipt) {
		t.Fatal("existing receipt changed")
	}
	entries, _ = os.ReadDir(parent)
	if len(entries) != 1 {
		t.Fatal("staging files left behind")
	}
}
func TestPublishConcurrentReservationAndSymlinkRefusal(t *testing.T) {
	parent := t.TempDir()
	out := filepath.Join(parent, "out")
	files := map[string][]byte{}
	for _, n := range outputNames {
		files[n] = []byte(n)
	}
	var wg sync.WaitGroup
	results := make(chan error, 2)
	for i := 0; i < 2; i++ {
		wg.Add(1)
		go func() { defer wg.Done(); results <- publish(parent, out, files, nil) }()
	}
	wg.Wait()
	close(results)
	success := 0
	for e := range results {
		if e == nil {
			success++
		}
	}
	if success != 1 {
		t.Fatal("exclusive output reservation", success)
	}
	link := filepath.Join(parent, "link")
	if e := os.Symlink(out, link); e != nil {
		t.Skip(e)
	}
	if e := publish(parent, link, files, nil); e == nil {
		t.Fatal("symlink output reused")
	}
}
func TestRootConfinementAndFileLimits(t *testing.T) {
	root := t.TempDir()
	nested := filepath.Join(root, "nested")
	if e := os.Mkdir(nested, 0700); e != nil {
		t.Fatal(e)
	}
	if ok, e := within(nested, root); e != nil || !ok {
		t.Fatal("ancestor check", e)
	}
	outside := t.TempDir()
	path := filepath.Join(outside, "file")
	os.WriteFile(path, []byte("secret"), 0600)
	if e := os.Symlink(path, filepath.Join(root, "escape")); e != nil {
		t.Skip(e)
	}
	if _, e := containedFile(root, "escape"); e == nil {
		t.Fatal("source symlink escaped")
	}
	if _, e := containedFile(root, "../file"); e == nil {
		t.Fatal("traversal admitted")
	}
	if _, e := readLimited(path, 2); e == nil {
		t.Fatal("large input admitted")
	}
	if _, e := readLimited(root, 100); e == nil {
		t.Fatal("directory read as file")
	}
}
func TestRunRejectsBeforeAnyOutputOnInvalidSchemaOrSource(t *testing.T) {
	parent := t.TempDir()
	before := filepath.Join(parent, "before")
	source := filepath.Join(parent, "source")
	os.Mkdir(before, 0700)
	os.Mkdir(source, 0700)
	recipe := filepath.Join(parent, "recipe.json")
	out := filepath.Join(parent, "out")
	os.WriteFile(recipe, []byte(`{}`), 0600)
	config := Config{RecipePath: recipe, BeforeDir: before, SourceRoot: source, OutDir: out}
	if _, e := Run(config); e == nil {
		t.Fatal("invalid schema admitted")
	}
	if _, e := os.Lstat(out); !os.IsNotExist(e) {
		t.Fatal("invalid recipe published output")
	}
	os.WriteFile(recipe, encoded(t, sampleDocument()), 0600)
	if _, e := Run(config); e == nil {
		t.Fatal("missing original source admitted")
	}
	if _, e := os.Lstat(out); !os.IsNotExist(e) {
		t.Fatal("source error published output")
	}
	config.OutDir = filepath.Join(before, "result")
	if _, e := Run(config); e == nil || !strings.Contains(e.Error(), "outside") {
		t.Fatal("output inside before admitted", e)
	}
	config.OutDir = filepath.Join(source, "result")
	if _, e := Run(config); e == nil || !strings.Contains(e.Error(), "outside") {
		t.Fatal("output inside source admitted", e)
	}
}

func TestPublishRefusesExistingFileAndOutputTreeAliases(t *testing.T) {
	parent := t.TempDir()
	path := filepath.Join(parent, "existing")
	os.WriteFile(path, []byte("keep"), 0600)
	if e := publish(parent, path, map[string][]byte{}, nil); e == nil {
		t.Fatal("existing file reused")
	}
	b, _ := os.ReadFile(path)
	if string(b) != "keep" {
		t.Fatal("existing file changed")
	}
	source := filepath.Join(parent, "source")
	before := filepath.Join(parent, "before")
	os.Mkdir(source, 0700)
	os.Mkdir(before, 0700)
	recipe := filepath.Join(parent, "recipe.json")
	os.WriteFile(recipe, encoded(t, sampleDocument()), 0600)
	alias := filepath.Join(parent, "alias")
	if e := os.Symlink(before, alias); e != nil {
		t.Skip(e)
	}
	if _, e := Run(Config{RecipePath: recipe, BeforeDir: before, SourceRoot: source, OutDir: filepath.Join(alias, "result")}); e == nil || !strings.Contains(e.Error(), "outside") {
		t.Fatal("aliased output tree admitted", e)
	}
}
