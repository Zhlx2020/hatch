import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui/js/detail.js"
s = p.read_text(encoding="utf-8")

s = s.replace('''  wrap.append(follow, prev, next);
  bodyEl.append(wrap);''',
'''  const runTo = document.createElement("button");
  runTo.textContent = "运行到此处";
  runTo.className = "accent";
  runTo.addEventListener("click", async () => {
    const target = hex(disAddr || eip, 8);
    await api.addBreakpoint(target);
    await api.cont();
    close();
  });
  wrap.append(follow, prev, next, runTo);
  bodyEl.append(wrap);''')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
