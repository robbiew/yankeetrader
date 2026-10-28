"""Replay the saved DOS missile and retaliation verifiers in a disposable legacy layout.

The historical verifiers write their summaries beside the inputs, so never run it
against the authoritative archive. This checks saved evidence, not new DOS runs.
"""
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='yt-missile-evidence-') as parent:
    recovery = Path(parent)/'recovery'
    subprocess.run([sys.executable,str(ROOT/'scripts/prepare_recovery_workspace.py'),str(recovery)],
                   check=True,capture_output=True)
    for report in ('yt-missiles','yt-ships'):
        subprocess.run([sys.executable,str(recovery/'analysis'/report/'verify_evidence.py')],check=True)
