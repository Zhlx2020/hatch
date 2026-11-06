import pathlib
import shutil
import uuid

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]


@pytest.fixture()
def workdir():
    """nasm 3.02 在 %TEMP% 下写产物会 Permission denied，测试也落在项目里。"""
    path = ROOT / ".run" / "tests" / uuid.uuid4().hex[:8]
    path.mkdir(parents=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


@pytest.fixture()
def src():
    return str(ROOT / "src")
