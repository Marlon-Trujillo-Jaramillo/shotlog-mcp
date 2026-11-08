"""Drives the real shotlog server over MCP, the way an AI client would. Used to record the README GIF."""
import asyncio, json, os, sys, time
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

C, D, R = "\033[36m", "\033[2m", "\033[0m"

def say(text):
    print(f"\n{C}> {text}{R}"); time.sleep(0.8)

def show(result, keys=None):
    data = json.loads(result.content[0].text)
    if keys:
        data = {k: data[k] for k in keys if k in data}
    print(D + json.dumps(data, ensure_ascii=False, indent=2) + R); time.sleep(1.6)

async def main():
    params = StdioServerParameters(command="uv", args=["run", "-q", "shotlog-mcp"],
                                   env={**os.environ}, cwd=sys.argv[1])
    async with stdio_client(params, errlog=open(os.devnull, "w")) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            say('save_screenshot(name="step1_ssh_version", app="Terminal", title_contains="shotlog-demo", ...)')
            show(await s.call_tool("save_screenshot", {
                "name": "step1_ssh_version", "app": "Terminal", "title_contains": "shotlog-demo",
                "activity": "Step 1 - Check the SSH client", "command": "ssh -V",
                "result": "OpenSSH client is installed"}), ["file", "source", "activity", "command", "result"])
            say("export_report(title=\"OS Lab - SSH\")")
            show(await s.call_tool("export_report", {"title": "OS Lab - SSH"}))

asyncio.run(main())
