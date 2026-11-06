import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/services/session.py"
s = p.read_text(encoding="utf-8")

s = s.replace("from . import assembler, workspace", "from . import build, workspace")
s = s.replace("                assembler.assemble(text, self.image)",
              "                build.build(text, name, self.image)")
s = s.replace('''    def prepare(self):
        first = next((f["name"] for f in workspace.list_files()), "")''',
              '''    def prepare(self):
        first = workspace.entry_file()''')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
