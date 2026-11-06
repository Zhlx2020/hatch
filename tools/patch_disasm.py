import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab"

# adapter: serve disassembly from the prebuilt map
p = root / "backend/qemu/adapter.py"
s = p.read_text(encoding="utf-8")
s = s.replace(
    "from ...core.errors import BackendError",
    "from ...core.errors import BackendError\nfrom ...services import disasm",
)
s = s.replace(
    "    def __init__(self, session_dir, image):\n        self._proc = QemuProcess(session_dir, image)\n        self._rsp = None",
    "    def __init__(self, session_dir, image):\n"
    "        self._proc = QemuProcess(session_dir, image)\n"
    "        self._image = image\n"
    "        self._rsp = None\n"
    "        self._lines = []",
)
s = s.replace(
    "        self._rsp = Rsp(config.HOST, config.GDB_PORT)\n        self._rsp.stop_reason()",
    "        self._rsp = Rsp(config.HOST, config.GDB_PORT)\n"
    "        self._lines = disasm.load(self._image)\n"
    "        self._rsp.stop_reason()",
)
s = s.replace(
    "    def hexdump(self, addr, count):",
    "    def disassemble(self, addr, count=8):\n"
    "        return disasm.around(self._lines, addr, count)\n"
    "\n"
    "    def hexdump(self, addr, count):",
)
p.write_text(s, encoding="utf-8", newline="\n")

# assembler: build the map right after a successful assemble
q = root / "services/assembler.py"
t = q.read_text(encoding="utf-8")
t = t.replace(
    "from ..core.errors import AssembleError",
    "from ..core.errors import AssembleError\nfrom . import disasm",
)
t = t.replace(
    "    with open(out_path, \"wb\") as fh:\n        fh.write(data)\n    return out_path",
    "    with open(out_path, \"wb\") as fh:\n        fh.write(data)\n"
    "    disasm.build(out_path)\n    return out_path",
)
q.write_text(t, encoding="utf-8", newline="\n")
print("ok")
