import * as api from "./api.js";

const box = document.getElementById("detail");
const tabsEl = document.getElementById("detail-tabs");
const bodyEl = document.getElementById("detail-body");
const closeEl = document.getElementById("detail-close");

const GPRS = ["eax", "ecx", "edx", "ebx", "esp", "ebp", "esi", "edi"];
const SEGS = ["cs", "ss", "ds", "es", "fs", "gs"];
const FLAGS = [
  [0, "CF", "进位"],
  [2, "PF", "奇偶"],
  [4, "AF", "半进位"],
  [6, "ZF", "零"],
  [7, "SF", "符号"],
  [9, "IF", "中断"],
  [10, "DF", "方向"],
  [11, "OF", "溢出"],
];

// 每种宽度对应一套真实寄存器名：eax → ax → ah / al
const NAMES = {
  dword: [...GPRS, "eip"],
  word: ["ax", "cx", "dx", "bx", "sp", "bp", "si", "di", "ip"],
  hi: ["ah", "ch", "dh", "bh"],
  lo: ["al", "cl", "dl", "bl"],
  bits: [...GPRS, "eip"],
};
const SOURCE = { hi: GPRS, lo: GPRS, word: [...GPRS, "eip"] };
const DIGITS = { dword: 8, word: 4, hi: 2, lo: 2 };

let width = "dword";
let tab = "regs";
let memAddr = 0;
let syntax = "intel";
let disAddr = 0;
let timer = null;
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
  // 面板每 700 毫秒重绘一次，正在输入的框不能被换掉。
  const active = document.activeElement;
  const editing = active && bodyEl.contains(active) && active.tagName === "INPUT"
    ? active : null;
  const inputs = [...bodyEl.querySelectorAll("input")];
  const index = editing ? inputs.indexOf(editing) : -1;
  const value = editing ? editing.value : "";
  const start = editing ? editing.selectionStart : 0;
  const end = editing ? editing.selectionEnd : 0;
  bodyEl.replaceChildren(stage);
  stage = null;
  if (index < 0) return;
  const again = bodyEl.querySelectorAll("input")[index];
  if (!again) return;
  again.value = value;
  again.focus();
  try {
    again.setSelectionRange(start, end);
  } catch (_) {
    /* number 类型不支持选区 */
  }
}

const hex = (value, digits) => value.toString(16).padStart(digits, "0");
const num = (value) => (typeof value === "number"
  ? value
  : parseInt(String(value || "0").replace(/^0x/i, ""), 16) || 0);

function signed(value) {
  return value > 0x7FFFFFFF ? value - 0x100000000 : value;
}

function cell(text, cls) {
  const span = document.createElement("span");
  span.className = cls || "";
  span.textContent = text;
  return span;
}

function head(text, extra) {
  const bar = document.createElement("div");
  bar.className = "detail-bar";
  if (text) bar.append(cell(text, "dim"));
  if (extra) bar.append(extra);
  return bar;
}

function jumpBox(value, apply) {
  const wrap = document.createElement("div");
  wrap.className = "jump";
  const input = document.createElement("input");
  input.value = hex(value, 8);
  input.spellcheck = false;
  input.addEventListener("keydown", (ev) => {
    if (ev.key !== "Enter") return;
    const next = parseInt(input.value.replace(/^0x/i, ""), 16);
    if (!Number.isNaN(next)) apply(next);
  });
  const go = document.createElement("button");
  go.textContent = "跳转";
  go.addEventListener("click", () => {
    const next = parseInt(input.value.replace(/^0x/i, ""), 16);
    if (!Number.isNaN(next)) apply(next);
  });
  wrap.append(cell("地址", "dim"), input, go);
  return { wrap, input };
}

// registers -----------------------------------------------------------
function field(value, mode) {
  if (mode === "word") return { shown: value & 0xFFFF, mask: 0xFFFF, shift: 0 };
  if (mode === "hi") return { shown: (value >>> 8) & 0xFF, mask: 0xFF00, shift: 8 };
  return { shown: value & 0xFF, mask: 0xFF, shift: 0 };
}

