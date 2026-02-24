#!/usr/bin/env python3
"""交互式录入六十四卦卦爻辞。可通过 uv run add-hexagram 或 python scripts/add_hexagram.py 调用。"""

from iching_bagua.add_hexagram import add_hexagram

if __name__ == "__main__":
    add_hexagram()
