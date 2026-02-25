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


def hexagram_relations_main() -> None:
    """查询卦象关系：错卦、综卦、同上下卦、卦序相邻。"""
    import argparse

    parser = argparse.ArgumentParser(description="卦象关系：错卦、综卦、同上下卦")
    parser.add_argument("hexagram", help="卦序(1-64) 或 卦名（如乾、坤、屯）")
    parser.add_argument("--same-top", action="store_true", help="仅筛选同上卦")
    parser.add_argument("--same-bottom", action="store_true", help="仅筛选同下卦")
    parser.add_argument("--no-keyword", action="store_true", help="不显示关键词相似")
    parser.add_argument("-k", "--keyword-top", type=int, default=10, help="关键词相似 top-k（默认 10）")
    args = parser.parse_args()

    try:
        from iching_bagua.hexagrams import list_hexagrams
        from comparison.relations import (
            get_same_trigram_hexagrams,
            order_to_symbol,
        )
        from comparison.similar import find_similar_hexagrams
    except ImportError as e:
        print(f"错误: 未安装 comparison 模块 - {e}", file=sys.stderr)
        sys.exit(1)

    # 解析输入：卦序或卦名
    卦序 = None
    try:
        n = int(args.hexagram)
        if 1 <= n <= 64:
            卦序 = n
    except ValueError:
        pass
    if 卦序 is None:
        for o, name, _ in list_hexagrams():
            if name == args.hexagram or args.hexagram in name:
                卦序 = o
                break
    if 卦序 is None:
        print(f"错误: 未找到卦「{args.hexagram}」", file=sys.stderr)
        sys.exit(1)

    # 获取卦名
    卦名 = ""
    for o, name, _ in list_hexagrams():
        if o == 卦序:
            卦名 = name
            break

    sim = find_similar_hexagrams(
        卦序,
        include_keyword=not args.no_keyword,
        keyword_top_k=args.keyword_top,
    )

    def _name(o: int) -> str:
        for ord_, n, _ in list_hexagrams():
            if ord_ == o:
                return n
        return str(o)

    print(f"卦序 {卦序}：{卦名} {order_to_symbol(卦序)}")
    print()
    print(f"错卦：{_name(sim['错卦']) if sim['错卦'] else '-'} {order_to_symbol(sim['错卦']) if sim['错卦'] else ''} (卦序 {sim['错卦']})")
    print(f"综卦：{_name(sim['综卦']) if sim['综卦'] else '-'} {order_to_symbol(sim['综卦']) if sim['综卦'] else ''} (卦序 {sim['综卦']})")
    adj = sim["卦序相邻"]
    prev_str = f"{_name(adj['前'])} ({adj['前']})" if adj["前"] else "无"
    next_str = f"{_name(adj['后'])} ({adj['后']})" if adj["后"] else "无"
    print(f"卦序相邻：前 {prev_str}，后 {next_str}")
    print()

    same_top = get_same_trigram_hexagrams(卦序, same_上卦=True, same_下卦=False)
    same_bottom = get_same_trigram_hexagrams(卦序, same_上卦=False, same_下卦=True)
    same_either = sim["同上下卦"]
    if args.same_top:
        print(f"同上卦（{len(same_top)} 卦）：{[_name(o) for o in same_top]}")
    elif args.same_bottom:
        print(f"同下卦（{len(same_bottom)} 卦）：{[_name(o) for o in same_bottom]}")
    else:
        print(f"同上卦或同下卦（{len(same_either)} 卦）：{[_name(o) for o in same_either]}")

    if not args.no_keyword and sim["关键词相似"]:
        print()
        print("关键词相似（Jaccard）：")
        for o, score in sim["关键词相似"]:
            print(f"  {_name(o)} ({o}) {order_to_symbol(o)} {score:.2f}")


def compare_hexagrams_main() -> None:
    """两卦对比：结构、卦辞、爻辞，输出 Markdown。"""
    import argparse

    parser = argparse.ArgumentParser(description="两卦对比：结构、卦辞、爻辞")
    parser.add_argument("hexagram_a", help="卦 A：卦序(1-64) 或 卦名")
    parser.add_argument("hexagram_b", help="卦 B：卦序(1-64) 或 卦名")
    parser.add_argument("-o", "--output", type=Path, help="输出 Markdown 文件路径")
    parser.add_argument("--no-llm", action="store_true", help="不调用 LLM 生成对比总结")
    parser.add_argument("--stdout", action="store_true", help="仅输出到 stdout，不保存文件")
    parser.add_argument("-d", "--hexagrams-dir", type=Path, help="卦爻辞目录")
    args = parser.parse_args()

    try:
        from comparison.compare import (
            _resolve_hexagram,
            build_comparison_md,
            compare_two_hexagrams,
            COMPARISONS_DIR,
        )
    except ImportError as e:
        print(f"错误: 未安装 comparison 模块 - {e}", file=sys.stderr)
        sys.exit(1)

    卦序A = _resolve_hexagram(args.hexagram_a, args.hexagrams_dir)
    卦序B = _resolve_hexagram(args.hexagram_b, args.hexagrams_dir)
    if 卦序A is None:
        print(f"错误: 未找到卦「{args.hexagram_a}」", file=sys.stderr)
        sys.exit(1)
    if 卦序B is None:
        print(f"错误: 未找到卦「{args.hexagram_b}」", file=sys.stderr)
        sys.exit(1)

    data = compare_two_hexagrams(卦序A, 卦序B, hexagrams_dir=args.hexagrams_dir)
    if not data:
        print("错误: 对比数据加载失败", file=sys.stderr)
        sys.exit(1)

    md = build_comparison_md(
        卦序A, 卦序B, data=data,
        hexagrams_dir=args.hexagrams_dir,
        use_llm_summary=not args.no_llm,
    )

    if args.stdout:
        print(md)
    else:
        out_path = args.output
        if not out_path:
            from iching_bagua.hexagrams import list_hexagrams
            名A = next((n for o, n, _ in list_hexagrams() if o == 卦序A), str(卦序A))
            名B = next((n for o, n, _ in list_hexagrams() if o == 卦序B), str(卦序B))
            COMPARISONS_DIR.mkdir(parents=True, exist_ok=True)
            out_path = COMPARISONS_DIR / f"{卦序A:02d}_{名A}_vs_{卦序B:02d}_{名B}.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md, encoding="utf-8")
        print(f"已保存: {out_path}")


