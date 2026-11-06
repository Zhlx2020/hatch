import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui/js/detail.js"
s = p.read_text(encoding="utf-8")


def sub(old, new, count=1):
    global s
    if s.count(old) != count:
        raise SystemExit("%d hits: %r" % (s.count(old), old[:60]))
    s = s.replace(old, new)


# 1) 暂存容器：整块渲染完再一次性换上去，避免中途空白
sub("""let timer = null;
let shown = false;""",
"""let timer = null;
let shown = false;
let stage = null;

function begin() {
  stage = document.createElement("div");
}

function add(...nodes) {
  stage.append(...nodes);
}

function commit() {
  if (!stage) return;
  bodyEl.replaceChildren(stage);
  stage = null;
}""")

# 2) 三个渲染函数都改成先建后换
sub("""function renderRegs(data) {
  bodyEl.textContent = "";
  const regs = data.regs || {};""",
"""function renderRegs(data) {
  begin();
  const regs = data.regs || {};""")
sub("  bodyEl.append(bar);\n\n  const names = NAMES[width];",
    "  add(bar);\n\n  const names = NAMES[width];")
sub("    bodyEl.append(row);\n  });", "    add(row);\n  });")
sub("  bodyEl.append(flags);", "  add(flags);")
sub("  bodyEl.append(segs);", "  add(segs);")
sub("""  note(width === "bits"
    ? "点方框翻转该位。"
    : "双击数值可写回；宽度只影响看到与写到的位置。");
}""",
"""  note(width === "bits"
    ? "点方框翻转该位。"
    : "双击数值可写回；宽度只影响看到与写到的位置。");
  commit();
}""")

sub("""async function renderMem() {
  bodyEl.textContent = "";""",
"""async function renderMem() {
  begin();""")
sub("  bodyEl.append(wrap);\n\n  if (!memAddr) memAddr = num(regs.eip);",
    "  add(wrap);\n\n  if (!memAddr) memAddr = num(regs.eip);")
sub("""  const data = await api.mem(hex(memAddr, 8), 256);
  if (data.error) return note(data.error);""",
"""  const data = await api.mem(hex(memAddr, 8), 256);
  if (data.error) {
    note(data.error);
    return commit();
  }""")
sub("""    line.append(cell(row.text, "text"));
    bodyEl.append(line);
  }""",
"""    line.append(cell(row.text, "text"));
    add(line);
  }""")
sub("""  note("单击字节把地址挪到它；" + (snap.state === "running" ? "运行中数据可能变化。" : "已暂停。"));
}""",
"""  note("单击字节把地址挪到它；" + (snap.state === "running" ? "运行中数据可能变化。" : "已暂停。"));
  commit();
}""")

sub("""async function renderDisasm() {
  bodyEl.textContent = "";""",
"""async function renderDisasm() {
  begin();""")
sub("  bodyEl.append(wrap);\n\n  const data = await api.disasm",
    "  add(wrap);\n\n  const data = await api.disasm")
sub("""  const data = await api.disasm(hex(disAddr || eip, 8), 48, syntax);
  if (data.error) return note(data.error);""",
"""  const data = await api.disasm(hex(disAddr || eip, 8), 48, syntax);
  if (data.error) {
    note(data.error);
    return commit();
  }""")
sub("""    bodyEl.append(line);
  }
  note(syntax === "intel\"""",
"""    add(line);
  }
  note(syntax === "intel\"""")
sub("""    : "AT&T 顺序是源,目的，寄存器带 %、立即数带 $。");
}""",
"""    : "AT&T 顺序是源,目的，寄存器带 %、立即数带 $。");
  commit();
}""")

sub("""function note(text) {
  const p = document.createElement("p");
  p.className = "dim";
  p.textContent = text;
  bodyEl.append(p);
}""",
"""function note(text) {
  const p = document.createElement("p");
  p.className = "dim";
  p.textContent = text;
  (stage || bodyEl).append(p);
}""")

p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
