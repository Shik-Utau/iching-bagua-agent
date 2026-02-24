"""八卦映射与卦爻辞 CLI 入口。"""

import sys
from pathlib import Path

from iching_bagua.add_hexagram import add_hexagram
from iching_bagua.bagua_mappings import DEFAULT_MAPPINGS_PATH, load, validate
from iching_bagua.hexagrams import HEXAGRAMS_DIR, validate_hexagrams
from iching_bagua.ingest_hexagram import ingest_and_save, text_to_hexagram_json


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


def add_hexagram_main() -> None:
    """交互式录入一卦。"""
    add_hexagram()


def validate_hexagrams_main() -> None:
    """验证卦爻辞数据。"""
    errors = validate_hexagrams()
    if not errors:
        count = len(list(HEXAGRAMS_DIR.glob("*.json")))
        print(f"验证通过：共 {count} 卦。")
    else:
        print("验证失败：", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)


def ingest_hexagram_main() -> None:
    """从大段文本生成卦爻辞 JSON。支持 --file 或 stdin。"""
    import argparse

    parser = argparse.ArgumentParser(description="从文本生成卦爻辞 JSON（使用 DeepSeek API）")
    parser.add_argument(
        "-f", "--file",
        type=Path,
        help="输入文本文件路径",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="输出 JSON 文件路径（默认保存到 data/hexagrams/）",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="仅输出 JSON 到 stdout，不保存文件",
    )
    args = parser.parse_args()

    if args.file:
        text = args.file.read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()

    if not text.strip():
        print("错误：未读取到文本。请通过 -f 指定文件或从 stdin 输入。", file=sys.stderr)
        sys.exit(1)

    try:
        if args.stdout:
            data = text_to_hexagram_json(text)
            import json
            print(json.dumps(data, ensure_ascii=False, indent=2))
        elif args.output:
            data = text_to_hexagram_json(text)
            import json
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"已保存: {args.output}")
        else:
            out_path = ingest_and_save(text)
            print(f"已保存: {out_path}")
    except RuntimeError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
