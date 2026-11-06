import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab"

p = root / "services/serial.py"
s = p.read_text(encoding="utf-8")
s = s.replace(
    "    def since(self, cursor=0):",
    '''    def tail(self, limit=4000):
        with self._mutex:
            return ANSI.sub("", "".join(self._lines))[-limit:]

    def since(self, cursor=0):''',
)
p.write_text(s, encoding="utf-8", newline="\n")

q = root / "services/session.py"
t = q.read_text(encoding="utf-8")
t = t.replace(
    "    # observation ----------------------------------------------------",
    '''    def serial_tail(self):
        return self.serial.tail() if self.serial else ""

    # observation ----------------------------------------------------''',
)
q.write_text(t, encoding="utf-8", newline="\n")

r = root / "web/handlers.py"
u = r.read_text(encoding="utf-8")
u = u.replace(
    "async def pause(_request):",
    '''async def serial(_request):
    return json_response({"text": await asyncio.to_thread(session.serial_tail)})


async def pause(_request):''',
)
r.write_text(u, encoding="utf-8", newline="\n")

v = root / "web/routes.py"
w = v.read_text(encoding="utf-8")
w = w.replace(
    '    ("POST", "/api/pause", handlers.pause),',
    '    ("POST", "/api/pause", handlers.pause),\n    ("GET", "/api/serial", handlers.serial),',
)
v.write_text(w, encoding="utf-8", newline="\n")

x = root / "assets/ui/js/panels.js"
y = x.read_text(encoding="utf-8")
y = y.replace(
    "export function clearSerial() {",
    '''export async function loadSerial() {
  const res = await fetch("/api/serial");
  const data = await res.json();
  if (data.text) {
    serialEl.textContent = data.text;
    serialEl.scrollTop = serialEl.scrollHeight;
  }
}

export function clearSerial() {''',
)
x.write_text(y, encoding="utf-8", newline="\n")
print("ok")
