import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/services/serial.py"
s = p.read_text(encoding="utf-8")

s = s.replace(
    '''                sock = socket.create_connection((config.HOST, config.SERIAL_PORT), 0.5)
                sock.settimeout(0.5)
                    self.connected = True''',
    '''                sock = socket.create_connection((config.HOST, config.SERIAL_PORT), 0.5)
                sock.settimeout(0.5)
                self.connected = True
                self._trace("connected")''',
)
s = s.replace(
    '''            text = chunk.decode("utf-8", "replace")''',
    '''            self._trace("read %d" % len(chunk))
            text = chunk.decode("utf-8", "replace")''',
)
s = s.replace(
    '''    def since(self, cursor=0):''',
    '''    def _trace(self, note):
        try:
            with open(config.RUN_DIR + "/serial.log", "a", encoding="utf-8") as fh:
                fh.write(note + "\\n")
        except OSError:
            pass

    def since(self, cursor=0):''',
)
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
