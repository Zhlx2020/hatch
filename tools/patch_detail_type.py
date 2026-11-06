import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui/styles/detail.css"
s = p.read_text(encoding="utf-8")

pairs = [
    ("  padding: 6vh 6vw;", "  padding: 4vh 4vw;"),
    ("  padding: 6px;\n  background: var(--panel);", "  padding: 8px;\n  background: var(--panel);"),
    ("#detail-tabs button { padding: 4px 10px; }",
     "#detail-tabs button { padding: 6px 14px; font-size: 14px; }"),
    ("  padding: 10px;\n  background: #0b0d10;", "  padding: 14px 16px;\n  background: #0b0d10;"),
    ('  font: 12px/1.5 "Cascadia Mono", Consolas, "Microsoft YaHei", monospace;',
     '  font: 14px/1.75 "Cascadia Mono", Consolas, "Microsoft YaHei", monospace;'),
    ("  gap: 4px;\n  margin-bottom: 8px;", "  gap: 6px;\n  margin-bottom: 12px;"),
    ("#detail-body input {\n  width: 110px;\n  padding: 2px 5px;",
     "#detail-body input {\n  width: 132px;\n  padding: 4px 7px;\n  font-size: 14px;"),
    ("  gap: 6px;\n  padding: 1px 0;", "  gap: 8px;\n  padding: 2px 0;"),
    ("#detail-body .reg .name { width: 52px; color: var(--dim); }",
     "#detail-body .reg .name { width: 62px; color: var(--dim); }"),
    ("#detail-body .gap { width: 8px; }", "#detail-body .gap { width: 12px; }"),
    ("  padding: 0;\n  width: 15px;\n  color: var(--dim);",
     "  padding: 0;\n  width: 19px;\n  height: 20px;\n  color: var(--dim);"),
    ("#detail-body .flag {\n  padding: 0 5px;", "#detail-body .flag {\n  padding: 2px 8px;"),
    ("  gap: 3px;\n  white-space: pre;", "  gap: 4px;\n  white-space: pre;"),
    ("  padding: 0 1px;\n  width: 22px;", "  padding: 0 2px;\n  width: 26px;"),
    ("  width: 150px;\n  color: #55606c;", "  width: 186px;\n  color: #55606c;"),
    ("#detail-body .dot {\n  width: 9px;\n  height: 9px;", "#detail-body .dot {\n  width: 11px;\n  height: 11px;"),
    ("#detail-body .modes { display: flex; gap: 4px; margin-left: 4px; }",
     "#detail-body .modes { display: flex; gap: 6px; margin-left: 6px; }"),
]
for old, new in pairs:
    if old not in s:
        raise SystemExit("miss: " + old[:40])
    s = s.replace(old, new)

s += """
/* 大字号下仍要能读：面板内按钮统一加高 */
#detail-body button { font-size: 13px; padding: 3px 9px; }
#detail-body .reg, #detail-body .memrow, #detail-body .disrow { min-height: 22px; }
"""

p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
