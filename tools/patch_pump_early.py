import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab"

# 1. server: hand the loop to a startup hook so the frame pump can start early
p = root / "web/server.py"
s = p.read_text(encoding="utf-8")
s = s.replace(
    "def run(port, ready=None):",
    "def run(port, ready=None, on_ready=None):",
)
s = s.replace(
    "    loop.run_until_complete(site.start())\n    if ready:",
    "    loop.run_until_complete(site.start())\n"
    "    if on_ready:\n"
    "        on_ready(loop)\n"
    "    if ready:",
)
s = s.replace(
    "def start_thread(port, ready=None):\n"
    "    thread = threading.Thread(target=run, args=(port, ready), daemon=True)",
    "def start_thread(port, ready=None, on_ready=None):\n"
    "    thread = threading.Thread(target=run, args=(port, ready, on_ready), daemon=True)",
)
p.write_text(s, encoding="utf-8", newline="\n")

# 2. main: start the pump on the server loop
q = root / "__main__.py"
t = q.read_text(encoding="utf-8")
t = t.replace(
    "    server.start_thread(args.port, ready)",
    "    server.start_thread(args.port, ready, lambda loop: loop.create_task(session.source.start()))",
)
q.write_text(t, encoding="utf-8", newline="\n")

# 3. readiness no longer depends on the prompt being echoed
r = root / "services/session.py"
u = r.read_text(encoding="utf-8")
start = u.index("    def _await_ready")
end = u.index("    def stop(self):")
u = u[:start] + '''    def _await_ready(self, timeout=8.0):
        """Bochs enters the debugger at once; the prompt is not reliably echoed,
        so this is a short hold plus a liveness check."""
        time.sleep(1.5)
        return self.backend.alive

''' + u[end:]
r.write_text(u, encoding="utf-8", newline="\n")
print("ok")