function compose(full, part, mode) {
  const { mask, shift } = field(full, mode);
  return ((full & ~mask) | ((part << shift) & mask)) >>> 0;
}

function renderRegs(data) {
  begin();
  const regs = data.regs || {};

  const modes = [
    ["dword", "双字 32"], ["word", "字 16"], ["hi", "高字节"],
    ["lo", "低字节"], ["bits", "按位"],
  ];
  const bar = head("宽度");
  for (const [key, label] of modes) {
    const button = document.createElement("button");
    button.textContent = label;
    button.className = key === width ? "on" : "";
    button.addEventListener("click", () => {
      width = key;
      renderRegs(data);
    });
    bar.append(button);
  }
  add(bar);

  const names = NAMES[width];
  names.forEach((name, index) => {
    const full = SOURCE[width] ? SOURCE[width][index] : name;
    const value = regs[full] || 0;
    const row = document.createElement("div");
    row.className = "reg" + (name === "eip" || name === "ip" ? " here" : "");
    row.append(cell(name, "name"));

    if (width === "bits") {
      for (let bit = 31; bit >= 0; bit -= 1) {
        const b = document.createElement("button");
        b.className = "bit" + ((value >>> bit) & 1 ? " on" : "");
        b.textContent = String((value >>> bit) & 1);
        b.title = "第 " + bit + " 位";
        b.addEventListener("click", () => write(full, value ^ (1 << bit)));
        row.append(b);
        if (bit % 8 === 0 && bit) row.append(cell(" ", "gap"));
      }
    } else if (width === "dword") {
      row.append(cell("0x" + hex(value, 8), "value"));
      row.append(cell(signed(value) + "", "dim"));
    } else {
      const part = field(value, width);
      row.append(cell("0x" + hex(part.shown, DIGITS[width]), "value"));
    }
    if (width !== "bits") {
      row.addEventListener("dblclick", () => editInline(row, name, full, value, width));
    }
    add(row);
  });

  const flags = document.createElement("div");
  flags.className = "reg flags";
  flags.append(cell("eflags", "name"));
  for (const [bit, name, meaning] of FLAGS) {
    const b = document.createElement("button");
    b.className = "flag" + ((regs.eflags >>> bit) & 1 ? " on" : "");
    b.textContent = name;
    b.title = name + " " + meaning + "（第 " + bit + " 位）";
    b.addEventListener("click", () => write("eflags", (regs.eflags || 0) ^ (1 << bit)));
    flags.append(b);
  }
  add(flags);

  const segs = document.createElement("div");
  segs.className = "reg";
  segs.append(cell("段", "name"));
  for (const name of SEGS) {
    segs.append(cell(name + ":" + hex(regs[name] || 0, 4), "value"));
  }
  add(segs);

  note(width === "bits"
    ? "点方框翻转该位。"
    : "双击数值可写回；宽度只影响看到与写到的位置。");
  commit();
}

function editInline(row, name, full, value, mode) {
  const part = mode === "dword" ? value : field(value, mode).shown;
  row.textContent = "";
  row.append(cell(name, "name"));
  const input = document.createElement("input");
  input.value = hex(part, DIGITS[mode] || 8);
  input.spellcheck = false;
  row.append(input);
  input.focus();
  input.select();
  const done = () => {
    const typed = parseInt(input.value.replace(/^0x/i, ""), 16);
    if (Number.isNaN(typed)) return reload();
    const next = mode === "dword" ? typed : compose(value, typed, mode);
    write(full, next);
  };
  input.addEventListener("keydown", (ev) => {
    if (ev.key === "Enter") done();
    if (ev.key === "Escape") reload();
  });
  input.addEventListener("blur", done);
}

async function write(name, value) {
  const out = await api.setReg(name, "0x" + hex(value >>> 0, 8));
  if (out.error) note(out.error);
  reload();
}

