import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/services/session.py"
s = p.read_text(encoding="utf-8")

s = s.replace("import threading\nimport traceback", "import threading\nimport time\nimport traceback")

s = s.replace("""        self.cache = {}
""", """        self.cache = {}
        self.stale = 0.0
""", 1) if "self.cache = {}" in s else s

old = """            if self.arbiter.state == state.BOOTING:
                # 启动过程里也要看得见机器：此时客户机停在复位点，读一下无害。
                data.update(self._snapshot())"""
new = """            if self.arbiter.state == state.BOOTING:
                # 启动过程里也要看得见机器：此时客户机停在复位点，读一下无害。
                data.update(self._snapshot())
            elif time.monotonic() - self.stale > 1.5 and not self.filling:
                # 运行中低频补读一次，面板不至于一直是空的
                self.filling = True
                try:
                    data.update(self._snapshot())
                finally:
                    self.filling = False"""
if old not in s:
    raise SystemExit("fast path not found")
s = s.replace(old, new)

s = s.replace("""        data["bps"] = self.breakpoints()""",
              """        self.stale = time.monotonic()
        data["bps"] = self.breakpoints()""")
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
