"""八卦映射 CLI 入口。"""

import sys
from pathlib import Path

from iching_bagua.bagua_mappings import DEFAULT_MAPPINGS_PATH, load, validate


def load_main() -> None:
    """加载并打印八卦映射数据。"""
    try:
        data = load()
        print(f"已加载 {len(data)} 卦，来源: {DEFAULT_MAPPINGS_PATH}")
        for name, gua in data.items():
            desc = gua.get("描述", "(无描述)")
            print(f"  {name} {gua.get('卦象', '')}（{gua.get('象征', '')}）: {desc[:40]}...")
    except FileNotFoundError as e:
        print(f"错误: 文件不存在 - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


def validate_main() -> None:
    """验证八卦映射数据。"""
    errors = validate()
    if not errors:
        print("验证通过：八卦映射数据完整且一致。")
    else:
        print("验证失败：", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)
