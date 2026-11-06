import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "src/oslab/services/cbuild.py"
s = p.read_text(encoding="utf-8")
s = s.replace("def _run(args):\n    result = subprocess.run(args, capture_output=True, text=True)",
              "def _run(args, env=None):\n"
              "    result = subprocess.run(args, capture_output=True, text=True, env=env)")
s = s.replace('''        _run([tool("gcc"), *CFLAGS, "-I", os.path.join(root, plan["dir"] or "."),
              "-c", src, "-o", target])''',
'''        _run([tool("gcc"), *CFLAGS, "-I", os.path.join(root, plan["dir"] or "."),
              "-c", src, "-o", target], env)''')
s = s.replace('''    _run([tool("ld"), "-m", "i386pe", "--disable-reloc-section", "-T",
          workspace.full(plan["link"], base), "-e", "_start", *objects, "-o", kernel])''',
'''    _run([tool("ld"), "-m", "i386pe", "--disable-reloc-section", "-T",
          workspace.full(plan["link"], base), "-e", "_start", *objects, "-o", kernel], env)''')
s = s.replace('''    _run([tool("objcopy"), "-O", "binary", "-j", ".text", "-j", ".rodata",
          "-j", ".data", kernel, flat])''',
'''    _run([tool("objcopy"), "-O", "binary", "-j", ".text", "-j", ".rodata",
          "-j", ".data", kernel, flat], env)''')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
