import pathlib

root = pathlib.Path(__file__).resolve().parents[1]

# 1. assembler: regex has three groups, message index was off
p = root / "src/oslab/services/assembler.py"
s = p.read_text(encoding="utf-8")
s = s.replace(
    'lines.append("%s:%s %s" % (match.group(1), match.group(2), match.group(4))',
    'lines.append("%s:%s %s" % (match.group(1), match.group(2), match.group(3))',
)
p.write_text(s, encoding="utf-8", newline="\n")

# 2. every source must be able to fault
t = root / "tests/unit/test_arbiter.py"
u = t.read_text(encoding="utf-8")
u = u.replace(
    '''def test_booting_to_stopped_rejected():
    arb = Arbiter()
    arb.to(state.BOOTING, "run")
    with pytest.raises(BadTransition):
        arb.to(state.STOPPED, "pause")''',
    '''def test_booting_cannot_jump_to_running_twice():
    arb = Arbiter()
    arb.to(state.BOOTING, "run")
    arb.to(state.RUNNING, "booted")
    with pytest.raises(BadTransition):
        arb.to(state.BOOTING, "again")''',
)
t.write_text(u, encoding="utf-8", newline="\n")

# 3. really exceed a floppy
v = root / "tests/unit/test_assembler.py"
w = v.read_text(encoding="utf-8")
w = w.replace('"nop\\n" * 700000', '"nop\\n" * 2000000')
v.write_text(w, encoding="utf-8", newline="\n")
print("ok")
