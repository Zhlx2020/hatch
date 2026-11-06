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

let width = "dword";
let tab = "regs";
let memAddr = 0;
let disAddr = 0;
let timer = null;
let shown = false;

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
function renderRegs(data) {
  bodyEl.textContent = "";
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
  bodyEl.append(bar);

  for (const name of [...GPRS, "eip"]) {
    const value = regs[name] || 0;
    const row = document.createElement("div");
    row.className = "reg" + (hex(value, 8) === data.eip ? " here" : "");
    row.append(cell(name, "name"));

    if (width === "bits") {
      for (let bit = 31; bit >= 0; bit -= 1) {
        const on = (value >>> bit) & 1;
        const b = document.createElement("button");
        b.className = "bit" + (on ? " on" : "");
        b.textContent = String((value >>> bit) & 1);
        b.title = "第 " + bit + " 位";
        b.addEventListener("click", () => write(name, value ^ (1 << bit)));
        row.append(b);
        if (bit % 8 === 0 && bit) row.append(cell(" ", "gap"));
      }
    } else if (width === "word") {
      row.append(cell("0x" + hex(value & 0xFFFF, 4), "value"));
    } else if (width === "hi") {
      row.append(cell("0x" + hex((value >>> 8) & 0xFF, 2), "value"));
      row.append(cell("ah/ch/dh/bh", "dim"));
    } else if (width === "lo") {
      row.append(cell("0x" + hex(value & 0xFF, 2), "value"));
      row.append(cell("al/cl/dl/bl", "dim"));
    } else {
      row.append(cell("0x" + hex(value, 8), "value"));
      row.append(cell(signed(value) + "", "dim"));
    }
    row.addEventListener("dblclick", () => editInline(row, name, value));
    bodyEl.append(row);
  }

  const flags = document.createElement("div");
  flags.className = "reg flags";
  flags.append(cell("eflags", "name"));
  for (const [bit, name, meaning] of FLAGS) {
    const on = (regs.eflags >>> bit) & 1;
    const b = document.createElement("button");
    b.className = "flag" + (on ? " on" : "");
    b.textContent = name;
    b.title = name + " " + meaning + "（第 " + bit + " 位）";
    b.addEventListener("click", () => write("eflags", (regs.eflags || 0) ^ (1 << bit)));
    flags.append(b);
  }
  bodyEl.append(flags);

  const segs = document.createElement("div");
  segs.className = "reg";
  segs.append(cell("段", "name"));
  for (const name of SEGS) {
    segs.append(cell(name + ":" + hex(regs[name] || 0, 4), "value"));
  }
  bodyEl.append(segs);

  const note = document.createElement("p");
  note.className = "dim";
  note.textContent = "双击数值可写回；位与标志可点。";
  bodyEl.append(note);
}

function editInline(row, name, value) {
  row.textContent = "";
  row.append(cell(name, "name"));
  const input = document.createElement("input");
  input.value = hex(value, 8);
  row.append(input);
  input.focus();
  input.select();
  const done = () => {
    const next = parseInt(input.value.replace(/^0x/i, ""), 16);
    if (!Number.isNaN(next)) write(name, next);
    else reload();
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
  bodyEl.textContent = "";
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
  bodyEl.append(wrap);

  if (!memAddr) memAddr = num(regs.eip);
  const data = await api.mem(hex(memAddr, 8), 256);
  if (data.error) return note(data.error);
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
    bodyEl.append(line);
  }
  note("单击字节把地址挪到它；" + (snap.state === "running" ? "运行中数据可能变化。" : "已暂停。"));
}

// disassembly ---------------------------------------------------------
async function renderDisasm() {
  bodyEl.textContent = "";
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
  wrap.append(follow, prev, next);
  bodyEl.append(wrap);

  const data = await api.disasm(hex(disAddr || eip, 8), 48);
  if (data.error) return note(data.error);
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
    bodyEl.append(line);
  }
  note("点圆点断点；双击行把地址挪到该处。");
}

function note(text) {
  const p = document.createElement("p");
  p.className = "dim";
  p.textContent = text;
  bodyEl.append(p);
}

// shell ---------------------------------------------------------------
async function draw() {
  if (!shown) return;
  const buttons = tabsEl.querySelectorAll("button");
  for (const button of buttons) {
    button.classList.toggle("on", button.dataset.tab === tab);
  }
  if (tab === "regs") return renderRegs(await api.regs());
  if (tab === "mem") return renderMem();
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
  for (const button of tabsEl.querySelectorAll("button")) {
    button.dataset.tab = button.dataset.tab || button.textContent;
  }
  tabsEl.addEventListener("click", (ev) => {
    const target = ev.target.closest("button");
    if (!target) return;
    open(target.dataset.tab);
  });
  closeEl.addEventListener("click", close);
  box.addEventListener("click", (ev) => {
    if (ev.target === box) close();
  });
  document.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape" && shown) close();
  });
}
