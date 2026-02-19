#!/usr/bin/env bash
set -euo pipefail

CFG="config/run.yaml"

python3 - <<'PY'
import yaml, subprocess, shlex
from pathlib import Path

cfg = yaml.safe_load(Path("config/run.yaml").read_text())
ticker = str(cfg.get("ticker","")).upper().strip()
mode = cfg.get("mode","hybrid")
peers = cfg.get("peers", [])
thesis = cfg.get("thesis","")

cmd = ["./scripts/run_snap.sh"]
# run_snap.sh already reads env/args in your setup, so we pass via env vars:
env = dict(**__import__("os").environ)
env["MODE"] = mode
env["TICKER"] = ticker
env["PEERS"] = ",".join(peers) if isinstance(peers, list) else str(peers)
env["THESIS"] = thesis

print("RUN:", " ".join(shlex.quote(x) for x in cmd))
subprocess.check_call(cmd, env=env)
PY
