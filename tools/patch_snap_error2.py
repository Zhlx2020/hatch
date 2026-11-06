import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/services/session.py"
s = p.read_text(encoding="utf-8")

s = s.replace('''        data = dict(self.cache)
        data.pop("state", None)''',
'''        data = dict(self.cache)
        for key in ("state", "error"):
            data.pop(key, None)''')

s = s.replace('''        except Exception as exc:            # a timeout must not lose the view
            if not self.last_error:
                data["error"] = "读取超时：%s" % exc''',
'''        except Exception as exc:            # a timeout must not lose the view
            data["error"] = "读取超时：%s" % exc''')

s = s.replace('''        if self.last_error and "error" not in data:
            data["error"] = self.last_error''',
'''        if self.last_error:                # 真正的失败原因优先于偶发读超时
            data["error"] = self.last_error''')

s = s.replace('''        self.cache = {k: v for k, v in data.items() if k not in ("serial", "state")}''',
'''        self.cache = {k: v for k, v in data.items()
                      if k not in ("serial", "state", "error")}''')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
