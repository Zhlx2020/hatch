import pathlib

root = pathlib.Path(__file__).resolve().parents[1] / "src/oslab"

p = root / "backend/qemu/rsp.py"
s = p.read_text(encoding="utf-8")
s = s.replace('''    def interrupt(self, timeout=3.0):
        with self.lock:
            self.sock.sendall(b"\\x03")
            return self._recv_packet(timeout)''',
'''    def interrupt(self, timeout=3.0):
        """Break into the guest. A silent stub is not fatal: return b""."""
        with self.lock:
            self.sock.sendall(b"\\x03")
            try:
                return self._recv_packet(timeout)
            except socket.timeout:
                return b""''')
p.write_text(s, encoding="utf-8", newline="\n")

q = root / "services/session.py"
t = q.read_text(encoding="utf-8")
t = t.replace("                except (BackendError, BadTransition):\n                    pass",
              "                except (BackendError, BadTransition, OSError, TimeoutError):\n                    pass")
q.write_text(t, encoding="utf-8", newline="\n")

h = root / "web/handlers.py"
u = h.read_text(encoding="utf-8")
u = u.replace('''    try:
        result = await asyncio.to_thread(session().run_file, name)
        return web.json_response(result)
    except OsLabError as exc:
        return web.json_response({"error": str(exc)}, status=400)''',
'''    try:
        result = await asyncio.to_thread(session().run_file, name)
        return web.json_response(result)
    except OsLabError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    except (OSError, TimeoutError) as exc:
        return web.json_response({"error": "启动失败：%s" % exc}, status=500)''')
h.write_text(u, encoding="utf-8", newline="\n")
print("ok")
