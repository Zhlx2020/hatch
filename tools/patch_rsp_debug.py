import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/backend/qemu/rsp.py"
s = p.read_text(encoding="utf-8")
s = s.replace('''    def _send(self, body):
        self.sock.sendall(b"$" + body + b"#%02x" % (sum(body) & 0xFF))''',
'''    def _send(self, body):
        _dbg(">> " + body.decode("ascii", "replace")[:40])
        self.sock.sendall(b"$" + body + b"#%02x" % (sum(body) & 0xFF))''')
s = s.replace('''            if char == b"#":
                self.sock.recv(2)
                return body''',
'''            if char == b"#":
                self.sock.recv(2)
                _dbg("<< " + body.decode("ascii", "replace")[:40])
                return body''')
s = s.replace('''class Rsp:''', '''def _dbg(text):
    import os
    import time

    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))), ".run", "rsp.log")
    try:
        with open(path, "a") as fh:
            fh.write("%.3f %s\\n" % (time.time(), text))
    except OSError:
        pass


class Rsp:''')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
