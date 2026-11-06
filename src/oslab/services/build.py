"""Build dispatch: a project manifest decides, the suffix is the fallback."""
import os

from ..core.errors import OsLabError
from . import assembler, cbuild, project, workspace

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
    result = assembler.assemble(text, image, includes=(include_dir,))
    return result, None


@register(".c")
def _c(text, path, image, base=None):
    directory = project.find(path, base)
    if not directory:
        raise OsLabError("C 文件要靠同目录的 %s 说明怎么链接" % project.MANIFEST)
    plan = project.load(directory, base)
    return cbuild.compile_project(plan, image, base, text=text)


def supported(path):
    return workspace.ext(path) in HANDLERS


def build(text, path, image, base=None):
    """Returns (image, line_map).

    A manifest in the file's project wins: it can pin the entry, the sources and
    the link script, so `path` may be a non-entry source of a C project.
    """
    directory = project.find(path, base)
    if directory:
        plan = project.load(directory, base)
        text_for_entry = text if plan["entry"] == workspace.safe(path) else None
        if plan["kind"] == "c":
            return cbuild.compile_project(plan, image, base, text=text_for_entry)
        handler = HANDLERS.get(".asm")
        source = text_for_entry
        if source is None:
            source = workspace.read(plan["entry"], base)
        result = handler(source, plan["entry"], image, base)
        return result, None

    handler = HANDLERS.get(workspace.ext(path))
    if handler is None:
        raise OsLabError("这个类型还不能运行：%s" % path)
    return handler(text, path, image, base)
