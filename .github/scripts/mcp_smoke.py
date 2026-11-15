"""MCP smoke test over stdio: handshake + tools/list, like a real client.

Usage: python3 mcp_smoke.py <expected tool count> <command> [args...]
Keeps stdin open until the tools/list answer arrives (closing it early lets the
server exit before replying, which made a naive `printf | docker run` flaky).
"""
import json
import subprocess
import sys
import threading

expected = int(sys.argv[1])
proc = subprocess.Popen(sys.argv[2:], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
timer = threading.Timer(60, proc.kill)
timer.start()


def send(msg: dict) -> None:
    proc.stdin.write(json.dumps(msg) + "\n")
    proc.stdin.flush()


def wait_for(msg_id: int) -> dict:
    for line in proc.stdout:
        if line.strip():
            msg = json.loads(line)
            if msg.get("id") == msg_id:
                return msg
    sys.exit(f"server exited before answering request {msg_id}")


try:
    send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-06-18", "capabilities": {},
        "clientInfo": {"name": "ci-smoke", "version": "1"}}})
    wait_for(1)
    send({"jsonrpc": "2.0", "method": "notifications/initialized"})
    send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    names = sorted(t["name"] for t in wait_for(2)["result"]["tools"])
finally:
    timer.cancel()
    proc.stdin.close()
    proc.wait(timeout=30)

print("tools:", names)
if len(names) != expected:
    sys.exit(f"expected {expected} tools, got {len(names)}")
