#!/usr/bin/env python3
"""
融合卦爻关联：用 new 的说明替换卦 md 的说明，支持任意卦。
对 new 的说明进行适度 MD 加粗以提升可读性，不更改原文。

用法:
  uv run merge-association <卦md> <新说明> [-o 输出路径]
  例如: uv run merge-association data/associations/03_屯.md data/associations/new.md
        uv run merge-association data/associations/04_蒙.md data/associations/new_蒙.md -o data/associations/04_蒙.md
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from association.merge import merge


def main():
    parser = argparse.ArgumentParser(
        description="融合卦爻关联：保留原文与翻译，用 new 的说明替换原说明"
    )
    parser.add_argument("original", type=Path, help="原文件路径（如 03_屯.md）")
    parser.add_argument("new_explanations", type=Path, help="新说明文件（如 new.md）")
    parser.add_argument("-o", "--output", type=Path, help="输出路径，默认覆盖原文件")
    args = parser.parse_args()

    out = args.output or args.original
    merge(args.original, args.new_explanations, out)
    print(f"已写入: {out}")


if __name__ == "__main__":
    main()
