import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/services/session.py"
s = p.read_text(encoding="utf-8")

start = s.index("    def _snapshot(self):")
second = s.index("    def _snapshot(self):", start + 10)
s = s[:start] + s[second:]

s = s.replace(
    '            "bps": self.breakpoints(),\n            "error": self.last_error,\n        }\n        self.cache',
    '            "bps": self.breakpoints(),\n'
    '            "serial": (self.serial.since(self.cursor)[0] if self.serial else ""),\n'
    '            "error": self.last_error,\n        }\n        self.cache',
)
p.write_text(s, encoding="utf-8", newline="\n")
print(s.count("def _snapshot"))
