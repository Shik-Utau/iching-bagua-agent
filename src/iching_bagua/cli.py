"""八卦映射与卦爻辞 CLI 入口。"""

import sys
from pathlib import Path

from iching_bagua.add_hexagram import add_hexagram
from iching_bagua.bagua_mappings import DEFAULT_MAPPINGS_PATH, load, validate
from iching_bagua.hexagrams import HEXAGRAMS_DIR, check_hexagram_literature, validate_hexagrams
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


def check_hexagram_literature_main() -> None:
    """检查卦爻辞 JSON 中缺失的彖传、大象传、小象传。"""
    results = check_hexagram_literature()
    for name, missing in results:
        if not missing:
            print(f"[{name}] ✓ 完整")
        else:
            print(f"[{name}] 缺失: {', '.join(missing)}")


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


def discover_associations_main() -> None:
    """运行关联发现（基于重卦结构），输出 Markdown 解释文档到 data/associations/。"""
    import argparse
    parser = argparse.ArgumentParser(description="卦爻辞与八卦映射的关联发现（输出 Markdown 解释）")
    parser.add_argument("--no-llm", action="store_true", help="不调用 LLM，仅输出结构框架（解释为空）")
    parser.add_argument("-d", "--hexagrams-dir", type=Path, help="卦爻辞目录（默认 data/hexagrams）")
    parser.add_argument("-o", "--output", type=Path, help="输出目录（默认 data/associations）")
    parser.add_argument("-H", "--hexagram", type=int, action="append", dest="hexagrams", metavar="N",
                        help="指定卦序，可多次使用（如 -H 1 -H 3）")
    args = parser.parse_args()
    try:
        from association.discovery import discover_associations
    except ImportError:
        print("错误: 未安装 association 模块，请运行 uv sync。", file=sys.stderr)
        sys.exit(1)
    try:
        saved = discover_associations(
            use_llm=not args.no_llm,
            hexagrams_dir=args.hexagrams_dir,
            output_path=args.output,
            hexagram_orders=args.hexagrams if args.hexagrams else None,
        )
        print(f"完成，共保存 {len(saved)} 个 Markdown 文件")
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
