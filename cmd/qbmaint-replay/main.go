// qbmaint-replay is a research adapter, separate from the playable yt command.
package main

import (
	"flag"
	"fmt"
	"github.com/robbiew/yankeetrader/internal/qbreplay"
	"io"
	"os"
	"path/filepath"
)

func run(args []string, stdout, stderr io.Writer) error {
	f := flag.NewFlagSet("qbmaint-replay", flag.ContinueOnError)
	f.SetOutput(stderr)
	var c qbreplay.Config
	f.StringVar(&c.RecipePath, "recipe", "", "research JSON: v1 initial or v2 convergence-three-day")
	f.StringVar(&c.BeforeDir, "before", "", "directory containing three original before files")
	f.StringVar(&c.SourceRoot, "source-root", "", "checkout root for declared source hashes")
	f.StringVar(&c.OutDir, "out", "", "new directory outside input/source trees; publishes replay/ inside it")
	if e := f.Parse(args); e != nil {
		if e == flag.ErrHelp {
			return nil
		}
		return e
	}
	if f.NArg() != 0 {
		return fmt.Errorf("unexpected positional arguments")
	}
	r, e := qbreplay.Run(c)
	if e != nil {
		return e
	}
	_, e = fmt.Fprintf(stdout, "Research replay %s written to %s (%d modeled RNG draws).\n", r.Name, filepath.Join(c.OutDir, "replay"), r.Draws)
	if e != nil {
		return fmt.Errorf("replay already published at %s; status output failed: %w", filepath.Join(c.OutDir, "replay"), e)
	}
	return nil
}
func main() {
	if e := run(os.Args[1:], os.Stdout, os.Stderr); e != nil {
		fmt.Fprintln(os.Stderr, e)
		os.Exit(1)
	}
}
