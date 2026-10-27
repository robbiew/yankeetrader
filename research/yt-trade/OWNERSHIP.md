# Port acquisition and treasury recovery

Nine isolated DOS sessions now cover an owned-port buyout, buyout followed by
collection, explicit cancellation, default cancellation, insufficient funds,
unowned purchase, self-purchase rejection, remote collection and the computer's
read-only report. Originals were not modified. The feeder suite is reproduced
with `python3 scripts/recover_navigation.py /tmp/yt-ownership --ownership`.

The controlled port produces 100 units of each commodity. Its price is
`floor((ore production + organics production + equipment production)/10) + 1`,
therefore 31 credits. Buying another player's port takes 31 from the buyer,
pays the seller 31 plus the existing 777-credit treasury, clears that treasury,
and transfers ownership. DOS also increments/decrements its cached port counts.
The Go version derives counts from actual ownership.

`B` does not require docking or spend turns. Both `N` and an empty confirmation
cancel. `$` collects all personally owned accounts remotely without turns.
Computer command `12` reports balances without clearing them. Team membership
does not grant another player's port income. Each case includes compressed
before/after saves, input, transcript and DOSBox log under `ownership-dos`;
`results.json` pins executable/save/input/transcript hashes and fixture patches.
`python3 scripts/verify_ownership_evidence.py` checks all 18 saves and the nine
Go fixtures against those saves. Static acquisition dispatch is at
`1000:2342..2709` and treasury dispatch at `1f42:8901..8c7c` in the archived
runtime-aware listings. QuickBASIC bytecode listings require runtime context.

## Modern implementation and deliberate fixes

The Go game implements acquisition, forced buyouts, reports and collection.
Earth remains unownable. Money uses exact integers. The confirmation expires in
five minutes and rechecks buyer, sector, port, owner, production-based price and
available cash in the saved-world transaction. The seller's credit capacity is
checked before any money or ownership changes. Any changed ownership invalidates
all docking agreements in that sector. Existing save files need no migration.

Collection checks capacity for every personal account before clearing any of
them. A repeated collection returns zero. An unusual pre-existing balance on an
unowned port is retained when that port is acquired; the current generator and
unowned trading do not create such balances. This preservation rule is not a
claim about untested DOS orphan balances.

Go tests cover the nine DOS outcomes, preview purity, stale confirmation,
expiry, replay, Earth, insufficient cash, overflow, personal/team separation,
docking invalidation and simultaneous buyers/collectors. A real PTY/GoDoors
smoke additionally follows a buyout with a trading commission to the new owner,
remote collection, repeated collection and reconnect. The report and receipts
use actual current data; exact DOS screen-cell parity for these new prompts,
large-universe report pagination and live-BBS feature acceptance remain untested.
