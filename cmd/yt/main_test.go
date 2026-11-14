package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"

	gd "github.com/robbiew/godoors"
)

func TestDoor32StableRecord(t *testing.T) {
	d := t.TempDir()
	p := filepath.Join(d, "DOOR32.SYS")
	if e := os.WriteFile(p, []byte("0\n0\n38400\nTest BBS\n42\nReal Name\nAlias\n10\n60\n0\n1\n"), 0600); e != nil {
		t.Fatal(e)
	}
	n, realName, e := door32Identity(d)
	if realName != "Real Name" {
		t.Fatal("missing real-name default", realName)
	}
	if e != nil || n != 42 {
		t.Fatalf("record=%d error=%v", n, e)
	}
	_ = os.WriteFile(p, []byte("0\n0\n0\nbbs\n-1\n"), 0600)
	if _, e = recordNumber(d); e == nil {
		t.Fatal("negative record accepted")
	}
}

const doorDropFixture = "[file]\r\nFILE_TIME=2026-11-14T10:00:00\r\n[system]\r\nSYS_SOFTWARE=Test 1.0\r\nSYS_NAME=Test\r\nSYS_OP=Sysop\r\nSYS_NODE_NUM=1\r\n[comm]\r\nCOMM_TYPE=stdio\r\nCOMM_CHARSET=CP437\r\n[user]\r\nUSER_ALIAS=Caller\r\nUSER_NUMBER=42\r\nUSER_KEY=42-1693526400\r\n%s[terminal]\r\nTERM_COLS=80\r\nTERM_ROWS=24\r\nTERM_TYPE=ansi\r\n[session]\r\n%s"

func readDoorDrop(t *testing.T, user, session string) gd.DropFile {
	t.Helper()
	p := filepath.Join(t.TempDir(), "DOORDROP.INI")
	if e := os.WriteFile(p, []byte(fmt.Sprintf(doorDropFixture, user, session)), 0600); e != nil {
		t.Fatal(e)
	}
	info, e := gd.ReadDropFile(p)
	if e != nil || info.INI == nil {
		t.Fatalf("%+v %v", info, e)
	}
	return info
}

func TestDoorDropIdentity(t *testing.T) {
	id, realName, minutes, e := doorDropIdentity(readDoorDrop(t, "", "TIME_LEFT=61\r\n"), "mybbs")
	if e != nil || id != "doordrop:mybbs:42-1693526400" || realName != "" || minutes != 2 {
		t.Fatalf("%q %q %d %v", id, realName, minutes, e)
	}
	_, realName, minutes, _ = doorDropIdentity(readDoorDrop(t, "USER_REALNAME=Real Name\r\n", ""), "mybbs")
	if realName != "Real Name" || minutes != 1440 {
		t.Fatalf("real name %q, unlimited minutes %d", realName, minutes)
	}
	if _, _, minutes, _ = doorDropIdentity(readDoorDrop(t, "", "TIME_LEFT=999999\r\n"), "mybbs"); minutes != 1440 {
		t.Fatalf("long session minutes %d", minutes)
	}
	if _, _, _, e = doorDropIdentity(readDoorDrop(t, "USER_ROLE=guest\r\n", ""), "mybbs"); e == nil {
		t.Fatal("guest accepted")
	}
}

func TestValidUserKey(t *testing.T) {
	for key, want := range map[string]bool{"42": true, "42-1693526400": true, "a.b_c-d": true, "": false, "-42": false, ".x": false, "a b": false, "a/b": false, strings.Repeat("a", 64): true, strings.Repeat("a", 65): false} {
		if validUserKey(key) != want {
			t.Errorf("validUserKey(%q) != %v", key, want)
		}
	}
}