def series_compare_main() -> None:
    """卦系列对比：固定预设或用户指定，逐爻位对比，输出 Markdown。"""
    import argparse

    parser = argparse.ArgumentParser(description="卦系列对比：固定预设或用户指定")
    parser.add_argument(
        "series",
        nargs="?",
        default="",
        help="预设名称（上经前六卦、含坎、屯蒙需讼师比等）或卦名/卦序列表，逗号分隔",
    )
    parser.add_argument("-o", "--output", type=Path, help="输出 Markdown 文件路径")
    parser.add_argument("--no-llm", action="store_true", help="不调用 LLM 生成系列总结")
    parser.add_argument("--stdout", action="store_true", help="仅输出到 stdout")
    parser.add_argument("-d", "--hexagrams-dir", type=Path, help="卦爻辞目录")
    parser.add_argument("-l", "--list-presets", action="store_true", help="列出可用预设")
    args = parser.parse_args()

    try:
        from comparison.series import (
            PRESET_SERIES,
            build_series_comparison_md,
            compare_series,
            get_series_orders,
            COMPARISONS_DIR,
        )
    except ImportError as e:
        print(f"错误: 未安装 comparison 模块 - {e}", file=sys.stderr)
        sys.exit(1)

    if args.list_presets:
        from comparison.series import _init_trigram_presets
        _init_trigram_presets()
        print("可用预设：")
        for name, orders in PRESET_SERIES.items():
            count = len(orders)
            print(f"  {name}: {count} 卦")
        return

    if not args.series:
        print("错误: 请指定预设名称或卦系列（逗号分隔）", file=sys.stderr)
        sys.exit(1)

    # 解析 series：预设名 或 逗号分隔的卦名/卦序
    if "," in args.series:
        parts = [x.strip() for x in args.series.split(",") if x.strip()]
        卦序列表 = get_series_orders(parts, hexagrams_dir=args.hexagrams_dir)
        series_name = args.series[:50] + ("…" if len(args.series) > 50 else "")
    else:
        卦序列表 = get_series_orders(args.series, hexagrams_dir=args.hexagrams_dir)
        series_name = args.series

    if not 卦序列表:
        print(f"错误: 未解析到有效卦系列「{args.series}」", file=sys.stderr)
        sys.exit(1)

    data = compare_series(卦序列表, hexagrams_dir=args.hexagrams_dir)
    if not data:
        print("错误: 系列对比数据加载失败", file=sys.stderr)
        sys.exit(1)

    md = build_series_comparison_md(
        卦序列表,
        data=data,
        series_name=series_name,
        hexagrams_dir=args.hexagrams_dir,
        use_llm_summary=not args.no_llm,
    )

    if args.stdout:
        print(md)
    else:
        out_path = args.output
        if not out_path:
            卦名串 = "_".join(g["卦名"] for g in data.get("卦列表", [])[:5])
            if len(data.get("卦列表", [])) > 5:
                卦名串 += "等"
            COMPARISONS_DIR.mkdir(parents=True, exist_ok=True)
            out_path = COMPARISONS_DIR / f"series_{卦名串}.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md, encoding="utf-8")
        print(f"已保存: {out_path}")


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


def merge_association_main() -> None:
    """融合卦爻关联：保留原文件的原文与翻译，删除原说明，替换为 new 的说明。支持任意卦。"""
    import argparse
    parser = argparse.ArgumentParser(
        description="融合卦爻关联：用 new 的说明替换卦 md 的说明，支持任意卦（如 03_屯.md、04_蒙.md）"
    )
    parser.add_argument("original", type=Path, help="卦的 md 文件路径（如 03_屯.md、04_蒙.md）")
    parser.add_argument("new_explanations", type=Path, help="新说明文件（含核心主题、问答、总结）")
    parser.add_argument("-o", "--output", type=Path, help="输出路径，默认覆盖原文件")
    args = parser.parse_args()
    from association.merge import merge
    out = args.output or args.original
    merge(args.original, args.new_explanations, out)
    print(f"已写入: {out}")
