# Superseded discovery trials — excluded from the accepted matrix

The retained pilot observer/launch/trace correspond to the two records in
`pilot-rea-bundle.json`. Their source and completion evidence were acquired via
REA. This pilot reported1,066 paired events, no errors/drops, natural DOSBox exit,
and exact six-file historical output equality. It is discovery provenance only;
the final verifier/model never reads its event stream as replay inputs.

The pilot used a fixed-argument declaration of variadic libc open on ARM64.
The host-created log/trace permissions were wrong; chmod600 repaired modes only,
without changing content. The final observer uses nonvariadic creat with an
explicit mode and Node supplies environment/stdio, so that defect is absent.

A later disposable Node trial at `/private/tmp/yt-neutral-observed-1` rejected its
trace flush because Frida serialized a native long as a string rather than a
number. Its DOSBox child had already exited naturally and output bytes were
exact, but the controller marked failure; it is not an accepted control. The
idle Node controller was then terminated explicitly after verifying no DOSBox
child remained. Final captures serialize the byte count as Number and verify
it against the exact retained JSON byte length. No accepted run was forced.

REA reported no authenticated artifact identity or target OS/architecture for
the pilot. The final matrix supplies independent disk hashes, loaded-module
UUID/prologue/architecture, guest code/frame evidence and strict lifecycle logs.
Do not treat this diagnostic bundle as establishing general observer neutrality.
