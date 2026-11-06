import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab"

prep = '''    def prepare(self):
        """Boot a placeholder so the screen has a live source before 运行."""
        from . import chapters

        start = next((c.start for c in chapters.load_all() if c.start), "")
        try:
            self.boot(start)
        except Exception:
            pass

    def _await_ready(self):'''

p = root / "services/session.py"
s = p.read_text(encoding="utf-8")
s = s.replace("    def _await_ready(self):", prep, 1)
p.write_text(s, encoding="utf-8", newline="\n")

q = root / "__main__.py"
t = q.read_text(encoding="utf-8")
t = t.replace("    state.install(session)\n", "    state.install(session)\n    session.prepare()\n", 1)
q.write_text(t, encoding="utf-8", newline="\n")
print("ok")
