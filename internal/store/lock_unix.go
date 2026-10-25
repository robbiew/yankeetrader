//go:build !windows

package store

import (
	"golang.org/x/sys/unix"
	"os"
)

func lock(f *os.File) error { return unix.Flock(int(f.Fd()), unix.LOCK_EX) }
func unlock(f *os.File)     { _ = unix.Flock(int(f.Fd()), unix.LOCK_UN) }
func syncDir(path string) error {
	f, e := os.Open(path)
	if e != nil {
		return e
	}
	defer f.Close()
	return f.Sync()
}
