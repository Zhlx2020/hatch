import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui"

p = root / "index.html"
s = p.read_text(encoding="utf-8")

s = s.replace(
    '<section class="pane"><h2>寄存器 / 断点</h2><pre id="regs">—</pre><pre id="bps" class="sub">无</pre></section>',
    '<section class="pane"><h2>寄存器 / 断点 <button class="mini more" data-open="regs">展开</button></h2>'
    '<pre id="regs">—</pre><pre id="bps" class="sub">无</pre></section>',
)
s = s.replace(
    '<section class="pane"><h2>反汇编</h2><pre id="disasm">—</pre></section>',
    '<section class="pane"><h2>反汇编 <button class="mini more" data-open="dis">展开</button></h2>'
    '<pre id="disasm">—</pre></section>',
)
s = s.replace(
    '<section class="pane"><h2>内存 @eip</h2><pre id="mem">—</pre></section>',
    '<section class="pane"><h2>内存 <button class="mini more" data-open="mem">展开</button></h2>'
    '<pre id="mem">—</pre></section>',
)
s = s.replace(
    '<script type="module" src="/ui/js/boot.js"></script>',
    """<div id="detail">
  <div id="detail-tabs">
    <button data-tab="regs">寄存器</button>
    <button data-tab="mem">内存</button>
    <button data-tab="dis">反汇编</button>
    <span class="grow"></span>
    <button id="detail-close">关闭</button>
  </div>
  <div id="detail-body"></div>
</div>

<script type="module" src="/ui/js/boot.js"></script>""",
)
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
