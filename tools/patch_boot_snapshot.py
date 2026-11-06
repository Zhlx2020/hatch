import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/services/session.py"
s = p.read_text(encoding="utf-8")

old = """        if self.arbiter.state in (state.RUNNING, state.BOOTING):
            text, cursor = self.serial.since(self.cursor) if self.serial else ("", 0)
            self.cursor = cursor
            return dict(self.cache, state=self.arbiter.state, file=self.file,
                        serial=text, error=self.last_error)"""

new = """        if self.arbiter.state in (state.RUNNING, state.BOOTING):
            text, cursor = self.serial.since(self.cursor) if self.serial else ("", 0)
            self.cursor = cursor
            data = dict(self.cache, state=self.arbiter.state, file=self.file,
                        serial=text, error=self.last_error)
            if self.arbiter.state == state.BOOTING:
                # 启动过程里也要看得见机器：此时客户机停在复位点，读一下无害。
                data.update(self._snapshot())
            return data"""

if old not in s:
    raise SystemExit("snapshot block not found")
s = s.replace(old, new)
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
