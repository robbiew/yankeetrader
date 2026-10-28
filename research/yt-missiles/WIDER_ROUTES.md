# Wider missile routes and mixed encounters

## Result

Controlled runs of the original Yankee Trader 3.6 DOS executable show cruise missiles following connected warps beyond one hop. A target at sector 102 (two hops from sector 100) and a target at sector 103 (three hops) were both reached. These runs establish tested reach, not a universal maximum range.

Interception follows the route and is ordered before later targets:

1. Hostile sector fighters intercept missiles before mines, ships, or planets. In a two-hop route, 5,000 fighters in intermediate sector 101 were destroyed before the surviving missiles reached a ship in sector 102.
2. Mines also intercept in an intermediate sector. One mine consumed one missile; the remainder attacked the ship beyond it.
3. A hostile planet on the route can be attacked before a farther ship. With a planet in sector 101 and a ship in sector 102, the planet was attacked and the ship was untouched.
4. At a shared destination, ships are processed before a planet. When the first ship was destroyed, remaining missiles continued to another ship, or to the planet when that was the other target. When the first ship survived and consumed the volley, later targets were untouched.

The two-hop route with a reverse warp removed still carried missiles from sector 100 to sector 102. The target did not retaliate along that route. A separate ordinary bidirectional two-hop and three-hop route produced return fire at sector 100. This is evidence that outbound travel and return fire use directional connectivity; exact return-path selection and behavior when a target has multiple possible routes need more cases.

## Evidence

The preserved DOS transcripts, key feeds, emulator logs, compressed before/after YTDATA.DAT saves, and SHA-256 manifest are in [evidence](wider/evidence/manifest.json). All cases use copied fixtures in a disposable recovery workspace; the immutable distribution was not edited. The `GAME.LOG` files are the primary evidence for ordering and targeting; saves support state comparisons. Random damage amounts vary and are not asserted as fixed values.

| Case | Controlled setup | Observed result |
|---|---|---|
| `route-2` | Enemy two warps away | Reached sector 102; return fire reached sector 100 |
| `route-3` | Enemy three warps away | Reached sector 103; return fire reached sector 100 |
| `route-2-mines` | One mine in intermediate sector | Mine consumed one missile; surviving volley reached Enemy |
| `route-2-fighters` | 5,000 hostile fighters in intermediate sector | Fighters intercepted before Enemy |
| `route-2-multiple-ships` | Two ships share target sector; first survives | First ship consumed volley; second untouched |
| `route-2-multiple-with-kill` | Two ships share target sector; first has low defenses | First destroyed; remaining volley continued to second |
| `route-2-ship-planet` | Ship and hostile planet share target sector | Ship handled first; remaining volley attacked and destroyed planet |
| `route-2-intermediate-planet` | Hostile planet lies between launcher and ship | Planet intercepted attack; farther ship untouched |
| `route-2-oneway` | Remove reverse connection from target sector | Outbound attack succeeded; no target return fire observed |

## Implementation guidance

## Go implementation

The current Go door routes over directed warps using a shortest path. Equal-length
routes use the stored warp order as a deterministic modern policy; the DOS
tie-break rule is unknown. The command displays its chosen course before asking
for a separate confirmation. A disconnected destination is rejected before
charging stock or a turn.

Each routed sector resolves hostile fighters, then mines, visible hostile ships
in player-ID order, then a hostile planet. Teammates and cloaked ships are
skipped, friendly sector defenses are bypassed, and friendly planets are passed
over. A destroyed ship or planet permits the shared remaining volley to
continue. Ship/planet combinations and multiple visible ships are therefore
supported in the routed encounter. The player-ID ordering and treatment of
friendly transit planets are explicit modern policies; the historical evidence
does not settle every ordering edge case.

For each visible target, preparation captures a directed route back to the
launcher when one exists. A surviving ship may fire one response volley along
that course; an outbound one-way route without a return path does not retaliate.
Return-path sectors resolve defenses, mines, hostile planets, and the explicit
original attacker target. They do not reveal or hit unrelated hidden ships.
Both routes and their encounter snapshots are rebound at commit, before the
missile stock or turn is spent. No save-format change was required.

The Go implementation does not claim recovered behavior for equal-path ties,
black-hole redirection, or every target ordering edge case. Native BBS
acceptance remains separate from the captured DOS reference runs.
