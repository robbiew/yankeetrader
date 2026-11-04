package main

import (
	"bufio"
	"errors"
	"flag"
	"fmt"
	gd "github.com/robbiew/godoors"
	"github.com/robbiew/yankeetrader/internal/door"
	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
	"github.com/robbiew/yankeetrader/internal/version"
	"io"
	prng "math/rand"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

func main() {
	if e := run(); e != nil {
		fmt.Fprintln(os.Stderr, e)
		os.Exit(1)
	}
}
func run() error {
	data := flag.String("data", "data", "world directory")
	showVersion := flag.Bool("version", false, "print application name and version")
	initWorld := flag.Bool("init", false, "create a new world; never overwrites")
	seasonExport := flag.String("season-export", "", "export a private full-season archive to a new file")
	adminReset := flag.Uint64("admin-reset", 0, "end this exact season without a winner; requires -season-export")
	maint := flag.Bool("maint", false, "run daily economy maintenance once")
	seed := flag.Int64("seed", 36, "universe seed")
	sectors := flag.Int("sectors", 3000, "sector count at initialization")
	generationProfile := flag.String("generation-profile", "", "new-world generation profile: qb36-v1")
	qbState := flag.String("qb-state", "", "raw post-RANDOMIZE state: unsigned decimal or 0x hexadecimal")
	qbDate := flag.String("qb-date", "", "explicit QB source date, YYYY-MM-DD (2026..2028)")
	dosWarps := flag.Bool("dos-warps", false, "use recovered DOS warp-generation rules for a new world")
	dosPorts := flag.Bool("dos-ports", false, "use recovered DOS port generation and pricing for a new world")
	genesisPorts := flag.Int("genesis-ports", 300, "initial Genesis threshold: 0 disables; 20..300; omitted defaults to 300")
	local := flag.String("local", "", "local player name")
	compact := flag.Bool("compact", false, "skip DOS startup and use the compact command interface")
	ascii := flag.Bool("ascii", false, "disable ANSI color and cursor control")
	drop := flag.String("drop", "", "Door32 drop-file directory")
	system := flag.String("system", "bbs", "stable BBS identity namespace")
	flag.Parse()
	if *showVersion {
		fmt.Printf("%s\n%s\n%s\n%s\n", version.String(), version.OriginalCredit, version.BasedOn, version.Repository)
		return nil
	}
	if flag.NArg() != 0 {
		return errors.New("unexpected arguments; use -help")
	}
	resetConfigured := false
	flag.Visit(func(f *flag.Flag) {
		if f.Name == "admin-reset" {
			resetConfigured = true
		}
	})
	if resetConfigured && *adminReset == 0 {
		return errors.New("-admin-reset requires a positive current season number")
	}
	adminMode := *seasonExport != "" || resetConfigured
	if adminMode && (*initWorld || *maint || *local != "" || *drop != "") {
		return errors.New("season administration cannot be combined with initialization, maintenance or play")
	}
	if *adminReset != 0 && *seasonExport == "" {
		return errors.New("-admin-reset requires -season-export to a new private archive file")
	}
	if *initWorld && *maint {
		return errors.New("choose either -init or -maint")
	}
	genesisConfigured := false
	dosPortsConfigured := false
	dosWarpsConfigured := false
	flag.Visit(func(f *flag.Flag) {
		if f.Name == "dos-warps" {
			dosWarpsConfigured = true
		}
		if f.Name == "dos-ports" {
			dosPortsConfigured = true
		}
		if f.Name == "genesis-ports" {
			genesisConfigured = true
		}
	})
	if genesisConfigured && !*initWorld {
		return errors.New("-genesis-ports is only supported with -init")
	}
	if dosWarpsConfigured && !*initWorld {
		return errors.New("-dos-warps is only supported with -init")
	}
	if dosPortsConfigured && !*initWorld {
		return errors.New("-dos-ports is only supported with -init")
	}
	visited := map[string]bool{}
	flag.Visit(func(f *flag.Flag) { visited[f.Name] = true })
	state, err := validateQBFlags(*initWorld, *generationProfile, *qbState, *qbDate, *sectors, visited)
	if err != nil {
		return err
	}
	st := store.Store{Dir: *data}
	if adminMode {
		out, err := st.ExportSeason(*seasonExport, *adminReset, time.Now(), *seed)
		if out.Archive != "" {
			fmt.Printf("Private season %d archive saved: %s (world SHA256 %s).\n", out.ArchivedSeason, out.Archive, out.SHA256)
		}
		if out.NewSeason != 0 {
			fmt.Printf("Administrative reset committed. Season %d is ready; old logins must reconnect. No winner declared.\n", out.NewSeason)
		}
		return err
	}
	if *initWorld {
		profile := ""
		if *dosPorts {
			profile = "dos"
		}
		warpProfile := ""
		if *dosWarps {
			warpProfile = "dos"
		}
		var w *game.World
		var e error
		if *generationProfile == game.QB36Profile {
			w, e = game.NewQB36(time.Now(), 36, state, *qbDate)
		} else {
			w, e = game.NewWithGeneration(time.Now(), *seed, *sectors, profile, warpProfile)
		}
		if e != nil {
			return e
		}
		if genesisConfigured {
			w.GenesisPorts = genesisPorts
			if e = w.Validate(); e != nil {
				return e
			}
		}
		if _, e = w.BootstrapWanderer(w.Created, prng.New(prng.NewSource(*seed)).Float64); e != nil {
			return e
		}
		if e = st.Create(w); e != nil {
			return e
		}
		fmt.Println("New world created.")
		return nil
	}
	if *maint {
		var receipt game.MaintenanceReceipt
		e := st.Update(func(w *game.World) error {
			var err error
			receipt, err = w.RunMaintenance(time.Now(), prng.Float64)
			return err
		})
		return printMaintenanceReceipt(os.Stdout, receipt, e)
	}
	if (*local == "") == (*drop == "") {
		return errors.New("choose -local <name> or -drop <directory>")
	}
	realName := *local
	ansi := !*ascii
	alias, identity, minutes := *local, "local:"+strings.ToLower(strings.TrimSpace(*local)), 180
	if *drop != "" {
		info, e := gd.OpenSession(*drop)
		if e != nil {
			return e
		}
		defer gd.CloseSession()
		ansi = info.Emulation == 1 && !*ascii
		alias = info.Alias
		minutes = info.TimeLeft
		uid, name, e := door32Identity(*drop)
		if e != nil {
			return e
		}
		realName = name
		identity = "door32:" + *system + ":" + strconv.Itoa(uid)
	}
	if minutes < 1 || minutes > 1440 {
		return errors.New("session time must be between 1 and 1440 minutes")
	}
	if e := gd.OpenInput(); e != nil {
		return e
	}
	defer gd.CloseSession()
	music := ansi && gd.IsCTerm()
	return (door.Session{Music: music, RealName: realName, Classic: !*compact, ANSI: ansi, Local: *drop == "", Store: st, Terminal: &door.GoDoors{}, Identity: identity, Alias: alias, Deadline: time.Now().Add(time.Duration(minutes) * time.Minute)}).Run()
}

// Door32 line five is the stable BBS user record number; alias is display only.
func recordNumber(dir string) (int, error) {
	n, _, err := door32Identity(dir)
	return n, err
}

func door32Identity(dir string) (int, string, error) {
	entries, e := os.ReadDir(dir)
	if e != nil {
		return 0, "", e
	}
	var path string
	for _, v := range entries {
		if strings.EqualFold(v.Name(), "door32.sys") {
			path = filepath.Join(dir, v.Name())
			break
		}
	}
	f, e := os.Open(path)
	if e != nil {
		return 0, "", e
	}
	defer f.Close()
	scan := bufio.NewScanner(f)
	for i := 0; i < 5; i++ {
		if !scan.Scan() {
			return 0, "", errors.New("Door32 user record number is missing")
		}
	}
	n, e := strconv.Atoi(strings.TrimSpace(scan.Text()))
	if e != nil || n < 1 {
		return 0, "", errors.New("Door32 user record number must be positive")
	}
	name := ""
	if scan.Scan() {
		name = strings.TrimSpace(scan.Text())
	}
	return n, name, nil
}

// A committed durability warning must retain both the saved outcome and any
// output failure. An aborted transaction must never print a success receipt.
func printMaintenanceReceipt(dst io.Writer, receipt game.MaintenanceReceipt, err error) error {
	var committed *store.DurabilityError
	if err != nil && !errors.As(err, &committed) {
		return err
	}
	var text strings.Builder
	if receipt.Ran {
		text.WriteString("Daily economy maintenance completed.\n")
		if receipt.Wanderer.Status != "" {
			fmt.Fprintf(&text, "Wanderer maintenance saved: %s", receipt.Wanderer.Status)
			if receipt.Wanderer.Reason != "" {
				fmt.Fprintf(&text, " (%s)", receipt.Wanderer.Reason)
			}
			if receipt.Wanderer.Destroyed {
				text.WriteString("; destroyed by later daily actions")
			}
			text.WriteString(".\n")
		}
	} else {
		text.WriteString("Maintenance already current; no daily phases repeated.\n")
	}
	_, output := io.WriteString(dst, text.String())
	return errors.Join(err, output)
}