// memory --------------------------------------------------------------
async function renderMem() {
  begin();
  const snap = await api.state();
  const regs = (await api.regs()).regs || {};
  const follow = (name) => () => {
    memAddr = num(regs[name]);
    renderMem();
  };
  const { wrap } = jumpBox(memAddr, (next) => {
    memAddr = next;
    renderMem();
  });
  for (const name of ["eip", "esp", "ebp"]) {
    const button = document.createElement("button");
    button.textContent = "跟随 " + name;
    button.addEventListener("click", follow(name));
    wrap.append(button);
  }
  const step = (delta) => {
    memAddr = (memAddr + delta) >>> 0;
    renderMem();
  };
  const prev = document.createElement("button");
  prev.textContent = "◀ 上页";
  prev.addEventListener("click", () => step(-256));
  const next = document.createElement("button");
  next.textContent = "下页 ▶";
  next.addEventListener("click", () => step(256));
  wrap.append(prev, next);
  add(wrap);

  if (!memAddr) memAddr = num(regs.eip);
  const data = await api.mem(hex(memAddr, 8), 256);
  if (data.error) {
    note(data.error);
    return commit();
  }
  memAddr = parseInt(data.addr, 16);

  for (const row of data.rows || []) {
    const line = document.createElement("div");
    line.className = "memrow";
    line.append(cell(row.addr, "addr"));
    for (let i = 0; i < 16; i += 1) {
      const byte = row.hex[i];
      const b = document.createElement("button");
      b.className = "byte" + (byte === "00" ? " zero" : "");
      b.textContent = byte === undefined ? "  " : byte;
      if (byte !== undefined) {
        b.addEventListener("click", () => {
          memAddr = parseInt(row.addr, 16) + i;
          renderMem();
        });
      }
      line.append(b);
    }
    line.append(cell(row.text, "text"));
    add(line);
  }
  note("单击字节把地址挪到它；" + (snap.state === "running" ? "运行中数据可能变化。" : "已暂停。"));
  commit();
}

// disassembly ---------------------------------------------------------
async function renderDisasm() {
  begin();
  const regs = (await api.regs()).regs || {};
  const eip = num(regs.eip);
  const { wrap } = jumpBox(disAddr || eip, (next) => {
    disAddr = next;
    renderDisasm();
  });
  const follow = document.createElement("button");
  follow.textContent = "跟随 eip";
  follow.addEventListener("click", () => {
    disAddr = eip;
    renderDisasm();
  });
  const step = (delta) => {
    disAddr = Math.max(0, (disAddr || eip) + delta);
    renderDisasm();
  };
  const prev = document.createElement("button");
  prev.textContent = "◀ 上";
  prev.addEventListener("click", () => step(-16 * 5));
  const next = document.createElement("button");
  next.textContent = "下 ▶";
  next.addEventListener("click", () => step(16 * 5));
  const modes = document.createElement("span");
  modes.className = "modes";
  for (const [key, label] of [["intel", "Intel"], ["att", "AT&T"]]) {
    const button = document.createElement("button");
    button.textContent = label;
    button.className = key === syntax ? "on" : "";
    button.addEventListener("click", () => {
      syntax = key;
      renderDisasm();
    });
    modes.append(button);
  }
  wrap.append(modes);

  const runTo = document.createElement("button");
  runTo.textContent = "运行到此处";
  runTo.className = "accent";
  runTo.addEventListener("click", async () => {
    const target = hex(disAddr || eip, 8);
    await api.addBreakpoint(target);
    await api.cont();
    close();
  });
  wrap.append(follow, prev, next, runTo);
  add(wrap);

  const data = await api.disasm(hex(disAddr || eip, 8), 48, syntax);
  if (data.error) {
    note(data.error);
    return commit();
  }
  disAddr = parseInt(data.addr, 16);

  const marks = await api.breakpoints();
  const active = new Set(Array.isArray(marks) ? marks : []);

  for (const row of data.rows || []) {
    const line = document.createElement("div");
    line.className = "disrow" + (row.addr === data.eip ? " here" : "");
    const dot = document.createElement("button");
    dot.className = "dot" + (active.has(row.addr) ? " on" : "");
    dot.title = "断点";
    dot.addEventListener("click", async () => {
      if (active.has(row.addr)) await api.dropBreakpoint(row.addr);
      else await api.addBreakpoint(row.addr);
      renderDisasm();
    });
    line.append(dot, cell(row.addr, "addr"), cell(row.bytes, "bytes"), cell(row.text, "op"));
    line.addEventListener("dblclick", () => {
      disAddr = parseInt(row.addr, 16);
      renderDisasm();
    });
    add(line);
  }
  note(syntax === "intel"
    ? "点圆点断点；双击行把地址挪到该处。"
    : "AT&T 顺序是源,目的，寄存器带 %、立即数带 $。");
  commit();
}

