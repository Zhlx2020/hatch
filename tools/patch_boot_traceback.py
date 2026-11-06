import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/services/session.py"
s = p.read_text(encoding="utf-8")
s = s.replace("import threading", "import threading\nimport traceback")
s = s.replace("""            except Exception as exc:
                self.last_error = str(exc)""",
"""            except Exception as exc:
                traceback.print_exc()
                self.last_error = str(exc) or exc.__class__.__name__""")
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
