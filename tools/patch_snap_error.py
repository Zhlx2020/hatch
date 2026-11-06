import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/services/session.py"
s = p.read_text(encoding="utf-8")
s = s.replace('''        except Exception as exc:            # a timeout must not lose the view
            data["error"] = "读取超时：%s" % exc''',
'''        except Exception as exc:            # a timeout must not lose the view
            if not self.last_error:
                data["error"] = "读取超时：%s" % exc''')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
