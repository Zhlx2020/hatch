"""Build dispatch: file extension decides the toolchain.

Assembly is implemented; C is registered here so the rest of the system never
has to special-case a suffix.
"""
import os

from ..core.errors import OsLabError
from . import assembler, workspace

HANDLERS = {}


def register(*suffixes):
    def wrap(fn):
        for suffix in suffixes:
            HANDLERS[suffix] = fn
        return fn

    return wrap


@register(".asm")
def _asm(text, path, image, base=None):
    include_dir = os.path.dirname(workspace.full(path, base)) or workspace.root(base)
    return assembler.assemble(text, image, includes=(include_dir,))


def supported(path):
    return workspace.ext(path) in HANDLERS


def build(text, path, image, base=None):
    handler = HANDLERS.get(workspace.ext(path))
    if handler is None:
        raise OsLabError("这个类型还不能运行：%s" % path)
    return handler(text, path, image, base)
