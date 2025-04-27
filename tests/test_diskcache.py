import pytest, tempfile, shutil, time
from pathlib import Path
from fastcore.test import *

try:
    from cogitarelink.core.cache import DiskCache
except ImportError:
    pytest.skip("diskcache package not installed", allow_module_level=True)

def test_diskcache_basic():
    d = Path(tempfile.mkdtemp())
    c = DiskCache(directory=d, maxsize=2, ttl=0.2)
    c.set("a", 1); c.set("b", 2)
    assert c.get("a") == 1
    c.set("c", 3)                  # triggers eviction
    assert c.get("a") is None
    time.sleep(0.3)
    assert c.get("b") is None
    stats = c.info()
    assert stats["hits"] >= 1 and stats["misses"] >= 1
    c.clear(); shutil.rmtree(d)