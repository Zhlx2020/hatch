import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/services/cbuild.py"
s = p.read_text(encoding="utf-8")

s = s.replace('DIAG = re.compile(r"^(?:.*[\\\\/])?([^\\\\/:]+):(\\d+):\\s*(.*)$")',
              'DIAG = re.compile(r"^(?:.*[\\\\/])?([^\\\\/:]+):(\\d+)(?::(\\d+))?:\\s*"\n'
              '                   r"(?:fatal\\s+)?(error|warning|note):\\s*(.*)$")\n'
              'SOURCE_DUMP = re.compile(r"^\\s*(\\d+\\s*\\||\\|)")')

s = s.replace('''        if text is not None and source == plan["entry"]:
            staged = os.path.join(out_dir, "u%d.c" % index)
            with open(staged, "w", newline="\\n", encoding="utf-8") as fh:
                fh.write(text)
            src = staged''',
'''        if text is not None and source == plan["entry"]:
            stage_dir = os.path.join(out_dir, "u%d" % index)
            os.makedirs(stage_dir, exist_ok=True)
            staged = os.path.join(stage_dir, os.path.basename(source))
            with open(staged, "w", newline="\\n", encoding="utf-8") as fh:
                fh.write(text)
            src = staged''')

s = s.replace('''def _clean(output):
    lines = []
    for line in (output or "").strip().splitlines():
        match = DIAG.match(line.strip())
        lines.append("%s:%s %s" % (match.group(1), match.group(2), match.group(3))
                     if match else line.strip())
    return "\\n".join(line for line in lines if line)''',
'''def _clean(output):
    """Keep `file:line: kind: message`, drop paths and echoed source lines."""
    lines = []
    for raw in (output or "").strip().splitlines():
        line = raw.strip()
        match = DIAG.match(line)
        if match:
            lines.append("%s:%s: %s: %s" % (match.group(1), match.group(2),
                                            match.group(4), match.group(5)))
        elif SOURCE_DUMP.match(line) or line.startswith("In function"):
            continue
        elif line.startswith("^"):
            continue
        elif line:
            lines.append(line)
    return "\\n".join(lines)''')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
