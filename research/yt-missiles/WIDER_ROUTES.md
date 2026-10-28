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

Represent a launch as traversal over connected sectors, not direct target lookup. Resolve each traversed sector's defenses and eligible targets in DOS order while decrementing one shared missile budget. Stop when the budget is exhausted or a target's handling consumes the volley. Keep outbound route discovery distinct from retaliation route discovery. Preserve the exact selected target and route context across asynchronous confirmation so a later state reload cannot redirect an attack.

Do not assume a fixed maximum hop count, shortest-path tie behavior, behavior for disconnected targets, black-hole redirection, or target ordering among multiple planets: these boundaries were not tested here. Native BBS acceptance is also separate from these DOS reference runs.
