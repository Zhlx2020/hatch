import pathlib

root = pathlib.Path(__file__).resolve().parents[1]

r = root / "src/oslab/backend/qemu/rsp.py"
s = r.read_text(encoding="utf-8")
s = s.replace('''    def _dispatch(self, body):
        if body[:1] in (STOP, b"W", b"X"):
            hook = self.on_stop
            if hook:
                hook(body)
            return
        with self.cond:
            self.mailbox.append(body)
            self.cond.notify_all()''',
'''    def _dispatch(self, body):
        with self.cond:
            self.mailbox.append(body)
            self.cond.notify_all()
        hook = self.on_stop
        if hook and body[:1] in (STOP, b"W", b"X"):
            hook(body)''')
s = s.replace('''            self.mailbox.clear()
            self._send(body)''', '''            self.mailbox.clear()
            self._send(body)''')
r.write_text(s, encoding="utf-8", newline="\n")

se = root / "src/oslab/services/session.py"
u = se.read_text(encoding="utf-8")

u = u.replace('''                self.backend = QemuBackend(self.dir, self.image, self.tune)
                self.backend.start()''',
'''                self.backend = QemuBackend(self.dir, self.image, self.tune)
                self.backend.start()
                self.backend.on_stop = self._on_stop''')

u = u.replace('''                if self.tune["run"]["pause_at_entry"]:
                    hit = self.backend.cont()
                else:
                    hit = "stopped"       # 停在入口等用户放行
                if hit == "stopped":
                    self.arbiter.to(state.STOPPED, "hit")
                else:
                    self.arbiter.to(state.RUNNING, "booted")''',
'''                self.arbiter.to(state.RUNNING, "booted")
                if self.tune["run"]["pause_at_entry"]:
                    self.backend.cont()
                    # 入口就有断点时会立刻停下来，等一小会儿再看
                    for _ in range(30):
                        if self.arbiter.state != state.RUNNING:
                            break
                        time.sleep(0.01)''')

u = u.replace('''    def cont(self):
        self.arbiter.guard(state.STOPPED, state.RUNNING)
        result = self._need_backend().cont()
        if result == "stopped":
            self.arbiter.to(state.STOPPED, "hit")
        else:
            self.arbiter.to(state.RUNNING, "cont")
        return result''',
'''    def cont(self):
        self.arbiter.guard(state.STOPPED, state.RUNNING)
        self.arbiter.to(state.RUNNING, "cont")     # 先立状态，回调才有处落脚
        self._need_backend().cont()
        return self.arbiter.state

    def _on_stop(self, packet):
        """gdbstub 推上来的停机（断点、暂停、结束）。跑在读线程里，只碰状态机。"""
        if self.arbiter.state not in (state.RUNNING, state.BOOTING):
            return
        try:
            self.arbiter.to(state.STOPPED, "hit" if packet[:1] == "T" else "exit")
        except BadTransition:
            pass''')

u = u.replace('''    def _resume(self):
        try:
            if self.backend.cont(wait=0.06) == "stopped":
                self.arbiter.to(state.STOPPED, "hit")
            else:
                self.arbiter.to(state.RUNNING, "resume")
        except (BackendError, BadTransition, OSError):
            pass''',
'''    def _resume(self):
        try:
            self.arbiter.to(state.RUNNING, "resume")
            self.backend.cont()
        except (BackendError, BadTransition, OSError):
            pass''')

u = u.replace('''        if self.arbiter.state in (state.RUNNING, state.BOOTING):
            text, cursor = self.serial.since(self.cursor) if self.serial else ("", 0)
            self.cursor = cursor
            data = dict(self.cache, state=self.arbiter.state, file=self.file,
                        serial=text, error=self.last_error)
            if self.arbiter.state == state.BOOTING:
                # 启动过程里也要看得见机器：此时客户机停在复位点，读一下无害。
                data.update(self._snapshot())
            elif time.monotonic() - self.stale > 1.5 and not self.filling:
                # 运行中低频补读一次，面板不至于一直是空的
                self.filling = True
                try:
                    data.update(self._snapshot())
                finally:
                    self.filling = False
            return data
        return self._snapshot()''',
'''        if self.arbiter.state in (state.RUNNING, state.BOOTING):
            text, cursor = self.serial.since(self.cursor) if self.serial else ("", 0)
            self.cursor = cursor
            # 运行中不碰 gdb：画面和串口照常，寄存器停在上一帧的值
            return dict(self.cache, state=self.arbiter.state, file=self.file,
                        serial=text, error=self.last_error)
        return self._snapshot()''')
se.write_text(u, encoding="utf-8", newline="\n")
print("ok")
