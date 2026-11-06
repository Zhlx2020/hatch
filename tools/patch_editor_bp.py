import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui/js/editor.js"
s = p.read_text(encoding="utf-8")

s = s.replace('''let current = "";
let saveTimer = null;
let checkTimer = null;
let dead = false;''',
'''let current = "";
let saveTimer = null;
let checkTimer = null;
let dead = false;
// 行号 → 地址；重启后自动重新写入，源文件改了则重解析
let pending = new Map();''')

s = s.replace('''  onSave: (run) => {''',
'''  onToggleLine: (line) => {
    toggleLine(line);
  },
  onSave: (run) => {''')

s = s.replace('''export function show(path, text) {
  current = path;''',
'''export function show(path, text) {
  if (path !== current) pending = new Map();
  current = path;''')

s = s.replace('''export function file() {''',
'''async function toggleLine(line) {
  if (!current || dead) return;
  const mapped = pending.get(line);
  if (mapped) {
    pending.delete(line);
    view.setBreakpoints([...pending.keys()]);
    if (mapped.addr) await api.dropBreakpoint(mapped.addr);
    return;
  }
  const out = await api.line(current, line);
  if (!out || !out.addr) {
    pending.set(line, { addr: "" });
    view.setBreakpoints([...pending.keys()]);
    if (out && out.reason) titleEl.textContent = out.reason;
    return;
  }
  pending.set(line, { addr: out.addr });
  view.setBreakpoints([...pending.keys()]);
  await api.addBreakpoint(out.addr);
}

/** 构建成功后把红点重新解析成地址，再写入调试器。 */
export async function applyBreakpoints() {
  const lines = [...pending.keys()];
  if (!lines.length || dead) return;
  for (const line of lines) {
    const out = await api.line(current, line);
    const old = pending.get(line);
    if (old && old.addr && old.addr !== (out && out.addr)) {
      await api.dropBreakpoint(old.addr);
    }
    pending.set(line, { addr: (out && out.addr) || "" });
    if (out && out.addr) await api.addBreakpoint(out.addr);
  }
  view.setBreakpoints([...pending.keys()]);
}

export function breakpoints() {
  return [...pending.keys()];
}

export function file() {''')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
