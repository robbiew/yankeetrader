# Spy trigger and target-notification research checklist

Target: archived DOS 3.6 YT.EXE, SHA-256
`c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`.
Only copied synthetic worlds are executed; no archive or Go gameplay mutations.

| Question | Required evidence | Disposition |
| --- | --- | --- |
| Which accepted, failed and read-only commands advance spies? | Complete DOS command/position witnesses; bounded native call-site search | Answered for selected gates/actions; indirect aliases remain unknown |
| Does visiting an empty sector reset report suppression? | Deterministic three-sector route; repeated and alternate positive findings | Answered by exact controls and retained boundaries |
| Does one spy suppress another's same-sector report? | Three spies hired normally, fixed routes, ordered reports | Answered: independent ordered reports/steps for all three |
| Does detection change caller sensor/attack eligibility? | Shared-cache byte reads, positive spy-to-sensor control | Answered for sensors/declined attack choices; no battle-outcome claim |
| Does detection drain the target's saved cloak? | Before/after target record plus exact target reload | Answered by exact controls and retained boundaries |
| Is a target notification persisted or shown at next login? | Exact parent world and auxiliary chain; target login/history; native writer boundary | Answered by exact controls and retained boundaries |

All 36 retained controls returned normally. Three target logins reopen exact
parent worlds and auxiliary files. Static observations, runtime observations and
remaining unknowns are separated in [RECOVERY.md](RECOVERY.md) and
[NATIVE.md](NATIVE.md). Pilot fixture/looting observations were used to refine the
controls; they are not substituted for the final independent verification.

No Go gameplay or save27 behavior changes with this research. Target notification
outside the tested path, indirect dispatch, simultaneous DOS processes and exact
random/tie semantics remain unresolved rather than silently enabled.
