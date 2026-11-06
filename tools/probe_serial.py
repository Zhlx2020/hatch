import sys

sys.path.insert(0, "src")
from oslab.web import state  # noqa: E402

sess = state.session()
snap = sess.snapshot()
print("state", snap.get("state"), "serial len", len(snap.get("serial") or ""))
print("cursor", sess.cursor, "buffer", len(sess.serial.tail()) if sess.serial else None)
print("since", sess.serial.since(sess.cursor)[0][:40] if sess.serial else None)
