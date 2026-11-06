import pathlib

root = pathlib.Path(__file__).resolve().parents[1]

rsp = root / "src/oslab/backend/qemu/rsp.py"
s = rsp.read_text(encoding="utf-8")
s = s.replace('''    def cont(self, wait=0.4):''', '''    def cont(self, wait=0.4):''')
rsp.write_text(s, encoding="utf-8", newline="\n")

ad = root / "src/oslab/backend/qemu/adapter.py"
t = ad.read_text(encoding="utf-8")
t = t.replace('''    def cont(self):
        stop = self._need().cont()''', '''    def cont(self, wait=0.4):
        stop = self._need().cont(wait)''')
ad.write_text(t, encoding="utf-8", newline="\n")

se = root / "src/oslab/services/session.py"
u = se.read_text(encoding="utf-8")

u = u.replace("import threading\n", "import threading\nfrom contextlib import contextmanager\n", 1)

u = u.replace('''    # observation ----------------------------------------------------''',
'''    # observation ----------------------------------------------------
    @contextmanager
    def _keep_running(self):
        """读寄存器或内存会让 QEMU 停下，本来在跑就得放它回去。

        不然每次面板补读都会把客户机按在原地：画面不刷新，键盘也读不到。
        """
        resume = self.arbiter.state == state.RUNNING and self.backend is not None \\
            and self.backend.alive
        try:
            yield
        finally:
            if resume:
                self._resume()

    def _resume(self):
        try:
            if self.backend.cont(wait=0.06) == "stopped":
                self.arbiter.to(state.STOPPED, "hit")
            else:
                self.arbiter.to(state.RUNNING, "resume")
        except (BackendError, BadTransition, OSError):
            pass
''')

u = u.replace('''    def reg_detail(self):
        backend = self._need_backend()
        return {"regs": backend.reg_map(), "eip": "%08x" % backend.eip(),
                "state": self.arbiter.state}''',
'''    def reg_detail(self):
        backend = self._need_backend()
        with self._keep_running():
            return {"regs": backend.reg_map(), "eip": "%08x" % backend.eip(),
                    "state": self.arbiter.state}''')

u = u.replace('''    def set_reg(self, name, value):
        backend = self._need_backend()
        backend.set_reg(name, value)
        return "%08x" % backend._reg_value(name)''',
'''    def set_reg(self, name, value):
        backend = self._need_backend()
        with self._keep_running():
            backend.set_reg(name, value)
            return "%08x" % backend._reg_value(name)''')

u = u.replace('''    def mem_rows(self, addr, count=256):
        rows = self._need_backend().mem_rows(addr & 0xFFFFFFF0, min(int(count), 1024))
        return {"addr": "%08x" % addr, "rows": rows}''',
'''    def mem_rows(self, addr, count=256):
        with self._keep_running():
            rows = self._need_backend().mem_rows(addr & 0xFFFFFFF0, min(int(count), 1024))
        return {"addr": "%08x" % addr, "rows": rows}''')

u = u.replace('''    def disasm_rows(self, addr, count=32, syntax="intel"):
        rows = self._need_backend().disasm_rows(addr, min(int(count), 256), syntax)
        return {"addr": "%08x" % addr, "rows": rows, "eip": "%08x" % self.eip()}''',
'''    def disasm_rows(self, addr, count=32, syntax="intel"):
        with self._keep_running():
            rows = self._need_backend().disasm_rows(addr, min(int(count), 256), syntax)
            return {"addr": "%08x" % addr, "rows": rows, "eip": "%08x" % self.eip()}''')

u = u.replace('''        try:
            eip = self.eip()
            data["eip"] = "%08x" % eip
            data["regs"] = self.backend.registers()
            data["disasm"] = self.backend.disassemble(eip, 8)
            data["mem"] = self.backend.hexdump(eip, 128)
            data["stack"] = self.backend.dump_stack(self._reg("esp"))
            data["line"] = sourcemap.line_at(self.source_map, eip)''',
'''        try:
            with self._keep_running():
                eip = self.eip()
                data["eip"] = "%08x" % eip
                data["regs"] = self.backend.registers()
                data["disasm"] = self.backend.disassemble(eip, 8)
                data["mem"] = self.backend.hexdump(eip, 128)
                data["stack"] = self.backend.dump_stack(self._reg("esp"))
                data["line"] = sourcemap.line_at(self.source_map, eip)''')

u = u.replace('''    def dump_memory(self, addr, count):
        return self._need_backend().hexdump(addr, count)''',
'''    def dump_memory(self, addr, count):
        with self._keep_running():
            return self._need_backend().hexdump(addr, count)''')

u = u.replace('''    def tables(self):
        return {"gdt": self._need_backend().gdt(), "idt": self._need_backend().idt()}''',
'''    def tables(self):
        with self._keep_running():
            return {"gdt": self._need_backend().gdt(), "idt": self._need_backend().idt()}''')
se.write_text(u, encoding="utf-8", newline="\n")
print("ok")
