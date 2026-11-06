import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui/js/boot.js"
s = p.read_text(encoding="utf-8")

s = s.replace('''  if (!path || !path.endsWith(".asm")) {
    say("先选一个 .asm 再运行", true);
    return;
  }''',
'''  if (!path || !C_RUNNABLE.some((suffix) => path.endsWith(suffix))) {
    say("先选一个 .asm 或 .c 文件再运行", true);
    return;
  }''')

s = s.replace('''    const result = await api.run(path);
    if (result.error) say(result.error, true);
    else say("已启动 " + path);''',
'''    const result = await api.run(path);
    if (result.error) say(result.error, true);
    else {
      say("已启动 " + path);
      // 构建完成后红点才对应得上地址
      await editor.applyBreakpoints();
      await refresh();
    }''')

s = s.replace('const CONTROLS = [', 'const C_RUNNABLE = [".asm", ".c"];\nconst CONTROLS = [')
p.write_text(s, encoding="utf-8", newline="\n")
print("refresh" in s)
