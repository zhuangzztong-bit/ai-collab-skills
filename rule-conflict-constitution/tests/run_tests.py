#!/usr/bin/env python3
"""一次跑完 tests/ 下的全部测试：python3 -I -B tests/run_tests.py（在仓库根目录或任何目录都行）。

全部通过退出 0，有失败或出错退出 1。不写 __pycache__。
"""

import sys

sys.dont_write_bytecode = True

from pathlib import Path  # noqa: E402
import unittest  # noqa: E402


def main():
    here = Path(__file__).resolve().parent
    suite = unittest.defaultTestLoader.discover(str(here), pattern="test_*.py", top_level_dir=str(here))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
