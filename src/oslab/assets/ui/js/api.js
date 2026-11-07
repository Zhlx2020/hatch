async function json(path, options) {
  const res = await fetch(path, options);
  return res.json().catch(() => ({}));
}

const post = (path, body) =>
  json(path, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body || {}),
  });

export const state = () => json("/api/state");

const enc = (path) => path.split("/").map(encodeURIComponent).join("/");

export const tree = () => json("/api/tree");
export const readFile = (path) => json("/api/file/" + enc(path));
export const writeFile = (path, text) =>
  json("/api/file/" + enc(path), {
    method: "PUT",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ text }),
  });

export const createNode = (path, kind) => post("/api/node", { path, kind });
export const renameNode = (path, name) => post("/api/node/rename", { path, name });
export const moveNode = (path, dir) => post("/api/node/move", { path, dir });
export const deleteNode = (path) =>
  json("/api/node?path=" + encodeURIComponent(path), { method: "DELETE" });

export const run = (name, lines, buildOnly) => post("/api/run", { name, lines: lines || [], build: !!buildOnly });
export const step = () => post("/api/step");
export const stepOver = () => post("/api/step-over");
export const cont = () => post("/api/cont");
export const pause = () => post("/api/pause");
export const reset = () => post("/api/reset");

export const breakpoints = () => json("/api/bps");
export const addBreakpoint = (addr) => post("/api/bp", { addr });
export const dropBreakpoint = (addr) =>
  json("/api/bp/" + addr, { method: "DELETE" });
export const memory = (addr, count) => post("/api/mem", { addr, count });
export const tables = () => post("/api/tables");

export const regs = () => json("/api/regs");
export const setReg = (name, value) => post("/api/reg", { name, value });
export const mem = (addr, count) => post("/api/mem", { addr, count });
export const disasm = (addr, count, syntax) =>
  post("/api/disasm", { addr, count, syntax });

export const check = (path, text) => post("/api/check", { path, text });

export const line = (path, row) =>
  json("/api/line?path=" + encodeURIComponent(path) + "&line=" + row);

export const serial = () => json("/api/serial");
export const settings = () => json("/api/settings");
export const disk = () => json("/api/disk");
export const elf = () => json("/api/elf");
export const saveSettings = (data) =>
  json("/api/settings", {
    method: "PUT",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(data || {}),
  });

export const templates = () => json("/api/templates");
export const applyTemplate = (name, dir) => post("/api/template", { name, dir });
