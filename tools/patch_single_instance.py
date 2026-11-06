import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab"

# --- single instance: free our ports, then guarantee the old backend is dead ---
p = root / "backend/qemu/process.py"
s = p.read_text(encoding="utf-8")
s = s.replace(
    "def _port_open(port):",
    '''def free_ports():
    """Kill whatever still owns our fixed ports (stale process from a crash)."""
    for port in (config.GDB_PORT, config.SERIAL_PORT, config.RFB_PORT):
        for pid in _owners(port):
            subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                           capture_output=True)


def _owners(port):
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "(Get-NetTCPConnection -LocalPort %d -ErrorAction SilentlyContinue)."
         "OwningProcess | Sort-Object -Unique" % port],
        capture_output=True, text=True,
    )
    return [int(x) for x in result.stdout.split() if x.strip().isdigit()]


def wait_free(ports=None, timeout=4.0):
    ports = ports or (config.GDB_PORT, config.SERIAL_PORT, config.RFB_PORT)
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not any(_port_open(p) for p in ports):
            return True
        time.sleep(0.1)
    return False


def _port_open(port):''',
)
s = s.replace(
    '''    def stop(self):
        if self.alive:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proc.kill()''',
    '''    def stop(self):
        if self.proc is None:
            return
        if self.alive:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=2)
        wait_free()''',
)
p.write_text(s, encoding="utf-8", newline="\n")

# --- teardown always frees the machine before a new one starts ---
q = root / "services/session.py"
t = q.read_text(encoding="utf-8")
t = t.replace(
    '''    def _teardown(self):
        if self.backend:
            try:
                self.backend.stop()
            except Exception:
                pass
            self.backend = None''',
    '''    def _teardown(self):
        if self.backend:
            try:
                self.backend.stop()
            except Exception:
                pass
            self.backend = None
        wait_free()''',
)
t = t.replace(
    "from ..backend.qemu.process import make_session_dir as make_qemu_dir",
    "from ..backend.qemu.process import make_session_dir as make_qemu_dir, wait_free",
)
# assemble first, then swap machines, so a syntax error leaves the old run intact
t = t.replace(
    '''                assembler.assemble(text, self.image)
                self._teardown()''',
    '''                assembler.assemble(text, self.image)
                self._teardown()''',
)
q.write_text(t, encoding="utf-8", newline="\n")

# --- clear leftovers at process start ---
r = root / "__main__.py"
u = r.read_text(encoding="utf-8")
u = u.replace(
    "    session.prepare()",
    "    free_ports()\n    session.prepare()",
)
u = u.replace(
    "from .services.session import Session",
    "from .backend.qemu.process import free_ports\nfrom .services.session import Session",
)
r.write_text(u, encoding="utf-8", newline="\n")
print("ok")
