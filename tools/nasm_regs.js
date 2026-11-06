const NAMES = [];
for (const base of ["ax", "bx", "cx", "dx"]) {
  NAMES.push(base);
  NAMES.push("e" + base);
  NAMES.push(base[0] + "l", base[0] + "h");
}
for (const base of ["si", "di", "bp", "sp"]) {
  NAMES.push(base);
  NAMES.push("e" + base);
  NAMES.push("i" + base + "l");
}
NAMES.push(
  "eax", "ebx", "ecx", "edx", "esi", "edi", "ebp", "esp", "eip",
  "cs", "ds", "es", "fs", "gs", "ss",
  "cr0", "cr2", "cr3", "cr4", "dr0", "dr1", "dr2", "dr3", "dr6", "dr7",
  "st0", "st1", "st2", "st3", "st4", "st5", "st6", "st7",
  "eflags", "flags",
);

export default new Set(NAMES);
