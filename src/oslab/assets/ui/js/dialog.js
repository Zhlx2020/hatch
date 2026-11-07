// 文件树的输入框：一个能校验、能报错、能认出文件类型的对话框。
// 用法：
//   const out = await dialog.input({ title, sub, chip, label, value, select, check, validate });
//   返回提交时的字段值对象，取消返回 null。

const root = document.getElementById("modal");
let current = null;

// 点空白处关掉；root 是常驻节点，监听只挂一次
root.addEventListener("mousedown", (ev) => {
  if (ev.target === root) close(null);
});

const ILLEGAL = /[:*?"<>|\\]/;
const RESERVED = new Set(["con", "prn", "aux", "nul", "com1", "com2", "lpt1", "lpt2"]);

function label(text) {
  const dot = text.lastIndexOf(".");
  if (dot < 1) return "";
  const ext = text.slice(dot + 1).toLowerCase();
  if (ext === "asm" || ext === "s" || ext === "inc") return "汇编";
  if (ext === "c" || ext === "h") return "C";
  if (ext === "toml" || ext === "json") return "配置";
  if (ext === "md") return "文档";
  return ext.toUpperCase();
}

// 单个“名字”字段的通用规则：不能为空、不能带分隔符、不能是保留名
// taken 是同一层已有的名字；exists 能顺着子路径查树上是否真的存在
function checkName(value, { allowSlash = false, taken = null, keep = "", base = "", exists = null } = {}) {
  const name = value.trim();
  if (!name) return "名字不能为空";
  if (ILLEGAL.test(name)) return '不能含 : * ? " < > | \\';
  if (!allowSlash && name.includes("/")) return "这一栏只填名字，不要带 /";
  if (/[/ ]$/.test(name)) return "结尾不要留空格";
  if (/\.$/.test(name.split("/").pop())) return "文件名结尾不要留点";
  const last = name.split("/").pop();
  if (RESERVED.has(last.toLowerCase())) return "这是 Windows 保留名";
  if (last.length > 64) return "名字太长（最多 64 字）";
  if (last !== keep && taken && taken.has(last)) return "同级已经有重名了";
  if (exists) {
    const full = base && name !== base && !name.startsWith(base + "/")
      ? base + "/" + name.replace(/^\/+/, "")
      : name;
    if (full !== keep && exists(full.replace(/\/+$/, ""))) return "这一层已经有同名的了";
  }
  return "";
}

function build(spec) {
  root.innerHTML = "";
  const sheet = document.createElement("form");
  sheet.className = "sheet";
  sheet.innerHTML = `
    <header>
      <span class="glyph"></span>
      <div>
        <h3></h3>
        <p class="sub"></p>
      </div>
    </header>
    <div class="fields"></div>
    <p class="note"></p>
    <footer>
      <span class="err"></span>
      <span class="grow"></span>
      <button type="button" class="ghost cancel">取消</button>
      <button type="submit" class="primary go"></button>
    </footer>`;

  sheet.querySelector("h3").textContent = spec.title;
  const sub = sheet.querySelector(".sub");
  sub.textContent = spec.sub || "";
  if (!spec.sub) sub.remove();
  const glyph = sheet.querySelector(".glyph");
  glyph.className = "glyph " + (spec.tone || "file");
  glyph.textContent = spec.tone === "danger" ? "!" : spec.tone === "dir" ? "▸" : "▤";
  sheet.querySelector(".go").textContent = spec.confirm || "确定";
  if (spec.tone === "danger") sheet.querySelector(".go").classList.add("danger");

  const note = sheet.querySelector(".note");
  note.innerHTML = spec.note || "";
  if (!spec.note) note.remove();

  const fields = sheet.querySelector(".fields");
  const inputs = [];
  for (const field of spec.fields || []) {
    const row = document.createElement("label");
    row.className = field.kind === "check" ? "field check" : "field";
    row.innerHTML = `<span class="cap"></span><span class="wrap"></span><span class="tip"></span>`;
    row.querySelector(".cap").textContent = field.label;
    const input = document.createElement(field.kind === "select" ? "select" : "input");
    if (field.kind === "select") {
      for (const option of field.options || []) {
        const one = document.createElement("option");
        one.value = option.value;
        one.textContent = option.label;
        if (option.value === field.value) one.selected = true;
        input.append(one);
      }
    } else if (field.kind === "check") {
      input.type = "checkbox";
      input.checked = Boolean(field.value);
      input.classList.remove("mono");
    } else {
      input.type = "text";
      input.value = field.value || "";
      input.placeholder = field.placeholder || "";
      input.autocomplete = "off";
      input.spellcheck = false;
      if (field.mono !== false) input.classList.add("mono");
    }
    row.querySelector(".wrap").append(input);
    if (field.suffix) {
      const tail = document.createElement("span");
      tail.className = "suffix";
      tail.textContent = field.suffix;
      row.querySelector(".wrap").append(tail);
    }
    fields.append(row);
    inputs.push({ field, input, tip: row.querySelector(".tip") });
  }

  return { sheet, inputs };
}

function validateNow() {
  if (!current) return "";
  for (const { field, input, tip } of current.inputs) {
    const msg = field.check ? field.check(currentValue(input)) : "";
    tip.textContent = msg;
    input.classList.toggle("bad", Boolean(msg));
    if (msg) return msg;
  }
  const extra = current.spec.validate ? current.spec.validate(
    Object.fromEntries(current.inputs.map((f) => [f.field.name, f.input.value]))) : "";
  return extra || "";
}

function refreshGo() {
  const problem = validateNow();
  current.sheet.querySelector(".go").disabled = Boolean(problem);
  return problem;
}

function currentValue(input) {
  if (input.type === "checkbox") return input.checked;
  return input.value.trim();
}

function values() {
  return Object.fromEntries(current.inputs.map((f) => [f.field.name, currentValue(f.input)]));
}

function close(result) {
  if (!current) return;
  const { resolve, restore, onKey, spec } = current;
  current = null;
  root.classList.remove("open");
  root.hidden = true;
  root.innerHTML = "";
  document.removeEventListener("keydown", onKey, true);
  if (restore && restore.focus) restore.focus();
  resolve(result);
}

function onKeydown(ev) {
  if (!current) return;
  if (ev.key === "Escape") {
    ev.preventDefault();
    ev.stopPropagation();
    close(null);
    return;
  }
  if (ev.key === "Tab") {
    const focusable = [...current.sheet.querySelectorAll("input, select, button")].filter(
      (el) => !el.disabled);
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (ev.shiftKey && document.activeElement === first) {
      ev.preventDefault();
      last.focus();
    } else if (!ev.shiftKey && document.activeElement === last) {
      ev.preventDefault();
      first.focus();
    }
    return;
  }
  if (ev.key === "Enter" && document.activeElement?.tagName !== "BUTTON") {
    ev.preventDefault();
    submit();
  }
}

async function submit() {
  if (!current || current.busy) return;
  const problem = refreshGo();
  if (problem) {
    const err = current.sheet.querySelector(".err");
    err.textContent = problem;
    return;
  }
  const spec = current.spec;
  const data = values();
  if (!spec.onsubmit) return close(data);
  current.busy = true;
  const go = current.sheet.querySelector(".go");
  const err = current.sheet.querySelector(".err");
  err.textContent = "";
  go.classList.add("busy");
  go.disabled = true;
  let out;
  try {
    out = await spec.onsubmit(data);
  } catch (e) {
    out = { error: String(e?.message || e) };
  }
  if (!current) return;
  current.busy = false;
  go.classList.remove("busy");
  if (out && out.error) {
    err.textContent = out.error;
    go.disabled = false;
    return;
  }
  close(out || data);
}

export function fileIcon(path) {
  return label(path);
}

export function nameProblem(value, options) {
  return checkName(value, options);
}

export function open(spec) {
  if (current) close(null);
  const { sheet, inputs } = build(spec);
  const restore = document.activeElement;
  root.hidden = false;
  root.append(sheet);
  requestAnimationFrame(() => root.classList.add("open"));

  current = { spec, sheet, inputs, restore, resolve: null, busy: false };

  for (const entry of inputs) {
    entry.input.addEventListener(entry.input.tagName === "SELECT" ? "change" : "input", () => {
      sheet.querySelector(".err").textContent = "";
      if (spec.oninput) spec.oninput(currentValue(entry.input), sheet, entry.field.name);
      refreshGo();
    });
  }
  sheet.querySelector(".cancel").addEventListener("click", () => close(null));
  for (const extra of spec.extra || []) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "ghost";
    button.textContent = extra.text;
    button.addEventListener("click", () => spec.onExtra?.(extra.act));
    sheet.querySelector(".cancel").before(button);
  }
  sheet.addEventListener("submit", (ev) => {
    ev.preventDefault();
    submit();
  });

  const onKey = (ev) => onKeydown(ev);
  document.addEventListener("keydown", onKey, true);

  const first = inputs[0]?.input;
  first?.focus();
  const pick = spec.select || "stem";
  if (first && pick !== "none" && first.tagName !== "SELECT") {
    const dot = first.value.lastIndexOf(".");
    if (pick === "stem" && dot > 0 && !first.value.includes("/")) first.setSelectionRange(0, dot);
    else first.select();
  }
  // 只有一个字段时可以按“词”定位到扩展名前
  refreshGo();
  if (spec.oninput && outputsFirst(spec)) spec.oninput(first.value, sheet, inputs[0].field.name);

  return new Promise((resolve) => {
    if (current) current.resolve = resolve;
  });
}

function outputsFirst(spec) {
  return spec.fields?.some((f) => f.name === spec.watch);
}
