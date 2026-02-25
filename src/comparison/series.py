"""卦系列对比：固定系列、用户指定、逐爻位对比、LLM 脉络。"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
HEXAGRAMS_DIR = PROJECT_ROOT / "data" / "hexagrams"
COMPARISONS_DIR = PROJECT_ROOT / "data" / "comparisons"

from .relations import get_hexagrams_with_trigram, order_to_symbol
from .compare import _load_hexagram, _or_empty, _resolve_hexagram


# 固定系列预设：名称 -> 卦序列表
PRESET_SERIES: dict[str, list[int]] = {
    "上经前六卦": [1, 2, 3, 4, 5, 6],       # 乾坤屯蒙需讼
    "屯蒙需讼师比": [3, 4, 5, 6, 7, 8],
    "上经前十卦": list(range(1, 11)),
    "含坎": [],  # 动态填充
    "含离": [],
    "含乾": [],
    "含坤": [],
    "含震": [],
    "含巽": [],
    "含艮": [],
    "含兑": [],
}


def _init_trigram_presets() -> None:
    """填充含某卦的预设。"""
    for 卦名 in ["坎", "离", "乾", "坤", "震", "巽", "艮", "兑"]:
        key = f"含{卦名}"
        if key in PRESET_SERIES and not PRESET_SERIES[key]:
            PRESET_SERIES[key] = get_hexagrams_with_trigram(卦名)


def get_series_orders(
    preset_or_list: str | list,
    *,
    hexagrams_dir: Path | None = None,
) -> list[int]:
    """解析系列为卦序列表。

    Args:
        preset_or_list: 预设名称（如「上经前六卦」「含坎」）或 卦序/卦名 列表
        hexagrams_dir: 卦数据目录

    Returns:
        卦序列表（已排序）
    """
    _init_trigram_presets()

    if isinstance(preset_or_list, list):
        orders: list[int] = []
        for x in preset_or_list:
            o = _resolve_hexagram(x, hexagrams_dir) if not isinstance(x, int) else (x if 1 <= x <= 64 else None)
            if o is not None:
                orders.append(o)
        return sorted(set(orders))

    name = str(preset_or_list).strip()
    if name in PRESET_SERIES:
        return PRESET_SERIES[name][:]
    # 尝试解析为单个卦，返回 [卦序]
    o = _resolve_hexagram(name, hexagrams_dir)
    return [o] if o is not None else []


def compare_series(
    卦序列表: list[int],
    *,
    hexagrams_dir: Path | None = None,
) -> dict:
    """系列对比数据：卦辞列表、逐爻位对比。"""
    if not 卦序列表:
        return {}

    hexagrams: list[dict] = []
    for o in 卦序列表:
        d = _load_hexagram(o, hexagrams_dir)
        if d:
            hexagrams.append({"卦序": o, "data": d, "卦名": d.get("元信息", {}).get("卦名", str(o))})

    if not hexagrams:
        return {}

    # 卦辞列表
    卦辞列表: list[dict] = []
    for h in hexagrams:
        g = h["data"].get("卦辞", {})
        卦辞列表.append({
            "卦序": h["卦序"],
            "卦名": h["卦名"],
            "原文": _or_empty(g.get("原文")),
            "白话": _or_empty(g.get("白话")),
            "吉凶": _or_empty(g.get("吉凶标签")),
        })

    # 逐爻位对比：爻位序 -> [各卦该爻位数据]
    def _yao_by_order(yaos: list, 爻位序: int) -> dict | None:
        for y in yaos:
            if y.get("爻位序") == 爻位序:
                return y
        return None

    爻位对比: list[dict] = []
    for 序 in range(1, 7):
        row: dict = {"爻位序": 序, "各卦": []}
        for h in hexagrams:
            yaos = h["data"].get("爻辞", [])
            y = _yao_by_order(yaos, 序)
            if y:
                row["各卦"].append({
                    "卦序": h["卦序"],
                    "卦名": h["卦名"],
                    "爻位": y.get("爻位", ""),
                    "原文": _or_empty(y.get("原文")),
                    "白话": _or_empty(y.get("白话")),
                    "当位": y.get("当位"),
                    "吉凶": _or_empty(y.get("吉凶标签")),
                })
            else:
                row["各卦"].append({"卦序": h["卦序"], "卦名": h["卦名"], "爻位": "", "原文": "", "白话": "", "当位": None, "吉凶": ""})
        爻位对比.append(row)

    return {
        "卦列表": [{"卦序": h["卦序"], "卦名": h["卦名"]} for h in hexagrams],
        "卦辞": 卦辞列表,
        "爻位对比": 爻位对比,
    }


def build_series_comparison_md(
    卦序列表: list[int],
    data: dict | None = None,
    *,
    series_name: str = "",
    hexagrams_dir: Path | None = None,
    use_llm_summary: bool = False,
) -> str:
    """构建系列对比的 Markdown 文本。"""
    if data is None:
        data = compare_series(卦序列表, hexagrams_dir=hexagrams_dir)
    if not data:
        return "（系列对比数据加载失败）"

    卦列表 = data.get("卦列表", [])
    卦辞列表 = data.get("卦辞", [])
    爻位对比 = data.get("爻位对比", [])

    if not 卦列表:
        return "（无卦数据）"

    标题 = series_name or "、".join(g["卦名"] for g in 卦列表)
    if len(标题) > 40:
        标题 = 标题[:37] + "..."

    lines = [
        f"# 卦系列对比：{标题}",
        "",
        "## 系列概览",
        "",
    ]

    # 卦画与卦名
    symbols = " | ".join(f"**{g['卦名']}** {order_to_symbol(g['卦序'])}" for g in 卦列表)
    lines.append(symbols)
    lines.append("")

    # 卦辞对比表
    lines.extend([
        "## 卦辞对比",
        "",
        "| 卦名 | 原文 | 白话 | 吉凶 |",
        "|------|------|------|------|",
    ])
    for g in 卦辞列表:
        原文 = (g.get("原文", "") or "")[:60] + ("…" if len(g.get("原文", "")) > 60 else "")
        白话 = (g.get("白话", "") or "")[:50] + ("…" if len(g.get("白话", "")) > 50 else "")
        lines.append(f"| {g.get('卦名', '')} | {原文} | {白话} | {g.get('吉凶', '')} |")
    lines.append("")

    # 逐爻位对比表
    爻位名 = ["初", "二", "三", "四", "五", "上"]
    for i, row in enumerate(爻位对比):
        序 = row.get("爻位序", i + 1)
        lines.extend([
            f"## 第{爻位名[i]}爻对比",
            "",
        ])
        # 表头：爻位 | 卦1 | 卦2 | ...
        表头 = "| 项目 | " + " | ".join(x["卦名"] for x in row.get("各卦", [])) + " |"
        sep = "|------|" + "|".join(["------"] * len(row.get("各卦", []))) + "|"
        lines.append(表头)
        lines.append(sep)

        # 各行：爻位、原文、白话、吉凶
        for 项目, key in [("爻位", "爻位"), ("原文", "原文"), ("白话", "白话"), ("吉凶", "吉凶")]:
            cells = [x.get(key, "") for x in row.get("各卦", [])]
            lines.append("| " + 项目 + " | " + " | ".join(str(c) for c in cells) + " |")
        lines.append("")

    if use_llm_summary:
        summary = _llm_series_summary(data)
        lines.extend([
            "## 系列脉络总结",
            "",
            summary,
            "",
        ])

    return "\n".join(lines)


def _llm_series_summary(data: dict, max_tokens: int = 500) -> str:
    """LLM 生成系列演变、共性、差异的总结。"""
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

    卦列表 = data.get("卦列表", [])
    卦辞列表 = data.get("卦辞", [])
    if not 卦列表 or not 卦辞列表:
        return "（数据不足）"

    卦名串 = "、".join(g["卦名"] for g in 卦列表)
    卦辞摘要 = "\n".join(f"- {g['卦名']}：{g.get('原文', '')[:40]}…" for g in 卦辞列表[:6])

    prompt = f"""请用 2-4 段话概括《周易》以下卦系列的脉络与特点：{卦名串}

卦辞摘要：
{卦辞摘要}

要求：从卦象共性、卦辞主旨演变、爻辞取象差异等方面简要分析，指出系列内的共同主题与各自特色。语言通俗，不超过 350 字。
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
