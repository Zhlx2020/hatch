import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/services/workspace.py"
s = p.read_text(encoding="utf-8")
s = s.replace('KINDS = {".asm", ".inc", ".c", ".h", ".txt", ".md"}',
              'KINDS = {".asm", ".inc", ".c", ".h", ".toml", ".txt", ".md"}')
s = s.replace('RUNNABLE = {".asm"}', 'RUNNABLE = {".asm", ".c"}')
s = s.replace('    ".h": "#pragma once\\n",', '    ".h": "#pragma once\\n",\n    ".toml": \'\',')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
