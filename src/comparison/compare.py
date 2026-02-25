"""两卦对比：结构、卦辞、爻辞、LLM 总结。"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
HEXAGRAMS_DIR = PROJECT_ROOT / "data" / "hexagrams"
COMPARISONS_DIR = PROJECT_ROOT / "data" / "comparisons"

from .relations import (
    get_cuogua,
    get_zonggua,
    order_to_symbol,
)


def _resolve_hexagram(卦序_or_卦名, hexagrams_dir: Path | None = None) -> int | None:
    """解析卦序或卦名为卦序。"""
    d = Path(hexagrams_dir) if hexagrams_dir else HEXAGRAMS_DIR
    if not d.exists():
        return None
    try:
        n = int(卦序_or_卦名)
        if 1 <= n <= 64:
            return n
    except (ValueError, TypeError):
        pass
    for p in sorted(d.glob("*.json")):
        try:
            import json
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
            name = data.get("元信息", {}).get("卦名", "")
            if name == 卦序_or_卦名 or (卦序_or_卦名 and 卦序_or_卦名 in name):
                return data.get("元信息", {}).get("卦序")
        except Exception:
            continue
    return None


def _load_hexagram(卦序: int, hexagrams_dir: Path | None = None) -> dict | None:
    """加载卦数据。"""
    import json
    d = Path(hexagrams_dir) if hexagrams_dir else HEXAGRAMS_DIR
    for p in d.glob(f"{卦序:02d}_*.json"):
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None


def _or_empty(val) -> str:
    """空值转空字符串。"""
    if val is None:
        return ""
    s = str(val).strip()
    return s if s else ""


def compare_two_hexagrams(
    卦序A: int,
    卦序B: int,
    *,
    hexagrams_dir: Path | None = None,
) -> dict:
    """两卦对比数据。返回结构化字典。"""
    dataA = _load_hexagram(卦序A, hexagrams_dir)
    dataB = _load_hexagram(卦序B, hexagrams_dir)
    if not dataA or not dataB:
        return {}

    metaA = dataA.get("元信息", {})
    metaB = dataB.get("元信息", {})

    上卦A = metaA.get("上下卦", {}).get("上卦", "")
    下卦A = metaA.get("上下卦", {}).get("下卦", "")
    上卦B = metaB.get("上下卦", {}).get("上卦", "")
    下卦B = metaB.get("上下卦", {}).get("下卦", "")

    错卦A = get_cuogua(卦序A)
    综卦A = get_zonggua(卦序A)
    综卦B = get_zonggua(卦序B)

    # 结构对比
    structure = {
        "卦A": {"卦序": 卦序A, "卦名": metaA.get("卦名", ""), "上卦": 上卦A, "下卦": 下卦A},
        "卦B": {"卦序": 卦序B, "卦名": metaB.get("卦名", ""), "上卦": 上卦B, "下卦": 下卦B},
        "错卦关系": 错卦A == 卦序B or get_cuogua(卦序B) == 卦序A,
        "综卦关系": 综卦A == 卦序B or 综卦B == 卦序A,
    }

    # 卦辞对比
    卦辞A = dataA.get("卦辞", {})
    卦辞B = dataB.get("卦辞", {})
    guaci = {
        "卦A": {
            "原文": _or_empty(卦辞A.get("原文")),
            "白话": _or_empty(卦辞A.get("白话")),
            "彖传": _or_empty(卦辞A.get("彖传")),
            "大象传": _or_empty(卦辞A.get("大象传")),
            "吉凶": _or_empty(卦辞A.get("吉凶标签")),
        },
        "卦B": {
            "原文": _or_empty(卦辞B.get("原文")),
            "白话": _or_empty(卦辞B.get("白话")),
            "彖传": _or_empty(卦辞B.get("彖传")),
            "大象传": _or_empty(卦辞B.get("大象传")),
            "吉凶": _or_empty(卦辞B.get("吉凶标签")),
        },
    }

    # 爻辞逐爻对比（按爻位序 1-6）
    def _yao_by_order(yaos: list, 爻位序: int) -> dict | None:
        for y in yaos:
            if y.get("爻位序") == 爻位序:
                return y
        return None

    爻辞A = dataA.get("爻辞", [])
    爻辞B = dataB.get("爻辞", [])
    yaos_compare: list[dict] = []
    for 序 in range(1, 7):
        yA = _yao_by_order(爻辞A, 序)
        yB = _yao_by_order(爻辞B, 序)
        yaos_compare.append({
            "爻位序": 序,
            "卦A": {
                "爻位": yA.get("爻位", "") if yA else "",
                "原文": _or_empty(yA.get("原文")) if yA else "",
                "白话": _or_empty(yA.get("白话")) if yA else "",
                "当位": yA.get("当位") if yA is not None else None,
                "吉凶": _or_empty(yA.get("吉凶标签")) if yA else "",
            } if yA else {},
            "卦B": {
                "爻位": yB.get("爻位", "") if yB else "",
                "原文": _or_empty(yB.get("原文")) if yB else "",
                "白话": _or_empty(yB.get("白话")) if yB else "",
                "当位": yB.get("当位") if yB is not None else None,
                "吉凶": _or_empty(yB.get("吉凶标签")) if yB else "",
            } if yB else {},
        })

    return {
        "structure": structure,
        "卦辞": guaci,
        "爻辞": yaos_compare,
    }


def build_comparison_md(
    卦序A: int,
    卦序B: int,
    data: dict | None = None,
    *,
    hexagrams_dir: Path | None = None,
    use_llm_summary: bool = False,
) -> str:
    """构建两卦对比的 Markdown 文本。"""
    if data is None:
        data = compare_two_hexagrams(卦序A, 卦序B, hexagrams_dir=hexagrams_dir)
    if not data:
        return "（对比数据加载失败）"

    structure = data.get("structure", {})
    guaci = data.get("卦辞", {})
    yaos = data.get("爻辞", [])

    名A = structure.get("卦A", {}).get("卦名", str(卦序A))
    名B = structure.get("卦B", {}).get("卦名", str(卦序B))
    上A = structure.get("卦A", {}).get("上卦", "")
    下A = structure.get("卦A", {}).get("下卦", "")
    上B = structure.get("卦B", {}).get("上卦", "")
    下B = structure.get("卦B", {}).get("下卦", "")

    lines = [
        f"# {名A} vs {名B} 对比",
        "",
        f"**{名A}** {order_to_symbol(卦序A)} | **{名B}** {order_to_symbol(卦序B)}",
        "",
        "## 结构对比",
        "",
        f"| 项目 | {名A} | {名B} |",
        "|------|------|------|",
        f"| 上下卦 | {上A}上{下A}下 | {上B}上{下B}下 |",
        f"| 错卦关系 | {'是' if structure.get('错卦关系') else '否'} | |",
        f"| 综卦关系 | {'是' if structure.get('综卦关系') else '否'} | |",
        "",
        "## 卦辞对比",
        "",
        "### 原文",
        "",
        f"| {名A} | {名B} |",
        "|------|------|",
        f"| {guaci.get('卦A', {}).get('原文', '')} | {guaci.get('卦B', {}).get('原文', '')} |",
        "",
        "### 白话",
        "",
        f"| {名A} | {名B} |",
        "|------|------|",
        f"| {guaci.get('卦A', {}).get('白话', '')} | {guaci.get('卦B', {}).get('白话', '')} |",
        "",
        "### 彖传",
        "",
        f"| {名A} | {名B} |",
        "|------|------|",
        f"| {guaci.get('卦A', {}).get('彖传', '') or '暂无'} | {guaci.get('卦B', {}).get('彖传', '') or '暂无'} |",
        "",
        "### 大象传",
        "",
        f"| {名A} | {名B} |",
        "|------|------|",
        f"| {guaci.get('卦A', {}).get('大象传', '') or '暂无'} | {guaci.get('卦B', {}).get('大象传', '') or '暂无'} |",
        "",
        "### 吉凶",
        "",
        f"| {名A} | {名B} |",
        "|------|------|",
        f"| {guaci.get('卦A', {}).get('吉凶', '')} | {guaci.get('卦B', {}).get('吉凶', '')} |",
        "",
        "## 爻辞逐爻对比",
        "",
    ]

    爻位名 = ["初", "二", "三", "四", "五", "上"]
    for i, row in enumerate(yaos):
        序 = row.get("爻位序", i + 1)
        a = row.get("卦A", {})
        b = row.get("卦B", {})
        当A = "✓" if a.get("当位") else ("✗" if a.get("当位") is False else "-")
        当B = "✓" if b.get("当位") else ("✗" if b.get("当位") is False else "-")
        lines.extend([
            f"### 第{爻位名[i]}爻",
            "",
            f"| 项目 | {名A} | {名B} |",
            "|------|------|------|",
            f"| 爻位 | {a.get('爻位', '')} | {b.get('爻位', '')} |",
            f"| 当位 | {当A} | {当B} |",
            f"| 原文 | {a.get('原文', '')} | {b.get('原文', '')} |",
            f"| 白话 | {a.get('白话', '')} | {b.get('白话', '')} |",
            f"| 吉凶 | {a.get('吉凶', '')} | {b.get('吉凶', '')} |",
            "",
        ])

    if use_llm_summary:
        summary = _llm_compare_summary(名A, 名B, data)
        lines.extend([
            "## 对比总结",
            "",
            summary,
            "",
        ])

    return "\n".join(lines)


def _llm_compare_summary(卦名A: str, 卦名B: str, data: dict, max_tokens: int = 400) -> str:
    """LLM 生成两卦对比的自然语言总结。"""
    import os
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        return "（需设置 DEEPSEEK_API_KEY 以生成 LLM 总结）"
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=api_key,
            base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        )
    except ImportError:
        return "（需安装 openai 库）"

    guaci = data.get("卦辞", {})
    a_orig = guaci.get("卦A", {}).get("原文", "")
    b_orig = guaci.get("卦B", {}).get("原文", "")
    structure = data.get("structure", {})

    prompt = f"""请用 2-4 段话概括《周易》{卦名A}卦与{卦名B}卦的对比要点。

已知信息：
- {卦名A}：{structure.get('卦A', {}).get('上卦', '')}上{structure.get('卦A', {}).get('下卦', '')}下，卦辞「{a_orig[:50]}...」
- {卦名B}：{structure.get('卦B', {}).get('上卦', '')}上{structure.get('卦B', {}).get('下卦', '')}下，卦辞「{b_orig[:50]}...」
- 错卦关系：{structure.get('错卦关系', False)}
- 综卦关系：{structure.get('综卦关系', False)}

要求：从卦象结构、卦辞主旨、爻辞取象差异等方面简要对比，语言通俗，不要超过 300 字。
"""
    try:
        r = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=max_tokens,
        )
        return (r.choices[0].message.content or "").strip()
    except Exception:
        return "（LLM 总结生成失败）"