// disk: 镜像在磁盘上的样子 --------------------------------------------
const HUMAN = (bytes) => (bytes >= 1024 ? (bytes / 1024).toFixed(1) + " KB" : bytes + " B");

function bar(regions, total) {
  const row = document.createElement("div");
  row.className = "map";
  for (const region of regions) {
    const slice = document.createElement("span");
    slice.className = "slice " + (region.kind || "unknown");
    slice.style.width = Math.max(1, (region.size / total) * 100) + "%";
    slice.title = region.kind_name + " · " + region.offset + "（" + HUMAN(region.size) + "）";
    slice.addEventListener("click", () => {
      bodyEl.querySelector(`[data-offset="${region.offset}"]`)?.scrollIntoView({ block: "center" });
    });
    row.append(slice);
  }
  return row;
}

async function renderDisk() {
  begin();
  const data = await api.disk();
  if (data.error) {
    note(data.error);
    return commit();
  }
  const bar0 = head("镜像 " + data.size + " 字节 · " + data.sectors + " 扇区 · 有效 "
    + HUMAN(data.used) + " · 全零 " + HUMAN(data.zero));
  add(bar0, bar(data.regions || [], data.size || 1));
  const HEAD = 65536;
  const zoom = (data.regions || []).filter((one) => one.offset < HEAD)
    .map((one) => ({ ...one, size: Math.min(one.size, HEAD - one.offset) }));
  add(head("前 64 KB 放大（整盘里这一段只有几个像素）"), bar(zoom, HEAD));

  for (const text of data.warnings || []) {
    const line = document.createElement("p");
    line.className = "warn";
    line.textContent = "⚠ " + text;
    add(line);
  }

  const marks = new Map();
  for (const mark of data.marks || []) {
    if (!marks.has(mark.offset)) marks.set(mark.offset, []);
    marks.get(mark.offset).push(mark);
  }

  for (const region of data.regions || []) {
    const row = document.createElement("div");
    row.className = "region " + (region.kind || "unknown");
    row.dataset.offset = region.offset;
    row.append(cell("0x" + region.offset.toString(16).padStart(6, "0"), "addr"));
    row.append(cell(HUMAN(region.size), "size"));
    row.append(cell(region.kind_name, "tag"));
    row.append(cell(region.label, "label"));
    add(row);
    if (region.note) {
      const p = document.createElement("p");
      p.className = "dim small";
      p.textContent = region.note;
      add(p);
    }
    if (region.hex) {
      const p = document.createElement("p");
      p.className = "bytes";
      p.textContent = region.hex + " …";
      add(p);
    }
    for (const item of region.fields || []) {
      const line = document.createElement("div");
      line.className = "field-row";
      line.append(cell(item.k, "tag"), cell(item.v, "value"));
      add(line);
      const p = document.createElement("p");
      p.className = "dim small";
      p.textContent = item.note;
      add(p);
    }
    if (marks.has(region.offset)) {
      for (const mark of marks.get(region.offset)) {
        const p = document.createElement("div");
        p.className = "field-row";
        p.append(cell("行 " + mark.line, "tag"), cell(mark.addr, "value"));
        add(p);
      }
    }
  }
  note("大小按扇区算，灰色是补到软盘容量的部分。点色条跳到对应段。");
  commit();
}

// elf: 链接产物的结构 --------------------------------------------------
function elfBytes(text) {
  if (text >= 1024) return (text / 1024).toFixed(1) + " KB";
  return text + " B";
}

