import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/assets/ui/index.html"
s = p.read_text(encoding="utf-8")

s = s.replace('  <button id="reset">复位</button>\n  <span id="status">待机</span>',
              '  <button id="reset">复位</button>\n'
              '  <button id="gear" class="mini" title="设置">设置</button>\n'
              '  <span id="status">待机</span>')

s = s.replace('''<div id="detail">''',
'''<div id="settings">
  <div id="settings-tabs">
    <button data-tab="run">启动按钮</button>
    <button data-tab="qemu">QEMU</button>
    <span class="grow"></span>
    <button id="settings-close">关闭</button>
  </div>
  <div id="settings-body"></div>
  <div id="settings-foot">
    <span id="settings-note">改完重启会话后生效</span>
    <span class="grow"></span>
    <button id="settings-reset" class="extra">恢复默认</button>
    <button id="settings-save" class="primary">保存</button>
  </div>
</div>

<div id="detail">''')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
