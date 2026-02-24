#!/usr/bin/env python3
"""校验六十四卦卦爻辞数据。可通过 uv run validate-hexagrams 或 python scripts/validate_hexagrams.py 调用。"""

import sys

from iching_bagua.hexagrams import HEXAGRAMS_DIR, validate_hexagrams


def main() -> None:
    errors = validate_hexagrams()
    if not errors:
        count = len(list(HEXAGRAMS_DIR.glob("*.json")))
        print(f"验证通过：共 {count} 卦。")
    else:
        print("验证失败：", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