async function renderElf() {
  begin();
  const data = await api.elf();
  if (data.error) {
    note(data.error);
    return commit();
  }
  add(head(data.path + " · " + data.bits + " 位 " + data.endian + " · " + data.machine
    + " · " + data.type));
  add(head("入口 0x" + num(data.entry).toString(16).padStart(8, "0")
    + " · 文件 " + elfBytes(data.size) + " · 可装入段 " + elfBytes(data.allocated || 0)));

  for (const text of data.warnings || []) {
    const line = document.createElement("p");
    line.className = "warn";
    line.textContent = "⚠ " + text;
    add(line);
  }

  if ((data.segments || []).length) {
    add(head("程序头（装载器看这里）"));
    for (const seg of data.segments) {
      const line = document.createElement("div");
      line.className = "field-row segment";
      line.append(cell(String(seg.index), "tag"), cell(seg.flags, "flag"),
        cell("0x" + num(seg.vaddr).toString(16).padStart(8, "0"), "value"),
        cell(elfBytes(seg.filesz) + " / 内存 " + elfBytes(seg.memsz), "dim"),
        cell("对齐 " + seg.align, "dim"));
      add(line);
    }
  }

  add(head("节（" + (data.sections || []).length + " 节）"));
  for (const section of data.sections || []) {
    const line = document.createElement("div");
    line.className = "field-row section";
    line.append(cell("[" + section.index + "]", "tag"));
    line.append(cell(section.name || "（无名）", "value"));
    line.append(cell(section.flags, "flag"));
    line.append(cell("0x" + num(section.addr).toString(16).padStart(8, "0"), "addr"));
    line.append(cell(section.type, "dim"));
    line.append(cell(elfBytes(section.size), "size"));
    add(line);
  }

  if (data.symbol_total) {
    add(head("符号 " + data.symbol_total + " 个" + (data.symbol_total > 200 ? "，先显示 200" : "")));
    for (const symbol of data.symbols || []) {
      const line = document.createElement("div");
      line.className = "field-row symbol";
      line.append(cell(symbol.value, "addr"), cell(symbol.kind, "tag"),
        cell(symbol.section, "dim"), cell(symbol.name, "value"));
      add(line);
    }
  }
  note("节对齐、可写+可执行、入口落在哪里都会被标出来；这是 objcopy 转出来的调试件：地址与磁盘镜像一致，节比镜像里多。");
  commit();
}

function note(text) {
  const p = document.createElement("p");
  p.className = "dim";
  p.textContent = text;
  (stage || bodyEl).append(p);
}

// shell ---------------------------------------------------------------
async function draw() {
  if (!shown) return;
  for (const button of tabsEl.querySelectorAll("button[data-tab]")) {
    button.classList.toggle("on", button.dataset.tab === tab);
  }
  if (tab === "regs") return renderRegs(await api.regs());
  if (tab === "mem") return renderMem();
  if (tab === "disk") return renderDisk();
  if (tab === "elf") return renderElf();
  return renderDisasm();
}

async function reload() {
  try {
    await draw();
  } catch (err) {
    note(String(err));
  }
}

export function open(which) {
  if (which) tab = which;
  shown = true;
  box.classList.add("open");
  reload();
  clearInterval(timer);
  timer = setInterval(reload, 700);
}

export function close() {
  shown = false;
  box.classList.remove("open");
  clearInterval(timer);
}

export function install() {
  bodyEl.addEventListener("focusin", (ev) => {
    const input = ev.target.closest("input");
    if (input) input.dataset.editing = "1";
  });
  bodyEl.addEventListener("focusout", (ev) => {
    const input = ev.target.closest("input");
    if (input) delete input.dataset.editing;
  });
  tabsEl.addEventListener("click", (ev) => {
    const target = ev.target.closest("button[data-tab]");
    if (target) open(target.dataset.tab);
  });
  closeEl.addEventListener("click", (ev) => {
    ev.stopPropagation();
    close();
  });
  box.addEventListener("click", (ev) => {
    if (ev.target === box) close();
  });
  document.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape" && shown) close();
  });
}
